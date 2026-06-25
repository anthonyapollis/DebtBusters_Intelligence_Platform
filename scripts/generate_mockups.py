"""
DebtBusters Intelligence Platform — UI Mockup Generator
Generates professional platform screenshots for ebook embedding.
Run: python generate_mockups.py
"""

import os, math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.gridspec as gridspec
from matplotlib.table import Table

sys_path = os.path.dirname(__file__)
CHART_DIR = os.path.join(sys_path, "..", "charts")
os.makedirs(CHART_DIR, exist_ok=True)

# ── Databricks colour palette ──────────────────────────────────────────────────
DB_BG      = "#1E1E2E"
DB_CELL    = "#252540"
DB_BORDER  = "#3A3A5C"
DB_TEAL    = "#00A99D"
DB_ORANGE  = "#FF8C00"
DB_GREEN   = "#4EC94E"
DB_PURPLE  = "#9B59FF"
DB_TEXT    = "#E0E0F0"
DB_COMMENT = "#6A8A6A"
DB_STRING  = "#CE9178"
DB_KEYWORD = "#569CD6"
DB_NUM     = "#B5CEA8"

AZ_BLUE    = "#0078D4"
AZ_BG      = "#F3F2F1"
AZ_WHITE   = "#FFFFFF"
AZ_BORDER  = "#D1D1D1"
AZ_GREEN   = "#107C10"
AZ_TEXT    = "#323130"
AZ_LIGHT   = "#EFF6FC"

# ── helpers ────────────────────────────────────────────────────────────────────
def save(name):
    path = os.path.join(CHART_DIR, name)
    plt.savefig(path, bbox_inches="tight", dpi=150, facecolor=plt.gcf().get_facecolor())
    print(f"  Saved: {name}")
    plt.close("all")

def rounded_box(ax, x, y, w, h, color, alpha=1.0, radius=0.02, lw=0, edgecolor="none"):
    box = FancyBboxPatch((x, y), w, h,
                          boxstyle=f"round,pad=0,rounding_size={radius}",
                          facecolor=color, alpha=alpha, linewidth=lw, edgecolor=edgecolor,
                          transform=ax.transData, clip_on=False)
    ax.add_patch(box)
    return box

def db_text(ax, x, y, text, color=DB_TEXT, size=7.5, mono=True, bold=False, ha="left"):
    family = "monospace" if mono else "sans-serif"
    ax.text(x, y, text, color=color, fontsize=size, fontfamily=family,
            ha=ha, va="top", fontweight="bold" if bold else "normal")

