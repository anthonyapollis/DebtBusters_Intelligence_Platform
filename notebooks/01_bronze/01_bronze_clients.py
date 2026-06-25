# Databricks Notebook — Bronze: Clients
# Ingest raw CSV from ADLS → Delta table with audit columns
# Idempotent: uses MERGE or overwrite with schema evolution

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.types import *
from delta.tables import DeltaTable
from datetime import datetime

RAW_PATH    = "/mnt/debtbusters/raw/clients.csv"
BRONZE_PATH = "/mnt/debtbusters/bronze/clients"
TABLE       = "debtbusters_bronze.clients"
BATCH_ID    = datetime.utcnow().strftime("%Y%m%d%H%M%S")

# COMMAND ----------
schema = StructType([
    StructField("client_id",        StringType(),  True),
    StructField("first_name",       StringType(),  True),
    StructField("last_name",        StringType(),  True),
    StructField("id_number",        StringType(),  True),
    StructField("dob",              StringType(),  True),
    StructField("age",              IntegerType(), True),
    StructField("age_band",         StringType(),  True),
    StructField("gender",           StringType(),  True),
    StructField("province",         StringType(),  True),
    StructField("city",             StringType(),  True),
    StructField("postal_code",      StringType(),  True),
    StructField("email",            StringType(),  True),
    StructField("mobile",           StringType(),  True),
    StructField("employment_status",StringType(),  True),
    StructField("employer_name",    StringType(),  True),
    StructField("gross_income",     DoubleType(),  True),
    StructField("income_band",      StringType(),  True),
    StructField("consent_status",   StringType(),  True),
    StructField("created_date",     StringType(),  True),
    StructField("source_system",    StringType(),  True),
])

# COMMAND ----------
df = (spark.read.format("csv")
      .option("header", True)
      .schema(schema)
      .load(RAW_PATH)
      .withColumn("_ingested_at",  F.current_timestamp())
      .withColumn("_batch_id",     F.lit(BATCH_ID))
      .withColumn("_source_file",  F.lit(RAW_PATH))
      .withColumn("_is_deleted",   F.lit(False))
)

print(f"Rows read: {df.count():,}")
display(df.limit(5))

# COMMAND ----------
(df.write
   .format("delta")
   .mode("overwrite")
   .option("mergeSchema", "true")
   .option("overwriteSchema", "true")
   .partitionBy("province")
   .save(BRONZE_PATH)
)

spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {TABLE}
    USING DELTA
    LOCATION '{BRONZE_PATH}'
""")

print(f"Bronze table {TABLE} written — {df.count():,} rows")
