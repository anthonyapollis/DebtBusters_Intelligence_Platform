# Databricks Notebook — ML Model 4: Credit Score Improvement Forecasting
# Predicts a client's credit score trajectory at 3, 6, 12 months post-debt-review enrolment
# Algorithm: Multi-output Gradient Boosting Regressor + time series features

# COMMAND ----------
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
from pyspark.sql import functions as F

mlflow.set_experiment("/debtbusters/credit_score_improvement")

# COMMAND ----------
credit  = spark.table("debtbusters_gold.fact_credit_monitoring").toPandas()
clients = spark.table("debtbusters_gold.dim_client").toPandas()
assess  = spark.table("debtbusters_gold.fact_assessment").toPandas()
cases   = spark.table("debtbusters_gold.fact_debt_review_case").toPandas()

# Sort by client + date to engineer time features
credit["monitoring_date"] = pd.to_datetime(credit["monitoring_date"])
credit = credit.sort_values(["client_key","monitoring_date"])

# Build training rows: for each record, simulate targets at +3/+6/+12 months
# We use a simple forward-fill from available data as proxy targets
credit["score_plus_3m"]  = credit.groupby("client_key")["credit_score"].shift(-3)
credit["score_plus_6m"]  = credit.groupby("client_key")["credit_score"].shift(-6)
credit["score_plus_12m"] = credit.groupby("client_key")["credit_score"].shift(-12)

# Rolling features
credit["rolling_3m_avg"]  = credit.groupby("client_key")["credit_score"].transform(lambda x: x.rolling(3,  min_periods=1).mean())
credit["rolling_6m_avg"]  = credit.groupby("client_key")["credit_score"].transform(lambda x: x.rolling(6,  min_periods=1).mean())
credit["rolling_3m_trend"]= credit.groupby("client_key")["score_change"].transform(lambda x: x.rolling(3,  min_periods=1).mean())

df = (credit.dropna(subset=["score_plus_3m","score_plus_6m","score_plus_12m"])
      .merge(clients[["client_key","age","employment_status","income_band","province"]], on="client_key", how="left")
      .merge(assess[["client_key","debt_to_income_ratio","total_debt_balance","over_indebted_flag"]].drop_duplicates("client_key"), on="client_key", how="left")
      .merge(cases[["client_key","case_stage","days_in_stage"]].drop_duplicates("client_key"), on="client_key", how="left")
)

# COMMAND ----------
cat_cols = ["credit_risk_band","employment_status","income_band","province","case_stage","bureau"]
for col in cat_cols:
    if col in df.columns:
        le = LabelEncoder()
        df[col+"_enc"] = le.fit_transform(df[col].fillna("UNKNOWN").astype(str))

feature_cols = [
    "credit_score","score_change","accounts_open","accounts_in_arrears",
    "judgements_count","defaults_count","enquiries_count",
    "total_credit_limit","total_utilisation_pct",
    "rolling_3m_avg","rolling_6m_avg","rolling_3m_trend",
    "age","debt_to_income_ratio","total_debt_balance","days_in_stage",
] + [c+"_enc" for c in cat_cols if c+"_enc" in df.columns]

feature_cols = [c for c in feature_cols if c in df.columns]
target_cols  = ["score_plus_3m","score_plus_6m","score_plus_12m"]

X = df[feature_cols].fillna(0)
y = df[target_cols].fillna(df["credit_score"])

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

# COMMAND ----------
with mlflow.start_run(run_name="credit_score_forecast_gb_v1"):
    base = GradientBoostingRegressor(
        n_estimators=300, learning_rate=0.05,
        max_depth=5, subsample=0.80, random_state=42
    )
    model = MultiOutputRegressor(base, n_jobs=-1)
    model.fit(X_tr, y_tr)

    y_pred = model.predict(X_te)

    for i, col in enumerate(target_cols):
        mae = mean_absolute_error(y_te.iloc[:,i], y_pred[:,i])
        r2  = r2_score(y_te.iloc[:,i], y_pred[:,i])
        mlflow.log_metric(f"mae_{col}",  mae)
        mlflow.log_metric(f"r2_{col}",   r2)
        print(f"{col}: MAE={mae:.1f} | R²={r2:.4f}")

    mlflow.sklearn.log_model(model, "credit_score_model",
                             registered_model_name="debtbusters_credit_score_forecast")

# COMMAND ----------
preds = pd.DataFrame(model.predict(X), columns=["score_3m","score_6m","score_12m"])
preds["improvement_12m"] = preds["score_12m"] - df["credit_score"].values[:len(preds)]
preds["trajectory"]      = preds["improvement_12m"].apply(
    lambda x: "Strong Improvement" if x > 50
    else "Moderate Improvement" if x > 20
    else "Flat" if x > -10
    else "Declining"
)
out = spark.createDataFrame(preds.reset_index(drop=True))
out.write.format("delta").mode("overwrite").save("/mnt/debtbusters/ml/credit_score_forecasts")
spark.sql("CREATE TABLE IF NOT EXISTS debtbusters_ml.credit_score_forecasts "
          "USING DELTA LOCATION '/mnt/debtbusters/ml/credit_score_forecasts'")
print("Credit score forecasts written.")