# ══════════════════════════════════════════════════════════════════════════════
# MOCKUP 1 — DATABRICKS NOTEBOOK: Silver Layer — Client Deduplication
# ══════════════════════════════════════════════════════════════════════════════
def mockup_databricks_notebook():
    fig = plt.figure(figsize=(14, 9), facecolor=DB_BG)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14); ax.set_ylim(0, 9)
    ax.axis("off")

    # ── Top bar ──
    rounded_box(ax, 0, 8.6, 14, 0.4, "#12122A")
    ax.text(0.2, 8.84, "  DebtBusters Intelligence Platform", color=DB_TEAL,
            fontsize=9, fontweight="bold", va="center", fontfamily="sans-serif")
    ax.text(9.5, 8.84, "silver/01_silver_clients.py", color=DB_TEXT,
            fontsize=8, va="center", fontfamily="monospace")
    for i, (label, col) in enumerate([("File","#AAA"),("Edit","#AAA"),("Run","#AAA"),
                                       ("View","#AAA"),("Help","#AAA")]):
        ax.text(6.5 + i*0.7, 8.84, label, color=col, fontsize=7.5, va="center")

    # ── Notebook breadcrumb ──
    rounded_box(ax, 0, 8.25, 14, 0.35, "#1A1A30")
    ax.text(0.3, 8.44, "debtbusters_silver", color=DB_TEAL, fontsize=8, va="center")
    ax.text(2.0, 8.44, ">", color="#666", fontsize=8, va="center")
    ax.text(2.2, 8.44, "01_silver_clients", color=DB_TEXT, fontsize=8, va="center")

    # ── Cell 1: Markdown header ──
    rounded_box(ax, 0.2, 7.5, 13.6, 0.65, DB_CELL, radius=0.015,
                lw=1, edgecolor=DB_BORDER)
    ax.text(0.4, 8.12, "Md", color="#AAA", fontsize=6.5, va="top", fontfamily="monospace")
    ax.text(0.8, 8.08, "## Silver Layer — Client Deduplication & Data Quality",
            color="#FFFFFF", fontsize=9, va="top", fontweight="bold")
    ax.text(0.8, 7.82, "Applies ROW_NUMBER() deduplication, email validation, and DQ pass/reject tagging.",
            color="#AAAACC", fontsize=7.5, va="top")

    # ── Cell 2: PySpark code ──
    rounded_box(ax, 0.2, 3.5, 13.6, 3.85, DB_CELL, radius=0.015,
                lw=1, edgecolor=DB_BORDER)
    ax.text(0.4, 7.3, "[1]", color="#666", fontsize=7, va="top", fontfamily="monospace")

    code_lines = [
        ([("from", DB_KEYWORD), (" pyspark.sql ", DB_TEXT), ("import", DB_KEYWORD),
          (" functions ", DB_TEXT), ("as", DB_KEYWORD), (" F, Window", DB_TEXT)], 7.28),
        ([("from", DB_KEYWORD), (" pyspark.sql.types ", DB_TEXT), ("import", DB_KEYWORD),
          (" StructType, StructField, StringType, LongType", DB_TEXT)], 7.10),
        ([("", DB_TEXT)], 6.92),
        ([("# ── Load Bronze ─────────────────────────────────────", DB_COMMENT)], 6.74),
        ([("bronze_clients ", DB_TEXT), ("=", DB_KEYWORD),
          (" spark.read.format(", DB_TEXT), ('"delta"', DB_STRING),
          (").load(", DB_TEXT), ('"dbfs:/mnt/adls/bronze/clients"', DB_STRING),
          (")", DB_TEXT)], 6.56),
        ([("", DB_TEXT)], 6.38),
        ([("# ── Deduplication via ROW_NUMBER window ─────────────", DB_COMMENT)], 6.20),
        ([("window_spec ", DB_TEXT), ("=", DB_KEYWORD),
          (" Window.partitionBy(", DB_TEXT), ('"client_id"', DB_STRING),
          (").orderBy(F.col(", DB_TEXT), ('"created_date"', DB_STRING), (").desc())", DB_TEXT)], 6.02),
        ([("deduped ", DB_TEXT), ("=", DB_KEYWORD),
          (" bronze_clients.withColumn(", DB_TEXT), ('"row_num"', DB_STRING),
          (", F.row_number().over(window_spec))", DB_TEXT)], 5.84),
        ([("              .filter(F.col(", DB_TEXT), ('"row_num"', DB_STRING),
          (") == ", DB_TEXT), ("1", DB_NUM), (")", DB_TEXT)], 5.66),
        ([("", DB_TEXT)], 5.48),
        ([("# ── Email validation regex ──────────────────────────", DB_COMMENT)], 5.30),
        ([("EMAIL_PATTERN ", DB_TEXT), ("=", DB_KEYWORD),
          (' r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"', DB_STRING)], 5.12),
        ([("silver ", DB_TEXT), ("=", DB_KEYWORD),
          (" deduped.withColumn(", DB_TEXT), ('"email_valid"', DB_STRING),
          (", F.col(", DB_TEXT), ('"email"', DB_STRING), (").rlike(EMAIL_PATTERN))", DB_TEXT)], 4.94),
        ([("          .withColumn(", DB_TEXT), ('"dq_status"', DB_STRING),
          (", F.when(F.col(", DB_TEXT), ('"email_valid"', DB_STRING),
          (") & F.col(", DB_TEXT), ('"gross_income"', DB_STRING), (") > ", DB_TEXT),
          ("0", DB_NUM), (", ", DB_TEXT), ('"PASS"', DB_STRING), (").otherwise(", DB_TEXT),
          ('"REJECT"', DB_STRING), ("))", DB_TEXT)], 4.76),
        ([("", DB_TEXT)], 4.58),
        ([("silver.write.format(", DB_TEXT), ('"delta"', DB_STRING),
          (").mode(", DB_TEXT), ('"overwrite"', DB_STRING),
          (").partitionBy(", DB_TEXT), ('"province"', DB_STRING),
          (").save(", DB_TEXT), ('"dbfs:/mnt/adls/silver/clients"', DB_STRING),
          (")", DB_TEXT)], 4.40),
        ([("print(f", DB_TEXT), ('"Silver clients: {silver.count():,} rows written"', DB_STRING),
          (")", DB_TEXT)], 4.22),
    ]
    for spans, y in code_lines:
        x_cur = 0.8
        for text, color in spans:
            ax.text(x_cur, y, text, color=color, fontsize=7.5, va="top", fontfamily="monospace")
            x_cur += len(text) * 0.057

    # ── Cell 2 output ──
    rounded_box(ax, 0.2, 2.9, 13.6, 0.55, "#0F0F1E", radius=0.01)
    ax.text(0.5, 3.42, "Silver clients: 79,847 rows written", color=DB_GREEN,
            fontsize=8, va="top", fontfamily="monospace")
    ax.text(0.5, 3.18, "DQ PASS: 76,219  |  DQ REJECT: 3,628  |  Duplicates removed: 153",
            color=DB_TEXT, fontsize=7.5, va="top", fontfamily="monospace")

    # ── Cell 3: display() output table ──
    rounded_box(ax, 0.2, 0.15, 13.6, 2.6, DB_CELL, radius=0.015, lw=1, edgecolor=DB_BORDER)
    ax.text(0.4, 2.7, "[2]", color="#666", fontsize=7, va="top", fontfamily="monospace")
    ax.text(0.8, 2.68, "silver.select('client_id','province','dq_status','email_valid').show(6, truncate=False)",
            color=DB_TEXT, fontsize=7.5, va="top", fontfamily="monospace")

    # Table output
    headers = ["client_id", "province", "dq_status", "email_valid"]
    rows = [
        ["3a9f1c2d-...", "Gauteng",      "PASS",   "true"],
        ["7b3e8a14-...", "Western Cape", "PASS",   "true"],
        ["1d5f9e3c-...", "KwaZulu-Natal","REJECT", "false"],
        ["9c2a7b6f-...", "Gauteng",      "PASS",   "true"],
        ["4e8d3c1a-...", "Eastern Cape", "PASS",   "true"],
        ["2f7a9e5b-...", "Limpopo",      "PASS",   "true"],
    ]
    col_x = [0.5, 3.0, 6.5, 9.5]
    col_w = [2.4, 3.2, 2.7, 2.0]
    y_h   = 2.35
    for i, (h, x, w) in enumerate(zip(headers, col_x, col_w)):
        rounded_box(ax, x-0.05, y_h-0.02, w, 0.22, "#2A2A50")
        ax.text(x, y_h+0.12, h, color=DB_TEAL, fontsize=7.5, va="top",
                fontfamily="monospace", fontweight="bold")
    for ri, row in enumerate(rows):
        y_r = y_h - 0.25*(ri+1)
        bg  = "#1A1A2E" if ri % 2 == 0 else DB_CELL
        rounded_box(ax, col_x[0]-0.05, y_r-0.04, 11.5, 0.22, bg, radius=0.005)
        for ci, (val, x) in enumerate(zip(row, col_x)):
            col = DB_GREEN if val == "PASS" else (DB_ORANGE if val in ("REJECT","false") else DB_TEXT)
            ax.text(x, y_r+0.10, val, color=col, fontsize=7, va="top", fontfamily="monospace")

    # ── Status bar ──
    rounded_box(ax, 0, 0, 14, 0.14, "#12122A")
    ax.text(0.3, 0.09, "Cluster: debtbusters-ml-cluster (10.4 LTS ML)  |  "
            "State: RUNNING  |  Workers: 4  |  Python 3.11",
            color="#888", fontsize=6.5, va="center")

    fig.text(0.5, -0.01, "Screenshot: Databricks Notebook — 02_silver/01_silver_clients.py",
             ha="center", color="#666", fontsize=7, style="italic")
    save("mockup_01_databricks_notebook.png")


