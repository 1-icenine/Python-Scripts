import os
import pandas as pd

def fix1():
    # Load CSV
    csv_filename = "eci_2025-06-23_to_2025-07-07.csv"
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)
    df = pd.read_csv(csv_path)

    # Fix GMT_capture_time column by replacing '-' with ':'
    df['GMT_capture_time'] = df['GMT_capture_time'].str.replace('-', ':')

    # Optional: verify the change
    print(df[['capture_date', 'GMT_capture_time']].head())

    # Save back to the same CSV (overwrite)
    df.to_csv(csv_path, index=False)
    print(f"✅ Fixed GMT_capture_time format and saved to {csv_path}")

def fix2():
    # Load the CSV
    csv_filename = "eci_2024-07-31_to_2025-07-07.csv"
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_filename)

    df = pd.read_csv(csv_path)

    # Fix capture_date to YYYY-MM-DD format
    df['capture_date'] = pd.to_datetime(df['capture_date'], errors='coerce').dt.strftime('%Y-%m-%d')

    # Fix GMT_capture_time by replacing dashes with colons (if needed)
    # If your times already use colons, you can skip this step
    if df['GMT_capture_time'].str.contains('-').any():
        df['GMT_capture_time'] = df['GMT_capture_time'].str.replace('-', ':')

    # Save back to CSV (overwrite or new file)
    df.to_csv(csv_path, index=False)
    print(f"✅ Fixed date and time formats saved to CSV.")

fix2()