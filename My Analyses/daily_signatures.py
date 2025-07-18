import pandas as pd
import matplotlib.pyplot as plt
import os

# Input the most recent date listed on CSV
latest_date = "2025-07-14"
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_filename = f"eci_2024-07-31_to_{latest_date}.csv"
csv_path = os.path.join(script_dir, "..", "CSVs", csv_filename)

df = pd.read_csv(csv_path)

campaign_end_date = pd.to_datetime("2025-07-31")

# --- Preprocessing ---
df['capture_date'] = pd.to_datetime(df['capture_date'])
earliest_dataset_date = df['capture_date'].min().date()   # <--- Moved here
df.sort_values(by='capture_date', inplace=True)

# Select only total number of signatories
df = df[df['Country'] == 'Total number of signatories']

# Pivot (will create a single column named 'Total number of signatories')
pivot_df = df.pivot_table(
    index='capture_date',
    columns='Country',
    values='Statements of Support',
    aggfunc='last'
)

# Compute daily new signatures
daily_signatures = pivot_df.diff().fillna(0).astype(int)

# --- Plotting ---
fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 10), sharex=True)

# Since we have only one column, get its name
country = pivot_df.columns[0]

# Plot daily new signatures
ax1.plot(daily_signatures.index, daily_signatures[country], label='Daily Signatures', color='tab:blue')
ax1.set_ylabel("Daily Signature Count")
ax1.grid(True, linestyle='--', alpha=0.5)
ax1.set_ylim(0, 1.8e5)
ax1.legend()

# Plot cumulative signatures
ax2.plot(pivot_df.index, pivot_df[country], label='Cumulative Signatures', color='tab:red')
ax2.set_ylabel("Cumulative Signatures")
ax2.grid(True, linestyle='--', alpha=0.5)
ax2.set_ylim(0, 1.6e6)
ax2.legend(loc='upper left')

plt.xticks(rotation=45)
fig.suptitle("Daily and Cumulative Signature Counts", fontsize=20, x=0.5, y=0.95)

# Set x-axis limits properly to date range
ax2.set_xlim(pivot_df.index.min(), campaign_end_date)

plt.tight_layout()
plt.subplots_adjust(top=0.9)
plt.show()