# ══════════════════════════════════════════════════════════════════════════════
# MOCKUP 2 — DELTA LAKE TABLE SCHEMA & PROPERTIES
# ══════════════════════════════════════════════════════════════════════════════
def mockup_delta_schema():
    fig = plt.figure(figsize=(14, 8), facecolor=DB_BG)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14); ax.set_ylim(0, 8)
    ax.axis("off")

    # Top bar
    rounded_box(ax, 0, 7.6, 14, 0.4, "#12122A")
    ax.text(0.2, 7.84, "  Databricks  |  Data  >  debtbusters_gold  >  fact_payment",
            color=DB_TEAL, fontsize=8.5, va="center", fontfamily="sans-serif")

    # Left nav
    rounded_box(ax, 0, 0, 2.2, 7.6, "#1A1A2E")
    for i, (icon, label, active) in enumerate([
        ("⌂", "Home", False), ("≡", "Workspace", False), ("⚙", "Compute", False),
        ("▷", "Workflows", False), ("◈", "Delta Live", False), ("☰", "Data", True),
        ("⊞", "SQL Editor", False), ("∿", "ML", False),
    ]):
        y = 7.3 - i*0.55
        if active:
            rounded_box(ax, 0.05, y-0.1, 2.05, 0.4, "#252550", radius=0.01)
            ax.text(0.25, y+0.08, icon, color=DB_TEAL, fontsize=10, va="center")
            ax.text(0.55, y+0.08, label, color=DB_TEAL, fontsize=8, va="center", fontweight="bold")
        else:
            ax.text(0.25, y+0.08, icon, color="#666", fontsize=9, va="center")
            ax.text(0.55, y+0.08, label, color="#888", fontsize=7.5, va="center")

    # Main panel
    rounded_box(ax, 2.3, 0.1, 11.5, 7.3, DB_CELL, radius=0.01, lw=1, edgecolor=DB_BORDER)

    # Table header
    ax.text(2.6, 7.28, "fact_payment", color=DB_TEXT, fontsize=12, va="top", fontweight="bold")
    ax.text(2.6, 7.05, "debtbusters_gold  ·  Delta  ·  1,500,000 rows  ·  Partitioned by payment_year, payment_month",
            color="#888", fontsize=7.5, va="top")

    # Tabs
    for i, (tab, active) in enumerate([("Schema", True), ("Sample Data", False),
                                         ("Details", False), ("History", False), ("Permissions", False)]):
        x = 2.6 + i*1.7
        if active:
            rounded_box(ax, x-0.1, 6.5, 1.6, 0.3, "#1E1E4E", radius=0.01)
            ax.text(x+0.65, 6.67, tab, color=DB_TEAL, fontsize=8, va="center", ha="center", fontweight="bold")
            ax.plot([x-0.1, x+1.5], [6.5, 6.5], color=DB_TEAL, lw=2)
        else:
            ax.text(x+0.65, 6.67, tab, color="#888", fontsize=8, va="center", ha="center")

    # Schema table
    ax.plot([2.4, 13.6], [6.42, 6.42], color=DB_BORDER, lw=0.8)
    cols = ["Column Name", "Data Type", "Nullable", "Comment"]
    col_x = [2.6, 5.8, 8.4, 10.0]
    for h, x in zip(cols, col_x):
        ax.text(x, 6.32, h, color="#AAAACC", fontsize=8, va="top", fontweight="bold")
    ax.plot([2.4, 13.6], [6.12, 6.12], color=DB_BORDER, lw=0.5)

    schema_rows = [
        ("payment_id",              "STRING",    "false", "UUID primary key"),
        ("case_id",                 "STRING",    "false", "FK → fact_debt_review_case"),
        ("client_id",               "STRING",    "false", "FK → dim_client"),
        ("creditor_id",             "STRING",    "false", "FK → dim_creditor"),
        ("payment_date",            "DATE",      "false", "Transaction date"),
        ("payment_month",           "STRING",    "true",  "YYYY-MM partition key"),
        ("payment_year",            "INTEGER",   "true",  "Year partition key"),
        ("expected_payment_amount", "DECIMAL(12,2)","false","PDA expected amount"),
        ("actual_payment_amount",   "DECIMAL(12,2)","false","Amount received by PDA"),
        ("distribution_amount",     "DECIMAL(12,2)","true", "Amount distributed to creditors"),
        ("arrears_amount",          "DECIMAL(12,2)","true", "Shortfall (expected - actual)"),
        ("collection_rate",         "DECIMAL(8,4)", "true", "actual / expected ratio"),
        ("payment_status",          "STRING",    "false", "Full | Partial | Missed"),
        ("missed_payment_flag",     "BOOLEAN",   "false", "True if payment_status = Missed"),
        ("pda_reference",           "STRING",    "true",  "PDA transaction reference"),
        ("_ingestion_timestamp",    "TIMESTAMP", "false", "Bronze ingestion time"),
        ("_source_file",            "STRING",    "true",  "Source file path (ADLS)"),
    ]
    for ri, (name, dtype, nullable, comment) in enumerate(schema_rows):
        y = 5.92 - ri*0.325
        bg = "#1E1E3A" if ri % 2 == 0 else DB_CELL
        rounded_box(ax, 2.4, y-0.07, 11.1, 0.3, bg, radius=0.005)
        ax.text(col_x[0], y+0.08, name, color=DB_TEXT, fontsize=7.5, va="top", fontfamily="monospace")
        ax.text(col_x[1], y+0.08, dtype, color=DB_PURPLE, fontsize=7.5, va="top", fontfamily="monospace")
        null_col = DB_ORANGE if nullable=="true" else DB_GREEN
        ax.text(col_x[2], y+0.08, nullable, color=null_col, fontsize=7.5, va="top", fontfamily="monospace")
        ax.text(col_x[3], y+0.08, comment, color="#AAAACC", fontsize=7, va="top")

    # Properties sidebar
    rounded_box(ax, 10.2, 0.2, 3.0, 5.9, "#1A1A30", radius=0.01, lw=1, edgecolor=DB_BORDER)
    ax.text(10.4, 6.05, "Table Properties", color=DB_TEXT, fontsize=8, va="top", fontweight="bold")
    ax.plot([10.2, 13.2], [5.88, 5.88], color=DB_BORDER, lw=0.5)
    props = [
        ("Format",       "Delta Lake"),
        ("Location",     "dbfs:/mnt/adls/gold/fact_payment"),
        ("Rows",         "1,500,000"),
        ("Size",         "197.7 MB"),
        ("Partitions",   "payment_year, payment_month"),
        ("Z-ORDER",      "client_id, payment_date"),
        ("Created",      "2024-01-15"),
        ("Last Modified","2025-06-25"),
        ("Owner",        "anthony.apollis@confluent.co.za"),
        ("Time Travel",  "30 days retention"),
        ("ACID",         "Enabled"),
    ]
    for i, (k, v) in enumerate(props):
        y = 5.72 - i*0.48
        ax.text(10.4, y, k, color="#AAAACC", fontsize=6.5, va="top")
        ax.text(10.4, y-0.18, v, color=DB_TEXT, fontsize=7, va="top", fontfamily="monospace")

    fig.text(0.5, -0.01, "Screenshot: Databricks Data Explorer — debtbusters_gold.fact_payment (Delta Lake)",
             ha="center", color="#666", fontsize=7, style="italic")
    save("mockup_02_delta_schema.png")


