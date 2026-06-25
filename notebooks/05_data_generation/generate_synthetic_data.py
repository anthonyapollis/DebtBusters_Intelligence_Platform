# Databricks Notebook — Synthetic Data Generation
# DebtBusters / Confluent Financial Wellness Platform
# Generates all source-layer CSV files for Bronze ingestion
# Run once on any Databricks cluster (DBR 13+) or locally with pip install faker

# COMMAND ----------
# %pip install faker
# COMMAND ----------

import random
import uuid
import math
from datetime import date, timedelta, datetime
import pandas as pd
import numpy as np
from faker import Faker
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
fake = Faker("en_ZA")
random.seed(42)
np.random.seed(42)

OUTPUT_PATH = "dbfs:/mnt/debtbusters/raw/"   # change to local path if running locally

# --------------------------------------------------------------------------- #
# REFERENCE DATA
# --------------------------------------------------------------------------- #

SA_PROVINCES = [
    "Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape",
    "Limpopo", "Mpumalanga", "North West", "Free State", "Northern Cape"
]
PROVINCE_WEIGHTS = [0.30, 0.17, 0.18, 0.10, 0.07, 0.06, 0.05, 0.05, 0.02]

CHANNELS = ["Google Ads", "Facebook", "SEO Organic", "Call Centre",
            "Referral", "Partner", "JustMoney Portal", "Email Campaign"]
CHANNEL_WEIGHTS = [0.28, 0.18, 0.15, 0.12, 0.08, 0.07, 0.07, 0.05]

EMPLOYMENT = ["Employed", "Self-Employed", "Contract", "Unemployed", "Pensioner"]
EMP_WEIGHTS = [0.58, 0.14, 0.12, 0.10, 0.06]

CREDITOR_NAMES = [
    "ABSA Bank", "Standard Bank", "FNB", "Nedbank", "Capitec",
    "African Bank", "Bayport", "RCS", "Edgars Credit", "Woolworths Financial",
    "MFC Vehicle Finance", "WesBank", "SA Home Loans", "ooba",
    "DirectAxis", "Wonga", "Lime24", "TymeBank", "Discovery Bank"
]

ACCOUNT_TYPES = [
    "Home Loan", "Vehicle Finance", "Personal Loan", "Credit Card",
    "Store Card", "Overdraft", "Micro Loan", "Student Loan"
]
ACCOUNT_TYPE_WEIGHTS = [0.15, 0.20, 0.25, 0.15, 0.10, 0.08, 0.05, 0.02]

FINANCIAL_PRODUCTS = [
    ("DC001", "Debt Counselling",    "Debt Management"),
    ("DC002", "Debt Consolidation",  "Debt Management"),
    ("CM001", "Credit Monitoring",   "Credit Services"),
    ("CR001", "Credit Repair",       "Credit Services"),
    ("IR001", "Insurance Review",    "Financial Planning"),
    ("FP001", "Financial Planning",  "Financial Planning"),
]

CASE_STAGES = [
    "Lead", "Assessment", "Application", "Review",
    "Court Order", "Active", "Completed", "Withdrawn"
]

NCR_STATUSES = ["Pending", "Registered", "Active", "Completed", "Withdrawn"]
LEGAL_STATUSES = ["Not Filed", "Filed", "Court Date Set", "Order Granted", "Order Declined"]

# --------------------------------------------------------------------------- #
# HELPERS
# --------------------------------------------------------------------------- #

def rand_date(start_year=2021, end_year=2025):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def rand_income():
    # SA income distribution — skewed right
    return round(random.lognormvariate(math.log(18000), 0.6), 2)

def rand_score():
    return random.randint(300, 850)

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

# --------------------------------------------------------------------------- #
# 1. DIM_CLIENT  (source)
# --------------------------------------------------------------------------- #

N_CLIENTS = 15_000

