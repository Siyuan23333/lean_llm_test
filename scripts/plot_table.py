import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Define the performance difference data
data = {
    "Model": [
        "Claude Sonnet 4", "o4-mini", "Gemini 2.5 Flash (thinking)",
        "Gemini 2.5 Flash", "Deepseek V3", "GPT-4o"
    ],
    "w/ Feedback": [3.69, -1.64, -1.64, 0.00, 0.82, 3.69],
    "w/ NL Proof": [-3.69, -0.82, -4.51, -2.87, -1.64, 1.64],
    "w/ Infoview": [-17.62, -1.23, -0.41, 0.81, -0.82, -0.82]
}

# Corresponding baseline values
baseline_values = {
    "Claude Sonnet 4": 22.54,
    "o4-mini": 24.59,
    "Gemini 2.5 Flash (thinking)": 18.03,
    "Gemini 2.5 Flash": 12.3,
    "Deepseek V3": 11.07,
    "GPT-4o": 8.61
}

# Create DataFrame and update row labels with baseline info
df = pd.DataFrame(data)
df.set_index("Model", inplace=True)
df.index = [f"{model}\nBaseline Pass@6 = {baseline_values[model]:.2f}" for model in df.index]

# Plotting
plt.figure(figsize=(10, 6))
ax = sns.heatmap(
    df,
    annot=True,
    cmap="RdYlGn",
    center=0,
    linewidths=0.5,
    fmt=".2f",
    cbar=False,
    vmin=-5, vmax=5,
    annot_kws={"size": 18}
)

# Format axis labels
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, ha='right', va='center', fontsize=15)
for label in ax.get_yticklabels():
    label.set_horizontalalignment('center')
    label.set_x(-0.23)
plt.xticks(rotation=0, ha='center', fontsize=15)

# Set titles and axis labels
# plt.title("Performance Change from Baseline Across Strategies", fontsize=14)
# plt.xlabel("Strategy", fontsize=13)
# plt.ylabel("Model", fontsize=13)

plt.tight_layout()
plt.show()