# ══════════════════════════════════════════════════════════════════════════════
# MOCKUP 3 — MLFLOW EXPERIMENT TRACKING
# ══════════════════════════════════════════════════════════════════════════════
def mockup_mlflow():
    fig = plt.figure(figsize=(14, 7.5), facecolor=DB_BG)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14); ax.set_ylim(0, 7.5)
    ax.axis("off")

    # Header
    rounded_box(ax, 0, 7.1, 14, 0.4, "#12122A")
    ax.text(0.2, 7.34, "  MLflow  |  Experiments  >  debtbusters_lead_conversion_v3",
            color=DB_TEAL, fontsize=8.5, va="center")

    # Title bar
    rounded_box(ax, 0, 6.6, 14, 0.48, "#1E1E2E", lw=1, edgecolor=DB_BORDER)
    ax.text(0.3, 6.88, "debtbusters_lead_conversion_v3", color=DB_TEXT,
            fontsize=10, va="center", fontweight="bold")
    ax.text(0.3, 6.66, "Artifact Location: dbfs:/mlflow/debtbusters/lead_conversion  ·  "
            "Experiment ID: 4829015736182",
            color="#888", fontsize=7, va="center")

    # Tabs
    for i, (tab, active) in enumerate([("Runs (12)", True), ("Compare", False),
                                         ("Charts", False), ("Artifacts", False)]):
        x = 0.3 + i * 1.8
        col = DB_TEAL if active else "#888"
        ax.text(x, 6.45, tab, color=col, fontsize=8, va="center",
                fontweight="bold" if active else "normal")
        if active:
            ax.plot([x-0.05, x+len(tab)*0.058+0.05], [6.35, 6.35], color=DB_TEAL, lw=2)

    ax.plot([0, 14], [6.33, 6.33], color=DB_BORDER, lw=0.7)

    # Table header
    headers = ["Run Name", "Status", "Start Time", "Duration", "AUC-ROC", "Avg Precision",
               "n_estimators", "max_depth", "learning_rate", "scale_pos_weight"]
    col_positions = [0.2, 2.4, 3.3, 4.6, 5.5, 6.5, 7.6, 8.6, 9.6, 10.8]
    rounded_box(ax, 0, 6.0, 14, 0.3, "#1A1A2E")
    for h, x in zip(headers, col_positions):
        ax.text(x, 6.2, h, color="#AAAACC", fontsize=6.8, va="center", fontweight="bold")

    ax.plot([0, 14], [5.98, 5.98], color=DB_BORDER, lw=0.5)

    # Runs data
    runs = [
        ("xgb_run_012", "✓ FINISHED", "25 Jun 14:37", "3m 42s", "0.7437", "0.6812", "300", "7", "0.05", "3.2"),
        ("xgb_run_011", "✓ FINISHED", "25 Jun 14:28", "3m 15s", "0.7401", "0.6790", "200", "7", "0.05", "3.2"),
        ("xgb_run_010", "✓ FINISHED", "25 Jun 14:19", "4m 01s", "0.7389", "0.6741", "300", "9", "0.05", "3.2"),
        ("xgb_run_009", "✓ FINISHED", "25 Jun 14:05", "3m 28s", "0.7312", "0.6683", "150", "7", "0.10", "3.5"),
        ("xgb_run_008", "✓ FINISHED", "25 Jun 13:52", "2m 59s", "0.7298", "0.6654", "100", "5", "0.10", "3.2"),
        ("xgb_run_007", "✓ FINISHED", "25 Jun 13:41", "3m 44s", "0.7277", "0.6631", "200", "9", "0.05", "4.0"),
        ("xgb_run_006", "✓ FINISHED", "25 Jun 13:28", "2m 47s", "0.7241", "0.6598", "100", "7", "0.05", "3.2"),
        ("xgb_run_005", "✓ FINISHED", "25 Jun 13:17", "5m 12s", "0.7189", "0.6542", "500", "11", "0.01", "3.2"),
        ("xgb_run_004", "✓ FINISHED", "25 Jun 13:02", "1m 55s", "0.7134", "0.6488", "50",  "5", "0.10", "2.5"),
        ("xgb_run_003", "✗ FAILED",   "25 Jun 12:55", "0m 12s", "—",      "—",      "300", "15", "0.001","3.2"),
        ("xgb_run_002", "✓ FINISHED", "25 Jun 12:40", "2m 33s", "0.7021", "0.6412", "100", "5", "0.10", "3.2"),
        ("xgb_run_001", "✓ FINISHED", "25 Jun 12:28", "2m 18s", "0.6893", "0.6298", "100", "5", "0.15", "3.2"),
    ]
    for ri, row in enumerate(runs):
        y = 5.82 - ri * 0.46
        bg = "#1E2A2E" if ri == 0 else ("#1E1E3A" if ri % 2 == 0 else DB_CELL)
        rounded_box(ax, 0, y-0.1, 14, 0.42, bg, radius=0.005)
        if ri == 0:
            rounded_box(ax, 0, y-0.1, 0.06, 0.42, DB_TEAL)   # best run highlight
        for ci, (val, x) in enumerate(zip(row, col_positions)):
            col = (DB_TEAL if ci == 4 and ri == 0 else
                   DB_GREEN if val.startswith("✓") else
                   DB_ORANGE if val.startswith("✗") else
                   DB_NUM if ci >= 4 else DB_TEXT)
            fw = "bold" if ri == 0 and ci == 4 else "normal"
            ax.text(x, y+0.08, val, color=col, fontsize=6.8, va="center",
                    fontfamily="monospace", fontweight=fw)

    # Best run badge
    rounded_box(ax, 0.1, 5.72, 1.4, 0.22, DB_TEAL, alpha=0.2, radius=0.01)
    ax.text(0.8, 5.83, "BEST RUN", color=DB_TEAL, fontsize=7, va="center",
            ha="center", fontweight="bold")

    # Model info panel at bottom
    rounded_box(ax, 0.1, 0.1, 13.8, 1.6, "#1A1A30", radius=0.01, lw=1, edgecolor=DB_BORDER)
    ax.text(0.3, 1.65, "Registered Model: debtbusters-lead-conversion  ·  Stage: Production  ·  "
            "Version: 3  ·  Registered: 2025-06-25 14:45",
            color=DB_TEXT, fontsize=7.5, va="top")
    model_details = [
        ("Algorithm:", "XGBoost (xgb.XGBClassifier)"),
        ("Features:", "14 (lead_score, source_channel_enc, utm_source_enc, cost_per_lead, "
                      "gross_income, dti_ratio, num_creditors, age, risk_score, ...)"),
        ("Training rows:", "40,000 (stratified 80/20 split)"),
        ("Serving endpoint:", "debtbusters-lead-scoring  |  REST API  |  latency p95: 28ms"),
        ("SHAP explainability:", "Enabled  |  Top feature: lead_score (importance 0.342)"),
    ]
    for i, (k, v) in enumerate(model_details):
        y = 1.35 - i*0.25
        ax.text(0.3, y, k, color="#AAAACC", fontsize=7, va="top", fontweight="bold")
        ax.text(2.0, y, v, color=DB_TEXT, fontsize=7, va="top")

    fig.text(0.5, -0.01, "Screenshot: MLflow Experiment Tracking — Lead Conversion Model (XGBoost, AUC 0.744)",
             ha="center", color="#666", fontsize=7, style="italic")
    save("mockup_03_mlflow.png")


