import os
import pandas as pd
import matplotlib.pyplot as plt

# Retrieve directory where my script is located
csv_filename = "eci_2024-07-31_to_2025-07-07.csv"
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CSVs", csv_filename)

# Load the CSV file
df = pd.read_csv(csv_path, dtype={"GMT_capture_time": str})
print("✅ Loaded CSV successfully!")

# Convert 'capture_date' to datetime
df["capture_date"] = pd.to_datetime(df["capture_date"], errors="coerce")

# Filter rows for Finland
finland_df = df[df["Country"] == "Finland"].copy()

# Fix time format from HH-MM-SS to HH:MM:SS
finland_df["GMT_capture_time"] = finland_df["GMT_capture_time"].str.replace("-", ":", regex=False)

# Combine capture_date and GMT_capture_time into full datetime
finland_df["full_datetime"] = pd.to_datetime(
    finland_df["capture_date"].dt.strftime("%Y-%m-%d") + " " + finland_df["GMT_capture_time"],
    errors="coerce"
)

# Keep only the most recent snapshot per capture_date
finland_df = finland_df.sort_values("full_datetime").groupby("capture_date").tail(1)
print(finland_df)

# Convert Statements of Support to numeric
finland_df["Statements of Support"] = pd.to_numeric(finland_df["Statements of Support"], errors="coerce")

# Sort by capture_date again (since groupby may shuffle it)
finland_df.sort_values("capture_date", inplace=True)

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