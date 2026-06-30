"""
DebtBusters Intelligence Platform — Map Generator
Produces:
  charts/15_sa_province_map.png      — static matplotlib choropleth (for ebook)
  charts/16_sa_risk_heatmap_map.png  — static risk overlay map
  charts/sa_interactive_map.html     — folium interactive map (portfolio extra)
Run: python generate_maps.py  (after generate_millions.py)
"""

import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import warnings
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(__file__))
from brand_colors import CONFLUENT, RAINBOW, DEBTBUSTERS, apply_confluent_style

DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
CHART_DIR = os.path.join(os.path.dirname(__file__), "..", "charts")
os.makedirs(CHART_DIR, exist_ok=True)
apply_confluent_style()

def load(name):
    pp = os.path.join(DATA_DIR, f"{name}.parquet")
    pc = os.path.join(DATA_DIR, f"{name}.csv")
    return pd.read_parquet(pp) if os.path.exists(pp) else pd.read_csv(pc)

print("Loading data…")
clients = load("clients")
assess  = load("assessments")
pays    = load("payments")
credit  = load("credit_monitoring")
leads   = load("leads")

# ── Province name standardiser ────────────────────────────────────────────────
NAME_MAP = {
    "GP":"Gauteng","WC":"Western Cape","KZN":"KwaZulu-Natal",
    "EC":"Eastern Cape","LP":"Limpopo","MP":"Mpumalanga",
    "FS":"Free State","NW":"North West","NC":"Northern Cape",
    "Gauteng":"Gauteng","Western Cape":"Western Cape",
    "KwaZulu-Natal":"KwaZulu-Natal","Eastern Cape":"Eastern Cape",
    "Limpopo":"Limpopo","Mpumalanga":"Mpumalanga",
    "Free State":"Free State","North West":"North West",
    "Northern Cape":"Northern Cape",
}
clients["province"] = clients["province"].map(NAME_MAP).fillna(clients["province"])

cli_slim = clients[["client_id","province","risk_score"]].drop_duplicates("client_id")

# ── 1. Core assessment stats ──────────────────────────────────────────────────
assess_prov = assess.merge(cli_slim, on="client_id", how="left")
prov = assess_prov.groupby("province").agg(
    clients       = ("assessment_id","count"),
    avg_dti       = ("debt_to_income_ratio","mean"),
    avg_debt      = ("total_debt_balance","mean"),
    over_indebted = ("over_indebted_flag","sum"),
    avg_risk      = ("risk_score","mean"),
    avg_income    = ("gross_income","mean"),
    avg_creditors = ("number_of_creditors","mean"),
    avg_disposable= ("disposable_income","mean"),
).reset_index()
prov["over_indebted_rate"] = prov["over_indebted"] / prov["clients"] * 100
prov["avg_dti_pct"]        = prov["avg_dti"] * 100
prov = prov.set_index("province")

# ── 2. Lead conversion rate by province ──────────────────────────────────────
leads_prov = leads.merge(cli_slim[["client_id","province"]], on="client_id", how="left")
leads_prov["province"] = leads_prov["province"].map(NAME_MAP).fillna(leads_prov["province"])
conv = leads_prov.groupby("province").agg(
    total_leads  = ("lead_id","count"),
    converted    = ("converted_flag","sum"),
    qualified    = ("qualified_flag","sum"),
).reset_index()
conv["conversion_rate"]    = conv["converted"]  / conv["total_leads"] * 100
conv["qualification_rate"] = conv["qualified"]   / conv["total_leads"] * 100
conv = conv.set_index("province")
prov = prov.join(conv[["total_leads","conversion_rate","qualification_rate"]], how="left")

# ── 3. Payment performance by province ───────────────────────────────────────
pays_prov = pays.merge(cli_slim[["client_id","province"]], on="client_id", how="left")
pays_prov["province"] = pays_prov["province"].map(NAME_MAP).fillna(pays_prov["province"])
pay_stats = pays_prov.groupby("province").agg(
    avg_collection_rate  = ("collection_rate","mean"),
    missed_payment_rate  = ("missed_payment_flag","mean"),
    total_arrears        = ("arrears_amount","sum"),
    total_payments       = ("actual_payment_amount","sum"),
).reset_index().set_index("province")
pay_stats["avg_collection_rate"]  *= 100
pay_stats["missed_payment_rate"]  *= 100
prov = prov.join(pay_stats, how="left")

# ── 4. Credit score improvement by province ───────────────────────────────────
credit["monitoring_date"] = pd.to_datetime(credit["monitoring_date"])
credit_cli = credit.merge(cli_slim[["client_id","province"]], on="client_id", how="left")
credit_cli["province"] = credit_cli["province"].map(NAME_MAP).fillna(credit_cli["province"])

earliest = credit_cli.sort_values("monitoring_date").groupby("client_id").first()[["credit_score","province"]].rename(columns={"credit_score":"score_intake"})
latest   = credit_cli.sort_values("monitoring_date").groupby("client_id").last()[["credit_score"]].rename(columns={"credit_score":"score_latest"})
score_df = earliest.join(latest).reset_index()
score_df["score_improvement"] = score_df["score_latest"] - score_df["score_intake"]

