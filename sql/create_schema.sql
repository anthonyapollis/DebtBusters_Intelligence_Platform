-- ============================================================
-- DebtBusters Intelligence Platform — Gold Star Schema DDL
-- Compatible with: Databricks SQL / Azure Synapse Analytics
-- ============================================================

-- DATABASES
CREATE DATABASE IF NOT EXISTS debtbusters_bronze;
CREATE DATABASE IF NOT EXISTS debtbusters_silver;
CREATE DATABASE IF NOT EXISTS debtbusters_gold;
CREATE DATABASE IF NOT EXISTS debtbusters_ml;

-- ============================================================
-- DIMENSIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS debtbusters_gold.dim_date (
    date_key         INT            NOT NULL,
    date             DATE           NOT NULL,
    year             INT,
    quarter          INT,
    quarter_label    VARCHAR(20),
    month            INT,
    month_name       VARCHAR(20),
    month_short      VARCHAR(5),
    month_year       VARCHAR(10),
    week_of_year     INT,
    day_of_week      INT,
    day_name         VARCHAR(15),
    day_short        VARCHAR(5),
    is_weekend       BOOLEAN,
    is_month_end     BOOLEAN,
    financial_year   VARCHAR(10),
    financial_quarter VARCHAR(5),
    CONSTRAINT pk_dim_date PRIMARY KEY (date_key)
)
USING DELTA
COMMENT 'Date dimension covering 2020-2030';

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.dim_client (
    client_key          VARCHAR(64)    NOT NULL,
    client_id           VARCHAR(36),
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    full_name           VARCHAR(200),
    age                 INT,
    age_band            VARCHAR(20),
    gender              VARCHAR(20),
    province            VARCHAR(50),
    city                VARCHAR(100),
    employment_status   VARCHAR(50),
    income_band         VARCHAR(30),
    gross_income        DECIMAL(15,2),
    consent_status      VARCHAR(20),
    is_consented        BOOLEAN,
    created_date        DATE,
    source_system       VARCHAR(50),
    _gold_at            TIMESTAMP,
    CONSTRAINT pk_dim_client PRIMARY KEY (client_key)
)
USING DELTA
COMMENT 'Client dimension — SCD Type 1';

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.dim_creditor (
    creditor_key    VARCHAR(64) NOT NULL,
    creditor_id     VARCHAR(36),
    creditor_name   VARCHAR(100),
    creditor_type   VARCHAR(50),
    industry        VARCHAR(50),
    ncr_registered  BOOLEAN,
    _gold_at        TIMESTAMP,
    CONSTRAINT pk_dim_creditor PRIMARY KEY (creditor_key)
)
USING DELTA;

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.dim_counsellor (
    counsellor_key  VARCHAR(64) NOT NULL,
    counsellor_id   VARCHAR(36),
    counsellor_name VARCHAR(100),
    team            VARCHAR(50),
    branch          VARCHAR(50),
    ncr_number      VARCHAR(20),
    active_flag     BOOLEAN,
    hire_date       DATE,
    _gold_at        TIMESTAMP,
    CONSTRAINT pk_dim_counsellor PRIMARY KEY (counsellor_key)
)
USING DELTA;

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.dim_financial_product (
    product_key      VARCHAR(64) NOT NULL,
    product_id       VARCHAR(36),
    product_code     VARCHAR(20),
    product_name     VARCHAR(100),
    product_category VARCHAR(100),
    fee_type         VARCHAR(30),
    active_flag      BOOLEAN,
    _gold_at         TIMESTAMP,
    CONSTRAINT pk_dim_financial_product PRIMARY KEY (product_key)
)
USING DELTA;

