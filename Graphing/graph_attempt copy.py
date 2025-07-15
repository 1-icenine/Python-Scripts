import os
import pandas as pd
import matplotlib.pyplot as plt

# Retrieve directory where my script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_filename = "eci_2024-07-31_to_2025-07-14.csv"

# Go one level up to reach SDG Scripts/, then into CSVs/
csv_path = os.path.join(script_dir, "..", "CSVs", csv_filename)

df = pd.read_csv(csv_path, dtype={"GMT_capture_time": str})

# Convert 'capture_date' to datetime
df["capture_date"] = pd.to_datetime(df["capture_date"], errors="coerce")

# Filter by the most recent date and time
df_latest = df[df["capture_date"] == "2025-07-14"].copy()
df_latest = df_latest[df_latest["GMT_capture_time"] == df_latest["GMT_capture_time"].max()].copy()
df_latest = df_latest[df_latest["Country"] != "Total number of signatories"]

# Sort by statements of support from highest to lowest
df_latest_sorted = df_latest.sort_values("Statements of Support", ascending=True)

# Plotting features
df_latest_sorted["Remaining Needed"] = df_latest_sorted.apply(
    lambda row: max(row["Threshold"] - row["Statements of Support"], 0), axis=1
)

# Dynamic colors (gray if pass threshold, else blue)
colors = ['gray' if rem == 0 else 'blue' 
          for rem in df_latest_sorted["Remaining Needed"]]

plt.figure(figsize=(16, max(6, len(df_latest_sorted) * 0.3)))
bars_support = plt.barh(df_latest_sorted["Country"], 
                        df_latest_sorted["Statements of Support"], 
                        color=colors, label="Support Count")

ax = plt.gca()
# Plot Threshold bars slightly thinner and transparent
for i, thresh in enumerate(df_latest_sorted["Threshold"]):
    # i is the index (matches y-position of the bar)
    # thresh is threshold for that country

    # y-position of the bar center
    y = i  
    # Plot a vertical dashed line at threshold, spanning only across the bar's y position ± some padding
    ax.vlines(x=thresh, ymin=y - 0.4, ymax=y + 0.4, colors='red', linestyles='dashed', linewidth=1)

plt.xlabel("Count of Statements of Support")
plt.title("Statements of Support by Country with Thresholds")

# Add support count labels on bars
labels = [
    "" if rem == 0 else f"{int(rem)} needed"
    for rem in df_latest_sorted["Remaining Needed"]
]

plt.bar_label(bars_support, labels=labels, padding=10)

plt.tight_layout()
plt.show()

# # Plot
# plt.figure(figsize=(10, 6))
# plt.bar(most_recent_df["Country"], most_recent_df["Statements of Support"], color="blue", label="Support Count")
# plt.xlabel("Date")
# plt.ylabel("Statements of Support")
# plt.title("Statements of Support Over Time (Finland) - Latest Snapshot per Day")
# plt.grid(True)
# plt.legend()
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.show()