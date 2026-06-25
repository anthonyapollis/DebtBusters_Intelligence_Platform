# Databricks Notebook — Silver: Leads & Assessments

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# ---------- LEADS ----------
raw_leads = spark.table("debtbusters_bronze.leads")

w = Window.partitionBy("lead_id").orderBy(F.desc("_ingested_at"))
leads = (raw_leads
         .withColumn("_rn", F.row_number().over(w)).filter(F.col("_rn") == 1).drop("_rn")
         .withColumn("lead_date",     F.to_date("lead_date", "yyyy-MM-dd"))
         .withColumn("source_channel",F.trim("source_channel"))
         .withColumn("lead_score",    F.col("lead_score").cast("int"))
         .withColumn("cost_per_lead", F.when(F.col("cost_per_lead") < 0, F.lit(None)).otherwise(F.col("cost_per_lead")))
         .withColumn("lead_year",     F.year("lead_date"))
         .withColumn("lead_month",    F.month("lead_date"))
         .withColumn("_silver_at",    F.current_timestamp())
)

leads_path = "/mnt/debtbusters/silver/leads"
(leads.write.format("delta")
 .mode("overwrite").option("mergeSchema", "true")
 .partitionBy("lead_year", "lead_month")
 .save(leads_path)
)
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_silver.leads USING DELTA LOCATION '{leads_path}'")
print(f"Silver leads: {leads.count():,} rows")

# COMMAND ----------
# ---------- ASSESSMENTS ----------
raw_assess = spark.table("debtbusters_bronze.assessments")

w2 = Window.partitionBy("assessment_id").orderBy(F.desc("_ingested_at"))
assessments = (raw_assess
               .withColumn("_rn", F.row_number().over(w2)).filter(F.col("_rn") == 1).drop("_rn")
               .withColumn("assessment_date",     F.to_date("assessment_date", "yyyy-MM-dd"))
               .withColumn("gross_income",         F.col("gross_income").cast("double"))
               .withColumn("net_income",           F.col("net_income").cast("double"))
               .withColumn("living_expenses",      F.col("living_expenses").cast("double"))
               .withColumn("total_debt_balance",   F.col("total_debt_balance").cast("double"))
               .withColumn("debt_to_income_ratio", F.col("debt_to_income_ratio").cast("double"))
               .withColumn("dti_band",
                   F.when(F.col("debt_to_income_ratio") < 0.40, "< 40%")
                    .when(F.col("debt_to_income_ratio") < 0.60, "40-60%")
                    .when(F.col("debt_to_income_ratio") < 0.80, "60-80%")
                    .otherwise("> 80%")
               )
               .withColumn("_silver_at", F.current_timestamp())
)

assess_path = "/mnt/debtbusters/silver/assessments"
(assessments.write.format("delta")
 .mode("overwrite").option("mergeSchema", "true")
 .save(assess_path)
)
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_silver.assessments USING DELTA LOCATION '{assess_path}'")
print(f"Silver assessments: {assessments.count():,} rows")