-- ============================================================
-- FACT TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_lead (
    lead_key        VARCHAR(64)    NOT NULL,
    lead_id         VARCHAR(36),
    client_key      VARCHAR(64),
    date_key        INT,
    source_channel  VARCHAR(50),
    campaign        VARCHAR(200),
    utm_source      VARCHAR(50),
    utm_medium      VARCHAR(50),
    lead_score      INT,
    lead_status     VARCHAR(30),
    cost_per_lead   DECIMAL(10,2),
    qualified_flag  BOOLEAN,
    assessed_flag   BOOLEAN,
    converted_flag  BOOLEAN,
    _gold_at        TIMESTAMP,
    CONSTRAINT pk_fact_lead PRIMARY KEY (lead_key),
    CONSTRAINT fk_lead_client  FOREIGN KEY (client_key)  REFERENCES debtbusters_gold.dim_client  (client_key),
    CONSTRAINT fk_lead_date    FOREIGN KEY (date_key)    REFERENCES debtbusters_gold.dim_date    (date_key)
)
USING DELTA
PARTITIONED BY (date_key)
COMMENT 'All marketing leads across channels';

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_assessment (
    assessment_key                  VARCHAR(64),
    assessment_id                   VARCHAR(36),
    client_key                      VARCHAR(64),
    counsellor_key                  VARCHAR(64),
    date_key                        INT,
    gross_income                    DECIMAL(15,2),
    net_income                      DECIMAL(15,2),
    living_expenses                 DECIMAL(15,2),
    total_debt_balance              DECIMAL(18,2),
    total_monthly_debt_instalment   DECIMAL(15,2),
    disposable_income               DECIMAL(15,2),
    debt_to_income_ratio            DECIMAL(8,4),
    dti_band                        VARCHAR(20),
    affordability_amount            DECIMAL(15,2),
    over_indebted_flag              BOOLEAN,
    recommended_product             VARCHAR(50),
    number_of_creditors             INT,
    _gold_at                        TIMESTAMP,
    CONSTRAINT pk_fact_assessment PRIMARY KEY (assessment_key)
)
USING DELTA
COMMENT 'Client financial affordability assessments';

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_debt_review_case (
    case_key                VARCHAR(64),
    case_id                 VARCHAR(36),
    client_key              VARCHAR(64),
    counsellor_key          VARCHAR(64),
    product_key             VARCHAR(64),
    application_date_key    INT,
    application_date        DATE,
    acceptance_date         DATE,
    court_order_date        DATE,
    completion_date         DATE,
    days_to_acceptance      INT,
    case_stage              VARCHAR(30),
    legal_status            VARCHAR(40),
    ncr_status              VARCHAR(30),
    court_order_status      VARCHAR(30),
    case_open_flag          BOOLEAN,
    is_completed            BOOLEAN,
    is_withdrawn            BOOLEAN,
    is_active               BOOLEAN,
    days_in_stage           INT,
    clearance_issued_flag   BOOLEAN,
    _gold_at                TIMESTAMP,
    CONSTRAINT pk_fact_case PRIMARY KEY (case_key)
)
USING DELTA
PARTITIONED BY (case_stage)
COMMENT 'Debt review cases lifecycle';

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_repayment_plan (
    plan_key                    VARCHAR(64),
    plan_id                     VARCHAR(36),
    case_id                     VARCHAR(36),
    creditor_key                VARCHAR(64),
    date_key                    INT,
    plan_date                   DATE,
    original_instalment         DECIMAL(12,2),
    proposed_instalment         DECIMAL(12,2),
    accepted_instalment         DECIMAL(12,2),
    accepted_flag               BOOLEAN,
    interest_rate_before        DECIMAL(6,4),
    interest_rate_after         DECIMAL(6,4),
    term_months_before          INT,
    term_months_after           INT,
    monthly_saving              DECIMAL(12,2),
    total_saving_estimated      DECIMAL(15,2),
    reduction_pct               DECIMAL(6,2),
    creditor_acceptance_status  VARCHAR(30),
    _gold_at                    TIMESTAMP,
    CONSTRAINT pk_fact_plan PRIMARY KEY (plan_key)
)
USING DELTA
COMMENT 'Negotiated repayment plans per creditor per case';

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_payment (
    payment_key             VARCHAR(64),
    payment_id              VARCHAR(36),
    case_id                 VARCHAR(36),
    client_key              VARCHAR(64),
    creditor_key            VARCHAR(64),
    date_key                INT,
    payment_date            DATE,
    payment_month           VARCHAR(10),
    payment_year            INT,
    expected_payment_amount DECIMAL(12,2),
    actual_payment_amount   DECIMAL(12,2),
    distribution_amount     DECIMAL(12,2),
    arrears_amount          DECIMAL(12,2),
    collection_rate         DECIMAL(8,4),
    payment_status          VARCHAR(20),
    missed_payment_flag     BOOLEAN,
    pda_reference           VARCHAR(30),
    _gold_at                TIMESTAMP,
    CONSTRAINT pk_fact_payment PRIMARY KEY (payment_key)
)
USING DELTA
PARTITIONED BY (payment_year, payment_month)
COMMENT 'Monthly PDA payments per client per creditor';

-- ---------------------------------------------------------- --

CREATE TABLE IF NOT EXISTS debtbusters_gold.fact_credit_monitoring (
    monitoring_key          VARCHAR(64),
    monitoring_id           VARCHAR(36),
    client_key              VARCHAR(64),
    date_key                INT,
    monitoring_date         DATE,
    credit_score            INT,
    score_change            INT,
    credit_risk_band        VARCHAR(30),
    accounts_open           INT,
    accounts_in_arrears     INT,
    judgements_count        INT,
    defaults_count          INT,
    enquiries_count         INT,
    total_credit_limit      DECIMAL(18,2),
    total_utilisation_pct   DECIMAL(6,4),
    bureau                  VARCHAR(30),
    _gold_at                TIMESTAMP,
    CONSTRAINT pk_fact_credit PRIMARY KEY (monitoring_key)
)
USING DELTA
COMMENT 'Credit bureau monitoring snapshots per client';


-- ============================================================
-- KPI VIEWS
-- ============================================================

