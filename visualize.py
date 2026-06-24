"""
Supply Chain Risk Dashboard — Python Visualisation
----------------------------------------------------
Author: Kumar Aditya
Purpose: Standalone Python charts for anyone who doesn't have Power BI.
         Produces the same KPIs as the .pbix dashboard.

Run after generate_data.py:
    python visualize.py
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import os

os.makedirs("outputs", exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading data...")
df   = pd.read_csv("data/supply_chain_data.csv", parse_dates=["order_date"])
sc   = pd.read_csv("data/supplier_scorecard.csv")
flags = pd.read_csv("data/risk_flags.csv")

# ── Colour helpers ─────────────────────────────────────────────────────────────
RISK_COLORS = {"High": "#e74c3c", "Medium": "#f39c12", "Low": "#2ecc71"}

def risk_color(label):
    return RISK_COLORS.get(label, "#95a5a6")


# ── Figure 1: KPI Summary + OTD trend ─────────────────────────────────────────
fig = plt.figure(figsize=(16, 10))
fig.patch.set_facecolor('#f8f9fa')
gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.4)

# KPI tiles
overall_otd     = df["on_time_delivery"].mean() * 100
avg_delay       = df[df["days_late"] > 0]["days_late"].mean()
defect_rate     = df["defect_rate"].mean() * 100
total_spend     = df["order_value_eur"].sum() / 1e6
high_risk_count = (sc["risk_label"] == "High").sum()

kpis = [
    ("On-Time Delivery", f"{overall_otd:.1f}%",  "#2980b9"),
    ("Avg Delay (late orders)", f"{avg_delay:.1f} days", "#e67e22"),
    ("Avg Defect Rate", f"{defect_rate:.2f}%",  "#8e44ad"),
    ("Annual Spend", f"€{total_spend:.1f}M",     "#27ae60"),
    ("High-Risk Suppliers", str(high_risk_count), "#e74c3c"),
]
for i, (label, value, color) in enumerate(kpis):
    col = i if i < 3 else i - 3
    row = 0 if i < 3 else 1
    ax = fig.add_subplot(gs[row, col if i < 3 else i - 3])
    ax.set_facecolor(color)
    ax.text(0.5, 0.65, value, ha='center', va='center', fontsize=22,
            fontweight='bold', color='white', transform=ax.transAxes)
    ax.text(0.5, 0.25, label, ha='center', va='center', fontsize=9,
            color='white', alpha=0.9, transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

# Monthly OTD trend
ax_trend = fig.add_subplot(gs[1:, :])
monthly = df.groupby("month")["on_time_delivery"].mean() * 100
ax_trend.plot(monthly.index, monthly.values, marker='o', color='#2980b9',
              linewidth=2.5, markersize=7, label='On-Time Delivery %')
ax_trend.axhline(y=90, color='#e74c3c', linestyle='--', linewidth=1.2,
                 label='90% target threshold')
ax_trend.fill_between(monthly.index, monthly.values, 90,
                      where=(monthly.values < 90),
                      alpha=0.15, color='#e74c3c', label='Below target')
ax_trend.set_xlim(1, 12)
ax_trend.set_ylim(60, 100)
ax_trend.set_xticks(range(1, 13))
ax_trend.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun',
                           'Jul','Aug','Sep','Oct','Nov','Dec'])
ax_trend.set_ylabel("On-Time Delivery (%)")
ax_trend.set_title("Monthly On-Time Delivery — 2024", fontsize=12, fontweight='bold')
ax_trend.legend(fontsize=9)
ax_trend.set_facecolor('#ffffff')
ax_trend.grid(axis='y', alpha=0.3)

plt.suptitle("Supply Chain Risk Dashboard — Overview", fontsize=14,
             fontweight='bold', y=0.98, color='#222222')
plt.savefig("outputs/01_kpi_overview.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: outputs/01_kpi_overview.png")


# ── Figure 2: Supplier Risk Scorecard ─────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor('#f8f9fa')

# Left: horizontal bar chart of OTD by supplier, coloured by risk
sc_sorted = sc.sort_values("otd_rate_pct")
colors    = [risk_color(r) for r in sc_sorted["risk_label"]]
bars = axes[0].barh(sc_sorted["supplier_name"], sc_sorted["otd_rate_pct"],
                    color=colors, edgecolor='white')
axes[0].axvline(x=90, color='#333333', linestyle='--', linewidth=1, label='90% target')
axes[0].set_xlim(0, 105)
axes[0].set_xlabel("On-Time Delivery Rate (%)")
axes[0].set_title("Supplier On-Time Delivery Rate", fontweight='bold')
axes[0].legend(fontsize=9)
for bar, val in zip(bars, sc_sorted["otd_rate_pct"]):
    axes[0].text(val + 0.5, bar.get_y() + bar.get_height()/2,
                 f"{val:.1f}%", va='center', fontsize=9)

# Right: scatter — OTD vs Defect Rate, sized by spend, coloured by risk
scatter_colors = [risk_color(r) for r in sc["risk_label"]]
sizes = (sc["annual_spend_eur"] / sc["annual_spend_eur"].max() * 600 + 60).tolist()
axes[1].scatter(sc["otd_rate_pct"], sc["defect_rate_pct"],
                s=sizes, c=scatter_colors, alpha=0.8, edgecolors='white', linewidth=1.2)
for _, row in sc.iterrows():
    axes[1].annotate(row["supplier_name"].split()[0],
                     (row["otd_rate_pct"], row["defect_rate_pct"]),
                     textcoords="offset points", xytext=(6, 3), fontsize=7, color='#444444')
axes[1].axvline(x=90, color='#333333', linestyle='--', linewidth=1, alpha=0.5)
axes[1].set_xlabel("On-Time Delivery Rate (%)")
axes[1].set_ylabel("Defect Rate (%)")
axes[1].set_title("OTD vs Defect Rate\n(bubble size = annual spend)", fontweight='bold')

legend_items = [mpatches.Patch(color=c, label=l)
                for l, c in RISK_COLORS.items()]
axes[1].legend(handles=legend_items, title="Risk Level", fontsize=9)

for ax in axes:
    ax.set_facecolor('#ffffff')
    ax.grid(alpha=0.2)

plt.suptitle("Supplier Risk Scorecard — 2024", fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig("outputs/02_supplier_scorecard.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: outputs/02_supplier_scorecard.png")


# ── Figure 3: Risk flags breakdown ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.patch.set_facecolor('#f8f9fa')

# Flags by supplier
flag_by_supplier = (flags.groupby("supplier_name")
                         .size()
                         .sort_values(ascending=False)
                         .head(8))
axes[0].barh(flag_by_supplier.index[::-1], flag_by_supplier.values[::-1],
             color='#e74c3c', alpha=0.85)
axes[0].set_xlabel("Number of Flagged Orders")
axes[0].set_title("Flagged Incidents by Supplier (Top 8)", fontweight='bold')

# Flags by disruption cause
flag_by_cause = flags["disruption_cause"].value_counts().head(7)
axes[1].barh(flag_by_cause.index[::-1], flag_by_cause.values[::-1],
             color='#e67e22', alpha=0.85)
axes[1].set_xlabel("Frequency")
axes[1].set_title("Disruption Causes — Flagged Orders", fontweight='bold')

for ax in axes:
    ax.set_facecolor('#ffffff')
    ax.grid(axis='x', alpha=0.2)

plt.suptitle("Supply Chain Risk Incidents — 2024", fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig("outputs/03_risk_incidents.png", dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: outputs/03_risk_incidents.png")

print("\nAll charts saved to outputs/. Open them or load the CSVs into Power BI.\n")
