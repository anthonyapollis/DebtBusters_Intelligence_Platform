"""
DebtBusters Intelligence Platform — Chart Generator
Produces 12 publication-quality charts with Confluent brand colors
Run: python generate_charts.py  (after generate_millions.py)
Output: ../charts/*.png
"""

import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
from matplotlib import cm
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(__file__))
from brand_colors import CONFLUENT, RAINBOW, DEBTBUSTERS, apply_confluent_style

DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
CHART_DIR  = os.path.join(os.path.dirname(__file__), "..", "charts")
os.makedirs(CHART_DIR, exist_ok=True)
apply_confluent_style()

# ── load data ─────────────────────────────────────────────────────────────────
def load(name):
    p_parquet = os.path.join(DATA_DIR, f"{name}.parquet")
    p_csv     = os.path.join(DATA_DIR, f"{name}.csv")
    if os.path.exists(p_parquet):
        return pd.read_parquet(p_parquet)
    return pd.read_csv(p_csv)

print("Loading data…")
leads    = load("leads")
assess   = load("assessments")
cases    = load("debt_review_cases")
pays     = load("payments")
credit   = load("credit_monitoring")
clients  = load("clients")
creditors= load("creditors")
plans    = load("repayment_plans")

# ── helpers ───────────────────────────────────────────────────────────────────
def savefig(name, fig=None):
    path = os.path.join(CHART_DIR, f"{name}.png")
    (fig or plt).savefig(path, bbox_inches="tight", facecolor=DEBTBUSTERS["light_grey"])
    print(f"  Saved: {name}.png")
    plt.close("all")

def add_logo_text(ax, text="Confluent | DebtBusters Intelligence Platform"):
    ax.annotate(text, xy=(1,0), xycoords="axes fraction",
                fontsize=7, color=DEBTBUSTERS["mid_grey"],
                ha="right", va="bottom",
                xytext=(0,-22), textcoords="offset points")

# ── CHART 1 — Lead Funnel (horizontal waterfall) ──────────────────────────────
print("\nGenerating charts…")

def chart_lead_funnel():
    total     = len(leads)
    qualified = int(leads["qualified_flag"].sum())
    assessed  = int(leads["assessed_flag"].sum())
    converted = int(leads["converted_flag"].sum())

    stages  = ["Total Leads","Qualified","Assessed","Converted"]
    values  = [total, qualified, assessed, converted]
    colors  = [CONFLUENT["blue"], CONFLUENT["teal"], CONFLUENT["green"], CONFLUENT["purple"]]
    rates   = ["100%",
               f"{qualified/total*100:.1f}%",
               f"{assessed/total*100:.1f}%",
               f"{converted/total*100:.1f}%"]

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax.set_facecolor("#FFFFFF")

    bars = ax.barh(stages[::-1], values[::-1], color=colors[::-1],
                   height=0.55, edgecolor="white", linewidth=0.8)

    for bar, val, rate in zip(bars, values[::-1], rates[::-1]):
        ax.text(bar.get_width() + total*0.01, bar.get_y() + bar.get_height()/2,
                f"{val:,}  ({rate})", va="center", fontsize=10,
                color=DEBTBUSTERS["navy"], fontweight="bold")

    ax.set_xlim(0, total * 1.28)
    ax.set_xlabel("Number of Leads", color=DEBTBUSTERS["navy"])
    ax.set_title("Lead Acquisition Funnel", fontsize=15, fontweight="bold",
                 color=DEBTBUSTERS["navy"], pad=12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:,.0f}"))
    ax.spines[["top","right"]].set_visible(False)
    add_logo_text(ax)
    savefig("01_lead_funnel", fig)

chart_lead_funnel()

