# DebtBusters Intelligence Platform
## Confluent Financial Wellness Group — Enterprise Data Warehouse on Databricks Azure

---

## Project Overview

End-to-end data engineering and ML portfolio project modelled on the Confluent/IDM group (DebtBusters, JustMoney). Covers the full South African debt counselling and financial wellness lifecycle: lead acquisition → affordability assessment → debt review → payment distribution → credit monitoring → debt clearance.

**Tech Stack:** Databricks (Azure) · Delta Lake · PySpark · MLflow · XGBoost · LightGBM · CatBoost · Power BI

---

## Architecture

```
Google Analytics / CRM / Call Centre / Credit Bureau / PDA Payments
                              │
                         ┌────▼────┐
                         │  Bronze  │  Raw Delta ingestion + audit columns
                         └────┬────┘
                              │
                         ┌────▼────┐
                         │  Silver  │  Cleaned · Deduplicated · Validated · Typed
                         └────┬────┘
                              │
                         ┌────▼────┐
                         │   Gold   │  Star schema dims + facts + KPI views
                         └────┬────┘
                              │
              ┌───────────────┼───────────────┐
         ┌────▼────┐    ┌─────▼─────┐   ┌────▼────┐
         │   ML    │    │  Power BI  │   │ Databricks│
         │ Models  │    │ Dashboards │   │  SQL     │
         └─────────┘    └───────────┘   └─────────┘
```

---

## Synthetic Data (80,000 clients · ~3.96M rows total)

| Entity              | Rows        |
|---------------------|-------------|
| Clients             | 80,000      |
| Leads               | 500,000     |
| Assessments         | 120,000     |
| Debt Review Cases   | 60,000      |
| Debt Accounts       | 700,000     |
| Repayment Plans     | 400,000     |
| Payments            | 1,500,000   |
| Credit Monitoring   | 600,000     |
| **Total**           | **~3,960,000** |

---

## Star Schema

**Dimensions:** Dim_Date · Dim_Client · Dim_Creditor · Dim_Counsellor · Dim_Financial_Product

**Facts:** Fact_Lead · Fact_Assessment · Fact_Debt_Review_Case · Fact_Repayment_Plan · Fact_Payment · Fact_Credit_Monitoring

---

## ML Models — Validated Results

| Model | Algorithm | Metric | Score | Business Interpretation |
|-------|-----------|--------|-------|------------------------|
| Lead Conversion | XGBoost | AUC | 0.74 | Identifies 74% of convertible leads — prioritise call centre outreach |
| Payment Default | LightGBM | AUC | 0.73 | Early-warning system — flag at-risk clients before they miss payment |
| Product Recommendation | Random Forest + Isotonic | Accuracy | 0.85 | 85% correct product match — reduces mis-sells and rework |
| Credit Score Forecast | Multi-output GBM | R² | 0.89 | Predicts 3/6/12-month score trajectory for client counselling |
| Client Churn | CatBoost + Optuna | AUC | 0.72 | Detects withdrawal risk early — enables targeted retention calls |

---

## Power BI Dashboard Pages

1. Executive Summary
2. Lead & Marketing Funnel
3. Client Affordability
4. Debt Review Operations
5. Payment Performance
6. Creditor Management
7. Credit Risk
8. ML Insights

---

## Notebook Execution Order

```
00_setup/00_create_database.py
00_setup/01_mount_storage.py
05_data_generation/generate_synthetic_data.py
01_bronze/01_bronze_clients.py
01_bronze/02_bronze_leads.py
01_bronze/03_bronze_assessments.py
01_bronze/04_bronze_cases_accounts_payments.py
02_silver/01_silver_clients.py
02_silver/02_silver_leads_assessments.py
02_silver/03_silver_cases_payments_credit.py
03_gold/01_dim_date.py
03_gold/02_dim_client.py
03_gold/03_dim_creditor_counsellor_product.py
03_gold/04_fact_lead.py
03_gold/05_fact_assessment.py
03_gold/06_fact_debt_review_case.py
03_gold/07_fact_payment_repayment_credit.py
04_ml/01_lead_conversion_model.py
04_ml/02_payment_default_model.py
04_ml/03_product_recommendation.py
04_ml/04_credit_score_improvement.py
04_ml/05_client_churn_model.py
```

---

## Key Business KPIs

| Domain | KPI |
|--------|-----|
| Marketing | Lead Conversion Rate · Cost per Conversion |
| Operations | Active Cases · Avg Days in Stage · Case Withdrawal Rate |
| Finance | Collection Rate · Missed Payment Rate · Total Arrears |
| Credit Risk | Avg Credit Score · High-Risk Client Count |
| Client Outcome | Clearances Issued · Debt Cleared Total |
| Creditor | Acceptance Rate · Interest Rate Reduction |

---

*Anthony Apollis · Portfolio Project 2026*
