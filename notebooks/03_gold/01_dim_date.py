# Databricks Notebook — Gold: Dim_Date
# Generates a complete date dimension from 2020-01-01 to 2030-12-31

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.types import *
import pandas as pd
from datetime import date, timedelta

GOLD_PATH = "/mnt/debtbusters/gold/dim_date"
TABLE     = "debtbusters_gold.dim_date"

# COMMAND ----------
start = date(2020, 1, 1)
end   = date(2030, 12, 31)
dates = []
d = start
while d <= end:
    quarter  = (d.month - 1) // 3 + 1
    is_month_end = (d + timedelta(days=1)).month != d.month
    dates.append({
        "date_key":         int(d.strftime("%Y%m%d")),
        "date":             d.isoformat(),
        "year":             d.year,
        "quarter":          quarter,
        "quarter_label":    f"Q{quarter} {d.year}",
        "month":            d.month,
        "month_name":       d.strftime("%B"),
        "month_short":      d.strftime("%b"),
        "month_year":       d.strftime("%Y-%m"),
        "week_of_year":     int(d.strftime("%V")),
        "day_of_week":      d.isoweekday(),       # 1=Mon, 7=Sun
        "day_name":         d.strftime("%A"),
        "day_short":        d.strftime("%a"),
        "is_weekend":       d.isoweekday() >= 6,
        "is_month_end":     is_month_end,
        "financial_year":   f"FY{d.year}" if d.month >= 3 else f"FY{d.year - 1}",  # SA fin year Mar-Feb
        "financial_quarter":f"FQ{((d.month - 3) % 12) // 3 + 1}",
    })
    d += timedelta(days=1)

pdf = pd.DataFrame(dates)
df  = spark.createDataFrame(pdf)

(df.write.format("delta")
   .mode("overwrite")
   .option("overwriteSchema", "true")
   .save(GOLD_PATH)
)
spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE} USING DELTA LOCATION '{GOLD_PATH}'")
print(f"Dim_Date: {df.count():,} rows written")
