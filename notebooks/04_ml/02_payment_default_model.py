# Databricks Notebook — ML Model 2: Payment Default Prediction
# Predicts probability a client will miss next payment
# Algorithm: LightGBM with MLflow + Feature Store

# COMMAND ----------
# %pip install lightgbm shap

# COMMAND ----------
import mlflow
import mlflow.lightgbm
import lightgbm as lgb
import shap
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report, average_precision_score
from sklearn.preprocessing import LabelEncoder

mlflow.set_experiment("/debtbusters/payment_default")

# COMMAND ----------
# Feature assembly
payments = spark.table("debtbusters_gold.fact_payment").toPandas()
clients  = spark.table("debtbusters_gold.dim_client").toPandas()
credit   = (spark.table("debtbusters_gold.fact_credit_monitoring")
            .groupBy("client_key")
            .agg(
                F.avg("credit_score").alias("avg_credit_score"),
                F.max("accounts_in_arrears").alias("max_accts_arrears"),
                F.sum("judgements_count").alias("total_judgements"),
                F.avg("total_utilisation_pct").alias("avg_utilisation"),
            )
            .toPandas()
)

from pyspark.sql import functions as F  # noqa

# Client-level payment aggregation (rolling window features)
pay_agg = (payments
           .groupby("client_key")
           .agg(
               total_payments      = ("payment_id",             "count"),
               total_missed        = ("missed_payment_flag",    "sum"),
               avg_collection_rate = ("collection_rate",        "mean"),
               total_arrears       = ("arrears_amount",         "sum"),
               avg_expected        = ("expected_payment_amount","mean"),
           )
           .reset_index()
)
pay_agg["miss_rate"] = pay_agg["total_missed"] / pay_agg["total_payments"]

df = (payments[["payment_id","client_key","missed_payment_flag","payment_year","payment_month"]]
      .merge(pay_agg,    on="client_key", how="left")
      .merge(credit,     on="client_key", how="left")
      .merge(clients[["client_key","age","employment_status","income_band","province"]], on="client_key", how="left")
)

df["target"] = df["missed_payment_flag"].astype(int)

# COMMAND ----------
cat_cols = ["employment_status","income_band","province"]
for col in cat_cols:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col].fillna("UNKNOWN").astype(str))

feature_cols = [
    "total_payments","total_missed","avg_collection_rate","total_arrears",
    "avg_expected","miss_rate","avg_credit_score","max_accts_arrears",
    "total_judgements","avg_utilisation","age","payment_year","payment_month",
] + [c + "_enc" for c in cat_cols]

feature_cols = [c for c in feature_cols if c in df.columns]
X = df[feature_cols].fillna(0)
y = df["target"]

print(f"Dataset: {len(X):,} | Default rate: {y.mean():.2%}")

# COMMAND ----------
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

lgb_params = {
    "objective":       "binary",
    "metric":          "auc",
    "n_estimators":    500,
    "learning_rate":   0.03,
    "num_leaves":      63,
    "max_depth":       -1,
    "min_child_samples": 50,
    "subsample":       0.80,
    "colsample_bytree":0.80,
    "is_unbalance":    True,
    "random_state":    42,
    "verbose":         -1,
}

with mlflow.start_run(run_name="payment_default_lgb_v1"):
    mlflow.log_params(lgb_params)

    model = lgb.LGBMClassifier(**lgb_params)
    model.fit(X_tr, y_tr,
              eval_set=[(X_te, y_te)],
              callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)])

    y_proba = model.predict_proba(X_te)[:,1]
    auc     = roc_auc_score(y_te, y_proba)
    aps     = average_precision_score(y_te, y_proba)

    mlflow.log_metric("auc_roc", auc)
    mlflow.log_metric("avg_precision_score", aps)
    mlflow.lightgbm.log_model(model, "payment_default_model",
                               registered_model_name="debtbusters_payment_default")

    print(f"AUC-ROC: {auc:.4f} | Avg Precision: {aps:.4f}")
    print(classification_report(y_te, (y_proba >= 0.40).astype(int)))

# COMMAND ----------
# Write risk scores back
X["default_risk_score"] = model.predict_proba(X.fillna(0))[:,1]
X["default_risk_band"]  = pd.cut(
    X["default_risk_score"],
    bins=[0, 0.20, 0.40, 0.60, 1.0],
    labels=["Low","Medium","High","Critical"]
)
out = spark.createDataFrame(X[["default_risk_score","default_risk_band"]].reset_index(drop=True))
out.write.format("delta").mode("overwrite").save("/mnt/debtbusters/ml/payment_default_scores")
spark.sql("CREATE TABLE IF NOT EXISTS debtbusters_ml.payment_default_scores "
          "USING DELTA LOCATION '/mnt/debtbusters/ml/payment_default_scores'")
print("Default risk scores written.")
