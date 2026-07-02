
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from credentials import get_credentials

DOCK_URL = "https://apollo.prod.target.com/warehouse/outbound/dock-status?location=593"


def create_driver():
    session_path = r"C:\Temp\ApolloSession"
    os.makedirs(session_path, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={session_path}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")

    return webdriver.Chrome(options=chrome_options)




def login_if_needed(driver, wait):
    driver.get(DOCK_URL)
    time.sleep(2)

    print("🔐 Checking login state...")

    # ✅ Check token FIRST instead of URL
    try:
        storage = driver.execute_script("""
            let items = {};
            for (let i = 0; i < localStorage.length; i++) {
                let key = localStorage.key(i);
                items[key] = localStorage.getItem(key);
            }
            return items;
        """)

        if "auth_access_token" in storage and storage["auth_access_token"]:
            print("✅ Token found — already logged in")
            return

    except:
        pass

    print("🔑 No token found — login required")

    # ✅ WAIT for IAM popup to clear
    print("⏳ Waiting for IAM popup to clear...")
    time.sleep(12)  # keep simple since you measured ~11s

    EMAIL, USER_ID, PASSWORD = get_credentials()

    # ✅ QUICK CHECK instead of long wait
    elements = driver.find_elements(By.XPATH, "//input[@type='email']")
    if elements:
        elements[0].send_keys(EMAIL)
        driver.find_element(By.XPATH, "//button").click()
        print("✅ Email submitted")

    elements = driver.find_elements(By.ID, "loginID")
    if elements:
        username = elements[0]
        password = driver.find_element(By.ID, "password")

        username.clear()
        username.send_keys(USER_ID)

        password.clear()
        password.send_keys(PASSWORD)

        driver.find_element(By.ID, "submit-button").click()

        print("✅ Login submitted")

    print("⏳ Waiting for Apollo to load...")
    wait.until(lambda d: "apollo.prod.target.com" in d.current_url)

    time.sleep(3)

    print("✅ Login flow complete")



# ✅ ✅ TIMESTAMP EXTRACTOR
def get_refresh_timestamp(driver):
    try:
        element = driver.find_element(By.XPATH, "//*[contains(text(), 'Data Refreshed')]")
        text = element.text.strip()

        print(f"🕒 Raw timestamp: {text}")

        clean = text.replace("Data Refreshed", "").strip()

        return clean

    except Exception as e:
        print(f"⚠️ Could not find timestamp: {e}")
        return ""


# ✅ ✅ TOKEN EXTRACTOR
def get_token(driver):
    storage = driver.execute_script("""
        let items = {};
        for (let i=0;i<localStorage.length;i++){
            let k = localStorage.key(i);
            items[k] = localStorage.getItem(k);
        }
        return items;
    """)

    if "auth_access_token" in storage:
        print("✅ Found token in key: auth_access_token")
        return storage["auth_access_token"]

    raise Exception("❌ auth_access_token not found")


# ✅ ✅ MAIN RUN FUNCTION
def run_scraper():
    driver = create_driver()
    wait = WebDriverWait(driver, 30)

    login_if_needed(driver, wait)

    token = get_token(driver)
    timestamp = get_refresh_timestamp(driver)

    driver.quit()

    return token, timestamp
