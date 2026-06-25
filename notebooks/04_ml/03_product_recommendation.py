# Databricks Notebook — ML Model 3: Financial Product Recommendation
# Multi-class classifier: recommends the best product per client
# (Debt Counselling / Debt Consolidation / Credit Repair / Credit Monitoring / Insurance Review)
# Algorithm: Random Forest + probability calibration

# COMMAND ----------
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, top_k_accuracy_score
from pyspark.sql import functions as F

mlflow.set_experiment("/debtbusters/product_recommendation")

# COMMAND ----------
assess  = spark.table("debtbusters_gold.fact_assessment").toPandas()
clients = spark.table("debtbusters_gold.dim_client").toPandas()
credit  = (spark.table("debtbusters_gold.fact_credit_monitoring")
           .groupBy("client_key")
           .agg(
               F.avg("credit_score").alias("avg_credit_score"),
               F.avg("total_utilisation_pct").alias("avg_utilisation"),
               F.sum("accounts_in_arrears").alias("total_arrears_accts"),
               F.sum("judgements_count").alias("total_judgements"),
           )
           .toPandas()
)

df = (assess
      .merge(clients[["client_key","age","gender","employment_status","income_band","province"]],
             on="client_key", how="left")
      .merge(credit, on="client_key", how="left")
)

# Use recommended_product as proxy label (in production this would be actual accepted product)
target_le = LabelEncoder()
df["target"] = target_le.fit_transform(df["recommended_product"].fillna("Credit Monitoring"))
print("Classes:", list(target_le.classes_))

# COMMAND ----------
cat_cols = ["gender","employment_status","income_band","province","dti_band"]
for col in cat_cols:
    if col in df.columns:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col].fillna("UNKNOWN").astype(str))

feature_cols = [
    "gross_income","net_income","living_expenses","total_debt_balance",
    "total_monthly_debt_instalment","disposable_income","debt_to_income_ratio",
    "affordability_amount","number_of_creditors","age",
    "avg_credit_score","avg_utilisation","total_arrears_accts","total_judgements",
    "over_indebted_flag",
] + [c + "_enc" for c in cat_cols if c + "_enc" in df.columns]

feature_cols = [c for c in feature_cols if c in df.columns]
X = df[feature_cols].fillna(0)
y = df["target"]

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

# COMMAND ----------
with mlflow.start_run(run_name="product_recommendation_rf_v1"):
    rf = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=20,
        class_weight="balanced", random_state=42, n_jobs=-1
    )
    cal_model = CalibratedClassifierCV(rf, cv=5, method="isotonic")
    cal_model.fit(X_tr, y_tr)

    y_pred  = cal_model.predict(X_te)
    y_proba = cal_model.predict_proba(X_te)

    acc     = accuracy_score(y_te, y_pred)
    top2    = top_k_accuracy_score(y_te, y_proba, k=2)

    mlflow.log_metric("accuracy",     acc)
    mlflow.log_metric("top2_accuracy",top2)
    mlflow.sklearn.log_model(cal_model, "product_recommendation_model",
                             registered_model_name="debtbusters_product_recommendation")

    print(f"Accuracy: {acc:.4f} | Top-2 Accuracy: {top2:.4f}")
    print(classification_report(y_te, y_pred, target_names=target_le.classes_))

# COMMAND ----------
# Write recommendations
proba_df            = pd.DataFrame(cal_model.predict_proba(X), columns=target_le.classes_)
proba_df["recommendation"] = target_le.inverse_transform(cal_model.predict(X))
proba_df["confidence"]     = proba_df.max(axis=1)

out = spark.createDataFrame(proba_df.reset_index(drop=True))
out.write.format("delta").mode("overwrite").save("/mnt/debtbusters/ml/product_recommendations")
spark.sql("CREATE TABLE IF NOT EXISTS debtbusters_ml.product_recommendations "
          "USING DELTA LOCATION '/mnt/debtbusters/ml/product_recommendations'")
print("Product recommendations written.")
