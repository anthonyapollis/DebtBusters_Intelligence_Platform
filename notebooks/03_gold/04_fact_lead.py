# Databricks Notebook — Gold: Fact_Lead
# Joins to Dim_Client, Dim_Date

# COMMAND ----------
from pyspark.sql import functions as F

GOLD_PATH = "/mnt/debtbusters/gold/fact_lead"
TABLE     = "debtbusters_gold.fact_lead"

# COMMAND ----------
leads  = spark.table("debtbusters_silver.leads")
d_cli  = spark.table("debtbusters_gold.dim_client").select("client_key","client_id")
d_date = spark.table("debtbusters_gold.dim_date").select("date_key", F.to_date("date","yyyy-MM-dd").alias("date"))

fact = (leads
        .join(d_cli,  "client_id",  "left")
        .join(d_date, leads["lead_date"] == d_date["date"], "left")
        .select(
            F.sha2("lead_id", 256).alias("lead_key"),
            "lead_id",
            F.coalesce("client_key",  F.lit("UNKNOWN")).alias("client_key"),
            F.coalesce("date_key",    F.lit(-1)).cast("int").alias("date_key"),
            "source_channel",
            "campaign",
            "utm_source",
            "utm_medium",
            "lead_score",
            "lead_status",
            "cost_per_lead",
            "qualified_flag",
            "assessed_flag",
            "converted_flag",
        )
        .withColumn("_gold_at", F.current_timestamp())
)

(fact.write.format("delta")
     .mode("overwrite")
     .option("overwriteSchema","true")
     .partitionBy("date_key")
     .save(GOLD_PATH)
)
spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE} USING DELTA LOCATION '{GOLD_PATH}'")
print(f"Fact_Lead: {fact.count():,} rows")
