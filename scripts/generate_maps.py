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

# ── Compute province-level stats ──────────────────────────────────────────────
assess_prov = assess.merge(
    clients[["client_id","province","risk_score"]].drop_duplicates("client_id"),
    on="client_id", how="left"
)
prov = assess_prov.groupby("province").agg(
    clients       = ("assessment_id","count"),
    avg_dti       = ("debt_to_income_ratio","mean"),
    avg_debt      = ("total_debt_balance","mean"),
    over_indebted = ("over_indebted_flag","sum"),
    avg_risk      = ("risk_score","mean"),
).reset_index()
prov["over_indebted_rate"] = prov["over_indebted"] / prov["clients"] * 100
prov["avg_dti_pct"]        = prov["avg_dti"] * 100

# Standardise province names used in the data
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
prov["province"] = prov["province"].map(NAME_MAP).fillna(prov["province"])
prov = prov.set_index("province")

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
# INTERACTIVE MAP — Folium
# ══════════════════════════════════════════════════════════════════════════════
print("Generating sa_interactive_map.html…")
import folium
from folium.plugins import MarkerCluster

# Province centroids for folium markers
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

m = folium.Map(
    location=[-29.0, 25.0], zoom_start=6,
    tiles="CartoDB positron",
    width="100%", height="100%"
)

# Title
title_html = """
<div style="position:fixed; top:10px; left:50%; transform:translateX(-50%);
     background:#0A1E3D; color:white; padding:12px 24px; border-radius:8px;
     font-family:Calibri,Arial,sans-serif; font-size:16px; font-weight:bold;
     z-index:1000; border-left:4px solid #E8363B; box-shadow:0 2px 8px rgba(0,0,0,0.3);">
 DebtBusters Intelligence Platform — South Africa Province Map
</div>
"""
m.get_root().html.add_child(folium.Element(title_html))

# Colour function
def risk_color(dti_pct):
    if dti_pct >= 75:   return "#E8363B"
    elif dti_pct >= 68: return "#F57C2D"
    elif dti_pct >= 62: return "#F5C842"
    else:               return "#52B748"

for pname, (lat, lon) in CENTROIDS.items():
    if pname not in prov.index:
        continue
    r = prov.loc[pname]
    dti    = r["avg_dti_pct"]
    n      = int(r["clients"])
    debt   = r["avg_debt"]
    oi     = r["over_indebted_rate"]
    risk   = r["avg_risk"]
    color  = risk_color(dti)
    radius = max(15, min(60, n / 500))

    popup_html = f"""
    <div style="font-family:Calibri,Arial,sans-serif; min-width:220px;">
      <h4 style="margin:0 0 8px; color:#0A1E3D; border-bottom:2px solid #E8363B; padding-bottom:4px;">
        {pname}
      </h4>
      <table style="width:100%; font-size:12px;">
        <tr><td><b>Clients assessed</b></td><td style="text-align:right">{n:,}</td></tr>
        <tr><td><b>Average DTI</b></td>
            <td style="text-align:right; color:{'#E8363B' if dti>=70 else '#52B748'}">{dti:.1f}%</td></tr>
        <tr><td><b>Average Debt</b></td>
            <td style="text-align:right">R{debt:,.0f}</td></tr>
        <tr><td><b>Over-Indebted</b></td>
            <td style="text-align:right">{oi:.1f}%</td></tr>
        <tr><td><b>Avg Risk Score</b></td>
            <td style="text-align:right">{risk:.3f}</td></tr>
      </table>
      <div style="margin-top:8px; padding:6px; background:#f5f5f5; border-radius:4px;
                  font-size:11px; color:#555;">
        {'⚠️ High priority province — DTI above 70%' if dti >= 70
         else '✅ Within manageable DTI range'}
      </div>
    </div>
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color="white",
        weight=2,
        fill=True,
        fill_color=color,
        fill_opacity=0.85,
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"{pname}: DTI {dti:.1f}% | {n:,} clients",
    ).add_to(m)

    folium.Marker(
        location=[lat, lon],
        icon=folium.DivIcon(
            html=f'<div style="font-size:9px; font-weight:bold; color:white; '
                 f'text-shadow:1px 1px 2px #000; text-align:center; '
                 f'width:60px; margin-left:-30px;">'
                 f'{ABBR.get(pname,pname[:2])}<br>{dti:.0f}%</div>',
            icon_size=(60, 30),
        )
    ).add_to(m)

# Legend
legend_html = """
<div style="position:fixed; bottom:30px; left:20px; z-index:1000;
     background:white; padding:12px 16px; border-radius:8px;
     border-left:4px solid #E8363B; font-family:Calibri,Arial,sans-serif;
     box-shadow:0 2px 8px rgba(0,0,0,0.2); font-size:12px;">
  <b style="color:#0A1E3D; display:block; margin-bottom:8px;">Average DTI by Province</b>
  <div><span style="background:#E8363B; width:14px; height:14px; display:inline-block; border-radius:50%; margin-right:6px;"></span>&ge;75% — Severe</div>
  <div><span style="background:#F57C2D; width:14px; height:14px; display:inline-block; border-radius:50%; margin-right:6px;"></span>68–75% — High</div>
  <div><span style="background:#F5C842; width:14px; height:14px; display:inline-block; border-radius:50%; margin-right:6px;"></span>62–68% — Elevated</div>
  <div><span style="background:#52B748; width:14px; height:14px; display:inline-block; border-radius:50%; margin-right:6px;"></span>&lt;62% — Manageable</div>
  <div style="margin-top:6px; font-size:10px; color:#888;">Bubble size = client volume<br>Click bubble for full stats</div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

html_path = os.path.join(CHART_DIR, "sa_interactive_map.html")
m.save(html_path)
print(f"  Saved: sa_interactive_map.html")

print("\nAll maps generated.")
