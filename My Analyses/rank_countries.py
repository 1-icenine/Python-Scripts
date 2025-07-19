import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from datetime import timedelta
import os

# Input the most recent date listed on CSV
latest_date = "2025-07-14"
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_filename = f"eci_2024-07-31_to_{latest_date}.csv"
csv_path = os.path.join(script_dir, "..", "CSVs", csv_filename)

df = pd.read_csv(csv_path)

# === Preprocessing ===
df['capture_date'] = pd.to_datetime(df['capture_date'])

earliest_dataset_date = df['capture_date'].min().date()
campaign_end_date = pd.to_datetime("2025-07-31")

# Filter for all instances where any country has surpassed its threshold value
df_edited  = df[
    (df["Country"] != "Total number of signatories") &
    (df["Statements of Support"] > df["Threshold"])
]

# Get the first date each country passed its threshold
first_passed = (
    df_edited.sort_values("capture_date")
    .drop_duplicates(subset="Country", keep="first")
)

# === Dictionary for region mapping ===
region_map = {
    'Finland': 'Northern Europe',
    'Sweden': 'Northern Europe',
    'Denmark': 'Northern Europe',
    'Ireland': 'Northern Europe',
    'Poland': 'Eastern Europe',
    'Estonia': 'Eastern Europe',
    'Lithuania': 'Eastern Europe',
    'Latvia': 'Eastern Europe',
    'Romania': 'Eastern Europe',
    'Slovakia': 'Eastern Europe',
    'Czechia': 'Eastern Europe',
    'Hungary': 'Eastern Europe',
    'Bulgaria': 'Eastern Europe',
    'Croatia': 'Eastern Europe',
    'Slovenia': 'Eastern Europe',
    'Austria': 'Eastern Europe',  # borderline Central Europe
    'Germany': 'Western Europe',
    'Netherlands': 'Western Europe',
    'Belgium': 'Western Europe',
    'France': 'Western Europe',
    'Spain': 'Southern Europe',
    'Portugal': 'Southern Europe',
    'Italy': 'Southern Europe',
    'Greece': 'Southern Europe'
}

# Assign region column, defaulting to 'Other' if country not found
first_passed['Region'] = first_passed['Country'].map(region_map).fillna('Other')

# Define colors for regions
region_colors = {
    'Northern Europe': '#1f77b4',  # blue
    'Eastern Europe': '#ff7f0e',   # orange
    'Western Europe': '#2ca02c',   # green
    'Southern Europe': '#d62728',  # red
}

# Map colors for each country
first_passed['Color'] = first_passed['Region'].map(region_colors)

# === Plotting ===
df_unique = first_passed.sort_values("capture_date")
df_unique["order"] = range(len(df_unique), 0, -1)  # Reverse order for y-axis

fig, ax = plt.subplots(figsize=(10, 8))

# Plot points with colors by region
ax.scatter(df_unique["capture_date"], df_unique["order"], color=df_unique["Color"], s=80)

# Horizontal lines with color per point
for _, row in df_unique.iterrows():
    ax.hlines(y=row["order"], xmin=earliest_dataset_date, xmax=row["capture_date"],
          color=row["Color"], linewidth=2)

# Tidy up axis
ax.set_yticks(df_unique["order"])
ax.set_yticklabels(df_unique["Country"])
ax.set_title("When Did Each Country Cross Their Respective Threshold?", fontsize=20, pad=10)
ax.grid(True, axis='x', linestyle='--', alpha=0.5)

# Add legend
legend_patches = [Patch(color=color, label=region) for region, color in region_colors.items()]
ax.legend(handles=legend_patches, title="Region", loc='upper right')

# Set x-axis date formatting and ticks
import matplotlib.dates as mdates
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

fig.patch.set_facecolor('#2E2E2E')  # dark grey figure background
ax.set_facecolor('#1E1E1E')         # even darker axes background
ax.tick_params(colors='white', which='both')  # ticks color
ax.xaxis.label.set_color('white')             # x-axis label color
ax.yaxis.label.set_color('white')             # y-axis label color
ax.title.set_color('white')                    # title color

plt.xlim(earliest_dataset_date, campaign_end_date)
plt.tight_layout()
plt.show()
