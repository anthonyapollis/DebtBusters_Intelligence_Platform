# Databricks Notebook — Gold: Fact_Debt_Review_Case

# COMMAND ----------
from pyspark.sql import functions as F

GOLD_PATH = "/mnt/debtbusters/gold/fact_debt_review_case"
TABLE     = "debtbusters_gold.fact_debt_review_case"

# COMMAND ----------
cases   = spark.table("debtbusters_silver.debt_review_cases")
d_cli   = spark.table("debtbusters_gold.dim_client").select("client_key","client_id")
d_coun  = spark.table("debtbusters_gold.dim_counsellor").select("counsellor_key","counsellor_id")
d_prod  = spark.table("debtbusters_gold.dim_financial_product").select("product_key","product_id")
d_date  = spark.table("debtbusters_gold.dim_date").select(
    "date_key", F.to_date("date","yyyy-MM-dd").alias("date")
)

fact = (cases
        .join(d_cli,  "client_id",     "left")
        .join(d_coun, "counsellor_id", "left")
        .join(d_prod, "product_id",    "left")
        .join(d_date, cases["application_date"] == d_date["date"], "left")
        .select(
            F.sha2("case_id",256).alias("case_key"),
            "case_id",
            F.coalesce("client_key",    F.lit("UNKNOWN")).alias("client_key"),
            F.coalesce("counsellor_key",F.lit("UNKNOWN")).alias("counsellor_key"),
            F.coalesce("product_key",   F.lit("UNKNOWN")).alias("product_key"),
            F.coalesce("date_key",      F.lit(-1)).cast("int").alias("application_date_key"),
            "application_date",
            "acceptance_date",
            "court_order_date",
            "completion_date",
            "days_to_acceptance",
            "case_stage",
            "legal_status",
            "ncr_status",
            "court_order_status",
            "case_open_flag",
            "days_in_stage",
            "clearance_issued_flag",
        )
        .withColumn("is_completed",   F.col("case_stage") == "Completed")
        .withColumn("is_withdrawn",   F.col("case_stage") == "Withdrawn")
        .withColumn("is_active",      F.col("case_stage") == "Active")
        .withColumn("_gold_at",       F.current_timestamp())
)

(fact.write.format("delta")
     .mode("overwrite").option("overwriteSchema","true")
     .partitionBy("case_stage")
     .save(GOLD_PATH)
)
spark.sql(f"CREATE TABLE IF NOT EXISTS {TABLE} USING DELTA LOCATION '{GOLD_PATH}'")
print(f"Fact_Debt_Review_Case: {fact.count():,} rows")