# ── CHART 2 — Leads by Channel (grouped bar MoM trend) ───────────────────────
def chart_channel_performance():
    leads["lead_date"] = pd.to_datetime(leads["lead_date"])
    leads["month_year"] = leads["lead_date"].dt.to_period("M").astype(str)

    top_ch = leads["source_channel"].value_counts().head(6).index.tolist()
    df = leads[leads["source_channel"].isin(top_ch)].copy()
    pivot = df.groupby(["month_year","source_channel"]).size().unstack(fill_value=0)
    # last 18 months
    pivot = pivot.tail(18)

    fig, ax = plt.subplots(figsize=(14, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax.set_facecolor("#FFFFFF")

    x = np.arange(len(pivot))
    w = 0.13
    for i,(col,color) in enumerate(zip(pivot.columns, RAINBOW)):
        ax.bar(x + i*w, pivot[col], width=w, color=color,
               label=col, alpha=0.88, edgecolor="white", linewidth=0.4)

    ax.set_xticks(x + w*2.5)
    ax.set_xticklabels(pivot.index, rotation=45, ha="right", fontsize=8)
    ax.set_title("Monthly Lead Volume by Channel", fontsize=14, fontweight="bold",
                 color=DEBTBUSTERS["navy"])
    ax.set_ylabel("Leads")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:,.0f}"))
    ax.legend(fontsize=8, ncol=3)
    ax.spines[["top","right"]].set_visible(False)
    add_logo_text(ax)
    savefig("02_channel_performance", fig)

chart_channel_performance()

# ── CHART 3 — DTI Distribution by Province ───────────────────────────────────
def chart_dti_province():
    df = assess.merge(clients[["client_id","province"]], on="client_id", how="left")
    provinces = (df.groupby("province")["debt_to_income_ratio"]
                  .mean().sort_values(ascending=False).index.tolist())

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax.set_facecolor("#FFFFFF")

    colors = RAINBOW[:len(provinces)]
    avgs   = [df[df["province"]==p]["debt_to_income_ratio"].mean()*100 for p in provinces]
    bars = ax.bar(provinces, avgs, color=colors, edgecolor="white", linewidth=0.6, width=0.65)

    for bar, val in zip(bars, avgs):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=9,
                fontweight="bold", color=DEBTBUSTERS["navy"])

    ax.axhline(70, color=CONFLUENT["red"], linestyle="--", linewidth=1.2, label="Over-Indebted Threshold (70%)")
    ax.set_ylabel("Average Debt-to-Income Ratio (%)")
    ax.set_title("Average DTI Ratio by Province", fontsize=14, fontweight="bold",
                 color=DEBTBUSTERS["navy"])
    ax.set_ylim(0, max(avgs)*1.25)
    ax.legend(fontsize=9)
    ax.spines[["top","right"]].set_visible(False)
    plt.xticks(rotation=30, ha="right")
    add_logo_text(ax)
    savefig("03_dti_by_province", fig)

chart_dti_province()

# ── CHART 4 — Case Pipeline Funnel ───────────────────────────────────────────
def chart_case_pipeline():
    stage_order = ["Lead","Assessment","Application","Review",
                   "Court Order","Active","Completed","Withdrawn"]
    counts = cases["case_stage"].value_counts().reindex(stage_order, fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax.set_facecolor("#FFFFFF")

    colors = [CONFLUENT["blue"], CONFLUENT["teal"], CONFLUENT["green"], CONFLUENT["yellow"],
              CONFLUENT["orange"], CONFLUENT["purple"], CONFLUENT["teal"], CONFLUENT["red"]]

    bars = ax.bar(stage_order, counts.values, color=colors,
                  edgecolor="white", linewidth=0.6, width=0.65)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+50,
                f"{val:,}", ha="center", va="bottom", fontsize=9, fontweight="bold",
                color=DEBTBUSTERS["navy"])

    ax.set_title("Debt Review Case Pipeline by Stage", fontsize=14, fontweight="bold",
                 color=DEBTBUSTERS["navy"])
    ax.set_ylabel("Number of Cases")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:,.0f}"))
    ax.spines[["top","right"]].set_visible(False)
    plt.xticks(rotation=20, ha="right")
    add_logo_text(ax)
    savefig("04_case_pipeline", fig)

chart_case_pipeline()

