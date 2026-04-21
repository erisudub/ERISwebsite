import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pandas as pd

cred = credentials.Certificate("service_account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

months = [
    ("2024-10-15", "2024-11-01"),  # 0 — partial October 2024
    ("2024-11-01", "2024-12-01"),  # 1 — November 2024
    ("2024-12-01", "2025-01-01"),  # 2 — December 2024
    ("2025-01-01", "2025-02-01"),  # 3 — January 2025
    ("2025-02-01", "2025-03-01"),  # 4 — February 2025
    ("2025-03-01", "2025-04-01"),  # 5 — March 2025
    ("2025-04-01", "2025-05-01"),  # 6 — April 2025
    ("2025-05-01", "2025-06-01"),  # 7 — May 2025
    ("2025-06-01", "2025-07-01"),  # 8 — June 2025
    ("2025-07-01", "2025-08-01"),  # 9 — July 2025
    ("2025-08-01", "2025-09-01"),  # 10 — August 2025
    ("2025-09-01", "2025-10-01"),  # 11 — September 2025
    ("2025-10-01", "2025-11-01"),  # 12 — October 2025
    ("2025-11-01", "2025-12-01"),  # 13 — November 2025
    ("2025-12-01", "2026-01-01"),  # 14 — December 2025
]

# ← Change this each day (0 today, 1 tomorrow, etc.)
MONTH_INDEX = 0

start_str, end_str = months[MONTH_INDEX]
start_ms = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
end_ms   = int(datetime.strptime(end_str,   "%Y-%m-%d").timestamp() * 1000)

print(f"Fetching {start_str} to {end_str}...")

data = []
for doc in db.collection("CTD_Data").stream():
    d = doc.to_dict()
    try:
        ts = d.get("date", {}).get("$date")
        if ts is None or not (start_ms <= ts < end_ms):
            continue
        data.append({
            "date":         datetime.fromtimestamp(ts / 1000),
            "instrument":   d.get("instrument"),
            "lat":          d.get("lat"),
            "lon":          d.get("lon"),
            "depth1":       d.get("depth1"),
            "oxygen":       d.get("oxygen"),
            "conductivity": d.get("conductivity"),
            "par":          d.get("par"),
            "pressure":     d.get("pressure"),
            "salinity":     d.get("salinity"),
            "temperature":  d.get("temperature"),
            "turbidity":    d.get("turbidity"),
        })
    except Exception as e:
        print(f"Skipping: {e}")

if data:
    new_df = pd.DataFrame(data).sort_values("date")
    
    # Append to existing CSV
    existing_df = pd.read_csv("ERIS_data_2015-2024.csv")
    combined = pd.concat([existing_df, new_df], ignore_index=True)
    combined.drop_duplicates(subset=["date", "instrument"], inplace=True)
    combined.sort_values("date", inplace=True)
    combined.to_csv("ERIS_data_2015-2024.csv", index=False)
    print(f"Appended {len(new_df)} records. Total: {len(combined)}")
else:
    print("No records found for this period.")