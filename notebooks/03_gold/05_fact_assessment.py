# Databricks Notebook — Gold: Fact_Assessment

# COMMAND ----------
from pyspark.sql import functions as F

GOLD_PATH = "/mnt/debtbusters/gold/fact_assessment"
TABLE     = "debtbusters_gold.fact_assessment"

# COMMAND ----------
assess  = spark.table("debtbusters_silver.assessments")
d_cli   = spark.table("debtbusters_gold.dim_client").select("client_key","client_id")
d_coun  = spark.table("debtbusters_gold.dim_counsellor").select("counsellor_key","counsellor_id")
d_date  = spark.table("debtbusters_gold.dim_date").select("date_key", F.to_date("date","yyyy-MM-dd").alias("date"))

fact = (assess
        .join(d_cli,  "client_id",     "left")
        .join(d_coun, "counsellor_id", "left")
        .join(d_date, assess["assessment_date"] == d_date["date"], "left")
        .select(
            F.sha2("assessment_id",256).alias("assessment_key"),
            "assessment_id",
            F.coalesce("client_key",    F.lit("UNKNOWN")).alias("client_key"),
            F.coalesce("counsellor_key",F.lit("UNKNOWN")).alias("counsellor_key"),
            F.coalesce("date_key",      F.lit(-1)).cast("int").alias("date_key"),
            "gross_income",
            "net_income",
            "living_expenses",
            "total_debt_balance",
            "total_monthly_debt_instalment",
            "disposable_income",
            "debt_to_income_ratio",
            "dti_band",
            "affordability_amount",
            "over_indebted_flag",
            "recommended_product",
            "number_of_creditors",
        )
        .withColumn("_gold_at", F.current_timestamp())
)

(fact.write.format("delta")
     .mode("overwrite").option("overwriteSchema","true")
     .save(GOLD_PATH)
)
spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE} USING DELTA LOCATION '{GOLD_PATH}'")
print(f"Fact_Assessment: {fact.count():,} rows")
