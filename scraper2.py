
from playwright.sync_api import sync_playwright
import time
import os
from credentials import get_credentials

DOCK_URL = "https://apollo.prod.target.com/warehouse/outbound/dock-status?location=593"
STATE_FILE = "state.json"


def run_scraper():

    EMAIL, USER_ID, PASSWORD = get_credentials()

    with sync_playwright() as p:

        # ✅ Decide headless mode based on session existence
        first_run = not os.path.exists(STATE_FILE)

        browser = p.chromium.launch(
            headless=not first_run  # ✅ headless after login
        )

        context = browser.new_context(
            storage_state=STATE_FILE if not first_run else None
        )

        page = context.new_page()

        print("🌐 Navigating to Apollo...")
        page.goto(DOCK_URL)

        # ✅ Detect if login required
        if "login" in page.url or "iam.target.com" in page.url:
            print("🔑 Login required")

            # ✅ WAIT for IAM popup/login form
            try:
                page.wait_for_selector("input#loginID", timeout=20000)
            except:
                print("⚠️ Waiting extra time for IAM popup...")
                time.sleep(12)

            # ✅ Fill login
            try:
                page.fill("#loginID", USER_ID)
                page.fill("#password", PASSWORD)
                page.click("#submit-button")
                print("✅ Login submitted")
            except Exception as e:
                print(f"⚠️ Login field issue: {e}")

            # ✅ Wait for Apollo to load
            page.wait_for_load_state("networkidle")
            time.sleep(3)

            print("✅ Login complete")

            # ✅ Save session
            context.storage_state(path=STATE_FILE)
            print("💾 Session saved")

        else:
            print("✅ Already logged in (session reused)")

        # ✅ Refresh to trigger backend update
        print("🔄 Refreshing page...")
        page.reload()
        page.wait_for_load_state("networkidle")

        time.sleep(2)

        # ✅ Extract timestamp
        try:
            element = page.locator("text=Data Refreshed").first
            text = element.inner_text()
            print(f"🕒 Raw timestamp: {text}")

            timestamp = text.replace("Data Refreshed", "").strip()
        except:
            timestamp = ""
            print("⚠️ Timestamp not found")

        # ✅ Extract token from localStorage
        token = page.evaluate("""
            () => {
                return localStorage.getItem("auth_access_token");
            }
        """)

        if not token:
            raise Exception("❌ auth_access_token not found")

        print("✅ Token retrieved")

        browser.close()

        return token, timestamp