CREATE OR REPLACE VIEW debtbusters_gold.vw_lead_funnel AS
SELECT
    d.year,
    d.month_year,
    d.quarter_label,
    fl.source_channel,
    COUNT(*)                                        AS total_leads,
    SUM(CASE WHEN fl.qualified_flag  THEN 1 ELSE 0 END) AS qualified_leads,
    SUM(CASE WHEN fl.assessed_flag   THEN 1 ELSE 0 END) AS assessed_leads,
    SUM(CASE WHEN fl.converted_flag  THEN 1 ELSE 0 END) AS converted_leads,
    ROUND(SUM(CASE WHEN fl.qualified_flag  THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS qualification_rate_pct,
    ROUND(SUM(CASE WHEN fl.converted_flag  THEN 1.0 ELSE 0 END) / COUNT(*) * 100, 2) AS conversion_rate_pct,
    ROUND(AVG(fl.cost_per_lead), 2)                 AS avg_cost_per_lead,
    ROUND(SUM(fl.cost_per_lead) /
          NULLIF(SUM(CASE WHEN fl.converted_flag THEN 1 ELSE 0 END),0), 2) AS cost_per_conversion
FROM   debtbusters_gold.fact_lead fl
JOIN   debtbusters_gold.dim_date  d  ON fl.date_key = d.date_key
GROUP  BY 1,2,3,4;

-- ---------------------------------------------------------- --

CREATE OR REPLACE VIEW debtbusters_gold.vw_payment_performance AS
SELECT
    d.year,
    d.month_year,
    d.quarter_label,
    dc.creditor_name,
    dc.creditor_type,
    COUNT(*)                                              AS payment_count,
    SUM(fp.expected_payment_amount)                       AS expected_total,
    SUM(fp.actual_payment_amount)                         AS actual_total,
    SUM(fp.arrears_amount)                                AS total_arrears,
    SUM(CASE WHEN fp.missed_payment_flag THEN 1 ELSE 0 END) AS missed_payments,
    ROUND(SUM(fp.actual_payment_amount) /
          NULLIF(SUM(fp.expected_payment_amount),0) * 100, 2) AS collection_rate_pct,
    ROUND(SUM(CASE WHEN fp.missed_payment_flag THEN 1.0 ELSE 0 END) /
          COUNT(*) * 100, 2)                              AS missed_payment_rate_pct
FROM   debtbusters_gold.fact_payment  fp
JOIN   debtbusters_gold.dim_date      d   ON fp.date_key    = d.date_key
JOIN   debtbusters_gold.dim_creditor  dc  ON fp.creditor_key= dc.creditor_key
GROUP  BY 1,2,3,4,5;

-- ---------------------------------------------------------- --

CREATE OR REPLACE VIEW debtbusters_gold.vw_case_pipeline AS
SELECT
    drc.case_stage,
    drc.legal_status,
    drc.ncr_status,
    dc.province,
    dcn.team,
    COUNT(*)                                              AS case_count,
    SUM(CASE WHEN drc.is_active    THEN 1 ELSE 0 END)    AS active_cases,
    SUM(CASE WHEN drc.is_completed THEN 1 ELSE 0 END)    AS completed_cases,
    SUM(CASE WHEN drc.is_withdrawn THEN 1 ELSE 0 END)    AS withdrawn_cases,
    SUM(CASE WHEN drc.clearance_issued_flag THEN 1 ELSE 0 END) AS clearances_issued,
    ROUND(AVG(drc.days_in_stage), 1)                     AS avg_days_in_stage,
    ROUND(AVG(drc.days_to_acceptance), 1)                AS avg_days_to_acceptance
FROM   debtbusters_gold.fact_debt_review_case drc
JOIN   debtbusters_gold.dim_client            dc  ON drc.client_key     = dc.client_key
JOIN   debtbusters_gold.dim_counsellor        dcn ON drc.counsellor_key = dcn.counsellor_key
GROUP  BY 1,2,3,4,5;

-- ---------------------------------------------------------- --

CREATE OR REPLACE VIEW debtbusters_gold.vw_client_affordability AS
SELECT
    d.year,
    d.quarter_label,
    dc.province,
    dc.income_band,
    dc.employment_status,
    COUNT(*)                                         AS assessments,
    SUM(CASE WHEN fa.over_indebted_flag THEN 1 ELSE 0 END) AS over_indebted_count,
    ROUND(AVG(fa.gross_income), 2)                   AS avg_gross_income,
    ROUND(AVG(fa.total_debt_balance), 2)             AS avg_total_debt,
    ROUND(AVG(fa.debt_to_income_ratio) * 100, 2)     AS avg_dti_pct,
    ROUND(AVG(fa.disposable_income), 2)              AS avg_disposable_income,
    ROUND(AVG(fa.number_of_creditors), 1)            AS avg_creditors,
    fa.recommended_product,
    COUNT(*) AS recommended_count
FROM   debtbusters_gold.fact_assessment  fa
JOIN   debtbusters_gold.dim_date         d   ON fa.date_key    = d.date_key
JOIN   debtbusters_gold.dim_client       dc  ON fa.client_key  = dc.client_key
GROUP  BY 1,2,3,4,5,13;
