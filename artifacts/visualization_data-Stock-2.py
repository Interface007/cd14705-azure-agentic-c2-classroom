import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Reconstruct cleaned dataset from analysis output
cleaned_data = [
    {"Date": "2025-09-01", "Website_Visits": 335.42},
    {"Date": "2025-09-02", "Website_Visits": 322.15},
    {"Date": "2025-09-03", "Website_Visits": 341.88},
    {"Date": "2025-09-05", "Website_Visits": 315.29},
    {"Date": "2025-09-06", "Website_Visits": 338.11},
    {"Date": "2025-09-07", "Website_Visits": 342.67},
    {"Date": "2025-09-09", "Website_Visits": 319.52},
    {"Date": "2025-09-11", "Website_Visits": 325.63},
    {"Date": "2025-09-12", "Website_Visits": 331.47},
    {"Date": "2025-09-13", "Website_Visits": 318.76},
    {"Date": "2025-09-14", "Website_Visits": 344.29},
    {"Date": "2025-09-15", "Website_Visits": 344.29},
]

stats = {
    "count": 12,
    "mean": 332.9166666667,
    "median": 333.445,
    "std": 10.3977463483,
    "min": 315.29,
    "max": 344.29
}

df = pd.DataFrame(cleaned_data)
df["Date"] = pd.to_datetime(df["Date"])

plt.style.use("seaborn-v0_8-whitegrid")
fig = plt.figure(figsize=(12, 6))

# Time series of cleaned data
ax1 = fig.add_subplot(1, 2, 1)
ax1.plot(df["Date"], df["Website_Visits"], marker="o", linestyle="-", color="tab:blue")
ax1.set_title("Cleaned Website Visits Over Time")
ax1.set_xlabel("Date")
ax1.set_ylabel("Website Visits")
ax1.tick_params(axis="x", rotation=45)

# Boxplot with stats annotation
ax2 = fig.add_subplot(1, 2, 2)
ax2.boxplot(df["Website_Visits"], vert=True, patch_artist=True,
            boxprops=dict(facecolor="lightblue", color="tab:blue"),
            medianprops=dict(color="red", linewidth=2))
ax2.set_title("Distribution of Cleaned Website Visits")
ax2.set_ylabel("Website Visits")

# Add statistics text box
text_str = (
    f"Summary (cleaned data)\n"
    f"Count: {stats['count']}\n"
    f"Mean: {stats['mean']:.2f}\n"
    f"Median: {stats['median']:.2f}\n"
    f"Std: {stats['std']:.2f}\n"
    f"Min: {stats['min']:.2f}\n"
    f"Max: {stats['max']:.2f}"
)
ax2.text(1.2, (stats["min"] + stats["max"]) / 2, text_str,
         fontsize=9, va="center", ha="left",
         bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.8))

plt.tight_layout()

output_path = "artifacts/data_visualization_data-Stock-2.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close(fig)