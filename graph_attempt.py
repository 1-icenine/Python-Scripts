import os
import pandas as pd
import matplotlib.pyplot as plt

# Retrieve directory where my script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

csv_filename = "eci_2024-07-31_to_2025-07-07.csv"
csv_path = os.path.join(script_dir, "CSVs", csv_filename)

# Load the CSV file (replace with your actual filename)
df = pd.read_csv(csv_path)
print("✅ Loaded CSV successfully!")

# Convert 'capture_date' to datetime if it's not already
df["capture_date"] = pd.to_datetime(df["capture_date"], errors="coerce")

# Filter rows for Finland
finland_df = df[df["Country"] == "Finland"].copy()

# Convert Statements of Support to integer (in case it's a string)
finland_df["Statements of Support"] = pd.to_numeric(finland_df["Statements of Support"], errors="coerce")

# Sort by capture_date
finland_df.sort_values("capture_date", inplace=True)

plt.figure(figsize=(10, 6))
plt.scatter(finland_df["capture_date"], finland_df["Statements of Support"], color="blue", label="Support Count")
plt.xlabel("Date")
plt.ylabel("Statements of Support")
plt.title("Statements of Support Over Time (Finland)")
plt.grid(True)
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()