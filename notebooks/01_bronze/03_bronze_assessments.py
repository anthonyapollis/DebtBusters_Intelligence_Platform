# Databricks Notebook — Bronze: Assessments
from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime

RAW_PATH    = "/mnt/debtbusters/raw/assessments.csv"
BRONZE_PATH = "/mnt/debtbusters/bronze/assessments"
TABLE       = "debtbusters_bronze.assessments"
BATCH_ID    = datetime.utcnow().strftime("%Y%m%d%H%M%S")

# COMMAND ----------
schema = StructType([
    StructField("assessment_id",                 StringType(), True),
    StructField("client_id",                     StringType(), True),
    StructField("counsellor_id",                 StringType(), True),
    StructField("assessment_date",               StringType(), True),
    StructField("gross_income",                  DoubleType(), True),
    StructField("net_income",                    DoubleType(), True),
    StructField("living_expenses",               DoubleType(), True),
    StructField("total_debt_balance",            DoubleType(), True),
    StructField("total_monthly_debt_instalment", DoubleType(), True),
    StructField("disposable_income",             DoubleType(), True),
    StructField("debt_to_income_ratio",          DoubleType(), True),
    StructField("affordability_amount",          DoubleType(), True),
    StructField("over_indebted_flag",            BooleanType(),True),
    StructField("recommended_product",           StringType(), True),
    StructField("number_of_creditors",           IntegerType(),True),
])

# COMMAND ----------
df = (spark.read.format("csv")
      .option("header", True)
      .schema(schema)
      .load(RAW_PATH)
      .withColumn("_ingested_at", F.current_timestamp())
      .withColumn("_batch_id",    F.lit(BATCH_ID))
)

(df.write.format("delta")
   .mode("overwrite")
   .option("mergeSchema", "true")
   .save(BRONZE_PATH)
)

spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE} USING DELTA LOCATION '{BRONZE_PATH}'")
print(f"Bronze assessments written — {df.count():,} rows")
