# Databricks Notebook — Gold: Dim_Client (SCD Type 1)
# Surrogate key assigned via monotonically_increasing_id (or hash for determinism)

# COMMAND ----------
from pyspark.sql import functions as F

SILVER_TABLE = "debtbusters_silver.clients"
GOLD_PATH    = "/mnt/debtbusters/gold/dim_client"
TABLE        = "debtbusters_gold.dim_client"

# COMMAND ----------
src = spark.table(SILVER_TABLE)

dim = (src
       .select(
           F.sha2(F.col("client_id"), 256).alias("client_key"),
           "client_id",
           "first_name",
           "last_name",
           "full_name",
           "age",
           "age_band",
           "gender",
           "province",
           "city",
           "employment_status",
           "income_band",
           "gross_income",
           "consent_status",
           "is_consented",
           "created_date",
           "source_system",
       )
       .withColumn("_gold_at", F.current_timestamp())
)

(dim.write.format("delta")
    .mode("overwrite")
    .option("overwriteSchema", "true")
    .save(GOLD_PATH)
)
spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE} USING DELTA LOCATION '{GOLD_PATH}'")
print(f"Dim_Client: {dim.count():,} rows")
