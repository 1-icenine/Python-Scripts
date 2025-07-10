from collections import defaultdict
from datetime import datetime

def count_snapshots_by_date(file_path):
    counts = defaultdict(int)

    with open(file_path, "r") as f:
        for line in f:
            url = line.strip()
            # Extract the timestamp part after "/web/"
            try:
                parts = url.split("/web/")
                if len(parts) < 2:
                    continue
                timestamp_part = parts[1].split("/")[0]
                # Parse timestamp to date
                dt = datetime.strptime(timestamp_part, "%Y%m%d%H%M%S")
                # Windows-friendly day format (no %-d)
                date_str = dt.strftime("%B %d, %Y").replace(" 0", " ")
            except Exception:
                continue

            counts[date_str] += 1

    # Sort dates
    sorted_dates = sorted(counts, key=lambda d: datetime.strptime(d, "%B %d, %Y"))

    previous_month = None
    for date_str in sorted_dates:
        dt = datetime.strptime(date_str, "%B %d, %Y")
        current_month = dt.strftime("%Y-%m")
        if previous_month and current_month != previous_month:
            print("=====")  # Separator for new month
        print(f"{date_str}: {counts[date_str]} links counted")
        previous_month = current_month

if __name__ == "__main__":
    file_path = "wayback_snapshot_urls.txt"
    count_snapshots_by_date(file_path)