credit_prov = score_df.groupby("province").agg(
    avg_score_intake     = ("score_intake","mean"),
    avg_score_latest     = ("score_latest","mean"),
    avg_score_improvement= ("score_improvement","mean"),
).reset_index().set_index("province")
prov = prov.join(credit_prov, how="left")

# ── 5. Credit utilisation from latest monitoring ──────────────────────────────
util_prov = credit_cli.sort_values("monitoring_date").groupby("client_id").last().reset_index()
util_prov["province"] = util_prov["province"].map(NAME_MAP).fillna(util_prov["province"])
util_stats = util_prov.groupby("province").agg(
    avg_utilisation     = ("total_utilisation_pct","mean"),
    avg_accts_arrears   = ("accounts_in_arrears","mean"),
).reset_index().set_index("province")
prov = prov.join(util_stats, how="left")

# ── 6. Province ranks ─────────────────────────────────────────────────────────
for col, ascending in [
    ("clients",True), ("avg_dti_pct",True), ("avg_debt",True),
    ("conversion_rate",False), ("avg_collection_rate",False),
    ("avg_score_improvement",False), ("missed_payment_rate",True),
    ("avg_income",False),
]:
    if col in prov.columns:
        prov[f"rank_{col}"] = prov[col].rank(ascending=ascending, method="min").astype(int)

# ── Approximate SA province polygon coordinates (lon, lat) ───────────────────
POLYGONS = {
    "Limpopo": [
        (26.5,-22.2),(31.8,-22.2),(32.0,-23.5),(31.5,-24.8),
        (30.5,-25.0),(29.5,-25.2),(28.5,-24.8),(27.5,-24.5),
        (26.5,-24.0),(26.0,-23.5),(26.0,-22.8),
    ],
    "Mpumalanga": [
        (28.5,-24.8),(31.5,-24.8),(32.0,-25.5),(32.5,-26.5),
        (31.5,-27.2),(30.5,-27.5),(29.5,-26.5),(28.5,-26.0),
    ],
    "Gauteng": [
        (27.0,-25.5),(28.5,-25.5),(28.5,-26.0),(29.0,-26.5),
        (28.0,-26.8),(27.0,-26.8),(26.7,-26.3),(27.0,-25.8),
    ],
    "North West": [
        (22.0,-25.5),(24.5,-23.0),(26.0,-22.8),(26.5,-22.2),
        (26.5,-24.0),(26.0,-24.5),(26.7,-26.3),(27.0,-26.8),
        (25.5,-27.2),(24.5,-28.0),(23.5,-27.5),(22.0,-27.0),
    ],
    "Free State": [
        (24.5,-28.0),(25.5,-27.2),(27.0,-26.8),(28.0,-26.8),
        (29.0,-26.5),(30.5,-27.5),(30.5,-29.0),(29.5,-30.5),
        (28.5,-31.0),(27.0,-31.0),(25.5,-30.0),(24.0,-29.5),
        (24.0,-28.5),
    ],
    "KwaZulu-Natal": [
        (29.5,-26.5),(30.5,-27.5),(31.5,-27.2),(32.5,-26.5),
        (32.9,-28.0),(32.8,-29.5),(31.5,-31.5),(30.0,-31.5),
        (29.5,-30.5),(30.5,-29.0),(30.5,-27.5),
    ],
    "Eastern Cape": [
        (24.0,-29.5),(25.5,-30.0),(27.0,-31.0),(28.5,-31.0),
        (29.5,-30.5),(30.0,-31.5),(31.5,-31.5),(30.0,-33.5),
        (28.5,-34.0),(26.5,-34.0),(25.0,-33.5),(22.5,-34.0),
        (22.0,-33.5),(23.0,-32.0),(23.5,-30.5),(24.0,-30.0),
    ],
    "Northern Cape": [
        (16.5,-28.5),(17.5,-27.5),(20.0,-26.5),(22.0,-25.5),
        (22.0,-27.0),(23.5,-27.5),(24.5,-28.0),(24.0,-28.5),
        (24.0,-30.0),(23.5,-30.5),(23.0,-32.0),(22.5,-34.0),
        (19.0,-34.5),(17.5,-33.5),(16.5,-30.5),
    ],
    "Western Cape": [
        (17.5,-33.5),(19.0,-34.5),(22.5,-34.0),(25.0,-33.5),
        (23.5,-34.5),(20.5,-35.0),(18.5,-34.8),(17.0,-34.5),
    ],
}

LABELS = {
    "Limpopo":      (29.2, -23.5),
    "Mpumalanga":   (30.2, -25.8),
    "Gauteng":      (27.9, -26.2),
    "North West":   (25.2, -25.8),
    "Free State":   (27.2, -29.0),
    "KwaZulu-Natal":(31.5, -28.8),
    "Eastern Cape": (26.5, -32.0),
    "Northern Cape":(20.2, -30.0),
    "Western Cape": (20.0, -33.8),
}

ABBR = {
    "Limpopo":"LP","Mpumalanga":"MP","Gauteng":"GP","North West":"NW",
    "Free State":"FS","KwaZulu-Natal":"KZN","Eastern Cape":"EC",
    "Northern Cape":"NC","Western Cape":"WC",
}

