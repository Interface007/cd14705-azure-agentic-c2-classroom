import pandas as pd
import matplotlib.pyplot as plt

# Reconstruct cleaned data
cleaned_data = [
    {"Date": "0", "Website_Visits": 0.168098513943885},
    {"Date": "1", "Website_Visits": -0.0734119310549213},
    {"Date": "2", "Website_Visits": 0.419437121504546},
    {"Date": "3", "Website_Visits": 0.230220916835063},
    {"Date": "4", "Website_Visits": 0.0484507206799331},
    {"Date": "5", "Website_Visits": 0.391118474373306},
    {"Date": "6", "Website_Visits": 0.0333945555006963},
    {"Date": "7", "Website_Visits": 1.17100815115389},
    {"Date": "8", "Website_Visits": 1.16815507161612},
    {"Date": "9", "Website_Visits": 0.607805363819905},
    {"Date": "10", "Website_Visits": 0.432580161112631},
    {"Date": "11", "Website_Visits": 0.647040281872396},
    {"Date": "12", "Website_Visits": 1.03387337068873},
    {"Date": "13", "Website_Visits": 1.22678726036446},
    {"Date": "14", "Website_Visits": 0.859549975331712},
    {"Date": "15", "Website_Visits": 0.349122174749509},
    {"Date": "16", "Website_Visits": 0.455812083688593},
    {"Date": "17", "Website_Visits": 1.2200715526193},
    {"Date": "18", "Website_Visits": 1.22256209861093},
    {"Date": "19", "Website_Visits": 0.730907477276784},
    {"Date": "20", "Website_Visits": 0.861362464936091},
    {"Date": "21", "Website_Visits": 0.769506674478894},
    {"Date": "22", "Website_Visits": 1.44187645033057},
    {"Date": "23", "Website_Visits": 0.817407820827712},
    {"Date": "25", "Website_Visits": 0.747056906819799},
    {"Date": "26", "Website_Visits": 1.20035167823485},
    {"Date": "27", "Website_Visits": 0.559532815605475},
    {"Date": "28", "Website_Visits": 1.10039255321637},
    {"Date": "29", "Website_Visits": 0.617749384067377},
    {"Date": "30", "Website_Visits": 0.804495403667214},
    {"Date": "31", "Website_Visits": 0.603531761994848},
    {"Date": "33", "Website_Visits": 1.38809746838289},
    {"Date": "34", "Website_Visits": 0.900963359397716},
    {"Date": "35", "Website_Visits": 1.17558243870828},
    {"Date": "36", "Website_Visits": 0.871996506252388},
    {"Date": "37", "Website_Visits": -0.0402149641233578},
    {"Date": "38", "Website_Visits": 0.376163460041828},
    {"Date": "39", "Website_Visits": 0.952524823630224},
    {"Date": "40", "Website_Visits": 0.878083098981395},
]

stats = {
    "count": 39,
    "mean": 0.8007394048516844,
    "median": 0.804495403667214,
    "std": 0.3690667292153073,
    "min": -0.0734119310549213,
    "max": 1.44187645033057
}

# Create DataFrame
df = pd.DataFrame(cleaned_data)
df["Date"] = df["Date"].astype(int)
df = df.sort_values("Date")

# Prepare figure
plt.style.use("seaborn-v0_8-whitegrid")
fig = plt.figure(figsize=(12, 6))

# Time series of cleaned data
ax1 = fig.add_subplot(1, 2, 1)
ax1.plot(df["Date"], df["Website_Visits"], marker="o", linestyle="-", color="tab:blue")
ax1.set_title("Cleaned Sensor 3 Values Over Time")
ax1.set_xlabel("Time (index)")
ax1.set_ylabel("Sensor Value")
ax1.axhline(stats["mean"], color="tab:orange", linestyle="--", linewidth=1.5, label=f"Mean = {stats['mean']:.2f}")
ax1.legend()

# Distribution with key statistics
ax2 = fig.add_subplot(1, 2, 2)
ax2.hist(df["Website_Visits"], bins=10, color="tab:green", alpha=0.7, edgecolor="black")
ax2.set_title("Distribution of Cleaned Sensor 3 Values")
ax2.set_xlabel("Sensor Value")
ax2.set_ylabel("Frequency")

# Vertical lines for statistics
ax2.axvline(stats["mean"], color="tab:orange", linestyle="--", linewidth=1.5, label=f"Mean = {stats['mean']:.2f}")
ax2.axvline(stats["median"], color="tab:red", linestyle="-.", linewidth=1.5, label=f"Median = {stats['median']:.2f}")
ax2.axvline(stats["min"], color="tab:purple", linestyle=":", linewidth=1.2, label=f"Min = {stats['min']:.2f}")
ax2.axvline(stats["max"], color="tab:brown", linestyle=":", linewidth=1.2, label=f"Max = {stats['max']:.2f}")
ax2.legend(fontsize=8)

plt.tight_layout()

# Save figure
output_path = "artifacts/data_visualization_data-Sensor-3.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.close(fig)