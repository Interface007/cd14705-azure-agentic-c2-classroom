import pandas as pd
import matplotlib.pyplot as plt
import os

# Create a DataFrame from the provided statistics
stats = {
    "Metric": ["count", "mean", "median", "std", "min", "max"],
    "Value": [0, 0, 0, 0, 0, 0]
}
df_stats = pd.DataFrame(stats)

# Create a figure for visualization
plt.figure(figsize=(8, 5))

# Bar plot of the statistics
plt.bar(df_stats["Metric"], df_stats["Value"], color="steelblue")

# Add titles and labels
plt.title("Cleaned Dataset Summary - Sensor 2 (Validation Failed)")
plt.xlabel("Statistic")
plt.ylabel("Value")

# Add text annotations for each bar
for idx, row in df_stats.iterrows():
    plt.text(idx, row["Value"] + 0.01, str(row["Value"]), ha='center', va='bottom', fontsize=9)

plt.tight_layout()

# Ensure the artifacts directory exists
output_path = "artifacts"
os.makedirs(output_path, exist_ok=True)

# Save the figure to the specified path
save_path = os.path.join(output_path, "data_visualization_data-Sensor-2.png")
plt.savefig(save_path)

plt.close()