import os
import re
import sys
import time
from datetime import datetime

from playwright.sync_api import sync_playwright

LOGIN_URL = "https://vectorblast.vip/user/login"
HOME_URL = "https://vectorblast.vip/home"
QUANTIFY_URL = "https://vectorblast.vip/quantify"

REMAINING_LABEL_TEXT = "Today's Quantifiable Count"
MODAL_TEXT_HINTS = ["VectorBlast Run Panel Process"]
CLOSE_SELECTORS = ["i.van-icon-cross"]

MODAL_WAIT_TIMEOUT_MS = 90_000


def log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")


def close_ad_popup(page):
    # The "Invitation Event" popup loads its image from S3, so it can appear a
    # few seconds after /home settles. Poll for the close icon rather than
    # taking a single snapshot after a fixed wait. Close icon (confirmed DOM):
    # <i class="van-badge__wrapper van-icon van-icon-cross">, which sits outside
    # the div.popup-con body.
    deadline = time.time() + 15
    while time.time() < deadline:
        for selector in CLOSE_SELECTORS:
            try:
                locator = page.locator(selector).first
                if locator.is_visible(timeout=500):
                    locator.click()
                    log(f"Closed ad popup via selector: {selector}")
                    return
            except Exception:
                continue
        page.wait_for_timeout(1000)
    log("No ad popup found to close (or already closed)")


def debug_shot(page, name):
    """Save a screenshot for post-mortem inspection via the workflow artifact."""
    try:
        page.screenshot(path=f"debug_{name}.png")
        log(f"Saved debug screenshot debug_{name}.png")
    except Exception as exc:
        log(f"Could not save debug screenshot {name}: {exc}")


def select_country_code(page, country_code):
    """Open the country-code popup, search, and pick the matching entry.

    The field defaults to "+--" (nothing selected) and must always be set.
    The popup markup is:
        div.popup-con > div.search-con > input.inp[placeholder="Search"]
                      > div.list > div.item > div.txt  (e.g. "대한민국 (+82)")
    """
    search_digits = country_code.lstrip("+")

    page.locator("div.set_area").click(timeout=5_000)
    debug_shot(page, "1_popup_open")

    search_box = page.get_by_placeholder("Search")
    search_box.wait_for(state="visible", timeout=5_000)
    search_box.fill(search_digits, timeout=5_000)
    debug_shot(page, "2_searched")

    # Scope to the popup's result list so we don't match stray ".item" nodes
    # elsewhere on the page. Each result's text is like "대한민국 (+82)".
    option = page.locator("div.list div.item").filter(has_text=country_code).first
    option.wait_for(state="visible", timeout=5_000)
    option.click(timeout=5_000)
    debug_shot(page, "3_after_select")

    # Verify the selection actually took effect; "+--" means it did not.
    selected = page.locator("div.set_area").inner_text().strip()
    log(f"Country code field now reads: {selected!r}")
    if search_digits not in selected:
        raise RuntimeError(
            f"Country code selection failed: field shows {selected!r}, "
            f"expected to contain {search_digits!r}"
        )


def login(page, country_code, phone_number, password):
    page.goto(LOGIN_URL, wait_until="networkidle")

    phone_input = page.get_by_placeholder("Enter your phone number")
    phone_input.wait_for(state="visible", timeout=30_000)

    select_country_code(page, country_code)

    phone_input.fill(phone_number)

    password_input = page.get_by_placeholder("Enter your password")
    password_input.fill(password)
    debug_shot(page, "4_filled")

    # The submit control is a div, not a <button>: <div class="submit-btn on">
    # wrapping an arrow <img>. Click it directly.
    page.locator("div.submit-btn").click(timeout=5_000)

    page.wait_for_url(re.compile(r".*/home"), timeout=30_000)
    log("Logged in successfully")


def read_remaining_count(page):
    """Read the "N/5" value from div.val, located via the div.name label.

    Confirmed real DOM:
        <div class="name">Today's Quantifiable Count</div>
        <div class="val">5/5</div>
    Label and value are separate sibling divs, not one contiguous string.
    """
    name_locator = page.locator("div.name", has_text=REMAINING_LABEL_TEXT).first
    try:
        name_locator.wait_for(state="visible", timeout=10_000)
    except Exception:
        return None

    val_locator = name_locator.locator("xpath=following-sibling::div[contains(@class,'val')][1]")
    try:
        val_text = val_locator.inner_text(timeout=5_000).strip()
    except Exception:
        return None

    match = re.match(r"(\d+)\s*/\s*\d+", val_text)
    if not match:
        return None
    return int(match.group(1))


def wait_for_modal_to_close(page):
    deadline = time.time() + MODAL_WAIT_TIMEOUT_MS / 1000
    while time.time() < deadline:
        content = page.content()
        if not any(hint in content for hint in MODAL_TEXT_HINTS):
            return True
        page.wait_for_timeout(2000)
    return False


def main():
    country_code = os.environ["VB_ID_CODE"]
    phone_number = os.environ["VB_ID_PHONENUMBER"]
    password = os.environ["VB_PASSWORD"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            login(page, country_code, phone_number, password)
        except Exception:
            page.screenshot(path="login_failure.png")
            log("Login failed, saved screenshot to login_failure.png")
            browser.close()
            raise

        close_ad_popup(page)

        page.goto(QUANTIFY_URL)
        page.wait_for_load_state("networkidle")

        remaining_before = read_remaining_count(page)
        log(f"Remaining count before: {remaining_before}")

        if remaining_before is None:
            log("Could not read remaining count, aborting")
            browser.close()
            sys.exit(1)

        if remaining_before <= 0:
            log("No remaining quantification slots today, exiting")
            browser.close()
            return

        page.click("div.start-btn")
        log("Clicked start-btn")

        modal_closed = wait_for_modal_to_close(page)
        if not modal_closed:
            log("Modal did not close within timeout")

        page.reload()
        page.wait_for_load_state("networkidle")
        remaining_after = read_remaining_count(page)
        log(f"Remaining count after: {remaining_after}")

        if remaining_after is not None and remaining_after < remaining_before:
            log("Success: remaining count decreased")
        else:
            log("Warning: remaining count did not decrease")

        browser.close()


if __name__ == "__main__":
    main()