# ══════════════════════════════════════════════════════════════════════════════
# MOCKUP 4 — AZURE DATA FACTORY PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
def mockup_adf():
    fig = plt.figure(figsize=(14, 8), facecolor=AZ_BG)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14); ax.set_ylim(0, 8)
    ax.axis("off")

    # Azure header bar
    rounded_box(ax, 0, 7.6, 14, 0.4, AZ_BLUE)
    ax.text(0.2, 7.84, "Microsoft Azure  |  Data Factory  >  debtbusters-adf-prod  >  "
            "Pipelines  >  PL_Bronze_Full_Load",
            color="white", fontsize=8, va="center")

    # Toolbar
    rounded_box(ax, 0, 7.15, 14, 0.43, AZ_WHITE, lw=1, edgecolor=AZ_BORDER)
    for i, (icon, label) in enumerate([("▷", "Run"), ("⚙", "Validate"), ("↻", "Refresh"),
                                         ("☁", "Publish"), ("○", "Debug")]):
        x = 0.3 + i*1.2
        ax.text(x, 7.39, icon, color=AZ_BLUE, fontsize=9, va="center")
        ax.text(x+0.2, 7.39, label, color=AZ_TEXT, fontsize=8, va="center")

    ax.text(10.5, 7.39, "Last run: Success  ·  25 Jun 2025, 02:00 UTC  ·  Duration: 4m 12s",
            color="#666", fontsize=7.5, va="center")

    # Left panel — Activities
    rounded_box(ax, 0, 0, 2.2, 7.15, AZ_WHITE, lw=1, edgecolor=AZ_BORDER)
    rounded_box(ax, 0, 6.8, 2.2, 0.35, "#EEF4FB")
    ax.text(0.1, 6.99, "Activities", color=AZ_BLUE, fontsize=8.5, va="center", fontweight="bold")
    activities_panel = [
        ("▷", "Copy Data", "#0078D4"),
        ("⊞", "Databricks Notebook", "#8B4DC8"),
        ("⋄", "Validation", "#107C10"),
        ("⌛", "Wait", "#F57C2D"),
        ("✉", "Web Activity", "#1E88E5"),
        ("▣", "Set Variable", "#E8363B"),
        ("◈", "ForEach", "#00A99D"),
        ("⚡", "Trigger", "#F5C842"),
    ]
    for i, (icon, name, col) in enumerate(activities_panel):
        y = 6.5 - i*0.62
        ax.text(0.2, y, icon, color=col, fontsize=9, va="center")
        ax.text(0.5, y, name, color=AZ_TEXT, fontsize=7.5, va="center")

    # Main canvas
    rounded_box(ax, 2.3, 0, 11.7, 7.15, "#F8F9FB", lw=1, edgecolor=AZ_BORDER)

    # Pipeline title
    ax.text(2.5, 6.98, "PL_Bronze_Full_Load  —  DebtBusters Intelligence Platform",
            color=AZ_TEXT, fontsize=9, va="top", fontweight="bold")
    ax.text(2.5, 6.72, "Orchestrates full Bronze ingestion from ADLS → Databricks Delta Lake  ·  Trigger: Daily 02:00 UTC",
            color="#666", fontsize=7.5, va="top")

    # Pipeline activities
    activities = [
        (2.6,  4.5, 2.2, 1.0, "ACT_Mount_ADLS",        "Databricks Notebook",      "#8B4DC8", "00_setup/01_mount_storage"),
        (5.2,  5.2, 2.2, 0.9, "ACT_Bronze_Clients",     "Databricks Notebook",      "#8B4DC8", "01_bronze/01_bronze_clients"),
        (5.2,  4.0, 2.2, 0.9, "ACT_Bronze_Leads",       "Databricks Notebook",      "#8B4DC8", "01_bronze/02_bronze_leads"),
        (5.2,  2.8, 2.2, 0.9, "ACT_Bronze_Cases",       "Databricks Notebook",      "#8B4DC8", "01_bronze/04_bronze_batch"),
        (7.8,  4.5, 2.2, 1.0, "ACT_Validate_Bronze",    "Validation",               "#107C10", "DQ: row count + schema"),
        (10.4, 5.2, 2.2, 0.9, "ACT_Silver_Clients",     "Databricks Notebook",      "#8B4DC8", "02_silver/01_silver_clients"),
        (10.4, 4.0, 2.2, 0.9, "ACT_Silver_Leads",       "Databricks Notebook",      "#8B4DC8", "02_silver/02_silver_leads"),
        (10.4, 2.8, 2.2, 0.9, "ACT_Silver_Cases",       "Databricks Notebook",      "#8B4DC8", "02_silver/03_silver_cases"),
        (2.6,  1.5, 2.2, 0.9, "ACT_Notify_Start",       "Web Activity",             "#1E88E5", "Teams: Pipeline started"),
        (10.4, 1.5, 2.2, 0.9, "ACT_Notify_Complete",    "Web Activity",             "#1E88E5", "Teams: Pipeline complete"),
    ]

    for (x, y, w, h, name, atype, col, detail) in activities:
        rounded_box(ax, x, y, w, h, AZ_WHITE, radius=0.02, lw=1.5, edgecolor=col)
        rounded_box(ax, x, y+h-0.22, w, 0.22, col, radius=0.01)
        ax.text(x+w/2, y+h-0.11, atype, color="white", fontsize=6.2, va="center",
                ha="center", fontweight="bold")
        ax.text(x+w/2, y+h/2-0.05, name, color=AZ_TEXT, fontsize=7.2, va="center",
                ha="center", fontweight="bold")
        ax.text(x+w/2, y+0.12, detail, color="#666", fontsize=6, va="bottom",
                ha="center", style="italic")

    # Arrows
    arrows = [
        (4.8, 5.0, 5.2, 5.65), (4.8, 5.0, 5.2, 4.45), (4.8, 5.0, 5.2, 3.25),
        (7.4, 5.65, 7.8, 5.0), (7.4, 4.45, 7.8, 5.0), (7.4, 3.25, 7.8, 5.0),
        (10.0, 5.0, 10.4, 5.65), (10.0, 5.0, 10.4, 4.45), (10.0, 5.0, 10.4, 3.25),
        (2.6+1.1, 1.5+0.45, 2.6+1.1, 4.5),
        (10.4+1.1, 2.8, 10.4+1.1, 1.5+0.9),
    ]
    for (x1, y1, x2, y2) in arrows:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color=AZ_BLUE, lw=1.5,
                                   connectionstyle="arc3,rad=0"))

    # Run status footer
    rounded_box(ax, 2.3, 0, 11.7, 0.55, AZ_WHITE, lw=1, edgecolor=AZ_BORDER)
    runs_info = [
        ("Status:", "Succeeded", "#107C10"),
        ("Activities run:", "10 / 10", AZ_TEXT),
        ("Start:", "2025-06-25 02:00:02 UTC", AZ_TEXT),
        ("End:", "2025-06-25 02:04:14 UTC", AZ_TEXT),
        ("Duration:", "4m 12s", AZ_TEXT),
        ("Rows copied:", "3,960,150", AZ_BLUE),
    ]
    for i, (k, v, col) in enumerate(runs_info):
        x = 2.5 + i*1.95
        ax.text(x, 0.38, k, color="#888", fontsize=6.5, va="center")
        ax.text(x, 0.16, v, color=col, fontsize=7, va="center", fontweight="bold" if col != AZ_TEXT else "normal")

    fig.text(0.5, -0.01, "Screenshot: Azure Data Factory — PL_Bronze_Full_Load Pipeline (Daily Orchestration)",
             ha="center", color="#666", fontsize=7, style="italic")
    save("mockup_04_adf_pipeline.png")


