# Databricks Notebook — Silver: Clients
# Clean, validate, standardise, deduplicate

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

BRONZE_TABLE = "debtbusters_bronze.clients"
SILVER_PATH  = "/mnt/debtbusters/silver/clients"
SILVER_TABLE = "debtbusters_silver.clients"

# COMMAND ----------
raw = spark.table(BRONZE_TABLE)

# Deduplicate: keep most recently ingested record per client_id
w   = Window.partitionBy("client_id").orderBy(F.desc("_ingested_at"))
df  = (raw
       .withColumn("_rn", F.row_number().over(w))
       .filter(F.col("_rn") == 1)
       .drop("_rn")
)

# Standardise & validate
df = (df
      .withColumn("first_name",       F.initcap(F.trim("first_name")))
      .withColumn("last_name",        F.initcap(F.trim("last_name")))
      .withColumn("full_name",        F.concat_ws(" ", "first_name", "last_name"))
      .withColumn("email",            F.lower(F.trim("email")))
      .withColumn("province",         F.trim("province"))
      .withColumn("employment_status",F.trim("employment_status"))
      .withColumn("consent_status",   F.trim("consent_status"))
      .withColumn("dob",              F.to_date("dob", "yyyy-MM-dd"))
      .withColumn("created_date",     F.to_date("created_date", "yyyy-MM-dd"))
      .withColumn("gross_income",     F.when(F.col("gross_income") < 0, F.lit(None)).otherwise(F.col("gross_income")))
      .withColumn("is_valid_email",   F.col("email").rlike(r'^[^@\s]+@[^@\s]+\.[^@\s]+$'))
      .withColumn("is_consented",     F.col("consent_status") == "Granted")
      .withColumn("_silver_at",       F.current_timestamp())
      .withColumn("_data_quality",    F.when(
                      F.col("client_id").isNull() |
                      F.col("first_name").isNull() |
                      F.col("last_name").isNull(),
                      "REJECT"
                  ).otherwise("PASS"))
)

# Write PASS records; quarantine REJECT
pass_df   = df.filter(F.col("_data_quality") == "PASS")
reject_df = df.filter(F.col("_data_quality") == "REJECT")

(pass_df.write.format("delta")
 .mode("overwrite")
 .option("mergeSchema", "true")
 .partitionBy("province")
 .save(SILVER_PATH)
)

spark.sql(f"CREATE TABLE IF NOT EXISTS {SILVER_TABLE} USING DELTA LOCATION '{SILVER_PATH}'")

reject_df.write.format("delta").mode("overwrite").save("/mnt/debtbusters/silver/_quarantine/clients")

print(f"Silver clients: {pass_df.count():,} PASS | {reject_df.count():,} REJECT")
