"""
DebtBusters Intelligence Platform — Master Runner
Executes the full local pipeline in the correct order:
  1. Generate 4M+ rows of synthetic data
  2. Generate 12 charts (Confluent brand colors)
  3. Generate Excel report (multi-sheet with charts)
  4. Train & validate 5 ML models + produce ML charts
  5. Generate Word ebook

Run: python run_all.py
Total time: ~8-15 minutes depending on hardware
"""

import subprocess, sys, time, os

BASE = os.path.dirname(__file__)

steps = [
    ("Installing requirements",
     [sys.executable, "-m", "pip", "install", "-q",
      "faker", "numpy", "pandas", "pyarrow", "matplotlib", "seaborn",
      "scikit-learn", "xgboost", "lightgbm", "catboost", "optuna",
      "shap", "openpyxl", "xlsxwriter", "python-docx", "Pillow"]),

    ("Generating 4,000,000+ rows of synthetic data",
     [sys.executable, os.path.join(BASE, "generate_millions.py")]),

    ("Generating 12 Confluent-branded charts",
     [sys.executable, os.path.join(BASE, "generate_charts.py")]),

    ("Generating Excel Intelligence Report (7 sheets)",
     [sys.executable, os.path.join(BASE, "generate_excel_report.py")]),

    ("Training & validating 5 ML models",
     [sys.executable, os.path.join(BASE, "ml_validation_report.py")]),

    ("Generating Word ebook",
     [sys.executable, os.path.join(BASE, "..", "ebook", "generate_ebook.py")]),
]

print("=" * 65)
print("  DebtBusters Intelligence Platform — Full Local Build")
print("=" * 65)
total_start = time.time()

for i,(label, cmd) in enumerate(steps, 1):
    print(f"\n[{i}/{len(steps)}] {label}…")
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=False, text=True)
    elapsed = time.time() - t0
    if result.returncode != 0:
        print(f"  ERROR in step {i}. Check output above.")
        sys.exit(1)
    print(f"  Done in {elapsed:.1f}s")

total = time.time() - total_start
print(f"\n{'='*65}")
print(f"  ALL STEPS COMPLETE in {total/60:.1f} minutes")
print(f"\n  Output files:")
print(f"    Data:   data/*.parquet")
print(f"    Charts: charts/*.png  (12 charts)")
print(f"    Excel:  excel/DebtBusters_Intelligence_Report.xlsx")
print(f"    Excel:  excel/ML_Validation_Report.xlsx")
print(f"    Ebook:  ebook/DebtBusters_Intelligence_Platform_Ebook.docx")
print(f"{'='*65}")
