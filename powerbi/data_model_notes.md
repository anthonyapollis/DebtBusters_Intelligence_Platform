# Power BI Data Model — DebtBusters Intelligence Platform

## Connection
- Datasource: Databricks SQL Endpoint (Azure)
- Mode: Import (scheduled refresh) or DirectQuery for real-time
- Connector: Databricks connector in Power BI Desktop

## Star Schema Relationships

| From Table         | From Column  | To Table               | To Column   | Cardinality |
|--------------------|--------------|------------------------|-------------|-------------|
| fact_lead          | client_key   | dim_client             | client_key  | Many → One  |
| fact_lead          | date_key     | dim_date               | date_key    | Many → One  |
| fact_assessment    | client_key   | dim_client             | client_key  | Many → One  |
| fact_assessment    | counsellor_key | dim_counsellor       | counsellor_key | Many → One |
| fact_assessment    | date_key     | dim_date               | date_key    | Many → One  |
| fact_debt_review_case | client_key | dim_client            | client_key  | Many → One  |
| fact_debt_review_case | counsellor_key | dim_counsellor    | counsellor_key | Many → One |
| fact_debt_review_case | product_key  | dim_financial_product | product_key | Many → One  |
| fact_debt_review_case | application_date_key | dim_date    | date_key    | Many → One  |
| fact_payment       | client_key   | dim_client             | client_key  | Many → One  |
| fact_payment       | creditor_key | dim_creditor           | creditor_key| Many → One  |
| fact_payment       | date_key     | dim_date               | date_key    | Many → One  |
| fact_repayment_plan | creditor_key | dim_creditor          | creditor_key| Many → One  |
| fact_repayment_plan | date_key    | dim_date               | date_key    | Many → One  |
| fact_credit_monitoring | client_key | dim_client           | client_key  | Many → One  |
| fact_credit_monitoring | date_key  | dim_date               | date_key    | Many → One  |

## Recommended Dashboard Pages

### 1. Executive Summary
- Active Cases, Collection Rate, Total Leads (card KPIs)
- Debt Cleared Total, Avg Credit Score trend
- Case funnel waterfall chart

### 2. Lead & Marketing
- Lead Funnel (qualified → assessed → converted)
- Cost per Lead / Cost per Conversion by channel
- Lead volume trend by month

### 3. Client Affordability
- Avg DTI by province (filled map)
- Income Band distribution
- Over-indebted rate trend
- Product Recommendation breakdown

### 4. Debt Review Operations
- Case Pipeline by stage (funnel visual)
- Avg Days in Stage (bar chart)
- Counsellor performance (cases per counsellor)
- NCR Status distribution

### 5. Payment Performance
- Collection Rate trend (line chart)
- Expected vs Actual payments (clustered bar)
- Missed Payment Rate by creditor
- Total Arrears by month

### 6. Creditor Management
- Creditor Acceptance Rate (bar chart sorted)
- Total Debt by Creditor Type
- Interest Rate Before vs After (scatter)
- Monthly Saving by Creditor

### 7. Credit Risk
- Credit Score distribution (histogram)
- Risk Band breakdown (donut)
- Score Improvement trajectory (line)
- High-Risk clients count (KPI card)

### 8. ML Insights
- Lead Conversion Score distribution
- Payment Default Risk heatmap (province × risk band)
- Churn Risk segments (treemap)
- Credit Score Forecast (3/6/12 month projections)
