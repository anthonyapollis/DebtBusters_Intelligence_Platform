# Databricks Notebook — Bronze: Leads
# Ingest raw CSV → Delta with audit columns

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime

RAW_PATH    = "/mnt/debtbusters/raw/leads.csv"
BRONZE_PATH = "/mnt/debtbusters/bronze/leads"
TABLE       = "debtbusters_bronze.leads"
BATCH_ID    = datetime.utcnow().strftime("%Y%m%d%H%M%S")

# COMMAND ----------
schema = StructType([
    StructField("lead_id",         StringType(), True),
    StructField("client_id",       StringType(), True),
    StructField("lead_date",       StringType(), True),
    StructField("source_channel",  StringType(), True),
    StructField("campaign",        StringType(), True),
    StructField("utm_source",      StringType(), True),
    StructField("utm_medium",      StringType(), True),
    StructField("lead_score",      IntegerType(),True),
    StructField("lead_status",     StringType(), True),
    StructField("cost_per_lead",   DoubleType(), True),
    StructField("qualified_flag",  BooleanType(),True),
    StructField("assessed_flag",   BooleanType(),True),
    StructField("converted_flag",  BooleanType(),True),
])

# COMMAND ----------
df = (spark.read.format("csv")
      .option("header", True)
      .schema(schema)
      .load(RAW_PATH)
      .withColumn("_ingested_at", F.current_timestamp())
      .withColumn("_batch_id",    F.lit(BATCH_ID))
      .withColumn("_source_file", F.lit(RAW_PATH))
      .withColumn("lead_year",    F.year(F.to_date("lead_date")))
      .withColumn("lead_month",   F.month(F.to_date("lead_date")))
)

(df.write.format("delta")
   .mode("overwrite")
   .option("mergeSchema", "true")
   .partitionBy("lead_year", "lead_month")
   .save(BRONZE_PATH)
)

spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE} USING DELTA LOCATION '{BRONZE_PATH}'")
print(f"Bronze leads written — {df.count():,} rows")