# ── CHART 5 — Collection Rate Trend ──────────────────────────────────────────
def chart_collection_rate():
    pays["payment_date"] = pd.to_datetime(pays["payment_date"])
    pays["month_year"]   = pays["payment_date"].dt.to_period("M").astype(str)

    monthly = pays.groupby("month_year").agg(
        expected=("expected_payment_amount","sum"),
        actual=("actual_payment_amount","sum"),
        missed=("missed_payment_flag","sum"),
        total=("payment_id","count"),
    ).reset_index()
    monthly["collection_rate"] = monthly["actual"] / monthly["expected"] * 100
    monthly["missed_rate"]     = monthly["missed"] / monthly["total"] * 100
    monthly = monthly.tail(24)

    fig, ax1 = plt.subplots(figsize=(13, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax1.set_facecolor("#FFFFFF")

    ax1.fill_between(monthly["month_year"], monthly["collection_rate"],
                     alpha=0.25, color=CONFLUENT["teal"])
    ax1.plot(monthly["month_year"], monthly["collection_rate"],
             color=CONFLUENT["teal"], linewidth=2.5, marker="o", markersize=4,
             label="Collection Rate %")
    ax1.axhline(95, color=CONFLUENT["green"], linestyle="--", linewidth=1, label="Target (95%)")
    ax1.set_ylabel("Collection Rate (%)", color=CONFLUENT["teal"])
    ax1.set_ylim(75, 105)

    ax2 = ax1.twinx()
    ax2.bar(monthly["month_year"], monthly["missed_rate"],
            color=CONFLUENT["red"], alpha=0.45, label="Missed Payment Rate %")
    ax2.set_ylabel("Missed Payment Rate (%)", color=CONFLUENT["red"])
    ax2.set_ylim(0, 40)

    ax1.set_title("Monthly Collection Rate vs Missed Payment Rate", fontsize=14,
                  fontweight="bold", color=DEBTBUSTERS["navy"])
    ax1.set_xticks(monthly["month_year"][::3])
    ax1.set_xticklabels(monthly["month_year"][::3], rotation=45, ha="right", fontsize=8)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, labels1+labels2, fontsize=9)
    ax1.spines[["top"]].set_visible(False)
    add_logo_text(ax1)
    savefig("05_collection_rate_trend", fig)

chart_collection_rate()

# ── CHART 6 — Credit Score Distribution ──────────────────────────────────────
def chart_credit_score_dist():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])

    for ax in axes:
        ax.set_facecolor("#FFFFFF")

    # histogram
    n, bins, patches = axes[0].hist(credit["credit_score"], bins=50,
                                     edgecolor="white", linewidth=0.3)
    norm = plt.Normalize(bins.min(), bins.max())
    for patch, left in zip(patches, bins):
        r = norm(left)
        patch.set_facecolor(plt.cm.RdYlGn(r))

    axes[0].set_title("Credit Score Distribution", fontsize=13, fontweight="bold",
                       color=DEBTBUSTERS["navy"])
    axes[0].set_xlabel("Credit Score")
    axes[0].set_ylabel("Count")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{x:,.0f}"))
    axes[0].axvline(580, color=CONFLUENT["red"],    linestyle="--", linewidth=1.2, label="High Risk (<580)")
    axes[0].axvline(670, color=CONFLUENT["yellow"], linestyle="--", linewidth=1.2, label="Medium Risk (<670)")
    axes[0].axvline(750, color=CONFLUENT["green"],  linestyle="--", linewidth=1.2, label="Low Risk (<750)")
    axes[0].legend(fontsize=8)

    # risk band donut
    band_counts = credit["credit_risk_band"].value_counts()
    band_order  = ["Very High Risk","High Risk","Medium Risk","Low Risk","Very Low Risk"]
    band_colors = [CONFLUENT["red"], CONFLUENT["orange"], CONFLUENT["yellow"],
                   CONFLUENT["green"], CONFLUENT["teal"]]
    band_vals   = [band_counts.get(b,0) for b in band_order]

    wedges, texts, autotexts = axes[1].pie(
        band_vals, labels=band_order, colors=band_colors,
        autopct="%1.1f%%", startangle=90,
        wedgeprops={"edgecolor":"white","linewidth":1.5},
        pctdistance=0.82
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_color("white")
        t.set_fontweight("bold")

    # make donut
    centre = plt.Circle((0,0), 0.55, color="#FFFFFF")
    axes[1].add_patch(centre)
    axes[1].text(0, 0, f"{len(credit):,}\nRecords", ha="center", va="center",
                 fontsize=9, color=DEBTBUSTERS["navy"], fontweight="bold")
    axes[1].set_title("Credit Risk Band Breakdown", fontsize=13, fontweight="bold",
                       color=DEBTBUSTERS["navy"])

    plt.tight_layout()
    add_logo_text(axes[1])
    savefig("06_credit_score_distribution", fig)

chart_credit_score_dist()

# ── CHART 7 — Top Creditors by Total Debt ────────────────────────────────────
def chart_creditor_debt():
    df = pays.groupby("creditor_id")["expected_payment_amount"].sum().reset_index()
    df = df.merge(creditors[["creditor_id","creditor_name"]], on="creditor_id")
    top = df.nlargest(12, "expected_payment_amount")

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax.set_facecolor("#FFFFFF")

    colors = [RAINBOW[i % len(RAINBOW)] for i in range(len(top))]
    bars = ax.barh(top["creditor_name"], top["expected_payment_amount"]/1e6,
                   color=colors, edgecolor="white", height=0.6)
    for bar in bars:
        ax.text(bar.get_width()+0.3, bar.get_y()+bar.get_height()/2,
                f"R{bar.get_width():.1f}M", va="center", fontsize=9,
                color=DEBTBUSTERS["navy"])

    ax.set_xlabel("Expected Payments (R Millions)")
    ax.set_title("Top 12 Creditors by Expected Payment Volume", fontsize=14,
                 fontweight="bold", color=DEBTBUSTERS["navy"])
    ax.spines[["top","right"]].set_visible(False)
    add_logo_text(ax)
    savefig("07_creditor_payments", fig)

chart_creditor_debt()

# ── CHART 8 — Income Band vs Over-Indebted ───────────────────────────────────
def chart_income_vs_debt():
    order = ["< R5k","R5k-R10k","R10k-R20k","R20k-R40k","R40k+"]
    df = assess.groupby("dti_band").agg(
        count=("assessment_id","count"),
        over_indebted=("over_indebted_flag","sum"),
        avg_dti=("debt_to_income_ratio","mean"),
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    for ax in axes: ax.set_facecolor("#FFFFFF")

    # Left: bar chart count by dti_band
    dti_order = ["< 40%","40-60%","60-80%","> 80%"]
    df2 = assess["dti_band"].value_counts().reindex(dti_order, fill_value=0)
    bar_colors = [CONFLUENT["green"], CONFLUENT["yellow"], CONFLUENT["orange"], CONFLUENT["red"]]
    axes[0].bar(df2.index, df2.values, color=bar_colors, edgecolor="white", width=0.55)
    for i, (idx, val) in enumerate(zip(df2.index, df2.values)):
        axes[0].text(i, val+200, f"{val:,}", ha="center", va="bottom",
                     fontsize=9, fontweight="bold", color=DEBTBUSTERS["navy"])
    axes[0].set_title("Clients by DTI Band", fontsize=13, fontweight="bold",
                       color=DEBTBUSTERS["navy"])
    axes[0].set_ylabel("Number of Clients")
    axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x:,.0f}"))
    axes[0].spines[["top","right"]].set_visible(False)

    # Right: stacked bar by recommended product
    prod_counts = assess["recommended_product"].value_counts()
    prod_colors = RAINBOW[:len(prod_counts)]
    axes[1].pie(prod_counts.values, labels=prod_counts.index, colors=prod_colors,
                autopct="%1.1f%%", startangle=90,
                wedgeprops={"edgecolor":"white","linewidth":1.5})
    axes[1].set_title("Recommended Product Distribution", fontsize=13,
                       fontweight="bold", color=DEBTBUSTERS["navy"])

    plt.tight_layout()
    add_logo_text(axes[1])
    savefig("08_dti_and_product_mix", fig)

chart_income_vs_debt()

# ── CHART 9 — Repayment Plan Savings ─────────────────────────────────────────
def chart_repayment_savings():
    accepted = plans[plans["accepted_flag"]==True].copy()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    for ax in axes: ax.set_facecolor("#FFFFFF")

    # Scatter: original vs proposed instalment
    sample = accepted.sample(min(3000, len(accepted)), random_state=42)
    axes[0].scatter(sample["original_instalment"], sample["proposed_instalment"],
                    alpha=0.30, s=8, color=CONFLUENT["blue"])
    max_val = max(sample["original_instalment"].max(), sample["proposed_instalment"].max())
    axes[0].plot([0,max_val],[0,max_val], color=CONFLUENT["red"],
                 linestyle="--", linewidth=1, label="No change line")
    axes[0].set_xlabel("Original Instalment (R)")
    axes[0].set_ylabel("Proposed Instalment (R)")
    axes[0].set_title("Original vs Proposed Instalment", fontsize=13, fontweight="bold",
                       color=DEBTBUSTERS["navy"])
    axes[0].legend(fontsize=9)
    axes[0].spines[["top","right"]].set_visible(False)

    # Histogram of monthly savings
    axes[1].hist(accepted["monthly_saving"], bins=50, color=CONFLUENT["teal"],
                 edgecolor="white", linewidth=0.3)
    axes[1].axvline(accepted["monthly_saving"].mean(), color=CONFLUENT["red"],
                    linestyle="--", linewidth=1.5,
                    label=f"Mean: R{accepted['monthly_saving'].mean():,.0f}")
    axes[1].set_xlabel("Monthly Saving (R)")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Distribution of Monthly Savings per Client", fontsize=13,
                       fontweight="bold", color=DEBTBUSTERS["navy"])
    axes[1].legend(fontsize=9)
    axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x:,.0f}"))
    axes[1].spines[["top","right"]].set_visible(False)

    plt.tight_layout()
    add_logo_text(axes[1])
    savefig("09_repayment_savings", fig)