def draw_sa_base(ax, values_dict, cmap, vmin, vmax, metric_label):
    """Draw SA province polygons coloured by values_dict {province: value}."""
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap_obj = mcolors.LinearSegmentedColormap.from_list("confluent", cmap)

    for pname, coords in POLYGONS.items():
        val = values_dict.get(pname, np.nan)
        color = cmap_obj(norm(val)) if not np.isnan(val) else "#CCCCCC"
        poly = MplPolygon(coords, closed=True, facecolor=color,
                          edgecolor="white", linewidth=1.5, zorder=2)
        ax.add_patch(poly)

    # Province labels
    for pname, (lx, ly) in LABELS.items():
        val = values_dict.get(pname, np.nan)
        abbr = ABBR.get(pname, pname[:2])
        val_str = f"{val:.1f}" if not np.isnan(val) else "N/A"
        ax.text(lx, ly, f"{abbr}\n{val_str}",
                ha="center", va="center", fontsize=7.5,
                fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=0.15", fc="none", ec="none"),
                zorder=5)

    # Colourbar
    sm = plt.cm.ScalarMappable(cmap=cmap_obj, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label(metric_label, fontsize=9, color=DEBTBUSTERS["navy"])
    cbar.ax.tick_params(labelsize=8)

    ax.set_xlim(15.5, 33.5)
    ax.set_ylim(-35.5, -21.5)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude °E", fontsize=9, color=DEBTBUSTERS["navy"])
    ax.set_ylabel("Latitude °S", fontsize=9, color=DEBTBUSTERS["navy"])
    ax.spines[["top","right"]].set_visible(False)
    ax.set_facecolor("#E8F4FD")

# ══════════════════════════════════════════════════════════════════════════════
# MAP 15 — Client DTI + Volume Choropleth
# ══════════════════════════════════════════════════════════════════════════════
print("\nGenerating 15_sa_province_map…")

fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
fig.suptitle("South Africa — Debt Counselling Intelligence Map\n"
             "Left: Average DTI by Province  |  Right: Client Volume by Province",
             fontsize=14, fontweight="bold", color=DEBTBUSTERS["navy"], y=1.01)

dti_vals    = prov["avg_dti_pct"].to_dict()
client_vals = prov["clients"].to_dict()

# Panel 1 — DTI (red=high, green=low)
ax1 = axes[0]
ax1.set_facecolor("#E8F4FD")
draw_sa_base(ax1, dti_vals,
             [CONFLUENT["green"], CONFLUENT["yellow"], CONFLUENT["orange"], CONFLUENT["red"]],
             vmin=55, vmax=80, metric_label="Avg DTI (%)")
ax1.set_title("Average Debt-to-Income Ratio\n(Red = most over-indebted)",
              fontsize=11, fontweight="bold", color=DEBTBUSTERS["navy"], pad=10)

# Overlay bubble sized by client count
for pname, (lx, ly) in LABELS.items():
    n = client_vals.get(pname, 0)
    if n > 0:
        size = (n / max(client_vals.values())) * 1500
        ax1.scatter(lx, ly - 0.6, s=size, color="white", alpha=0.35,
                    edgecolors=DEBTBUSTERS["navy"], linewidth=0.8, zorder=6)

# Bubble legend
for n_val, lbl in [(5000,"5k"), (15000,"15k"), (30000,"30k")]:
    s = (n_val / max(client_vals.values())) * 1500
    ax1.scatter([], [], s=s, color="white", alpha=0.5,
                edgecolors=DEBTBUSTERS["navy"], linewidth=0.8, label=f"{lbl} clients")
ax1.legend(title="Client Volume", fontsize=7, title_fontsize=8,
           loc="lower left", framealpha=0.8)
ax1.annotate("Confluent | DebtBusters Intelligence Platform",
             xy=(1,0), xycoords="axes fraction", fontsize=7,
             color=DEBTBUSTERS["mid_grey"], ha="right", va="bottom",
             xytext=(0,-18), textcoords="offset points")

# Panel 2 — Client Volume (teal=low, blue=high)
ax2 = axes[1]
ax2.set_facecolor("#E8F4FD")
draw_sa_base(ax2, client_vals,
             [CONFLUENT["teal"], CONFLUENT["blue"], CONFLUENT["purple"]],
             vmin=0, vmax=max(client_vals.values()), metric_label="Client Count")
ax2.set_title("Client Volume by Province\n(Purple = highest volume)",
              fontsize=11, fontweight="bold", color=DEBTBUSTERS["navy"], pad=10)

# Risk score overlay circles
risk_vals = prov["avg_risk"].to_dict()
for pname, (lx, ly) in LABELS.items():
    r = risk_vals.get(pname, 0)
    if r > 0:
        col = CONFLUENT["red"] if r > 0.6 else CONFLUENT["orange"] if r > 0.45 else CONFLUENT["green"]
        ax2.scatter(lx, ly - 0.6, s=300, color=col, alpha=0.85,
                    edgecolors="white", linewidth=1.2, zorder=6)

legend_els = [
    mpatches.Patch(color=CONFLUENT["red"],    label="High Risk (score >0.60)"),
    mpatches.Patch(color=CONFLUENT["orange"], label="Medium Risk (0.45–0.60)"),
    mpatches.Patch(color=CONFLUENT["green"],  label="Low Risk (<0.45)"),
]
ax2.legend(handles=legend_els, title="Avg Risk Score", fontsize=7,
           title_fontsize=8, loc="lower left", framealpha=0.8)
ax2.annotate("Confluent | DebtBusters Intelligence Platform",
             xy=(1,0), xycoords="axes fraction", fontsize=7,
             color=DEBTBUSTERS["mid_grey"], ha="right", va="bottom",
             xytext=(0,-18), textcoords="offset points")

plt.tight_layout()
path = os.path.join(CHART_DIR, "15_sa_province_map.png")
plt.savefig(path, bbox_inches="tight", facecolor=DEBTBUSTERS["light_grey"], dpi=150)
print(f"  Saved: 15_sa_province_map.png")
plt.close("all")

# ══════════════════════════════════════════════════════════════════════════════
# MAP 16 — Over-Indebtedness + Credit Score Map
# ══════════════════════════════════════════════════════════════════════════════
print("Generating 16_sa_risk_profile_map…")

# Credit score data per province
credit_prov = credit.merge(
    clients[["client_id","province"]].drop_duplicates("client_id"),
    on="client_id", how="left"
)
credit_name_map = NAME_MAP
credit_prov["province"] = credit_prov["province"].map(credit_name_map).fillna(credit_prov["province"])
prov_credit = credit_prov.groupby("province")["credit_score"].mean()

fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.patch.set_facecolor(DEBTBUSTERS["light_grey"])
fig.suptitle("South Africa — Risk & Credit Intelligence Map\n"
             "Left: Over-Indebtedness Rate  |  Right: Average Credit Score",
             fontsize=14, fontweight="bold", color=DEBTBUSTERS["navy"], y=1.01)

oi_vals     = prov["over_indebted_rate"].to_dict()
cscore_vals = prov_credit.to_dict()

# Panel 1 — Over-indebted rate
ax3 = axes[0]
ax3.set_facecolor("#E8F4FD")
draw_sa_base(ax3, oi_vals,
             [CONFLUENT["green"], CONFLUENT["yellow"], CONFLUENT["orange"], CONFLUENT["red"]],
             vmin=50, vmax=90, metric_label="Over-Indebted Rate (%)")
ax3.set_title("Over-Indebtedness Rate by Province\n(% of assessed clients classified over-indebted)",
              fontsize=11, fontweight="bold", color=DEBTBUSTERS["navy"], pad=10)
ax3.axhline(-35.2, color=DEBTBUSTERS["mid_grey"], linewidth=0, alpha=0)
ax3.annotate("Confluent | DebtBusters Intelligence Platform",
             xy=(1,0), xycoords="axes fraction", fontsize=7,
             color=DEBTBUSTERS["mid_grey"], ha="right", va="bottom",
             xytext=(0,-18), textcoords="offset points")

# Panel 2 — Average credit score (red=low, green=high)
ax4 = axes[1]
ax4.set_facecolor("#E8F4FD")
draw_sa_base(ax4, cscore_vals,
             [CONFLUENT["red"], CONFLUENT["orange"], CONFLUENT["yellow"], CONFLUENT["green"]],
             vmin=450, vmax=620, metric_label="Avg Credit Score (300–850)")
ax4.set_title("Average Credit Score at Intake by Province\n(Green = higher scores, less severe at entry)",
              fontsize=11, fontweight="bold", color=DEBTBUSTERS["navy"], pad=10)
ax4.annotate("Confluent | DebtBusters Intelligence Platform",
             xy=(1,0), xycoords="axes fraction", fontsize=7,
             color=DEBTBUSTERS["mid_grey"], ha="right", va="bottom",
             xytext=(0,-18), textcoords="offset points")

plt.tight_layout()
path2 = os.path.join(CHART_DIR, "16_sa_risk_profile_map.png")
plt.savefig(path2, bbox_inches="tight", facecolor=DEBTBUSTERS["light_grey"], dpi=150)
print(f"  Saved: 16_sa_risk_profile_map.png")
plt.close("all")

# ══════════════════════════════════════════════════════════════════════════════
# INTERACTIVE MAP — Folium (4 layers, rich popups, province polygon fills)
# ══════════════════════════════════════════════════════════════════════════════
print("Generating sa_interactive_map.html…")
import folium, json

# Province centroids [lat, lon]
CENTROIDS = {
    "Limpopo":      (-23.5, 29.0),
    "Mpumalanga":   (-25.8, 30.2),
    "Gauteng":      (-26.2, 27.9),
    "North West":   (-25.8, 25.2),
    "Free State":   (-29.0, 27.2),
    "KwaZulu-Natal":(-28.8, 30.8),
    "Eastern Cape": (-32.0, 26.5),
    "Northern Cape":(-30.0, 20.2),
    "Western Cape": (-33.8, 20.0),
}

# ── Colour helpers ────────────────────────────────────────────────────────────
def dti_color(v):
    if v >= 75:   return "#E8363B"
    elif v >= 68: return "#F57C2D"
    elif v >= 62: return "#F5C842"
    else:         return "#52B748"

def interp_color(v, lo, hi, low_c="#52B748", mid_c="#F5C842", hi_c="#E8363B"):
    t = max(0.0, min(1.0, (v - lo) / (hi - lo + 1e-9)))
    if t < 0.5:
        r0,g0,b0 = int(low_c[1:3],16),int(low_c[3:5],16),int(low_c[5:7],16)
        r1,g1,b1 = int(mid_c[1:3],16),int(mid_c[3:5],16),int(mid_c[5:7],16)
        t2 = t * 2
    else:
        r0,g0,b0 = int(mid_c[1:3],16),int(mid_c[3:5],16),int(mid_c[5:7],16)
        r1,g1,b1 = int(hi_c[1:3],16),int(hi_c[3:5],16),int(hi_c[5:7],16)
        t2 = (t - 0.5) * 2
    return "#{:02X}{:02X}{:02X}".format(
        int(r0 + (r1-r0)*t2), int(g0 + (g1-g0)*t2), int(b0 + (b1-b0)*t2))

def bar(val, lo, hi, color):
    pct = max(0, min(100, (val - lo) / (hi - lo + 1e-9) * 100))
    return (f'<div style="background:#e8e8e8;border-radius:3px;height:6px;margin:2px 0 4px;">'
            f'<div style="background:{color};width:{pct:.0f}%;height:6px;border-radius:3px;"></div></div>')

def badge(txt, color):
    return (f'<span style="background:{color}22;border:1px solid {color};color:{color};'
            f'font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px;">{txt}</span>')

# ── Build rich popup HTML ─────────────────────────────────────────────────────
def build_popup(pname, r):
    dti     = r.get("avg_dti_pct", 0)
    n       = int(r.get("clients", 0))
    debt    = r.get("avg_debt", 0)
    oi      = r.get("over_indebted_rate", 0)
    risk    = r.get("avg_risk", 0)
    income  = r.get("avg_income", 0)
    creds   = r.get("avg_creditors", 0)
    disp    = r.get("avg_disposable", 0)
    conv    = r.get("conversion_rate", 0)
    qual    = r.get("qualification_rate", 0)
    leads_n = int(r.get("total_leads", 0))
    coll    = r.get("avg_collection_rate", 0)
    miss    = r.get("missed_payment_rate", 0)
    s_in    = r.get("avg_score_intake", 0)
    s_lat   = r.get("avg_score_latest", 0)
    s_imp   = r.get("avg_score_improvement", 0)
    util    = r.get("avg_utilisation", 0)
    acca    = r.get("avg_accts_arrears", 0)
    rk_n    = int(r.get("rank_clients", 0))
    rk_dti  = int(r.get("rank_avg_dti_pct", 0))
    rk_conv = int(r.get("rank_conversion_rate", 0))
    rk_coll = int(r.get("rank_avg_collection_rate", 0))
    rk_imp  = int(r.get("rank_avg_score_improvement", 0))
    rk_inc  = int(r.get("rank_avg_income", 0))

    sev_label = ("SEVERE" if dti>=75 else "HIGH" if dti>=68 else "ELEVATED" if dti>=62 else "MANAGEABLE")
    sev_color = dti_color(dti)

    html = f"""
<div style="font-family:'Segoe UI',Arial,sans-serif;width:310px;padding:4px;">
  <div style="background:#0A1E3D;color:white;padding:10px 14px;border-radius:8px 8px 0 0;
              border-left:4px solid #E8363B;margin:-4px -4px 10px -4px;">
    <div style="font-size:16px;font-weight:800;">{pname}</div>
    <div style="display:flex;gap:6px;margin-top:4px;">
      {badge(f'DTI {sev_label}', sev_color)}
      {badge(f'#{rk_n} by volume', '#1E88E5')}
      {badge(f'#{rk_imp} credit recovery', '#00A99D')}
    </div>
  </div>

  <div style="font-size:11px;font-weight:700;color:#0A1E3D;text-transform:uppercase;
              letter-spacing:0.8px;margin-bottom:4px;border-bottom:1px solid #e8e8e8;
              padding-bottom:3px;">Financial Stress</div>
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr><td style="color:#666;padding:1px 0;">Clients Assessed</td>
        <td style="text-align:right;font-weight:700;">{n:,}</td></tr>
    <tr><td style="color:#666;">Leads Generated</td>
        <td style="text-align:right;font-weight:700;">{leads_n:,}</td></tr>
    <tr><td style="color:#666;">Avg DTI</td>
        <td style="text-align:right;font-weight:700;color:{sev_color};">{dti:.1f}%</td></tr>
  </table>
  {bar(dti, 50, 85, sev_color)}
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr><td style="color:#666;padding:1px 0;">Over-Indebted Rate</td>
        <td style="text-align:right;font-weight:700;color:#E8363B;">{oi:.1f}%</td></tr>
    <tr><td style="color:#666;">Avg Total Debt</td>
        <td style="text-align:right;font-weight:700;">R{debt:,.0f}</td></tr>
    <tr><td style="color:#666;">Avg Gross Income</td>
        <td style="text-align:right;font-weight:700;">R{income:,.0f}/mo</td></tr>
    <tr><td style="color:#666;">Avg Disposable Income</td>
        <td style="text-align:right;font-weight:700;">R{disp:,.0f}/mo</td></tr>
    <tr><td style="color:#666;">Avg No. of Creditors</td>
        <td style="text-align:right;font-weight:700;">{creds:.1f}</td></tr>
    <tr><td style="color:#666;">ML Risk Score</td>
        <td style="text-align:right;font-weight:700;color:{'#E8363B' if risk>0.6 else '#F57C2D' if risk>0.45 else '#52B748'};">{risk:.3f}</td></tr>
  </table>

  <div style="font-size:11px;font-weight:700;color:#0A1E3D;text-transform:uppercase;
              letter-spacing:0.8px;margin:8px 0 4px;border-bottom:1px solid #e8e8e8;
              padding-bottom:3px;">Lead & Conversion</div>
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr><td style="color:#666;padding:1px 0;">Lead Conversion Rate</td>
        <td style="text-align:right;font-weight:700;color:#1E88E5;">{conv:.1f}%</td></tr>
  </table>
  {bar(conv, 0, 30, '#1E88E5')}
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr><td style="color:#666;">Qualification Rate</td>
        <td style="text-align:right;font-weight:700;">{qual:.1f}%</td></tr>
    <tr><td style="color:#666;">Rank (conversion)</td>
        <td style="text-align:right;font-weight:700;">#{rk_conv} of 9</td></tr>
  </table>

  <div style="font-size:11px;font-weight:700;color:#0A1E3D;text-transform:uppercase;
              letter-spacing:0.8px;margin:8px 0 4px;border-bottom:1px solid #e8e8e8;
              padding-bottom:3px;">Payment Performance</div>
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr><td style="color:#666;padding:1px 0;">Avg Collection Rate</td>
        <td style="text-align:right;font-weight:700;color:{'#52B748' if coll>=85 else '#F57C2D'};">{coll:.1f}%</td></tr>
  </table>
  {bar(coll, 60, 100, '#52B748' if coll>=85 else '#F57C2D')}
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr><td style="color:#666;">Missed Payment Rate</td>
        <td style="text-align:right;font-weight:700;color:#E8363B;">{miss:.1f}%</td></tr>
    <tr><td style="color:#666;">Rank (collection)</td>
        <td style="text-align:right;font-weight:700;">#{rk_coll} of 9</td></tr>
  </table>

  <div style="font-size:11px;font-weight:700;color:#0A1E3D;text-transform:uppercase;
              letter-spacing:0.8px;margin:8px 0 4px;border-bottom:1px solid #e8e8e8;
              padding-bottom:3px;">Credit Recovery</div>
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr><td style="color:#666;padding:1px 0;">Score at Intake</td>
        <td style="text-align:right;font-weight:700;">{s_in:.0f}</td></tr>
    <tr><td style="color:#666;">Latest Score</td>
        <td style="text-align:right;font-weight:700;">{s_lat:.0f}</td></tr>
    <tr><td style="color:#666;">Score Improvement</td>
        <td style="text-align:right;font-weight:700;color:{'#52B748' if s_imp>0 else '#E8363B'};">{'+'if s_imp>0 else ''}{s_imp:.1f} pts</td></tr>
  </table>
  {bar(max(s_imp,0), 0, 80, '#00A99D')}
  <table style="width:100%;font-size:12px;border-collapse:collapse;">
    <tr><td style="color:#666;">Credit Utilisation</td>
        <td style="text-align:right;font-weight:700;color:{'#E8363B' if util>75 else '#52B748'};">{util:.1f}%</td></tr>
    <tr><td style="color:#666;">Avg Accounts in Arrears</td>
        <td style="text-align:right;font-weight:700;">{acca:.1f}</td></tr>
    <tr><td style="color:#666;">Rank (credit recovery)</td>
        <td style="text-align:right;font-weight:700;">#{rk_imp} of 9</td></tr>
  </table>

  <div style="margin-top:8px;padding:7px 10px;border-radius:6px;font-size:11px;
      background:{'#FFF0F0' if dti>=70 else '#F0FFF4'};
      border-left:3px solid {'#E8363B' if dti>=70 else '#52B748'};">
    {'&#9888; High priority — DTI above 70%, focus counsellor capacity here' if dti>=70
     else '&#10003; Within manageable range — maintain and optimise'}
  </div>
</div>"""
    return html

# ── Base map ──────────────────────────────────────────────────────────────────
m = folium.Map(location=[-29.0, 25.0], zoom_start=6,
               tiles="CartoDB positron", width="100%", height="100%")

# ── Nav bar (injected once on the base map) ───────────────────────────────────
nav_html = """
<style>
#db-nav{position:fixed;top:0;left:0;right:0;z-index:99999;
  background:rgba(10,30,61,0.97);border-bottom:2px solid #E8363B;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 18px;height:50px;font-family:'Segoe UI',Arial,sans-serif;
  backdrop-filter:blur(6px);}
#db-nav .brand{font-size:13px;font-weight:700;color:#fff;white-space:nowrap;}
#db-nav .brand span{color:#E8363B;}
#db-nav .links{display:flex;gap:5px;flex-wrap:wrap;}
#db-nav .links a{color:#fff;text-decoration:none;padding:5px 11px;
  border-radius:16px;font-size:11px;font-weight:600;
  border:1px solid rgba(255,255,255,0.2);transition:all 0.18s;white-space:nowrap;}
#db-nav .links a:hover{background:#E8363B;border-color:#E8363B;}
#db-nav .links a.primary{background:#E8363B;border-color:#E8363B;}
#db-nav .links a.teal{background:#00A99D;border-color:#00A99D;}
.folium-map{margin-top:50px!important;}
</style>
<div id="db-nav">
  <div class="brand"><span>DebtBusters</span> Intelligence Platform</div>
  <div class="links">
    <a href="index.html">&#127968; Home</a>
    <a href="index.html#kpis">&#128200; KPIs</a>
    <a href="index.html#models">&#129302; ML</a>
    <a href="https://github.com/anthonyapollis/DebtBusters_Intelligence_Platform/raw/master/ebook/DebtBusters_Intelligence_Platform_Ebook_v7.docx" target="_blank" class="teal">&#128218; Ebook</a>
    <a href="https://github.com/anthonyapollis/DebtBusters_Intelligence_Platform/raw/master/excel/DebtBusters_Intelligence_Report.xlsx" target="_blank">&#128202; KPI Excel</a>
    <a href="https://github.com/anthonyapollis/DebtBusters_Intelligence_Platform/raw/master/excel/ML_Validation_Report.xlsx" target="_blank">&#129302; ML Excel</a>
    <a href="https://github.com/anthonyapollis/DebtBusters_Intelligence_Platform" target="_blank" class="primary">&#128279; GitHub</a>
  </div>
</div>
"""
m.get_root().html.add_child(folium.Element(nav_html))

# ── Layer 1: DTI Severity (default ON) ───────────────────────────────────────
dti_layer = folium.FeatureGroup(name="&#128308; DTI Severity", show=True)
for pname, coords in POLYGONS.items():
    if pname not in prov.index: continue
    val   = prov.loc[pname, "avg_dti_pct"]
    color = dti_color(val)
    folium.Polygon(
        locations=[[lat, lon] for lon, lat in coords],
        color="white", weight=1.5, fill=True,
        fill_color=color, fill_opacity=0.55,
        tooltip=f"{pname}: DTI {val:.1f}%",
    ).add_to(dti_layer)
dti_layer.add_to(m)

# ── Layer 2: Credit Recovery (OFF by default) ─────────────────────────────────
credit_layer = folium.FeatureGroup(name="&#128153; Credit Recovery", show=False)
imp_vals = prov["avg_score_improvement"].dropna()
for pname, coords in POLYGONS.items():
    if pname not in prov.index: continue
    val   = prov.loc[pname, "avg_score_improvement"]
    color = interp_color(val, imp_vals.min(), imp_vals.max(),
                         low_c="#E8363B", mid_c="#F5C842", hi_c="#52B748")
    folium.Polygon(
        locations=[[lat, lon] for lon, lat in coords],
        color="white", weight=1.5, fill=True,
        fill_color=color, fill_opacity=0.55,
        tooltip=f"{pname}: +{val:.1f} credit pts",
    ).add_to(credit_layer)
credit_layer.add_to(m)

# ── Layer 3: Payment Performance (OFF by default) ─────────────────────────────
pay_layer = folium.FeatureGroup(name="&#128200; Collection Rate", show=False)
coll_vals = prov["avg_collection_rate"].dropna()
for pname, coords in POLYGONS.items():
    if pname not in prov.index: continue
    val   = prov.loc[pname, "avg_collection_rate"]
    color = interp_color(val, coll_vals.min(), coll_vals.max(),
                         low_c="#E8363B", mid_c="#F5C842", hi_c="#52B748")
    folium.Polygon(
        locations=[[lat, lon] for lon, lat in coords],
        color="white", weight=1.5, fill=True,
        fill_color=color, fill_opacity=0.55,
        tooltip=f"{pname}: {val:.1f}% collection",
    ).add_to(pay_layer)
pay_layer.add_to(m)

# ── Layer 4: Lead Conversion (OFF by default) ─────────────────────────────────
conv_layer = folium.FeatureGroup(name="&#128270; Lead Conversion", show=False)
conv_vals = prov["conversion_rate"].dropna()
for pname, coords in POLYGONS.items():
    if pname not in prov.index: continue
    val   = prov.loc[pname, "conversion_rate"]
    color = interp_color(val, conv_vals.min(), conv_vals.max(),
                         low_c="#E8363B", mid_c="#F5C842", hi_c="#52B748")
    folium.Polygon(
        locations=[[lat, lon] for lon, lat in coords],
        color="white", weight=1.5, fill=True,
        fill_color=color, fill_opacity=0.55,
        tooltip=f"{pname}: {val:.1f}% conversion",
    ).add_to(conv_layer)
conv_layer.add_to(m)

# ── CircleMarkers — one per province, rich popup, sized by client volume ──────
marker_layer = folium.FeatureGroup(name="&#9679; Province Bubbles", show=True)
for pname, (lat, lon) in CENTROIDS.items():
    if pname not in prov.index: continue
    r      = prov.loc[pname].to_dict()
    dti    = r.get("avg_dti_pct", 0)
    n      = int(r.get("clients", 0))
    color  = dti_color(dti)
    radius = max(14, min(58, n / 500))

    folium.CircleMarker(
        location=[lat, lon], radius=radius,
        color="white", weight=2,
        fill=True, fill_color=color, fill_opacity=0.85,
        popup=folium.Popup(build_popup(pname, r), max_width=330),
        tooltip=f"<b>{pname}</b> — DTI {dti:.1f}% | {n:,} clients | Click for full stats",
    ).add_to(marker_layer)

    # Label — pointer-events:none so clicks reach the CircleMarker
    folium.Marker(
        location=[lat, lon],
        icon=folium.DivIcon(
            html=(f'<div style="font-size:9px;font-weight:800;color:white;'
                  f'text-shadow:1px 1px 3px #000;text-align:center;'
                  f'width:64px;margin-left:-32px;pointer-events:none;">'
                  f'{ABBR.get(pname, pname[:2])}<br>{dti:.0f}%</div>'),
            icon_size=(64, 30),
        )
    ).add_to(marker_layer)
marker_layer.add_to(m)

# ── Layer control ─────────────────────────────────────────────────────────────
folium.LayerControl(collapsed=False, position="topright").add_to(m)

# ── Province ranking table (bottom-right panel) ───────────────────────────────
rank_rows = ""
for pname in prov.sort_values("clients", ascending=False).index:
    r   = prov.loc[pname]
    dti = r.get("avg_dti_pct", 0)
    n   = int(r.get("clients", 0))
    imp = r.get("avg_score_improvement", 0)
    col = dti_color(dti)
    rank_rows += (
        f'<tr><td style="font-weight:600;font-size:11px;">{ABBR.get(pname,pname[:2])}</td>'
        f'<td style="text-align:right;font-size:11px;">{n:,}</td>'
        f'<td style="text-align:right;font-size:11px;color:{col};">{dti:.1f}%</td>'
        f'<td style="text-align:right;font-size:11px;color:{"#52B748" if imp>0 else "#E8363B"};">{"+" if imp>0 else ""}{imp:.0f}</td>'
        f'</tr>'
    )

rank_panel = f"""
<div style="position:fixed;bottom:20px;right:20px;z-index:9999;
     background:white;border-radius:10px;padding:12px 14px;
     border-left:4px solid #0A1E3D;font-family:'Segoe UI',Arial,sans-serif;
     box-shadow:0 4px 16px rgba(0,0,0,0.2);min-width:220px;">
  <div style="font-size:11px;font-weight:800;color:#0A1E3D;
              margin-bottom:8px;text-transform:uppercase;letter-spacing:0.8px;">
    Province Rankings
  </div>
  <table style="width:100%;border-collapse:collapse;">
    <thead>
      <tr style="border-bottom:1px solid #e8e8e8;">
        <th style="text-align:left;font-size:10px;color:#888;padding-bottom:4px;">Province</th>
        <th style="text-align:right;font-size:10px;color:#888;">Clients</th>
        <th style="text-align:right;font-size:10px;color:#888;">DTI</th>
        <th style="text-align:right;font-size:10px;color:#888;">Cr+</th>
      </tr>
    </thead>
    <tbody>{rank_rows}</tbody>
  </table>
  <div style="font-size:9px;color:#aaa;margin-top:6px;">
    Cr+ = avg credit score improvement pts
  </div>
</div>
"""
m.get_root().html.add_child(folium.Element(rank_panel))

# ── Legend ────────────────────────────────────────────────────────────────────
legend_html = """
<div style="position:fixed;bottom:20px;left:20px;z-index:9999;
     background:white;padding:12px 16px;border-radius:10px;
     border-left:4px solid #E8363B;font-family:'Segoe UI',Arial,sans-serif;
     box-shadow:0 4px 16px rgba(0,0,0,0.2);font-size:12px;min-width:190px;">
  <b style="color:#0A1E3D;display:block;margin-bottom:8px;font-size:12px;">
    DTI Severity (Active Layer)
  </b>
  <div style="margin:3px 0;"><span style="background:#E8363B;width:12px;height:12px;
    display:inline-block;border-radius:50%;margin-right:7px;"></span>&#8805;75% — Severe</div>
  <div style="margin:3px 0;"><span style="background:#F57C2D;width:12px;height:12px;
    display:inline-block;border-radius:50%;margin-right:7px;"></span>68–75% — High</div>
  <div style="margin:3px 0;"><span style="background:#F5C842;width:12px;height:12px;
    display:inline-block;border-radius:50%;margin-right:7px;"></span>62–68% — Elevated</div>
  <div style="margin:3px 0;"><span style="background:#52B748;width:12px;height:12px;
    display:inline-block;border-radius:50%;margin-right:7px;"></span>&lt;62% — Manageable</div>
  <div style="margin-top:8px;padding-top:8px;border-top:1px solid #eee;
              font-size:10px;color:#888;line-height:1.5;">
    Bubble size = client volume<br>
    <b>Click bubble</b> for 12 province metrics<br>
    Toggle layers top-right &#9654;
  </div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ── Save ──────────────────────────────────────────────────────────────────────
html_path = os.path.join(CHART_DIR, "sa_interactive_map.html")
m.save(html_path)
print(f"  Saved: sa_interactive_map.html ({os.path.getsize(html_path)//1024} KB)")

import shutil
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "public")
os.makedirs(PUBLIC_DIR, exist_ok=True)
pub_path = os.path.join(PUBLIC_DIR, "map.html")
shutil.copy2(html_path, pub_path)
print(f"  Mirrored: public/map.html")

print("\nAll maps generated.")
