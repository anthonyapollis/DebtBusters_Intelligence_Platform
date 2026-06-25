# Databricks Notebook — ML Model 5: Client Churn / Case Withdrawal Prediction
# Predicts probability a client will withdraw from debt counselling before completion
# Algorithm: CatBoost with Optuna hyperparameter tuning + MLflow

# COMMAND ----------
# %pip install catboost optuna

# COMMAND ----------
import mlflow
import mlflow.catboost
import catboost as cb
import optuna
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import roc_auc_score, classification_report
from pyspark.sql import functions as F

mlflow.set_experiment("/debtbusters/client_churn")
optuna.logging.set_verbosity(optuna.logging.WARNING)

# COMMAND ----------
cases   = spark.table("debtbusters_gold.fact_debt_review_case").toPandas()
clients = spark.table("debtbusters_gold.dim_client").toPandas()
assess  = spark.table("debtbusters_gold.fact_assessment").toPandas()
pay_agg = (spark.table("debtbusters_gold.fact_payment")
           .groupBy("client_key")
           .agg(
               F.count("payment_id").alias("total_payments"),
               F.sum(F.col("missed_payment_flag").cast("int")).alias("missed_payments"),
               F.avg("collection_rate").alias("avg_collection_rate"),
               F.sum("arrears_amount").alias("total_arrears"),
           )
           .toPandas()
)

df = (cases
      .merge(clients[["client_key","age","gender","employment_status","income_band","province"]], on="client_key", how="left")
      .merge(assess[["client_key","debt_to_income_ratio","total_debt_balance","disposable_income",
                     "over_indebted_flag","number_of_creditors"]].drop_duplicates("client_key"), on="client_key", how="left")
      .merge(pay_agg, on="client_key", how="left")
)

# Target: 1 = withdrawn/churned
df["target"] = (df["case_stage"] == "Withdrawn").astype(int)
print(f"Churn rate: {df['target'].mean():.2%}")

# COMMAND ----------
cat_features = ["gender","employment_status","income_band","province",
                "legal_status","ncr_status","court_order_status"]

num_features = ["age","debt_to_income_ratio","total_debt_balance","disposable_income",
                "number_of_creditors","days_in_stage","days_to_acceptance",
                "total_payments","missed_payments","avg_collection_rate","total_arrears"]

all_features = [f for f in cat_features + num_features if f in df.columns]

for col in cat_features:
    if col in df.columns:
        df[col] = df[col].fillna("UNKNOWN").astype(str)

for col in num_features:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

X = df[all_features]
y = df["target"]

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20, random_state=42, stratify=y)

cat_idx = [all_features.index(c) for c in cat_features if c in all_features]

# COMMAND ----------
def objective(trial):
    params = {
        "iterations":        trial.suggest_int("iterations", 200, 800),
        "depth":             trial.suggest_int("depth", 4, 10),
        "learning_rate":     trial.suggest_float("learning_rate", 0.01, 0.15),
        "l2_leaf_reg":       trial.suggest_float("l2_leaf_reg", 1, 20),
        "bagging_temperature":trial.suggest_float("bagging_temperature", 0, 1),
        "random_strength":   trial.suggest_float("random_strength", 1, 10),
        "border_count":      trial.suggest_int("border_count", 32, 254),
        "auto_class_weights":"Balanced",
        "eval_metric":       "AUC",
        "verbose":           0,
        "random_seed":       42,
    }
    model = cb.CatBoostClassifier(**params)
    model.fit(X_tr, y_tr, cat_features=cat_idx,
              eval_set=(X_te, y_te), early_stopping_rounds=50, verbose=False)
    return roc_auc_score(y_te, model.predict_proba(X_te)[:,1])

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=30, show_progress_bar=True)
print(f"Best AUC: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")

# COMMAND ----------
with mlflow.start_run(run_name="client_churn_catboost_v1"):
    best = study.best_params
    best.update({"auto_class_weights":"Balanced","eval_metric":"AUC",
                 "verbose":0,"random_seed":42})
    mlflow.log_params(best)

    model = cb.CatBoostClassifier(**best)
    model.fit(X_tr, y_tr, cat_features=cat_idx,
              eval_set=(X_te, y_te), early_stopping_rounds=50, verbose=False)

    y_proba = model.predict_proba(X_te)[:,1]
    auc     = roc_auc_score(y_te, y_proba)

    mlflow.log_metric("auc_roc", auc)
    mlflow.catboost.log_model(model, "client_churn_model",
                              registered_model_name="debtbusters_client_churn")

    print(f"Final AUC-ROC: {auc:.4f}")
    print(classification_report(y_te, (y_proba >= 0.40).astype(int)))

# COMMAND ----------
X["churn_risk_score"]   = model.predict_proba(X)[:,1]
X["churn_risk_segment"] = pd.cut(
    X["churn_risk_score"],
    bins=[0,0.20,0.40,0.65,1.0],
    labels=["Low","Medium","High","Critical"]
)
out = spark.createDataFrame(X[["churn_risk_score","churn_risk_segment"]].reset_index(drop=True))
out.write.format("delta").mode("overwrite").save("/mnt/debtbusters/ml/client_churn_scores")
spark.sql("CREATE TABLE IF NOT EXISTS debtbusters_ml.client_churn_scores "
          "USING DELTA LOCATION '/mnt/debtbusters/ml/client_churn_scores'")
print("Churn risk scores written.")
