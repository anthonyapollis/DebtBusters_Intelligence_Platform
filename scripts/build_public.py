"""
Build the public/ Netlify folder:
  - Regenerates public/map.html (folium map with nav bar injected)
  - Copies/symlinks static assets are handled by generate_maps.py
Run: python scripts/build_public.py
"""

import os, sys, re

ROOT   = os.path.join(os.path.dirname(__file__), "..")
PUBLIC = os.path.join(ROOT, "public")
CHARTS = os.path.join(ROOT, "charts")
os.makedirs(PUBLIC, exist_ok=True)

# ── Step 1: regenerate the folium map into charts/ ────────────────────────────
print("Generating maps (folium + matplotlib)…")
exec(open(os.path.join(ROOT, "scripts", "generate_maps.py"), encoding="utf-8").read())

# ── Step 2: read the raw folium HTML ──────────────────────────────────────────
src = os.path.join(CHARTS, "sa_interactive_map.html")
with open(src, encoding="utf-8") as f:
    html = f.read()

# ── Step 3: build the nav bar HTML to inject ──────────────────────────────────
NAV_CSS = """
<style id="db-nav-style">
#db-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 99999;
  background: rgba(10,30,61,0.97);
  border-bottom: 2px solid #E8363B;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px; height: 52px;
  font-family: 'Segoe UI', Arial, sans-serif;
  backdrop-filter: blur(8px);
}
#db-nav .brand {
  font-size: 14px; font-weight: 700; color: #fff; white-space: nowrap;
}
#db-nav .brand span { color: #E8363B; }
#db-nav .links { display: flex; gap: 6px; flex-wrap: wrap; }
#db-nav .links a {
  color: #fff; text-decoration: none;
  padding: 5px 13px; border-radius: 18px; font-size: 12px; font-weight: 600;
  border: 1px solid rgba(255,255,255,0.2);
  transition: all 0.18s; white-space: nowrap;
}
#db-nav .links a:hover { background: #E8363B; border-color: #E8363B; }
#db-nav .links a.primary { background: #E8363B; border-color: #E8363B; }
#db-nav .links a.teal    { background: #00A99D; border-color: #00A99D; }
/* Push leaflet map down to clear nav */
.folium-map { margin-top: 52px !important; }
body > div:first-of-type { padding-top: 52px; }
</style>
"""

NAV_HTML = """
<div id="db-nav">
  <div class="brand"><span>DebtBusters</span> Intelligence Platform</div>
  <div class="links">
    <a href="index.html">&#127968; Home</a>
    <a href="index.html#kpis">&#128200; KPIs</a>
    <a href="index.html#models">&#129302; ML Models</a>
    <a href="index.html#deliverables">&#128230; Deliverables</a>
    <a href="https://github.com/anthonyapollis/DebtBusters_Intelligence_Platform/raw/master/ebook/DebtBusters_Intelligence_Platform_Ebook_v7.docx"
       target="_blank" class="teal">&#128218; Ebook</a>
    <a href="https://github.com/anthonyapollis/DebtBusters_Intelligence_Platform/raw/master/excel/DebtBusters_Intelligence_Report.xlsx"
       target="_blank">&#128202; KPI Excel</a>
    <a href="https://github.com/anthonyapollis/DebtBusters_Intelligence_Platform/raw/master/excel/ML_Validation_Report.xlsx"
       target="_blank">&#129302; ML Excel</a>
    <a href="https://github.com/anthonyapollis/DebtBusters_Intelligence_Platform"
       target="_blank" class="primary">&#128279; GitHub</a>
  </div>
</div>
"""

# ── Step 4: inject before </head> and after <body> ────────────────────────────
if "</head>" in html:
    html = html.replace("</head>", NAV_CSS + "\n</head>", 1)
else:
    html = NAV_CSS + html

if "<body>" in html:
    html = html.replace("<body>", "<body>\n" + NAV_HTML, 1)
else:
    # folium sometimes omits <body>
    html = NAV_HTML + html

# ── Step 5: write to public/map.html ─────────────────────────────────────────
dest = os.path.join(PUBLIC, "map.html")
with open(dest, "w", encoding="utf-8") as f:
    f.write(html)

print(f"  Saved: public/map.html ({os.path.getsize(dest)//1024} KB)")
print("\npublic/ folder ready for Netlify.")
