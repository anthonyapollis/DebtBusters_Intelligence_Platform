# Databricks Notebook — Gold: Dim_Creditor / Dim_Counsellor / Dim_Financial_Product

# COMMAND ----------
from pyspark.sql import functions as F

def write_dim(silver_table, gold_path, gold_table, select_expr):
    src = spark.table(silver_table)
    dim = src.selectExpr(*select_expr).withColumn("_gold_at", F.current_timestamp())
    (dim.write.format("delta")
        .mode("overwrite").option("overwriteSchema","true")
        .save(gold_path)
    )
    spark.sql(f"CREATE TABLE IF NOT EXISTS {gold_table} USING DELTA LOCATION '{gold_path}'")
    print(f"{gold_table}: {dim.count():,} rows")

# ---------- DIM_CREDITOR ----------
write_dim(
    "debtbusters_bronze.creditors",
    "/mnt/debtbusters/gold/dim_creditor",
    "debtbusters_gold.dim_creditor",
    [
        "sha2(creditor_id, 256) AS creditor_key",
        "creditor_id",
        "creditor_name",
        "creditor_type",
        "industry",
        "ncr_registered",
    ]
)

# ---------- DIM_COUNSELLOR ----------
write_dim(
    "debtbusters_bronze.counsellors",
    "/mnt/debtbusters/gold/dim_counsellor",
    "debtbusters_gold.dim_counsellor",
    [
        "sha2(counsellor_id, 256) AS counsellor_key",
        "counsellor_id",
        "counsellor_name",
        "team",
        "branch",
        "ncr_number",
        "active_flag",
        "hire_date",
    ]
)

# ---------- DIM_FINANCIAL_PRODUCT ----------
write_dim(
    "debtbusters_bronze.financial_products",
    "/mnt/debtbusters/gold/dim_financial_product",
    "debtbusters_gold.dim_financial_product",
    [
        "sha2(product_id, 256) AS product_key",
        "product_id",
        "product_code",
        "product_name",
        "product_category",
        "fee_type",
        "active_flag",
    ]
)

print("\nAll support dimensions written.")