chart_repayment_savings()

# ── CHART 10 — Creditor Acceptance Rate ──────────────────────────────────────
def chart_acceptance_rate():
    df = plans.groupby("creditor_id").agg(
        total=("plan_id","count"),
        accepted=("accepted_flag","sum"),
    ).reset_index()
    df["acceptance_rate"] = df["accepted"] / df["total"] * 100
    df = df.merge(creditors[["creditor_id","creditor_name"]], on="creditor_id")
    df = df[df["total"] > 100].nlargest(14, "total").sort_values("acceptance_rate", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax.set_facecolor("#FFFFFF")

    colors = [CONFLUENT["green"] if r >= 80 else CONFLUENT["yellow"] if r >= 65
              else CONFLUENT["red"] for r in df["acceptance_rate"]]
    bars = ax.barh(df["creditor_name"], df["acceptance_rate"], color=colors,
                   edgecolor="white", height=0.6)
    for bar, val in zip(bars, df["acceptance_rate"]):
        ax.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
                f"{val:.1f}%", va="center", fontsize=9, fontweight="bold",
                color=DEBTBUSTERS["navy"])
    ax.axvline(82, color=CONFLUENT["teal"], linestyle="--", linewidth=1.2, label="Industry avg (82%)")
    ax.set_xlabel("Creditor Acceptance Rate (%)")
    ax.set_title("Creditor Acceptance Rate — Repayment Plans", fontsize=14,
                 fontweight="bold", color=DEBTBUSTERS["navy"])
    ax.set_xlim(0, 110)
    ax.legend(fontsize=9)
    ax.spines[["top","right"]].set_visible(False)
    add_logo_text(ax)
    savefig("10_creditor_acceptance_rate", fig)

