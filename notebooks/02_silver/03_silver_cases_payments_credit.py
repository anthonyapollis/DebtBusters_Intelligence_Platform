# Databricks Notebook — Silver: Cases / Debt Accounts / Repayment Plans / Payments / Credit Monitoring

# COMMAND ----------
from pyspark.sql import functions as F
from pyspark.sql.window import Window

def dedup(df, pk):
    w = Window.partitionBy(pk).orderBy(F.desc("_ingested_at"))
    return df.withColumn("_rn", F.row_number().over(w)).filter(F.col("_rn") == 1).drop("_rn")

# ---------- DEBT REVIEW CASES ----------
cases = (dedup(spark.table("debtbusters_bronze.debt_review_cases"), "case_id")
         .withColumn("application_date", F.to_date("application_date", "yyyy-MM-dd"))
         .withColumn("acceptance_date",  F.to_date("acceptance_date",  "yyyy-MM-dd"))
         .withColumn("court_order_date", F.to_date("court_order_date", "yyyy-MM-dd"))
         .withColumn("completion_date",  F.to_date("completion_date",  "yyyy-MM-dd"))
         .withColumn("days_to_acceptance",
             F.datediff("acceptance_date", "application_date"))
         .withColumn("_silver_at", F.current_timestamp())
)
p = "/mnt/debtbusters/silver/debt_review_cases"
cases.write.format("delta").mode("overwrite").option("mergeSchema","true").save(p)
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_silver.debt_review_cases USING DELTA LOCATION '{p}'")
print(f"Silver cases: {cases.count():,}")

# ---------- DEBT ACCOUNTS ----------
accts = (dedup(spark.table("debtbusters_bronze.debt_accounts"), "account_id")
         .withColumn("open_date",     F.to_date("open_date", "yyyy-MM-dd"))
         .withColumn("current_balance",F.col("current_balance").cast("double"))
         .withColumn("interest_rate",  F.col("interest_rate").cast("double"))
         .withColumn("interest_rate_pct", F.round(F.col("interest_rate") * 100, 2))
         .withColumn("_silver_at", F.current_timestamp())
)
p = "/mnt/debtbusters/silver/debt_accounts"
accts.write.format("delta").mode("overwrite").option("mergeSchema","true").save(p)
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_silver.debt_accounts USING DELTA LOCATION '{p}'")
print(f"Silver debt_accounts: {accts.count():,}")

# ---------- REPAYMENT PLANS ----------
plans = (dedup(spark.table("debtbusters_bronze.repayment_plans"), "plan_id")
         .withColumn("plan_date",         F.to_date("plan_date", "yyyy-MM-dd"))
         .withColumn("monthly_saving",     F.col("monthly_saving").cast("double"))
         .withColumn("total_saving_estimated", F.col("total_saving_estimated").cast("double"))
         .withColumn("reduction_pct",
             F.when(F.col("original_instalment") > 0,
                    F.round((F.col("original_instalment") - F.col("proposed_instalment")) /
                             F.col("original_instalment") * 100, 2))
              .otherwise(F.lit(None))
         )
         .withColumn("_silver_at", F.current_timestamp())
)
p = "/mnt/debtbusters/silver/repayment_plans"
plans.write.format("delta").mode("overwrite").option("mergeSchema","true").save(p)
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_silver.repayment_plans USING DELTA LOCATION '{p}'")
print(f"Silver repayment_plans: {plans.count():,}")

# ---------- PAYMENTS ----------
payments = (dedup(spark.table("debtbusters_bronze.payments"), "payment_id")
            .withColumn("payment_date",  F.to_date("payment_date", "yyyy-MM-dd"))
            .withColumn("payment_year",  F.year("payment_date"))
            .withColumn("payment_month", F.month("payment_date"))
            .withColumn("collection_rate",
                F.when(F.col("expected_payment_amount") > 0,
                       F.round(F.col("actual_payment_amount") /
                                F.col("expected_payment_amount"), 4))
                 .otherwise(F.lit(None))
            )
            .withColumn("_silver_at", F.current_timestamp())
)
p = "/mnt/debtbusters/silver/payments"
payments.write.format("delta").mode("overwrite").option("mergeSchema","true")\
    .partitionBy("payment_year","payment_month").save(p)
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_silver.payments USING DELTA LOCATION '{p}'")
print(f"Silver payments: {payments.count():,}")

# ---------- CREDIT MONITORING ----------
credit = (dedup(spark.table("debtbusters_bronze.credit_monitoring"), "monitoring_id")
          .withColumn("monitoring_date", F.to_date("monitoring_date", "yyyy-MM-dd"))
          .withColumn("credit_score",    F.col("credit_score").cast("int"))
          .withColumn("_silver_at",      F.current_timestamp())
)
p = "/mnt/debtbusters/silver/credit_monitoring"
credit.write.format("delta").mode("overwrite").option("mergeSchema","true").save(p)
spark.sql(f"CREATE TABLE IF NOT EXISTS debtbusters_silver.credit_monitoring USING DELTA LOCATION '{p}'")
print(f"Silver credit_monitoring: {credit.count():,}")

print("\nAll silver tables written.")
