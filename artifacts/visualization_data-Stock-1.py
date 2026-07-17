import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Reconstruct cleaned dataset
cleaned_data = [
    {"Date": "2025-09-01", "Website_Visits": 187.95},
    {"Date": "2025-09-03", "Website_Visits": 193.84},
    {"Date": "2025-09-04", "Website_Visits": 179.66},
    {"Date": "2025-09-05", "Website_Visits": 160.43},
    {"Date": "2025-09-07", "Website_Visits": 199.32},
    {"Date": "2025-09-08", "Website_Visits": 171.58},
    {"Date": "2025-09-09", "Website_Visits": 165.91},
    {"Date": "2025-09-10", "Website_Visits": 182.75},
]

stats = {
    "count": 8,
    "mean": 180.93,
    "median": 181.205,
    "std": 13.07,
    "min": 160.43,
    "max": 199.32
}

df = pd.DataFrame(cleaned_data)
df["Date"] = pd.to_datetime(df["Date"])

# Create figure with two subplots: time series and bar summary
fig, axes = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={"height_ratios": [2, 1]})
fig.suptitle("Cleaned Dataset Summary: Website Visits (Mapped from AAPL_Stock_Price)", fontsize=14, fontweight="bold")

# Time series plot of cleaned data
ax1 = axes[0]
ax1.plot(df["Date"], df["Website_Visits"], marker="o", linestyle="-", color="tab:blue", label="Cleaned Website Visits")
ax1.set_xlabel("Date")
ax1.set_ylabel("Website Visits")
ax1.set_title("Website Visits Over Time (Cleaned Data)")
ax1.grid(True, linestyle="--", alpha=0.4)
ax1.legend()

# Annotate mean line
ax1.axhline(stats["mean"], color="tab:orange", linestyle="--", linewidth=1.5, label=f"Mean = {stats['mean']}")
ax1.legend()

# Bar chart of key statistics
ax2 = axes[1]
stat_names = ["mean", "median", "min", "max"]
stat_values = [stats["mean"], stats["median"], stats["min"], stats["max"]]

bars = ax2.bar(stat_names, stat_values, color=["tab:orange", "tab:green", "tab:red", "tab:purple"])
ax2.set_ylabel("Website Visits")
ax2.set_title("Descriptive Statistics (Cleaned Data)")

# Annotate bar values
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.2f}", ha="center", va="bottom", fontsize=9)

ax2.grid(axis="y", linestyle="--", alpha=0.3)

plt.tight_layout(rect=[0, 0.03, 1, 0.95])

output_path = "artifacts/data_visualization_data-Stock-1.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close(fig)