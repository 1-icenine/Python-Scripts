import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import timedelta

# --- Configuration ---
latest_date = "2025-07-14"
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_filename = f"eci_2024-07-31_to_{latest_date}.csv"
csv_path = os.path.join(script_dir, "../..", "CSVs", csv_filename)

# --- Load and preprocess ---
df = pd.read_csv(csv_path)
df['capture_date'] = pd.to_datetime(df['capture_date'])
df.sort_values(by='capture_date', inplace=True)

campaign_end_date = pd.to_datetime("2025-07-31")
earliest_dataset_date = df['capture_date'].min().date()
target_country = "Malta"

# Filter for country of interest (ex: Luxembourg)
df = df[df['Country'] == target_country]

# Get threshold
threshold = df['Threshold'].iloc[-1]

# Pivot: Date -> Signature Count
pivot_df = df.pivot_table(
    index='capture_date',
    columns='Country',
    values='Statements of Support',
    aggfunc='last'
)

# Calculate daily signature count
daily_signatures = pivot_df.diff().fillna(0).astype(int)

# --- Calculate Extrapolated Linear Goal ---
current_date = pivot_df.index.max()
current_signatures = pivot_df[target_country].iloc[-1]
days_remaining = (campaign_end_date - current_date).days

if days_remaining > 0:
    daily_needed = (threshold - current_signatures) / days_remaining
else:
    daily_needed = 0

# Create extrapolated goal series for cumulative plot
future_dates = pd.date_range(start=current_date, end=campaign_end_date, freq='D')
projected_signatures = [current_signatures + i * daily_needed for i in range(len(future_dates))]
linear_projection = pd.Series(data=projected_signatures, index=future_dates)

# --- Print summary ---
print(f"As of {current_date.date()}, {target_country} has {current_signatures:,} signatures.")
print(f"To reach the threshold of {int(threshold)} by {campaign_end_date.date()},")
print(f"They need to collect {int(daily_needed)} signatures per day for the remaining {days_remaining} days.")

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 10), sharex=True)

# Plot 1: Daily new signatures (actual)
ax1.plot(daily_signatures.index, daily_signatures[target_country], label='Daily Signatures', color='tab:blue')

# Plot required daily rate as a horizontal dashed line
ax1.axhline(y=daily_needed, color='tab:green', linestyle='--', label=f'Required Daily Rate')

# Vertical deadline line
ax1.axvline(x=campaign_end_date, color='black', linestyle='--', alpha=0.7, label='Deadline (July 31)')

ax1.set_ylabel("Daily Signature Count")
# ax1.grid(True, linestyle='--', alpha=0.5)
ax1.legend(loc='upper left')
ax1.set_ylim(0, 400)

# Label box with needed daily rate
midpoint_date = earliest_dataset_date + (campaign_end_date.date() - earliest_dataset_date) / 2
midpoint_date = pd.to_datetime(midpoint_date)

ax1.text(
    midpoint_date, 
    daily_needed + 10,  # slightly above the dashed line
    f"{int(daily_needed)} signatures/day needed", 
    color='tab:green', 
    ha='center', 
    va='bottom', 
    fontsize=11, 
    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="tab:green")
)

# Plot 2: Cumulative actual + projection
ax2.plot(pivot_df.index, pivot_df[target_country], label='Cumulative Signatures', color='tab:red')
ax2.plot(linear_projection.index, linear_projection.values, label='Projected Path to Threshold', linestyle='--', color='tab:green')
ax2.axhline(y=threshold, color='gray', linestyle=':', label='Threshold')
ax2.axvline(x=campaign_end_date, color='black', linestyle='--', alpha=0.7)

ax2.set_ylabel("Cumulative Signatures")
ax2.grid(True, linestyle='--', alpha=0.25)
ax2.legend(loc='upper left', bbox_to_anchor=(0, 0.925))
ax2.set_ylim(0, 4500)

# Set ticks and format on shared x-axis
ax2.xaxis.set_major_locator(mdates.MonthLocator())
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')

plt.suptitle(f"{target_country} Signatures & Projection to Reach Threshold by July 31st", 
             fontsize=20, x=0.53, y=0.97)
plt.xticks(rotation=45)
plt.xlim(earliest_dataset_date, campaign_end_date + timedelta(days=30))

plt.tight_layout()
plt.subplots_adjust(top=0.93)

# --- Annotation: Remaining signatures needed ---
remaining_needed = threshold - current_signatures

# Coordinates for the annotation
x_pos = campaign_end_date + timedelta(days=3)  # Shift right a bit from the deadline
y_start = current_signatures
y_end = threshold

# Draw short horizontal lines at current and target signature levels
ax2.hlines(y=y_start, xmin=x_pos - timedelta(days=1), xmax=x_pos + timedelta(days=1), colors='black')
ax2.hlines(y=y_end, xmin=x_pos - timedelta(days=1), xmax=x_pos + timedelta(days=1), colors='black')

# Draw vertical double arrow between the two horizontal lines
ax2.annotate(
    '', 
    xy=(x_pos, y_end), 
    xytext=(x_pos, y_start),
    arrowprops=dict(arrowstyle='<->', color='black', lw=1.5),
)

# Add a text label to the right of the arrow
ax2.text(
    x_pos + timedelta(days=3),
    (y_start + y_end) / 2,
    f"{int(remaining_needed):,} \nneeded",
    va='center',
    ha='left',
    fontsize=10,
    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray')
)

plt.show()