chart_acceptance_rate()

# ── CHART 11 — Province Heat Map (bubble) ────────────────────────────────────
def chart_province_bubble():
    assess_prov = assess.merge(clients[["client_id","province"]], on="client_id", how="left")
    df = assess_prov.groupby("province").agg(
        clients=("assessment_id","count"),
        avg_debt=("total_debt_balance","mean"),
        avg_dti=("debt_to_income_ratio","mean"),
        over_indebted=("over_indebted_flag","sum"),
    ).reset_index()
    df["over_indebted_rate"] = df["over_indebted"] / df["clients"] * 100

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax.set_facecolor("#FFFFFF")

    scatter = ax.scatter(
        df["avg_dti"]*100, df["avg_debt"]/1000,
        s=df["clients"]/10, c=df["over_indebted_rate"],
        cmap="RdYlGn_r", alpha=0.85, edgecolors="white", linewidth=1.5,
        vmin=30, vmax=80
    )
    for _, row in df.iterrows():
        ax.annotate(row["province"],
                    (row["avg_dti"]*100+0.2, row["avg_debt"]/1000+0.5),
                    fontsize=8.5, color=DEBTBUSTERS["navy"], fontweight="bold")

    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Over-Indebted Rate (%)", color=DEBTBUSTERS["navy"])
    ax.set_xlabel("Average DTI Ratio (%)")
    ax.set_ylabel("Average Total Debt (R Thousands)")
    ax.set_title("Province: Debt Burden vs DTI vs Over-Indebted Rate\n(bubble size = assessment volume)",
                 fontsize=13, fontweight="bold", color=DEBTBUSTERS["navy"])
    ax.spines[["top","right"]].set_visible(False)
    add_logo_text(ax)
    savefig("11_province_bubble", fig)