def build_clients():
    rows = []
    for _ in range(N_CLIENTS):
        dob = rand_date(1955, 2000)
        age = (date(2025, 1, 1) - dob).days // 365
        gross = rand_income()
        rows.append({
            "client_id":        str(uuid.uuid4()),
            "first_name":       fake.first_name(),
            "last_name":        fake.last_name(),
            "id_number":        fake.numerify("######0######"),
            "dob":              dob.isoformat(),
            "age":              age,
            "age_band":         ("18-25" if age < 26 else "26-35" if age < 36
                                 else "36-45" if age < 46 else "46-55" if age < 56 else "56+"),
            "gender":           random.choice(["Male", "Female"]),
            "province":         random.choices(SA_PROVINCES, PROVINCE_WEIGHTS)[0],
            "city":             fake.city(),
            "postal_code":      fake.postcode(),
            "email":            fake.email(),
            "mobile":           fake.phone_number(),
            "employment_status":random.choices(EMPLOYMENT, EMP_WEIGHTS)[0],
            "employer_name":    fake.company(),
            "gross_income":     gross,
            "income_band":      ("< R5k" if gross < 5000 else
                                 "R5k-R10k" if gross < 10000 else
                                 "R10k-R20k" if gross < 20000 else
                                 "R20k-R40k" if gross < 40000 else "R40k+"),
            "consent_status":   random.choices(["Granted", "Withdrawn"], [0.95, 0.05])[0],
            "created_date":     rand_date(2021, 2025).isoformat(),
            "source_system":    random.choice(["CRM", "Portal", "CallCentre"]),
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 2. DIM_CREDITOR  (source)
# --------------------------------------------------------------------------- #

def build_creditors():
    rows = []
    for name in CREDITOR_NAMES:
        rows.append({
            "creditor_id":   str(uuid.uuid4()),
            "creditor_name": name,
            "creditor_type": ("Bank" if "Bank" in name or name in ["ABSA Bank","Nedbank","FNB","Standard Bank"] else
                              "Retailer" if name in ["Edgars Credit","Woolworths Financial","RCS"] else
                              "Vehicle Finance" if "Finance" in name or "WesBank" in name else
                              "Micro Lender" if name in ["Wonga","Lime24","African Bank","Bayport"] else
                              "Home Loan"),
            "industry":      "Financial Services",
            "ncr_registered": True,
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 3. DIM_COUNSELLOR  (source)
# --------------------------------------------------------------------------- #

N_COUNSELLORS = 80

def build_counsellors():
    rows = []
    teams = ["Johannesburg A", "Johannesburg B", "Cape Town", "Durban",
             "Pretoria", "Online Team A", "Online Team B"]
    for _ in range(N_COUNSELLORS):
        rows.append({
            "counsellor_id":   str(uuid.uuid4()),
            "counsellor_name": fake.name(),
            "team":            random.choice(teams),
            "branch":          random.choice(["Sandton", "Rosebank", "Century City",
                                              "Umhlanga", "Menlyn", "Remote"]),
            "ncr_number":      fake.numerify("DC####"),
            "active_flag":     random.choices([True, False], [0.90, 0.10])[0],
            "hire_date":       rand_date(2015, 2023).isoformat(),
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 4. DIM_FINANCIAL_PRODUCT
# --------------------------------------------------------------------------- #

def build_products():
    rows = []
    for code, name, cat in FINANCIAL_PRODUCTS:
        rows.append({
            "product_id":       str(uuid.uuid4()),
            "product_code":     code,
            "product_name":     name,
            "product_category": cat,
            "fee_type":         random.choice(["Monthly", "Once-Off", "Percentage"]),
            "active_flag":      True,
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 5. FACT_LEAD  (source)
# --------------------------------------------------------------------------- #

N_LEADS = 40_000

def build_leads(clients):
    client_ids = clients["client_id"].tolist()
    rows = []
    for _ in range(N_LEADS):
        lead_date = rand_date(2021, 2025)
        qualified  = random.random() < 0.60
        assessed   = qualified and (random.random() < 0.55)
        converted  = assessed and (random.random() < 0.45)
        rows.append({
            "lead_id":         str(uuid.uuid4()),
            "client_id":       random.choice(client_ids),
            "lead_date":       lead_date.isoformat(),
            "source_channel":  random.choices(CHANNELS, CHANNEL_WEIGHTS)[0],
            "campaign":        fake.catch_phrase()[:60],
            "utm_source":      random.choice(["google","facebook","email","organic","partner"]),
            "utm_medium":      random.choice(["cpc","social","email","referral","organic"]),
            "lead_score":      random.randint(1, 100),
            "lead_status":     ("Converted" if converted else
                                "Assessed"  if assessed  else
                                "Qualified" if qualified else "Unqualified"),
            "cost_per_lead":   round(random.uniform(35, 280), 2),
            "qualified_flag":  qualified,
            "assessed_flag":   assessed,
            "converted_flag":  converted,
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 6. FACT_ASSESSMENT  (source)
# --------------------------------------------------------------------------- #

N_ASSESSMENTS = 18_000

def build_assessments(clients, counsellors):
    client_ids     = clients["client_id"].tolist()
    counsellor_ids = counsellors["counsellor_id"].tolist()
    rows = []
    for _ in range(N_ASSESSMENTS):
        gross     = rand_income()
        tax_rate  = 0.18 if gross < 18000 else 0.26 if gross < 35000 else 0.31
        net       = round(gross * (1 - tax_rate), 2)
        living    = round(gross * random.uniform(0.25, 0.45), 2)
        total_debt_instalment = round(gross * random.uniform(0.30, 0.75), 2)
        disposable = round(net - living - total_debt_instalment, 2)
        total_debt = round(total_debt_instalment * random.uniform(18, 60), 2)
        dti        = round(total_debt_instalment / net, 4) if net > 0 else 0
        over_indebted = disposable < 0 or dti > 0.70

        rows.append({
            "assessment_id":              str(uuid.uuid4()),
            "client_id":                  random.choice(client_ids),
            "counsellor_id":              random.choice(counsellor_ids),
            "assessment_date":            rand_date(2021, 2025).isoformat(),
            "gross_income":               gross,
            "net_income":                 net,
            "living_expenses":            living,
            "total_debt_balance":         total_debt,
            "total_monthly_debt_instalment": total_debt_instalment,
            "disposable_income":          disposable,
            "debt_to_income_ratio":       dti,
            "affordability_amount":       max(0, disposable),
            "over_indebted_flag":         over_indebted,
            "recommended_product":        random.choices(
                ["Debt Counselling","Debt Consolidation","Credit Repair","Credit Monitoring","Insurance Review"],
                [0.45, 0.25, 0.15, 0.10, 0.05]
            )[0],
            "number_of_creditors":        random.randint(1, 12),
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 7. FACT_DEBT_REVIEW_CASE  (source)
# --------------------------------------------------------------------------- #

N_CASES = 9_000

def build_cases(clients, counsellors, products):
    client_ids     = clients["client_id"].tolist()
    counsellor_ids = counsellors["counsellor_id"].tolist()
    product_ids    = products[products["product_category"] == "Debt Management"]["product_id"].tolist()
    rows = []
    for _ in range(N_CASES):
        app_date  = rand_date(2021, 2024)
        stage_idx = random.choices(range(len(CASE_STAGES)),
                                   [0.02,0.04,0.06,0.08,0.10,0.45,0.20,0.05])[0]
        stage     = CASE_STAGES[stage_idx]
        days      = random.randint(1, 730)

        accepted_date  = (app_date + timedelta(days=random.randint(5, 30))).isoformat() \
                          if stage_idx >= 2 else None
        court_date     = (app_date + timedelta(days=random.randint(31, 120))).isoformat() \
                          if stage_idx >= 4 else None
        completed_date = (app_date + timedelta(days=random.randint(365, 1460))).isoformat() \
                          if stage == "Completed" else None

        rows.append({
            "case_id":              str(uuid.uuid4()),
            "client_id":            random.choice(client_ids),
            "counsellor_id":        random.choice(counsellor_ids),
            "product_id":           random.choice(product_ids),
            "application_date":     app_date.isoformat(),
            "acceptance_date":      accepted_date,
            "court_order_date":     court_date,
            "completion_date":      completed_date,
            "case_stage":           stage,
            "legal_status":         random.choices(LEGAL_STATUSES,
                                        [0.10,0.20,0.20,0.40,0.10])[0],
            "ncr_status":           random.choices(NCR_STATUSES,
                                        [0.05,0.15,0.55,0.15,0.10])[0],
            "court_order_status":   random.choices(["Pending","Granted","Declined","Not Required"],
                                        [0.10,0.55,0.10,0.25])[0],
            "case_open_flag":       stage in ["Application","Review","Court Order","Active"],
            "days_in_stage":        days,
            "clearance_issued_flag":stage == "Completed" and random.random() < 0.92,
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 8. FACT_DEBT_ACCOUNT  (source)
# --------------------------------------------------------------------------- #

N_ACCOUNTS = 55_000

def build_debt_accounts(clients, creditors):
    client_ids   = clients["client_id"].tolist()
    creditor_ids = creditors["creditor_id"].tolist()
    rows = []
    for _ in range(N_ACCOUNTS):
        acc_type = random.choices(ACCOUNT_TYPES, ACCOUNT_TYPE_WEIGHTS)[0]
        balance  = round(random.lognormvariate(math.log(45000), 0.8), 2)
        balance  = clamp(balance, 500, 2_500_000)
        rate     = round(random.uniform(0.08, 0.285), 4)
        term     = random.randint(6, 300)
        instalment = round((balance * rate / 12) / (1 - (1 + rate/12) ** -term), 2)

        status = random.choices(
            ["Current","In Arrears","Restructured","Settled","Written Off"],
            [0.40, 0.25, 0.20, 0.12, 0.03]
        )[0]

        rows.append({
            "account_id":                  str(uuid.uuid4()),
            "client_id":                   random.choice(client_ids),
            "creditor_id":                 random.choice(creditor_ids),
            "account_type":                acc_type,
            "account_number":              fake.numerify("ACC-########"),
            "original_balance":            round(balance * random.uniform(0.8, 1.5), 2),
            "current_balance":             balance,
            "interest_rate":               rate,
            "original_monthly_instalment": round(instalment * 1.2, 2),
            "current_monthly_instalment":  instalment,
            "term_months":                 term,
            "account_status":              status,
            "open_date":                   rand_date(2015, 2024).isoformat(),
            "arrears_amount":              round(instalment * random.uniform(0, 3), 2) \
                                            if status == "In Arrears" else 0.0,
            "missed_payments_count":       random.randint(1, 12) \
                                            if status == "In Arrears" else 0,
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 9. FACT_REPAYMENT_PLAN  (source)
# --------------------------------------------------------------------------- #

N_PLANS = 35_000

def build_repayment_plans(cases, debt_accounts, creditors):
    case_ids    = cases["case_id"].tolist()
    account_ids = debt_accounts["account_id"].tolist()
    creditor_ids= creditors["creditor_id"].tolist()
    rows = []
    for _ in range(N_PLANS):
        orig_instalment = round(random.uniform(500, 8000), 2)
        reduction_pct   = random.uniform(0.10, 0.45)
        proposed        = round(orig_instalment * (1 - reduction_pct), 2)
        accepted        = random.random() < 0.82
        accepted_amt    = proposed if accepted else None
        rate_before     = round(random.uniform(0.10, 0.285), 4)
        rate_after      = round(rate_before * random.uniform(0.40, 0.80), 4) if accepted else None
        term_before     = random.randint(6, 120)
        term_after      = random.randint(term_before, 300) if accepted else None

        rows.append({
            "plan_id":                  str(uuid.uuid4()),
            "case_id":                  random.choice(case_ids),
            "account_id":               random.choice(account_ids),
            "creditor_id":              random.choice(creditor_ids),
            "plan_date":                rand_date(2021, 2025).isoformat(),
            "original_instalment":      orig_instalment,
            "proposed_instalment":      proposed,
            "accepted_instalment":      accepted_amt,
            "accepted_flag":            accepted,
            "interest_rate_before":     rate_before,
            "interest_rate_after":      rate_after,
            "term_months_before":       term_before,
            "term_months_after":        term_after,
            "monthly_saving":           round(orig_instalment - proposed, 2) if accepted else 0,
            "total_saving_estimated":   round((orig_instalment - proposed) * (term_after or 0), 2) \
                                         if accepted and term_after else 0,
            "creditor_acceptance_status": "Accepted" if accepted else \
                                           random.choice(["Rejected","Counter-Proposed","Pending"]),
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 10. FACT_PAYMENT  (source)
# --------------------------------------------------------------------------- #

N_PAYMENTS = 120_000

def build_payments(cases, debt_accounts, creditors):
    case_ids     = cases["case_id"].tolist()
    account_ids  = debt_accounts["account_id"].tolist()
    creditor_ids = creditors["creditor_id"].tolist()
    rows = []
    for _ in range(N_PAYMENTS):
        pay_date   = rand_date(2021, 2025)
        expected   = round(random.uniform(300, 6500), 2)
        missed     = random.random() < 0.12
        actual     = 0.0 if missed else round(expected * random.uniform(0.90, 1.05), 2)
        arrears    = round(expected - actual, 2) if actual < expected else 0.0
        distributed= round(actual * random.uniform(0.92, 1.0), 2)

        rows.append({
            "payment_id":             str(uuid.uuid4()),
            "case_id":                random.choice(case_ids),
            "account_id":             random.choice(account_ids),
            "creditor_id":            random.choice(creditor_ids),
            "payment_date":           pay_date.isoformat(),
            "payment_month":          pay_date.strftime("%Y-%m"),
            "expected_payment_amount":expected,
            "actual_payment_amount":  actual,
            "distribution_amount":    distributed,
            "arrears_amount":         arrears,
            "payment_status":         ("Missed"   if missed else
                                       "Partial"  if actual < expected * 0.99 else
                                       "Full"),
            "missed_payment_flag":    missed,
            "pda_reference":          fake.numerify("PDA-#######"),
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# 11. FACT_CREDIT_MONITORING  (source)
# --------------------------------------------------------------------------- #

N_CREDIT_RECORDS = 45_000

def build_credit_monitoring(clients):
    client_ids = clients["client_id"].tolist()
    rows = []
    for _ in range(N_CREDIT_RECORDS):
        score   = rand_score()
        change  = random.randint(-60, 80)
        rows.append({
            "monitoring_id":       str(uuid.uuid4()),
            "client_id":           random.choice(client_ids),
            "monitoring_date":     rand_date(2021, 2025).isoformat(),
            "credit_score":        score,
            "score_change":        change,
            "credit_risk_band":    ("Very High Risk" if score < 480 else
                                    "High Risk"      if score < 580 else
                                    "Medium Risk"    if score < 670 else
                                    "Low Risk"       if score < 750 else
                                    "Very Low Risk"),
            "accounts_open":       random.randint(1, 15),
            "accounts_in_arrears": random.randint(0, 8),
            "judgements_count":    random.randint(0, 4),
            "defaults_count":      random.randint(0, 5),
            "enquiries_count":     random.randint(0, 20),
            "total_credit_limit":  round(random.uniform(5000, 800000), 2),
            "total_utilisation_pct":round(random.uniform(0.10, 0.95), 4),
            "bureau":              random.choice(["TransUnion","Experian","Compuscan","XDS"]),
        })
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- #
# MAIN — generate & write
# --------------------------------------------------------------------------- #

def write_csv(df, name):
    path = f"{OUTPUT_PATH}{name}.csv"
    # Write via PySpark if on Databricks
    sdf = spark.createDataFrame(df)
    sdf.coalesce(1).write.mode("overwrite").option("header", True).csv(path)
    print(f"Written {len(df):,} rows → {path}")

if __name__ == "__main__" or True:
    print("Generating clients...")
    clients     = build_clients()
    print("Generating creditors...")
    creditors   = build_creditors()
    print("Generating counsellors...")
    counsellors = build_counsellors()
    print("Generating products...")
    products    = build_products()
    print("Generating leads...")
    leads       = build_leads(clients)
    print("Generating assessments...")
    assessments = build_assessments(clients, counsellors)
    print("Generating cases...")
    cases       = build_cases(clients, counsellors, products)
    print("Generating debt accounts...")
    debt_accts  = build_debt_accounts(clients, creditors)
    print("Generating repayment plans...")
    plans       = build_repayment_plans(cases, debt_accts, creditors)
    print("Generating payments...")
    payments    = build_payments(cases, debt_accts, creditors)
    print("Generating credit monitoring...")
    credit_mon  = build_credit_monitoring(clients)

    write_csv(clients,     "clients")
    write_csv(creditors,   "creditors")
    write_csv(counsellors, "counsellors")
    write_csv(products,    "financial_products")
    write_csv(leads,       "leads")
    write_csv(assessments, "assessments")
    write_csv(cases,       "debt_review_cases")
    write_csv(debt_accts,  "debt_accounts")
    write_csv(plans,       "repayment_plans")
    write_csv(payments,    "payments")
    write_csv(credit_mon,  "credit_monitoring")

    print("\nAll synthetic source files written successfully.")
    print(f"Total rows generated: {sum(len(d) for d in [clients,creditors,counsellors,products,leads,assessments,cases,debt_accts,plans,payments,credit_mon]):,}")
