# Databricks Notebook — Gold: Fact_Payment / Fact_Repayment_Plan / Fact_Credit_Monitoring

# COMMAND ----------
from pyspark.sql import functions as F

d_cli   = spark.table("debtbusters_gold.dim_client").select("client_key","client_id")
d_cred  = spark.table("debtbusters_gold.dim_creditor").select("creditor_key","creditor_id")
d_date  = spark.table("debtbusters_gold.dim_date").select("date_key", F.to_date("date","yyyy-MM-dd").alias("date"))

# ---------- FACT_PAYMENT ----------
payments = spark.table("debtbusters_silver.payments")

fact_pay = (payments
            .join(d_cli,  "client_id",  "left")
            .join(d_cred, "creditor_id","left")
            .join(d_date, payments["payment_date"] == d_date["date"], "left")
            .select(
                F.sha2("payment_id",256).alias("payment_key"),
                "payment_id",
                "case_id",
                F.coalesce("client_key",  F.lit("UNKNOWN")).alias("client_key"),
                F.coalesce("creditor_key",F.lit("UNKNOWN")).alias("creditor_key"),
                F.coalesce("date_key",    F.lit(-1)).cast("int").alias("date_key"),
                "payment_date",
                "payment_month",
                "payment_year",
                "expected_payment_amount",
                "actual_payment_amount",
                "distribution_amount",
                "arrears_amount",
                "collection_rate",
                "payment_status",
                "missed_payment_flag",
                "pda_reference",
            )
            .withColumn("_gold_at", F.current_timestamp())
)
p = "/mnt/debtbusters/gold/fact_payment"
(fact_pay.write.format("delta").mode("overwrite").option("overwriteSchema","true")
 .partitionBy("payment_year","payment_month").save(p))
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_payment USING DELTA LOCATION '{p}'")
print(f"Fact_Payment: {fact_pay.count():,}")

# ---------- FACT_REPAYMENT_PLAN ----------
plans = spark.table("debtbusters_silver.repayment_plans")

fact_plans = (plans
              .join(d_cred, "creditor_id","left")
              .join(d_date, plans["plan_date"] == d_date["date"], "left")
              .select(
                  F.sha2("plan_id",256).alias("plan_key"),
                  "plan_id",
                  "case_id",
                  F.coalesce("creditor_key",F.lit("UNKNOWN")).alias("creditor_key"),
                  F.coalesce("date_key",    F.lit(-1)).cast("int").alias("date_key"),
                  "plan_date",
                  "original_instalment",
                  "proposed_instalment",
                  "accepted_instalment",
                  "accepted_flag",
                  "interest_rate_before",
                  "interest_rate_after",
                  "term_months_before",
                  "term_months_after",
                  "monthly_saving",
                  "total_saving_estimated",
                  "reduction_pct",
                  "creditor_acceptance_status",
              )
              .withColumn("_gold_at", F.current_timestamp())
)
p = "/mnt/debtbusters/gold/fact_repayment_plan"
(fact_plans.write.format("delta").mode("overwrite").option("overwriteSchema","true").save(p))
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_repayment_plan USING DELTA LOCATION '{p}'")
print(f"Fact_Repayment_Plan: {fact_plans.count():,}")

# ---------- FACT_CREDIT_MONITORING ----------
credit = spark.table("debtbusters_silver.credit_monitoring")

fact_credit = (credit
               .join(d_cli,  "client_id", "left")
               .join(d_date, credit["monitoring_date"] == d_date["date"], "left")
               .select(
                   F.sha2("monitoring_id",256).alias("monitoring_key"),
                   "monitoring_id",
                   F.coalesce("client_key",F.lit("UNKNOWN")).alias("client_key"),
                   F.coalesce("date_key",  F.lit(-1)).cast("int").alias("date_key"),
                   "monitoring_date",
                   "credit_score",
                   "score_change",
                   "credit_risk_band",
                   "accounts_open",
                   "accounts_in_arrears",
                   "judgements_count",
                   "defaults_count",
                   "enquiries_count",
                   "total_credit_limit",
                   "total_utilisation_pct",
                   "bureau",
               )
               .withColumn("_gold_at", F.current_timestamp())
)
p = "/mnt/debtbusters/gold/fact_credit_monitoring"
(fact_credit.write.format("delta").mode("overwrite").option("overwriteSchema","true").save(p))
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_credit_monitoring USING DELTA LOCATION '{p}'")
print(f"Fact_Credit_Monitoring: {fact_credit.count():,}")

print("\nAll gold fact tables written.")
