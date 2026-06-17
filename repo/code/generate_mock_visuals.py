"""
Generates fully synthetic illustrative visuals that mimic the structure of the
Power BI dashboard described in the case study README, WITHOUT any real data.

All nutrient names, values, and specification limits below are invented for
illustration only and do not represent any real product, company, or dataset.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

np.random.seed(42)
plt.rcParams.update({
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

OUT = "/home/claude/repo/visuals"

# ---------------------------------------------------------------------------
# Synthetic dataset: a few fictional "nutrients" with monthly samples over
# ~3 years, each with a target spec, mild seasonality, and a few outliers.
# ---------------------------------------------------------------------------
nutrients = {
    "Nutrient A": {"target": 100, "tol": 12, "season_amp": 8,  "trend": 0.05, "noise": 4},
    "Nutrient B": {"target": 50,  "tol": 6,  "season_amp": 1,  "trend": 0.0,  "noise": 2},
    "Nutrient C": {"target": 220, "tol": 25, "season_amp": 18, "trend": -0.1, "noise": 9},
}

dates = pd.date_range("2022-01-01", "2024-12-01", freq="MS")
rows = []
for name, p in nutrients.items():
    for i, d in enumerate(dates):
        seasonal = p["season_amp"] * np.cos(2 * np.pi * (d.month - 1) / 12)
        trend = p["trend"] * i
        value = p["target"] + seasonal + trend + np.random.normal(0, p["noise"])
        rows.append({"nutrient": name, "date": d, "value": value, "target": p["target"], "tol": p["tol"]})

df = pd.DataFrame(rows)

# inject a few synthetic outliers
outlier_idx = df.sample(6, random_state=1).index
df.loc[outlier_idx, "value"] += np.random.choice([-1, 1], size=6) * np.random.uniform(25, 40, size=6)

# guarantee at least one clearly visible outlier in Nutrient A specifically,
# so the illustrative scatter/outlier-detection chart has something to flag
nutrient_a_rows = df[df["nutrient"] == "Nutrient A"].index
forced_outlier_idx = np.random.choice(nutrient_a_rows, size=2, replace=False)
df.loc[forced_outlier_idx, "value"] += np.random.choice([-1, 1], size=2) * np.random.uniform(30, 38, size=2)

df["lcl"] = df["target"] - df["tol"]
df["ucl"] = df["target"] + df["tol"]
df["out_of_spec"] = (df["value"] < df["lcl"]) | (df["value"] > df["ucl"])

# modified z-score per nutrient for outlier flagging
def modified_z(group):
    med = group["value"].median()
    mad = (group["value"] - med).abs().median()
    if mad == 0:
        return pd.Series(0, index=group.index)
    return 0.6745 * (group["value"] - med) / mad

df["mod_z"] = df.groupby("nutrient", group_keys=False).apply(modified_z)
df["is_outlier"] = df["mod_z"].abs() > 3.5

# ---------------------------------------------------------------------------
# 1. Summary statistics bar chart (mean, RSD%, recovery% per nutrient)
# ---------------------------------------------------------------------------
summary = df.groupby("nutrient").agg(
    mean_value=("value", "mean"),
    std_value=("value", "std"),
    target=("target", "first"),
).reset_index()
summary["rsd_pct"] = (summary["std_value"] / summary["mean_value"]) * 100
summary["recovery_pct"] = (summary["mean_value"] / summary["target"]) * 100

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
colors = ["#3B7DD8", "#E0A93B", "#4FA37A"]

axes[0].bar(summary["nutrient"], summary["recovery_pct"], color=colors)
axes[0].axhline(100, color="grey", linestyle="--", linewidth=1)
axes[0].set_title("Recovery % (illustrative)")
axes[0].set_ylabel("Recovery %")
axes[0].set_ylim(80, 120)

axes[1].bar(summary["nutrient"], summary["rsd_pct"], color=colors)
axes[1].set_title("RSD % (illustrative)")
axes[1].set_ylabel("RSD %")

fig.suptitle("Summary Statistics View (synthetic example data)", fontsize=12, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(f"{OUT}/01_summary_statistics.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Scatter / outlier detection view for one nutrient
# ---------------------------------------------------------------------------
sub = df[df["nutrient"] == "Nutrient A"].sort_values("date")

fig, ax = plt.subplots(figsize=(9, 4.5))
ax.fill_between(sub["date"], sub["lcl"], sub["ucl"], color="#D7E8F7", alpha=0.6, label="Spec range")
normal = sub[~sub["is_outlier"]]
outliers = sub[sub["is_outlier"]]
ax.scatter(normal["date"], normal["value"], color="#3B7DD8", s=35, label="In range")
ax.scatter(outliers["date"], outliers["value"], color="#D9534F", s=55, marker="D", label="Flagged outlier")
ax.axhline(sub["target"].iloc[0], color="grey", linestyle="--", linewidth=1, label="Target")
ax.set_title("Monitoring Overview & Outlier Detection — Nutrient A (synthetic example data)", fontweight="bold")
ax.set_ylabel("Measured value (arbitrary units)")
ax.legend(loc="upper left", fontsize=8, frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(f"{OUT}/02_scatter_outlier_view.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------------------
# 3. Seasonality view for one nutrient (monthly average + rolling avg)
# ---------------------------------------------------------------------------
sub = df[df["nutrient"] == "Nutrient C"].sort_values("date").copy()
sub["rolling_avg"] = sub["value"].rolling(3, min_periods=1).mean()
monthly_avg = sub.groupby(sub["date"].dt.month)["value"].mean()

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

axes[0].plot(sub["date"], sub["value"], color="#B0B0B0", linewidth=1, alpha=0.6, label="Monthly value")
axes[0].plot(sub["date"], sub["rolling_avg"], color="#4FA37A", linewidth=2, label="3-month rolling avg")
axes[0].set_title("Trend with rolling average")
axes[0].legend(fontsize=8, frameon=False)
axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

axes[1].bar(monthly_avg.index, monthly_avg.values, color="#4FA37A")
axes[1].set_title("Average by calendar month")
axes[1].set_xlabel("Month")
axes[1].set_xticks(range(1, 13))

fig.suptitle("Seasonality View — Nutrient C (synthetic example data)", fontsize=12, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.92])
fig.savefig(f"{OUT}/03_seasonality_view.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------------------
# 4. Predictive trend view: regression line + R^2 + volatility classification
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4.5))
markers = ["o", "s", "^"]
for (name, p), marker in zip(nutrients.items(), markers):
    sub = df[df["nutrient"] == name].sort_values("date").reset_index(drop=True)
    x = np.arange(len(sub))
    y = sub["value"].values
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    ax.plot(sub["date"], y_pred, linestyle="--", linewidth=2,
             label=f"{name} (R²={r2:.2f})")
    ax.scatter(sub["date"], y, s=12, alpha=0.35)

ax.set_title("Predictive Trends View — regression fit per nutrient (synthetic example data)", fontweight="bold")
ax.set_ylabel("Measured value (arbitrary units)")
ax.legend(fontsize=8, frameon=False)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(f"{OUT}/04_predictive_trends_view.png", dpi=150)
plt.close(fig)

# volatility classification table -> saved as small figure too
def volatility_category(rsd):
    if rsd < 5:
        return "Stable"
    elif rsd < 15:
        return "Moderate"
    elif rsd < 30:
        return "Volatile"
    return "Highly Volatile"

summary["volatility_category"] = summary["rsd_pct"].apply(volatility_category)
print(summary[["nutrient", "mean_value", "rsd_pct", "recovery_pct", "volatility_category"]].round(2))

print("\nAll mock visuals saved to:", OUT)
