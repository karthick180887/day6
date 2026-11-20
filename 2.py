import pandas as pd
import matplotlib.pyplot as plt

customers = pd.read_csv("data/customers_raw.csv")

# Count each class and convert to percentages
counts = customers["churned"].value_counts().sort_index()   # 0 = retained, 1 = churned
pct = counts / counts.sum() * 100

print(f"Total rows        : {counts.sum():,}")
print(f"Missing 'churned' : {customers['churned'].isna().sum()}")
pd.DataFrame({"customers": counts, "percent": pct.round(1)}).rename(index={0: "Retained (0)", 1: "Churned (1)"})
############################################################################################
labels = ["Retained (0)", "Churned (1)"]
colors = ["#2a78d6", "#eb6834"]                              # blue = stays, orange = leaves

fig, ax = plt.subplots(figsize=(8, 2.8))
bars = ax.barh(labels, pct.values, color=colors, height=0.55)

# Print the % and the customer count at the end of each bar
for bar, p, n in zip(bars, pct.values, counts.values):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
            f"{p:.1f}%  ({n:,} customers)", va="center", fontsize=11, color="#333333")

ax.set_xlim(0, 100)
ax.set_xlabel("Share of customers (%)")
ax.set_title(f"StreamPulse churn split: {pct[0]:.0f}% retained vs {pct[1]:.0f}% churned "
             f"(n = {counts.sum():,})", loc="left", fontsize=12)
ax.invert_yaxis()                                            # Retained on top
for side in ["top", "right"]:
    ax.spines[side].set_visible(False)
ax.grid(axis="x", color="#e5e5e5", linewidth=0.8)
ax.set_axisbelow(True)
plt.tight_layout()
plt.show()
