import os
import pandas as pd
import matplotlib.pyplot as plt

# Retrieve directory where my script is located
csv_filename = "eci_2024-07-31_to_2025-07-07.csv"
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CSVs", csv_filename)
df = pd.read_csv(csv_path, dtype={"GMT_capture_time": str})

# Convert 'capture_date' to datetime
df["capture_date"] = pd.to_datetime(df["capture_date"], errors="coerce")

# Filter rows for Finland
finland_df = df[df["Country"] == "Finland"].copy()

# Robust time parsing helper
def safe_parse_time(t):
    try:
        # Try strict HH:MM:SS format
        return pd.to_datetime(t, format="%H:%M:%S").time()
    except Exception:
        try:
            # Fallback: flexible parsing
            return pd.to_datetime(t).time()
        except Exception:
            return pd.NaT

# Apply robust parser
finland_df["GMT_capture_time_parsed"] = finland_df["GMT_capture_time"].apply(safe_parse_time)

# Combine date and time safely
def combine_date_time(row):
    if pd.notnull(row["capture_date"]) and pd.notnull(row["GMT_capture_time_parsed"]):
        return pd.Timestamp.combine(row["capture_date"].date(), row["GMT_capture_time_parsed"])
    else:
        return pd.NaT

finland_df["full_datetime"] = finland_df.apply(combine_date_time, axis=1)

# Check and print rows with invalid datetime
invalid_rows = finland_df[finland_df["full_datetime"].isna()]
if not invalid_rows.empty:
    print("⚠️ Warning: Some rows have invalid date/time combinations and will be excluded:")
    print(invalid_rows[["capture_date", "GMT_capture_time"]])

# Keep only the most recent snapshot per capture_date
finland_df = finland_df.sort_values("full_datetime").groupby("capture_date").tail(1)

# Convert Statements of Support to numeric
finland_df["Statements of Support"] = pd.to_numeric(finland_df["Statements of Support"], errors="coerce")

# Sort by capture_date again (since groupby may shuffle it)
finland_df.sort_values("capture_date", inplace=True)

print(finland_df)

# Plot
plt.figure(figsize=(10, 6))
plt.scatter(finland_df["capture_date"], finland_df["Statements of Support"], color="blue", label="Support Count")
plt.xlabel("Date")
plt.ylabel("Statements of Support")
plt.title("Statements of Support Over Time (Finland) - Latest Snapshot per Day")
plt.grid(True)
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
