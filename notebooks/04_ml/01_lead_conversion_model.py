# Databricks Notebook — ML Model 1: Lead Conversion Prediction
# Predicts probability that a lead converts to a paying debt-review client
# Algorithm: XGBoost with MLflow tracking

# COMMAND ----------
# %pip install xgboost shap

# COMMAND ----------
import mlflow
import mlflow.xgboost
import xgboost as xgb
import shap
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from pyspark.sql import functions as F

mlflow.set_experiment("/debtbusters/lead_conversion")

# COMMAND ----------
# Feature engineering: join leads → assessments → clients
leads   = spark.table("debtbusters_gold.fact_lead").toPandas()
assess  = spark.table("debtbusters_gold.fact_assessment").toPandas()
clients = spark.table("debtbusters_gold.dim_client").toPandas()

df = (leads
      .merge(assess[["client_key","gross_income","net_income","debt_to_income_ratio",
                      "over_indebted_flag","total_debt_balance","number_of_creditors"]],
             on="client_key", how="left")
      .merge(clients[["client_key","age","age_band","gender","province",
                       "employment_status","income_band"]],
             on="client_key", how="left")
)

# Target
df["target"] = df["converted_flag"].astype(int)

# COMMAND ----------
# Encode categoricals
cat_cols = ["source_channel","utm_source","utm_medium","lead_status",
            "age_band","gender","province","employment_status","income_band"]

le_map = {}
for col in cat_cols:
    le = LabelEncoder()
    df[col + "_enc"] = le.fit_transform(df[col].fillna("UNKNOWN").astype(str))
    le_map[col] = le

# Features
feature_cols = (
    ["lead_score","cost_per_lead","lead_score",
     "gross_income","net_income","debt_to_income_ratio","total_debt_balance","number_of_creditors"]
    + [c + "_enc" for c in cat_cols]
)
feature_cols = [c for c in feature_cols if c in df.columns]

X = df[feature_cols].fillna(0)
y = df["target"]

print(f"Dataset: {len(X):,} rows | {y.mean():.2%} conversion rate")

# COMMAND ----------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# COMMAND ----------
params = {
    "n_estimators":    400,
    "max_depth":       6,
    "learning_rate":   0.05,
    "subsample":       0.80,
    "colsample_bytree":0.80,
    "scale_pos_weight":len(y[y==0]) / len(y[y==1]),   # handle imbalance
    "use_label_encoder": False,
    "eval_metric":    "auc",
    "random_state":    42,
}

with mlflow.start_run(run_name="lead_conversion_xgb_v1"):
    mlflow.log_params(params)

    model = xgb.XGBClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        early_stopping_rounds=30,
        verbose=50,
    )

    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred  = (y_proba >= 0.50).astype(int)

    auc     = roc_auc_score(y_test, y_proba)
    report  = classification_report(y_test, y_pred, output_dict=True)

    mlflow.log_metric("auc_roc",   auc)
    mlflow.log_metric("precision", report["1"]["precision"])
    mlflow.log_metric("recall",    report["1"]["recall"])
    mlflow.log_metric("f1_score",  report["1"]["f1-score"])

    mlflow.xgboost.log_model(model, "lead_conversion_model",
                              registered_model_name="debtbusters_lead_conversion")

    print(f"\nAUC-ROC: {auc:.4f}")
    print(classification_report(y_test, y_pred))

# COMMAND ----------
# SHAP feature importance
explainer   = shap.TreeExplainer(model)
shap_vals   = explainer.shap_values(X_test[:500])
shap.summary_plot(shap_vals, X_test[:500], feature_names=feature_cols, show=False)

# COMMAND ----------
# Write predictions back to gold
X["lead_conversion_score"] = model.predict_proba(X.fillna(0))[:, 1]
X["lead_conversion_segment"] = pd.cut(
    X["lead_conversion_score"],
    bins=[0, 0.25, 0.50, 0.75, 1.0],
    labels=["Low","Medium","High","Very High"]
)
pred_df = spark.createDataFrame(
    X[["lead_conversion_score","lead_conversion_segment"]].reset_index(drop=True)
)
pred_df.write.format("delta").mode("overwrite").save("/mnt/debtbusters/ml/lead_conversion_predictions")
spark.sql("CREATE TABLE IF NOT EXISTS debtbusters_ml.lead_conversion_predictions "
          "USING DELTA LOCATION '/mnt/debtbusters/ml/lead_conversion_predictions'")
print("Predictions written to debtbusters_ml.lead_conversion_predictions")
