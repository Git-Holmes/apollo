
import requests
import pandas as pd
import urllib3
from datetime import datetime
import pytz

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_URL = "https://apollo-bff-proxy.prod.target.com/proxy/warehouse-data-services/shipping_status/v3"


# ✅ ✅ TIMESTAMP FORMATTER (SAFE)
def format_timestamp(ts):
    if not ts or not isinstance(ts, str):
        return ""

    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        dt = dt.astimezone(pytz.timezone("US/Pacific"))
        return dt.strftime("%b %d, %I:%M %p PDT").lstrip("0")
    except:
        return ""


# ✅ ✅ MAIN API FUNCTION
def fetch_apollo_data(token, location_id=593):

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "x-api-key": "8fcacfb14c379f6240ec6d44284aaf01cb770108",
        "x-origin-id": "593",
        "origin": "https://apollo.prod.target.com",
        "referer": "https://apollo.prod.target.com/",
        "user-agent": "Mozilla/5.0",
        "x-support-group-info": "Assignment Group: Warehouse Data Services, CI: CI12805062"
    }

    params = {
        "location_id": location_id,
        "get_load_zone": "true"
    }

    response = requests.get(API_URL, headers=headers, params=params, verify=False)

    if response.status_code != 200:
        raise Exception(f"❌ API call failed: {response.status_code}")

    raw_data = response.json()

    # ✅ Flatten nested list structure
    data = []
    for block in raw_data:
        if isinstance(block, list):
            data.extend(block)
        else:
            data.append(block)

    rows = []

    # ✅ Parse JSON
    for item in data:
        if not isinstance(item, dict):
            continue

        try:
            lp_list = item.get("load_progress_distribution_center", [])
            lp = lp_list[0] if isinstance(lp_list, list) and lp_list else {}

            trailer = item.get("trailer_data", {})

            conveyable = lp.get("conveyable", {})
            non_conveyable = lp.get("non_conveyable", {})
            over_pack = lp.get("over_pack", {})

            rows.append({
                "Door": item.get("door"),
                "Store": item.get("store"),
                "Trailer": trailer.get("id"),

                "Operational Cut Time": item.get("cuttoff_date_time"),

                "Coloaded": "Yes" if trailer.get("is_co_loaded") else "No",

                "Open Time": trailer.get("opened_at"),
                "Age": trailer.get("open_duration"),

                "Weight": lp.get("total_weight"),
                "Cube %": lp.get("fill_percentage"),

                "Trailer Size": trailer.get("size"),
                "Total Cartons": lp.get("total_container_count"),

                "Con": conveyable.get("count"),
                "NonCon": non_conveyable.get("count"),
                "Overpack": over_pack.get("count"),
            })

        except Exception as e:
            print(f"⚠️ Skipping row: {e}")

    df = pd.DataFrame(rows)

    # ✅ Sort by Total Cartons (largest first)
    df = df.sort_values(by="Total Cartons", ascending=False).reset_index(drop=True)

    # ✅ Format timestamps safely
    df["Operational Cut Time"] = df["Operational Cut Time"].apply(format_timestamp)
    df["Open Time"] = df["Open Time"].apply(format_timestamp)

    print("✅ API data mapped successfully")

    return df
