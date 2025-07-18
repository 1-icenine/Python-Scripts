import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.ticker as mtick

# Input the most recent date listed on CSV
latest_date = "2025-07-14"
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_filename = f"eci_2024-07-31_to_{latest_date}.csv"
csv_path = os.path.join(script_dir, "../..", "CSVs", csv_filename)

df = pd.read_csv(csv_path)

# --- Preprocessing ---
df["capture_date"] = pd.to_datetime(df["capture_date"], errors="coerce")

# Filters for most recent date and earliest time
df_latest_date = df[df["capture_date"] == latest_date]
max_time = df_latest_date["GMT_capture_time"].max()
df_latest = df_latest_date[
    (df_latest_date["GMT_capture_time"] == max_time) &
    (df_latest_date["Country"] != "Total number of signatories")
]

# Sorts by statements of support from lowest to highest
df_latest_sorted = df_latest.sort_values("Statements of Support", ascending=False)

# Calculates remaining signatures needed to pass threshold
df_latest_sorted["Remaining Needed"] = (
    df_latest_sorted["Threshold"] - df_latest_sorted["Statements of Support"]
).clip(lower=0)

# --- Plotting --- 
# Sets bar colors based on remaining signature count
colors = [
    'gray' if rem == 0 else 'blue' 
    for rem in df_latest_sorted["Remaining Needed"]
]

# Sets figure size parameters
FIG_WIDTH, BAR_HEIGHT, MIN_HEIGHT = 16, 0.3, 6
fig_height = max(MIN_HEIGHT, len(df_latest_sorted) * BAR_HEIGHT)
plt.figure(figsize=(FIG_WIDTH, fig_height))
bars_support = plt.barh(df_latest_sorted["Country"], 
                        df_latest_sorted["Statements of Support"], 
                        color=colors, label="Support Count")

# Draw red dashed lines showing threshold for each country
ax = plt.gca()
ax.xaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
for bar_idx, thresh in enumerate(df_latest_sorted["Threshold"]):
    ax.vlines(x=thresh, ymin=bar_idx - 0.4, ymax=bar_idx + 0.4,
              colors='red', linestyles='dashed', linewidth=1)

# Sets up legend for the graphs
blue_patch = Patch(color='blue', label='Below Threshold')
gray_patch = Patch(color='gray', label='Threshold Met')
red_line = Line2D([], [], color='red', linestyle='--', label='Threshold Value')
plt.legend(handles=[blue_patch, gray_patch, red_line], loc='upper right')

# Sets up the positioning and descriptions for the labels
for y, (i, row) in enumerate(df_latest_sorted.iterrows()):
    y = df_latest_sorted.index.get_loc(i)
    support = row["Statements of Support"]
    threshold = row["Threshold"]
    percent = row["Percentage"]
    remaining = row["Remaining Needed"]

    if remaining > 0:
        label = f"{int(remaining)} needed ({percent:.1f}% Complete)"
        xpos = 1.3*threshold  # small offset to the right of the red line
        ax.text(xpos, y, label, va='center', fontsize=9)

plt.xlabel("Count of Statements of Support")
plt.title(f'Statements of Support by Country with Thresholds ({latest_date})', fontsize=20)
plt.grid(axis = 'x')
plt.tight_layout()
plt.show()
