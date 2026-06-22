import os
import re
import sys
import time
from datetime import datetime

from playwright.sync_api import sync_playwright

LOGIN_URL = "https://vectorblast.vip/user/login"
HOME_URL = "https://vectorblast.vip/home"
QUANTIFY_URL = "https://vectorblast.vip/quantify"

REMAINING_RE = re.compile(r"수량화\s*가능한\s*시간[\s\S]{0,30}?(\d+)\s*/\s*5")
MODAL_TEXT_HINTS = ["양자화 시작 중", "실행 패널 프로세스"]
CLOSE_SELECTORS = ['[class*="close"]', '[aria-label="close"]', '[aria-label="Close"]']

MODAL_WAIT_TIMEOUT_MS = 90_000


def log(msg):
    print(f"[{datetime.now().isoformat(timespec='seconds')}] {msg}")


def close_ad_popup(page):
    page.wait_for_timeout(6000)
    for selector in CLOSE_SELECTORS:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=1000):
                locator.click()
                log(f"Closed ad popup via selector: {selector}")
                return
        except Exception:
            continue
    log("No ad popup found to close (or already closed)")


def login(page, country_code, phone_number, password):
    page.goto(LOGIN_URL, wait_until="networkidle")

    phone_input = page.get_by_placeholder("Enter your phone number")
    phone_input.wait_for(state="visible", timeout=30_000)

    if country_code != "+82":
        try:
            code_dropdown = page.get_by_text(re.compile(r"^\+\d+$")).first
            code_dropdown.click(timeout=5_000)
            # The dropdown's search box matches on digits only, without the "+" prefix.
            search_digits = country_code.lstrip("+")
            page.get_by_role("textbox").last.fill(search_digits, timeout=5_000)
            page.get_by_text(country_code, exact=True).click(timeout=5_000)
        except Exception:
            log(f"Could not change country code dropdown to {country_code}, leaving default")

    phone_input.fill(phone_number)

    password_input = page.get_by_placeholder("Enter your password")
    password_input.fill(password)

    submit_button = page.locator("form button, form >> button").last
    try:
        submit_button.click(timeout=5_000)
    except Exception:
        log("Submit button not found, falling back to Enter key")
        password_input.press("Enter")

    page.wait_for_url(re.compile(r".*/home"), timeout=30_000)
    log("Logged in successfully")


def read_remaining_count(page):
    content = page.content()
    match = REMAINING_RE.search(content)
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

        login(page, country_code, phone_number, password)
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
