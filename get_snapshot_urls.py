from waybackpy import WaybackMachineCDXServerAPI
from datetime import timedelta, datetime
import time
import os

# === Setup ===
url = "https://citizens-initiative.europa.eu/initiatives/details/2024/000007_en"
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# === Snapshot fetching ===
start_time = time.time()
cdx_api = WaybackMachineCDXServerAPI(url, user_agent)
snapshots = list(cdx_api.snapshots())
duration = time.time() - start_time

# === Extract snapshot dates ===
def extract_date(snapshot):
    timestamp = snapshot.archive_url.split("/")[4]  # e.g. 20240612133710
    return datetime.strptime(timestamp[:8], "%Y%m%d")  # extract YYYYMMDD

# === Generate filename and directory path ===
if snapshots:
    snapshot_dates = [extract_date(s) for s in snapshots]
    latest = max(snapshot_dates)
    earliest = min(snapshot_dates)
    filename = f"snapshotLinks_{earliest.date()}_to_{latest.date()}.txt"
else:
    filename = "snapshotLinks_NO_SNAPSHOTS.txt"

# === File destination ===
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_dir = os.path.join(base_dir, "Snapshot Links")
os.makedirs(csv_dir, exist_ok=True)  # Create folder if it doesn't exist
full_path = os.path.join(csv_dir, filename)

# === Write output ===
with open(full_path, "w", encoding="utf-8") as f:
    for snapshot in snapshots:
        f.write(snapshot.archive_url + "\n")

print(f"\nSaved {len(snapshots)} snapshots to '{full_path}'")
print("\nTime taken: " + str(timedelta(seconds=round(duration))) + "\n")
