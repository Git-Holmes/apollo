import tkinter as tk
from threading import Thread
import pythoncom
import time
import pandas as pd
import json
import os

from scraper import run_scraper
from api_scraper import fetch_apollo_data
from write_to_tvm import write_to_tvm

running = False

SETTINGS_FILE = "settings.json"


def load_threshold():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)

            return int(settings.get("threshold", 2300))

    except Exception as e:
        print(f"⚠️ Could not load settings: {e}")

    return 2300


def save_threshold(value):
    try:
        settings = {
            "threshold": int(value)
        }

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

    except Exception as e:
        print(f"⚠️ Could not save settings: {e}")

def run_pipeline():
    alert_count = 0
    alert_df = pd.DataFrame()
    timestamp = ""

    try:
        pythoncom.CoInitialize()

        total_start = time.time()

        # ✅ STEP 1: SELENIUM (login + refresh + token + timestamp)
        t1 = time.time()
        token, timestamp = run_scraper()
        print(f"⏱ Selenium + Token + Timestamp: {time.time() - t1:.2f}s")

        # ✅ STEP 2: API CALL
        t2 = time.time()
        df, api_timestamp = fetch_apollo_data(token)

        # ✅ API timestamp is now source of truth
        if api_timestamp:
            timestamp = api_timestamp

        print(f"⏱ API Fetch: {time.time() - t2:.2f}s")



        
        try:
            threshold = int(threshold_entry.get())

            save_threshold(threshold)

        except ValueError:
            alert_label.config(
                text="❌ Threshold must be a number",
                fg="red"
            )

            return 0, pd.DataFrame(), timestamp, 2300
        
        
        # ✅ STEP 3: EXCEL WRITE
        t3 = time.time()
        write_to_tvm(df, timestamp, threshold)
        print(f"⏱ Excel Write: {time.time() - t3:.2f}s")



        alert_df = df[df["Total Cartons"] >= threshold]
        alert_count = len(alert_df)

        if alert_count > 0:
            print(f"🚨 {alert_count} trailers reached threshold!")

            for _, row in alert_df.iterrows():
                print(
                    f"Store {row['Store']} → "
                    f"{row['Total Cartons']} cartons"
                )

        else:
            print("✅ No trailers at threshold")

        print(f"🚀 TOTAL RUNTIME: {time.time() - total_start:.2f}s")
        print("✅ Pipeline complete")

    except Exception as e:
        print(f"❌ Error: {e}")

    finally:
        pythoncom.CoUninitialize()

    return alert_count, alert_df, timestamp, threshold


def start_pipeline():
    global running

    if running:
        print("⚠️ Already running...")
        return

    running = True

    def wrapper():
        global running

        try:
            alert_count, alert_df, timestamp, threshold = run_pipeline()

            timestamp_label.config(
                text=f"Last Updated: {timestamp}"
            )

            if alert_count > 0:

                alert_label.config(
                    text=f"🚨 {alert_count} trailers above {threshold}",
                    fg="red"
                )

                lines = []

                for _, row in alert_df.iterrows():
                    lines.append(
                        f"Store {str(row['Store']).ljust(4)} | "
                        f"Door D-{str(row['Door']).zfill(3)} | "
                        f"{row['Total Cartons']} cartons"
                    )

                details_text.config(state="normal")

                details_text.delete("1.0", tk.END)

                details_text.insert(
                    tk.END,
                    "\n".join(lines)
                )

                details_text.config(state="disabled")

                print(f"🚨 UI ALERT: {alert_count} trailers ready")

            else:

                alert_label.config(
                    text=f"✅ No trailers above {threshold}",
                    fg="green"
                )

                details_text.config(state="normal")

                details_text.delete("1.0", tk.END)

                details_text.config(state="disabled")

        except Exception as e:
            print(f"❌ UI Error: {e}")

        finally:
            running = False

    Thread(target=wrapper).start()

saved_threshold = load_threshold()

root = tk.Tk()
root.title("TVM Tool")
root.geometry("500x450")
root.minsize(500, 450)

# ✅ TITLE
title_label = tk.Label(
    root,
    text="Apollo Trailer Monitor",
    font=("Arial", 14, "bold")
)
title_label.pack(pady=10)

# ✅ LAST UPDATED
timestamp_label = tk.Label(
    root,
    text="Last Updated: --",
    font=("Arial", 9)
)
timestamp_label.pack()

# ✅ THRESHOLD
threshold_frame = tk.Frame(root)
threshold_frame.pack(pady=(0, 10))

tk.Label(
    threshold_frame,
    text="Threshold:"
).pack(side="left")

threshold_entry = tk.Entry(
    threshold_frame,
    width=8
)
threshold_entry.pack(side="left", padx=5)

threshold_entry.insert(0, str(saved_threshold))

tk.Label(
    threshold_frame,
    text="cartons"
).pack(side="left")

# ✅ ALERT LABEL
alert_label = tk.Label(
    root,
    text="✅ No trailers at threshold",
    fg="green"
)
alert_label.pack(pady=10)

# ✅ ALERT DETAILS FRAME
details_frame = tk.Frame(root)
details_frame.pack(fill="both", expand=True, padx=10, pady=5)

# ✅ Add Scrollable Text Area
scrollbar = tk.Scrollbar(details_frame)
scrollbar.pack(side="right", fill="y")

details_text = tk.Text(
    details_frame,
    height=10,
    width=50,
    wrap="word",
    font=("Arial", 9)
)

details_text.pack(
    side="left",
    fill="both",
    expand=True
)

details_text.config(
    yscrollcommand=scrollbar.set
)

scrollbar.config(
    command=details_text.yview
)

details_text.config(state="disabled")

# ✅ BUTTON
tk.Button(
    root,
    text="Get Apollo Data",
    command=start_pipeline
).pack(side="bottom", pady=10)

root.mainloop()