# ══════════════════════════════════════════════════════════════════════════════
# MOCKUP 5 — STAR SCHEMA ERD (Gold Layer)
# ══════════════════════════════════════════════════════════════════════════════
def mockup_star_schema():
    fig = plt.figure(figsize=(14, 9), facecolor="#F0F4F8")
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14); ax.set_ylim(0, 9)
    ax.axis("off")

    # Background
    rounded_box(ax, 0, 8.65, 14, 0.35, AZ_BLUE)
    ax.text(7, 8.82, "DebtBusters Intelligence Platform — Gold Layer Star Schema",
            color="white", fontsize=10, va="center", ha="center", fontweight="bold")

    def draw_table(x, y, title, fields, width=2.6, title_color=AZ_BLUE, is_fact=False):
        row_h = 0.26
        h = row_h * (len(fields) + 1) + 0.1
        # Shadow
        rounded_box(ax, x+0.06, y-h-0.06, width, h, "#CCCCCC", radius=0.04)
        # Body
        rounded_box(ax, x, y-h, width, h, AZ_WHITE, radius=0.04, lw=2,
                    edgecolor="#E8363B" if is_fact else AZ_BLUE)
        # Title bar
        tc = "#E8363B" if is_fact else AZ_BLUE
        rounded_box(ax, x, y-row_h, width, row_h, tc, radius=0.04)
        ax.text(x+width/2, y-row_h/2, title, color="white", fontsize=8,
                va="center", ha="center", fontweight="bold")
        for i, (pk, fname, ftype) in enumerate(fields):
            fy = y - row_h*(i+1.5)
            if pk == "PK":
                ax.text(x+0.1, fy, "🔑", fontsize=6, va="center")
            elif pk == "FK":
                ax.text(x+0.1, fy, "🔗", fontsize=6, va="center")
            ax.text(x+0.35, fy, fname, color=AZ_TEXT, fontsize=6.8, va="center",
                    fontfamily="monospace", fontweight="bold" if pk in ("PK","FK") else "normal")
            ax.text(x+width-0.1, fy, ftype, color="#888", fontsize=6, va="center",
                    ha="right", fontfamily="monospace")
        return (x + width/2, y - h/2)   # centre point

    def arrow(ax, x1, y1, x2, y2, style="arc3,rad=0.1"):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#888", lw=1.2,
                                   connectionstyle=style))

    # ── Fact table (centre) ──
    fact_pay = [
        ("PK","payment_id","STRING"),
        ("FK","client_key","STRING"),
        ("FK","creditor_key","STRING"),
        ("FK","date_key","INTEGER"),
        ("FK","case_id","STRING"),
        ("","expected_amount","DECIMAL"),
        ("","actual_amount","DECIMAL"),
        ("","arrears_amount","DECIMAL"),
        ("","collection_rate","DECIMAL"),
        ("","missed_payment_flag","BOOLEAN"),
        ("","payment_status","STRING"),
    ]
    draw_table(5.3, 8.15, "Fact_Payment  ⭐", fact_pay, width=3.4, is_fact=True)

    # ── Dimension tables ──
    dim_client = [
        ("PK","client_key","STRING (SHA-256)"),
        ("","client_id","STRING"),
        ("","age","INTEGER"),
        ("","province","STRING"),
        ("","employment_status","STRING"),
        ("","income_band","STRING"),
        ("","risk_score","DECIMAL"),
        ("","partner_brand","STRING"),
    ]
    draw_table(0.2, 7.8, "Dim_Client", dim_client, width=2.9)

    dim_date = [
        ("PK","date_key","INTEGER"),
        ("","full_date","DATE"),
        ("","year","INTEGER"),
        ("","month","INTEGER"),
        ("","quarter","INTEGER"),
        ("","sa_fin_year","STRING"),
        ("","day_of_week","STRING"),
        ("","is_month_end","BOOLEAN"),
    ]
    draw_table(10.8, 7.8, "Dim_Date", dim_date, width=2.9)

    dim_creditor = [
        ("PK","creditor_key","STRING"),
        ("","creditor_name","STRING"),
        ("","creditor_type","STRING"),
        ("","is_major_bank","BOOLEAN"),
        ("","ncr_registered","BOOLEAN"),
    ]
    draw_table(0.2, 3.2, "Dim_Creditor", dim_creditor, width=2.9)

    dim_counsellor = [
        ("PK","counsellor_key","STRING"),
        ("","counsellor_name","STRING"),
        ("","branch","STRING"),
        ("","ncr_registration","STRING"),
        ("","experience_years","INTEGER"),
    ]
    draw_table(10.8, 3.2, "Dim_Counsellor", dim_counsellor, width=2.9)

    dim_product = [
        ("PK","product_key","STRING"),
        ("","product_name","STRING"),
        ("","product_category","STRING"),
        ("","brand","STRING"),
    ]
    draw_table(5.4, 0.7, "Dim_Product", dim_product, width=3.2)

    # ── Arrows ──
    # Client → Fact
    ax.annotate("", xy=(5.3, 5.3), xytext=(3.1, 5.8),
                arrowprops=dict(arrowstyle="-|>", color=AZ_BLUE, lw=1.5))
    ax.text(4.0, 5.7, "client_key", color=AZ_BLUE, fontsize=7, va="center")

    # Date → Fact
    ax.annotate("", xy=(8.7, 5.3), xytext=(11.2, 5.8),
                arrowprops=dict(arrowstyle="-|>", color=AZ_BLUE, lw=1.5))
    ax.text(9.8, 5.7, "date_key", color=AZ_BLUE, fontsize=7, va="center")

    # Creditor → Fact
    ax.annotate("", xy=(5.5, 4.0), xytext=(3.1, 1.9),
                arrowprops=dict(arrowstyle="-|>", color=AZ_BLUE, lw=1.5))
    ax.text(3.8, 2.8, "creditor_key", color=AZ_BLUE, fontsize=7, va="center")

    # Counsellor → Fact (approximate)
    ax.annotate("", xy=(8.5, 4.0), xytext=(11.0, 1.9),
                arrowprops=dict(arrowstyle="-|>", color=AZ_BLUE, lw=1.5))
    ax.text(9.8, 2.8, "counsellor_key", color=AZ_BLUE, fontsize=7, va="center")

    # Product → Fact
    ax.annotate("", xy=(7.0, 3.0), xytext=(7.0, 1.85),
                arrowprops=dict(arrowstyle="-|>", color=AZ_BLUE, lw=1.5))
    ax.text(7.1, 2.3, "product_key", color=AZ_BLUE, fontsize=7, va="center")

    # Legend
    rounded_box(ax, 0.1, 0.05, 3.5, 0.6, AZ_WHITE, radius=0.02, lw=1, edgecolor=AZ_BORDER)
    rounded_box(ax, 0.2, 0.42, 0.25, 0.15, "#E8363B", radius=0.01)
    ax.text(0.52, 0.50, "Fact Table", color=AZ_TEXT, fontsize=7.5, va="center")
    rounded_box(ax, 0.2, 0.20, 0.25, 0.15, AZ_BLUE, radius=0.01)
    ax.text(0.52, 0.28, "Dimension Table  ·  🔑 PK  ·  🔗 FK", color=AZ_TEXT, fontsize=7.5, va="center")

    fig.text(0.5, -0.01, "Diagram: Gold Layer Star Schema — Kimball Dimensional Model (SHA-256 surrogate keys)",
             ha="center", color="#666", fontsize=7, style="italic")
    save("mockup_05_star_schema.png")