chart_province_bubble()

# ── CHART 12 — Executive Dashboard KPI Summary ───────────────────────────────
def chart_executive_dashboard():
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor(DEBTBUSTERS["navy"])

    # Title bar
    fig.text(0.5, 0.95, "DebtBusters Intelligence Platform",
             ha="center", va="center", fontsize=22, fontweight="bold",
             color="white")
    fig.text(0.5, 0.91, "Building Financially Healthy Societies, Together  |  Powered by Confluent Group",
             ha="center", va="center", fontsize=11, color=CONFLUENT["teal"])

    # KPI cards
    kpis = [
        ("Total Clients",        f"{len(clients):,}",     CONFLUENT["blue"]),
        ("Total Leads",          f"{len(leads):,}",       CONFLUENT["teal"]),
        ("Conversion Rate",      f"{leads['converted_flag'].mean()*100:.1f}%", CONFLUENT["green"]),
        ("Active Cases",         f"{int((cases['case_stage']=='Active').sum()):,}", CONFLUENT["purple"]),
        ("Collection Rate",      f"{pays['actual_payment_amount'].sum()/pays['expected_payment_amount'].sum()*100:.1f}%", CONFLUENT["teal"]),
        ("Total Debt Managed",   f"R{assess['total_debt_balance'].sum()/1e9:.1f}B", CONFLUENT["orange"]),
        ("Avg Credit Score",     f"{int(credit['credit_score'].mean())}",    CONFLUENT["yellow"]),
        ("Monthly Savings",      f"R{plans[plans['accepted_flag']==True]['monthly_saving'].mean():,.0f}", CONFLUENT["green"]),
    ]

    gs = GridSpec(2, 4, figure=fig, top=0.87, bottom=0.60, hspace=0.3, wspace=0.08)
    for i,(label, val, color) in enumerate(kpis):
        ax = fig.add_subplot(gs[i//4, i%4])
        ax.set_facecolor(color)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.text(0.5, 0.62, val, ha="center", va="center",
                fontsize=20, fontweight="bold", color="white", transform=ax.transAxes)
        ax.text(0.5, 0.22, label, ha="center", va="center",
                fontsize=9, color="white", alpha=0.9, transform=ax.transAxes)

    # Inline mini charts
    gs2 = GridSpec(1, 3, figure=fig, top=0.55, bottom=0.08, wspace=0.3)

    # Mini 1: Case stages
    ax1 = fig.add_subplot(gs2[0])
    ax1.set_facecolor("#1E3A5F")
    stage_c = cases["case_stage"].value_counts()
    sc = [CONFLUENT["blue"],CONFLUENT["teal"],CONFLUENT["green"],CONFLUENT["yellow"],
          CONFLUENT["orange"],CONFLUENT["purple"],CONFLUENT["teal"],CONFLUENT["red"]]
    ax1.bar(stage_c.index, stage_c.values, color=sc[:len(stage_c)],
            edgecolor=DEBTBUSTERS["navy"], linewidth=0.5)
    ax1.set_title("Case Stage Distribution", color="white", fontsize=10, fontweight="bold")
    ax1.set_facecolor("#1E3A5F")
    ax1.tick_params(colors="white", labelsize=7)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{x:,.0f}"))
    plt.setp(ax1.get_xticklabels(), rotation=30, ha="right")
    for spine in ax1.spines.values(): spine.set_color("#2A4A6F")

    # Mini 2: Monthly payments
    ax2 = fig.add_subplot(gs2[1])
    pays["payment_date"] = pd.to_datetime(pays["payment_date"])
    m = pays.groupby(pays["payment_date"].dt.to_period("M")).agg(
        exp=("expected_payment_amount","sum"),
        act=("actual_payment_amount","sum"),
    ).tail(18)
    x = np.arange(len(m))
    ax2.fill_between(x, m["exp"]/1e6, alpha=0.35, color=CONFLUENT["blue"], label="Expected")
    ax2.fill_between(x, m["act"]/1e6, alpha=0.65, color=CONFLUENT["teal"], label="Actual")
    ax2.set_title("Payment Flow (R Millions)", color="white", fontsize=10, fontweight="bold")
    ax2.set_facecolor("#1E3A5F")
    ax2.tick_params(colors="white", labelsize=7)
    ax2.set_xticks(x[::4])
    ax2.set_xticklabels([str(m.index[i]) for i in range(0,len(m),4)], rotation=30, ha="right")
    ax2.legend(fontsize=7, facecolor="#1E3A5F", labelcolor="white")
    for spine in ax2.spines.values(): spine.set_color("#2A4A6F")

    # Mini 3: Risk band pie
    ax3 = fig.add_subplot(gs2[2])
    rc = credit["credit_risk_band"].value_counts()
    rc_order = ["Very High Risk","High Risk","Medium Risk","Low Risk","Very Low Risk"]
    rc_colors = [CONFLUENT["red"],CONFLUENT["orange"],CONFLUENT["yellow"],CONFLUENT["green"],CONFLUENT["teal"]]
    rc_vals = [rc.get(b,0) for b in rc_order]
    ax3.pie(rc_vals, colors=rc_colors, startangle=90,
            wedgeprops={"edgecolor":DEBTBUSTERS["navy"],"linewidth":1},
            labels=[b.replace(" Risk","") for b in rc_order],
            textprops={"color":"white","fontsize":8})
    centre = plt.Circle((0,0),0.52,color="#1E3A5F")
    ax3.add_patch(centre)
    ax3.set_facecolor("#1E3A5F")
    ax3.text(0,0,"Credit\nRisk", ha="center", va="center", fontsize=9,
             color="white", fontweight="bold")
    ax3.set_title("Credit Risk Segments", color="white", fontsize=10, fontweight="bold")

    # Confluent rainbow stripe at bottom
    stripe_ax = fig.add_axes([0, 0, 1, 0.015])
    stripe_ax.set_xticks([]); stripe_ax.set_yticks([])
    for j, color in enumerate(RAINBOW):
        stripe_ax.axvspan(j/len(RAINBOW), (j+1)/len(RAINBOW), facecolor=color)

    savefig("12_executive_dashboard", fig)

chart_executive_dashboard()

# ── CHART 13 — Client Retention Curve by DTI Band ───────────────────────────
def chart_retention_curve():
    df = cases.copy()
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col is None:
        print("  Skipping retention curve — no date column found"); return
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    ref_date = pd.Timestamp("2024-06-30")
    df["months_active"] = ((ref_date - df[date_col]).dt.days / 30.44).clip(0, 60)

    if "withdrawal_flag" in df.columns:
        df["withdrew"] = df["withdrawal_flag"].fillna(0).astype(int)
    elif "case_stage" in df.columns:
        df["withdrew"] = df["case_stage"].str.lower().str.contains("withdraw", na=False).astype(int)
    else:
        df["withdrew"] = 0

    df = df.merge(
        assess[["client_id","debt_to_income_ratio"]].drop_duplicates("client_id"),
        on="client_id", how="left"
    )
    df["dti_band"] = pd.cut(
        df["debt_to_income_ratio"].fillna(0.65) * 100,
        bins=[0, 50, 65, 80, 200],
        labels=["Low DTI (<50%)", "Medium (50–65%)", "High (65–80%)", "Very High (>80%)"]
    )

    months = np.arange(0, 49)
    band_colors = [CONFLUENT["green"], CONFLUENT["teal"], CONFLUENT["orange"], CONFLUENT["red"]]
    band_labels = ["Low DTI (<50%)", "Medium (50–65%)", "High (65–80%)", "Very High (>80%)"]

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    ax.set_facecolor("#FFFFFF")

    for band, color in zip(band_labels, band_colors):
        subset = df[df["dti_band"] == band]
        if len(subset) < 50:
            continue
        total = len(subset)
        survival = []
        for m in months:
            still = (
                ((subset["withdrew"] == 0) & (subset["months_active"] >= m)) |
                ((subset["withdrew"] == 1) & (subset["months_active"] > m))
            ).sum()
            survival.append(still / total * 100)
        ax.plot(months, survival, color=color, linewidth=2.5,
                label=f"{band}  (n={total:,})", alpha=0.9)

    for v, lbl in [(12, "12M"), (24, "24M"), (36, "36M")]:
        ax.axvline(v, color=DEBTBUSTERS["mid_grey"], linestyle=":", linewidth=1, alpha=0.5)
        ax.text(v + 0.4, 3, lbl, fontsize=8, color=DEBTBUSTERS["mid_grey"])

    ax.fill_between([0, 6], 0, 105, alpha=0.06, color=CONFLUENT["red"],
                    label="Critical first 6M (highest withdrawal risk)")
    ax.set_xlim(0, 48); ax.set_ylim(0, 103)
    ax.set_xlabel("Months Since Case Intake", fontsize=11)
    ax.set_ylabel("% of Clients Still Enrolled", fontsize=11)
    ax.set_title("Client Retention Curve — Survival by DTI Band\n"
                 "(Higher DTI = steeper early withdrawal)",
                 fontsize=14, fontweight="bold", color=DEBTBUSTERS["navy"])
    ax.legend(fontsize=10, loc="upper right")
    ax.spines[["top","right"]].set_visible(False)
    add_logo_text(ax)
    savefig("13_client_retention_curve", fig)

chart_retention_curve()

# ── CHART 14 — Seasonal Collection Rate Heatmap ──────────────────────────────
def chart_cohort_heatmap():
    import matplotlib.colors as mcolors
    df = pays.copy()
    df["payment_date"] = pd.to_datetime(df["payment_date"], errors="coerce")
    df = df.dropna(subset=["payment_date"])
    df["year"]  = df["payment_date"].dt.year
    df["month"] = df["payment_date"].dt.month

    if "collection_rate" in df.columns:
        pivot = df.groupby(["year","month"])["collection_rate"].mean().reset_index()
        pivot["collection_rate"] *= 100
    else:
        pivot = df.groupby(["year","month"]).agg(
            act=("actual_payment_amount","sum"), exp=("expected_payment_amount","sum")
        ).reset_index()
        pivot["collection_rate"] = (pivot["act"] / pivot["exp"].replace(0, np.nan) * 100).clip(0, 100)

    piv_table = pivot.pivot(index="month", columns="year", values="collection_rate")
    month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "confluent_heat", [CONFLUENT["red"], CONFLUENT["yellow"], CONFLUENT["green"]])

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
    im = ax.imshow(piv_table.values, cmap=cmap, aspect="auto", vmin=80, vmax=100)

    ax.set_yticks(range(len(piv_table.index)))
    ax.set_yticklabels([month_names[m-1] for m in piv_table.index], fontsize=10)
    ax.set_xticks(range(len(piv_table.columns)))
    ax.set_xticklabels([str(c) for c in piv_table.columns], fontsize=11, fontweight="bold")

    for i in range(len(piv_table.index)):
        for j in range(len(piv_table.columns)):
            val = piv_table.values[i, j]
            if not np.isnan(val):
                txt_color = "white" if val < 87 else DEBTBUSTERS["navy"]
                ax.text(j, i, f"{val:.1f}%", ha="center", va="center",
                        fontsize=9, fontweight="bold", color=txt_color)

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.set_label("Collection Rate (%)", fontsize=10)
    ax.set_title("Collection Rate Heatmap — Month × Year\n"
                 "(Jan & Jul seasonal dips clearly visible; improving trend year-on-year)",
                 fontsize=13, fontweight="bold", color=DEBTBUSTERS["navy"])
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("Month", fontsize=11)
    add_logo_text(ax)
    plt.tight_layout()
    savefig("14_cohort_collection_rate", fig)

chart_cohort_heatmap()

print(f"\nAll 14 charts saved to: {CHART_DIR}")
