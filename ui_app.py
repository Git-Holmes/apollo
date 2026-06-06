
import tkinter as tk
from threading import Thread
import pythoncom
import time

from scraper import run_scraper
from api_scraper import fetch_apollo_data
from write_to_tvm import write_to_tvm

running = False


def run_pipeline():
    try:
        pythoncom.CoInitialize()

        total_start = time.time()

        # ✅ STEP 1: SELENIUM (login + refresh + token + timestamp)
        t1 = time.time()
        token, timestamp = run_scraper()
        print(f"⏱ Selenium + Token + Timestamp: {time.time() - t1:.2f}s")

        # ✅ STEP 2: API CALL
        t2 = time.time()
        df = fetch_apollo_data(token)
        print(f"⏱ API Fetch: {time.time() - t2:.2f}s")

        # ✅ STEP 3: EXCEL WRITE
        t3 = time.time()
        write_to_tvm(df, timestamp)
        print(f"⏱ Excel Write: {time.time() - t3:.2f}s")

        # ✅ TOTAL TIME
        print(f"🚀 TOTAL RUNTIME: {time.time() - total_start:.2f}s")
        print("✅ Pipeline complete")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        pythoncom.CoUninitialize()


def start_pipeline():
    global running

    if running:
        print("⚠️ Already running...")
        return

    running = True

    def wrapper():
        global running
        run_pipeline()
        running = False

    Thread(target=wrapper).start()


root = tk.Tk()
root.title("Apollo Tool")
root.geometry("350x200")

tk.Button(root, text="Get Apollo Data", command=start_pipeline).pack(pady=20)

root.mainloop()