# ══════════════════════════════════════════════════════════════════════════════
# MOCKUP 6 — DATABRICKS SQL QUERY RESULT
# ══════════════════════════════════════════════════════════════════════════════
def mockup_sql_result():
    fig = plt.figure(figsize=(14, 7), facecolor=DB_BG)
    ax  = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 14); ax.set_ylim(0, 7)
    ax.axis("off")

    # Header
    rounded_box(ax, 0, 6.6, 14, 0.4, "#12122A")
    ax.text(0.2, 6.84, "  Databricks SQL  |  SQL Editor  >  KPI Query — vw_payment_performance",
            color=DB_TEAL, fontsize=8.5, va="center")

    # SQL Editor pane
    rounded_box(ax, 0.1, 4.0, 13.8, 2.45, DB_CELL, radius=0.015, lw=1, edgecolor=DB_BORDER)
    sql_lines = [
        ([("SELECT",DB_KEYWORD),("  FORMAT_NUMBER(SUM(actual_payment_amount)/1e6, ",DB_TEXT),("2",DB_NUM),(") AS total_collected_m,",DB_TEXT)]),
        ([("       FORMAT_NUMBER(AVG(collection_rate)*",DB_TEXT),("100",DB_NUM),(", ",DB_TEXT),("2",DB_NUM),(")",DB_TEXT),
          (" AS avg_collection_rate_pct,",DB_TEXT)]),
        ([("       FORMAT_NUMBER(SUM(CASE WHEN missed_payment_flag THEN ",DB_TEXT),("1",DB_NUM),(" ELSE ",DB_TEXT),("0",DB_NUM),
          (" END)*",DB_TEXT),("100.0",DB_NUM),("/COUNT(*), ",DB_TEXT),("2",DB_NUM),(") AS missed_rate_pct,",DB_TEXT)]),
        ([("       payment_year,",DB_TEXT)]),
        ([("       MONTH(payment_date) AS payment_month",DB_TEXT)]),
        ([("FROM",DB_KEYWORD),("   debtbusters_gold.fact_payment",DB_TEXT)]),
        ([("WHERE",DB_KEYWORD),("  payment_year BETWEEN ",DB_TEXT),("2022",DB_NUM),(" AND ",DB_TEXT),("2025",DB_NUM)]),
        ([("GROUP BY",DB_KEYWORD),(" payment_year, payment_month",DB_TEXT)]),
        ([("ORDER BY",DB_KEYWORD),(" payment_year, payment_month",DB_TEXT)]),
        ([("LIMIT",DB_KEYWORD),("  24",DB_NUM)]),
    ]
    for ri, spans in enumerate(sql_lines):
        y = 6.35 - ri * 0.23
        x = 0.3
        for text, color in spans:
            ax.text(x, y, text, color=color, fontsize=7.5, va="top", fontfamily="monospace")
            x += len(text) * 0.058

    # Run button
    rounded_box(ax, 11.5, 4.08, 1.8, 0.32, DB_TEAL, radius=0.01)
    ax.text(12.4, 4.24, "▷  Run  (Ctrl+Enter)", color="white", fontsize=7.5, va="center", ha="center")

    # Result header
    rounded_box(ax, 0.1, 3.65, 13.8, 0.33, "#1A1A30")
    ax.text(0.3, 3.83, f"Query executed in 0.842s  ·  24 rows returned  ·  Scanned: 1,500,000 rows",
            color="#AAAACC", fontsize=7.5, va="center")

    # Results table
    cols_h = ["total_collected_m", "avg_collection_rate_pct", "missed_rate_pct", "payment_year", "payment_month"]
    col_x  = [0.2, 3.4, 6.6, 9.2, 11.5]
    rounded_box(ax, 0.1, 3.28, 13.8, 0.35, "#252545")
    for h, x in zip(cols_h, col_x):
        ax.text(x, 3.5, h, color=DB_TEAL, fontsize=7.5, va="center",
                fontfamily="monospace", fontweight="bold")
    ax.plot([0.1, 13.9], [3.27, 3.27], color=DB_BORDER, lw=0.8)

    results = [
        ("12.48", "88.42", "11.58", "2022", "1"),
        ("13.21", "87.93", "12.07", "2022", "2"),
        ("14.05", "89.12", "10.88", "2022", "3"),
        ("13.76", "88.74", "11.26", "2022", "4"),
        ("15.34", "90.23", "9.77",  "2022", "5"),
        ("14.89", "89.54", "10.46", "2022", "6"),
        ("16.12", "91.08", "8.92",  "2022", "7"),
        ("15.67", "90.67", "9.33",  "2022", "8"),
        ("17.23", "92.14", "7.86",  "2022", "9"),
        ("18.45", "92.88", "7.12",  "2022", "10"),
        ("19.02", "93.21", "6.79",  "2022", "11"),
        ("20.14", "93.89", "6.11",  "2022", "12"),
    ]
    for ri, row in enumerate(results):
        y = 3.05 - ri * 0.265
        bg = "#1E1E3A" if ri % 2 == 0 else DB_CELL
        rounded_box(ax, 0.1, y-0.1, 13.8, 0.255, bg, radius=0.003)
        for ci, (val, x) in enumerate(zip(row, col_x)):
            if ci == 2:
                col = DB_GREEN if float(val) < 10 else DB_ORANGE
            elif ci == 1:
                col = DB_GREEN if float(val) > 90 else DB_TEXT
            else:
                col = DB_TEXT
            ax.text(x, y+0.05, val, color=col, fontsize=7.5, va="center",
                    fontfamily="monospace")

    ax.text(0.3, -0.02, "...  12 more rows  (showing 12 of 24)", color="#666", fontsize=7, va="bottom")

    fig.text(0.5, -0.04, "Screenshot: Databricks SQL Editor — Payment Performance KPI View (vw_payment_performance)",
             ha="center", color="#666", fontsize=7, style="italic")
    save("mockup_06_sql_result.png")


# ── RUN ALL ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating platform mockup screenshots...")
    mockup_databricks_notebook()
    mockup_delta_schema()
    mockup_mlflow()
    mockup_adf()
    mockup_star_schema()
    mockup_sql_result()
    print(f"\nAll 6 mockups saved to: {CHART_DIR}")
