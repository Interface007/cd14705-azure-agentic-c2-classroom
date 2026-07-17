import pandas as pd
import matplotlib.pyplot as plt

# Reconstruct cleaned dataset
cleaned_data = [
    {"Date": "2025-09-01", "Website_Visits": 542},
    {"Date": "2025-09-02", "Website_Visits": 489},
    {"Date": "2025-09-03", "Website_Visits": 563},
    {"Date": "2025-09-04", "Website_Visits": 512},
    {"Date": "2025-09-06", "Website_Visits": 598},
    {"Date": "2025-09-07", "Website_Visits": 621},
    {"Date": "2025-09-08", "Website_Visits": 505},
    {"Date": "2025-09-10", "Website_Visits": 534},
    {"Date": "2025-09-11", "Website_Visits": 511},
    {"Date": "2025-09-12", "Website_Visits": 490},
    {"Date": "2025-09-13", "Website_Visits": 523},
    {"Date": "2025-09-14", "Website_Visits": 514},
    {"Date": "2025-09-16", "Website_Visits": 527},
    {"Date": "2025-09-17", "Website_Visits": 499},
    {"Date": "2025-09-19", "Website_Visits": 488},
    {"Date": "2025-09-20", "Website_Visits": 531},
]

stats = {
    "count": 16,
    "mean": 524.8125,
    "median": 521.5,
    "std": 37.2907,
    "min": 488,
    "max": 621
}

df = pd.DataFrame(cleaned_data)
df["Date"] = pd.to_datetime(df["Date"])

plt.style.use("seaborn-v0_8-whitegrid")
fig, axes = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [3, 1]})

# Time series of cleaned website visits
axes[0].plot(df["Date"], df["Website_Visits"], marker="o", linestyle="-", color="#1f77b4")
axes[0].set_title("Cleaned Website Visits Over Time (Outliers Removed)")
axes[0].set_xlabel("Date")
axes[0].set_ylabel("Website Visits")
axes[0].tick_params(axis="x", rotation=45)

# Statistics summary bar chart
stat_names = ["mean", "median", "min", "max"]
stat_values = [stats["mean"], stats["median"], stats["min"], stats["max"]]

axes[1].bar(stat_names, stat_values, color=["#2ca02c", "#ff7f0e", "#1f77b4", "#d62728"])
axes[1].set_title("Summary Statistics of Cleaned Website Visits")
axes[1].set_ylabel("Visits")

for i, v in enumerate(stat_values):
    axes[1].text(i, v + 3, f"{v:.1f}", ha="center", va="bottom", fontsize=9)

plt.tight_layout()
output_path = "artifacts/data_visualization.png"
plt.savefig(output_path, dpi=300)
plt.close(fig)