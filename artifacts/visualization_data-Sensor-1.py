import pandas as pd
import matplotlib.pyplot as plt
import os

# Reconstruct cleaned dataset from analysis output
cleaned_data = [
    {"Date": "1", "Website_Visits": 0.12},
    {"Date": "2", "Website_Visits": 0.83},
    {"Date": "3", "Website_Visits": 1.37},
    {"Date": "4", "Website_Visits": 1.11},
    {"Date": "6", "Website_Visits": -0.78},
    {"Date": "7", "Website_Visits": -1.42},
    {"Date": "8", "Website_Visits": -1.18},
    {"Date": "9", "Website_Visits": -0.21},
    {"Date": "10", "Website_Visits": 0.91},
    {"Date": "11", "Website_Visits": 1.48},
    {"Date": "12", "Website_Visits": 1.09},
    {"Date": "13", "Website_Visits": 0.05},
    {"Date": "14", "Website_Visits": -1.02},
    {"Date": "15", "Website_Visits": -1.55},
    {"Date": "17", "Website_Visits": 0.15},
    {"Date": "18", "Website_Visits": 1.18},
    {"Date": "19", "Website_Visits": 1.62},
]

stats = {
    "count": 17,
    "mean": 0.2071,
    "median": 0.12,
    "std": 1.0817,
    "min": -1.55,
    "max": 1.62
}

df = pd.DataFrame(cleaned_data)
df["Date"] = df["Date"].astype(int)
df = df.sort_values("Date")

# Prepare figure
fig, axes = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [3, 1]})
fig.suptitle("Cleaned Dataset Summary - Sensor 1", fontsize=14, fontweight="bold")

# Top plot: time series of cleaned Website_Visits
axes[0].plot(df["Date"], df["Website_Visits"], marker="o", linestyle="-", color="tab:blue")
axes[0].axhline(0, color="gray", linewidth=0.8, linestyle="--")
axes[0].set_xlabel("Date (Index)")
axes[0].set_ylabel("Website Visits (Standardized)")
axes[0].set_title("Cleaned Website Visits Over Time")
axes[0].grid(True, linestyle="--", alpha=0.4)

# Bottom plot: bar chart of summary statistics
stat_names = ["mean", "median", "min", "max"]
stat_values = [stats["mean"], stats["median"], stats["min"], stats["max"]]
bar_colors = ["tab:green", "tab:orange", "tab:red", "tab:purple"]

axes[1].bar(stat_names, stat_values, color=bar_colors)
axes[1].axhline(0, color="gray", linewidth=0.8, linestyle="--")
axes[1].set_ylabel("Value")
axes[1].set_title("Summary Statistics (Cleaned Data)")
for i, v in enumerate(stat_values):
    axes[1].text(i, v, f"{v:.2f}", ha="center", va="bottom" if v >= 0 else "top")

plt.tight_layout(rect=[0, 0, 1, 0.96])

# Ensure artifacts directory exists and save figure
output_path = "artifacts/data_visualization_data-Sensor-1.png"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
plt.savefig(output_path, dpi=300)
plt.close(fig)