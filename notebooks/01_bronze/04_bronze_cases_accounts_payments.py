# Databricks Notebook — Bronze: Cases / Debt Accounts / Repayment Plans / Payments / Credit Monitoring
# Batch ingestion of remaining source entities

# COMMAND ----------
from pyspark.sql import functions as F
from datetime import datetime

BATCH_ID = datetime.utcnow().strftime("%Y%m%d%H%M%S")

TABLES = {
    "debt_review_cases":  "/mnt/debtbusters/raw/debt_review_cases.csv",
    "debt_accounts":      "/mnt/debtbusters/raw/debt_accounts.csv",
    "repayment_plans":    "/mnt/debtbusters/raw/repayment_plans.csv",
    "payments":           "/mnt/debtbusters/raw/payments.csv",
    "credit_monitoring":  "/mnt/debtbusters/raw/credit_monitoring.csv",
    "creditors":          "/mnt/debtbusters/raw/creditors.csv",
    "counsellors":        "/mnt/debtbusters/raw/counsellors.csv",
    "financial_products": "/mnt/debtbusters/raw/financial_products.csv",
}

# COMMAND ----------
for tbl, raw_path in TABLES.items():
    df = (spark.read.format("csv")
          .option("header", True)
          .option("inferSchema", True)
          .load(raw_path)
          .withColumn("_ingested_at", F.current_timestamp())
          .withColumn("_batch_id",    F.lit(BATCH_ID))
          .withColumn("_source_file", F.lit(raw_path))
    )
    bronze_path = f"/mnt/debtbusters/bronze/{tbl}"
    (df.write.format("delta")
       .mode("overwrite")
       .option("mergeSchema", "true")
       .save(bronze_path)
    )
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS debtbusters_bronze.{tbl}
        USING DELTA LOCATION '{bronze_path}'
    """)
    print(f"  {tbl}: {df.count():,} rows → {bronze_path}")

print("\nAll bronze tables loaded.")
