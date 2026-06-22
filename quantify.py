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


def login(page, email, password):
    page.goto(LOGIN_URL)
    page.fill('input[type="email"], input[name="email"], input[type="text"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
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
    email = os.environ["VB_EMAIL"]
    password = os.environ["VB_PASSWORD"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login(page, email, password)
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
