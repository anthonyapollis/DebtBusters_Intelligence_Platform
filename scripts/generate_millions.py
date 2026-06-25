"""
DebtBusters Intelligence Platform — Scale-Up Data Generator
Produces 4,000,000+ rows of synthetic SA debt-counselling data
Run locally: python generate_millions.py
Output: ../data/*.parquet (or .csv if parquet unavailable)
"""

import random
import uuid
import math
import os
import sys
from datetime import date, timedelta
import pandas as pd
import numpy as np

# ── seed ──────────────────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT_DIR, exist_ok=True)

USE_PARQUET = True
try:
    import pyarrow
except ImportError:
    USE_PARQUET = False
    print("pyarrow not found — writing CSV instead")

# ── scale ─────────────────────────────────────────────────────────────────────
N_CLIENTS       =  80_000
N_LEADS         = 500_000
N_ASSESSMENTS   = 120_000
N_CASES         =  60_000
N_DEBT_ACCOUNTS = 700_000
N_PLANS         = 400_000
N_PAYMENTS    = 1_500_000
N_CREDIT        = 600_000

# ── reference data ────────────────────────────────────────────────────────────
SA_PROVINCES      = ["Gauteng","Western Cape","KwaZulu-Natal","Eastern Cape",
                     "Limpopo","Mpumalanga","North West","Free State","Northern Cape"]
PROV_W            = [0.30,0.17,0.18,0.10,0.07,0.06,0.05,0.05,0.02]

CHANNELS          = ["Google Ads","Facebook","SEO Organic","Call Centre",
                     "Referral","Partner","JustMoney Portal","Email Campaign",
                     "Sanlam Referral","Fincheck Referral"]
CHAN_W            = [0.26,0.17,0.13,0.11,0.07,0.06,0.07,0.05,0.05,0.03]

EMPLOYMENT        = ["Employed","Self-Employed","Contract","Unemployed","Pensioner"]
EMP_W             = [0.58,0.14,0.12,0.10,0.06]

CREDITORS         = [
    "ABSA Bank","Standard Bank","FNB","Nedbank","Capitec","African Bank","Bayport",
    "RCS","Edgars Credit","Woolworths Financial","MFC Vehicle Finance","WesBank",
    "SA Home Loans","ooba","DirectAxis","Wonga","Lime24","TymeBank","Discovery Bank",
    "Old Mutual Finance","Sanlam Personal Loans","Izwe Loans","Boodle",
]

ACCOUNT_TYPES     = ["Home Loan","Vehicle Finance","Personal Loan","Credit Card",
                     "Store Card","Overdraft","Micro Loan","Student Loan"]
ACCT_W            = [0.15,0.20,0.25,0.15,0.10,0.08,0.05,0.02]

PRODUCTS          = [
    ("DC001","Debt Counselling",   "Debt Management"),
    ("DC002","Debt Consolidation", "Debt Management"),
    ("DC003","Debt Settlement",    "Debt Management"),
    ("CM001","Credit Monitoring",  "Credit Services"),
    ("CR001","Credit Repair",      "Credit Services"),
    ("IR001","Insurance Review",   "Financial Planning"),
    ("FP001","Financial Planning", "Financial Planning"),
]

CASE_STAGES       = ["Lead","Assessment","Application","Review",
                     "Court Order","Active","Completed","Withdrawn"]
STAGE_W           = [0.02,0.04,0.06,0.08,0.10,0.45,0.20,0.05]

BUREAUS           = ["TransUnion","Experian","Compuscan","XDS"]
SA_CITIES         = ["Johannesburg","Cape Town","Durban","Pretoria","Port Elizabeth",
                     "Bloemfontein","Polokwane","Nelspruit","Kimberley","Rustenburg",
                     "Pietermaritzburg","East London","Soweto","Benoni","Tembisa"]

# ── helpers ───────────────────────────────────────────────────────────────────
def rand_date(y0=2019, y1=2025):
    s = date(y0,1,1); e = date(y1,12,31)
    return s + timedelta(days=random.randint(0,(e-s).days))

def rand_income():
    return round(np.random.lognormal(math.log(18_000), 0.6), 2)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def write(df: pd.DataFrame, name: str):
    if USE_PARQUET:
        p = os.path.join(OUT_DIR, f"{name}.parquet")
        df.to_parquet(p, index=False)
    else:
        p = os.path.join(OUT_DIR, f"{name}.csv")
        df.to_csv(p, index=False)
    print(f"  {name:30s}: {len(df):>10,} rows  ->  {os.path.basename(p)}")

# ── generators ────────────────────────────────────────────────────────────────

def gen_clients():
    rng_c = np.random.default_rng(SEED+99)
    ages  = rng_c.integers(18, 70, N_CLIENTS)
    rows  = []
    for i in range(N_CLIENTS):
        gross = rand_income()
        age   = int(ages[i])
        emp   = random.choices(EMPLOYMENT, EMP_W)[0]
        # risk_score: 0 = low risk (stable client), 1 = high risk (likely default/churn)
        # driven by income (lower = riskier), employment (unemployed = riskier), age
        income_risk = max(0, 1 - gross / 50000)           # 0 at R50k+, 1 at R0
        emp_risk    = {"Employed":0.1,"Self-Employed":0.3,"Contract":0.35,
                       "Unemployed":0.85,"Pensioner":0.45}[emp]
        age_risk    = 0.05 if 35 <= age <= 55 else 0.25   # peak earners = lower risk
        risk_score  = float(np.clip(income_risk*0.50 + emp_risk*0.35 + age_risk*0.15 +
                                    rng_c.uniform(-0.10, 0.10), 0.01, 0.99))
        rows.append({
            "client_id":         str(uuid.uuid4()),
            "age":               age,
            "age_band":          ("18-25" if age<26 else "26-35" if age<36
                                  else "36-45" if age<46 else "46-55" if age<56 else "56+"),
            "gender":            random.choice(["Male","Female"]),
            "province":          random.choices(SA_PROVINCES, PROV_W)[0],
            "city":              random.choice(SA_CITIES),
            "employment_status": emp,
            "gross_income":      gross,
            "income_band":       ("< R5k"       if gross<5000
                                  else "R5k-R10k"  if gross<10000
                                  else "R10k-R20k" if gross<20000
                                  else "R20k-R40k" if gross<40000 else "R40k+"),
            "consent_status":    random.choices(["Granted","Withdrawn"],[0.95,0.05])[0],
            "created_date":      rand_date(2019,2025).isoformat(),
            "source_system":     random.choice(["CRM","Portal","CallCentre","JustMoney"]),
            "partner_brand":     random.choices(["DebtBusters","JustMoney","Confluent","Direct"],
                                                [0.45,0.30,0.15,0.10])[0],
            "risk_score":        round(risk_score, 4),   # causal signal injected here
        })
    return pd.DataFrame(rows)


def gen_creditors():
    rows = []
    for name in CREDITORS:
        rows.append({
            "creditor_id":   str(uuid.uuid4()),
            "creditor_name": name,
            "creditor_type": ("Bank" if any(b in name for b in ["Bank","ABSA","Nedbank","FNB","Standard","Tyme","Discovery"])
                              else "Retailer" if any(r in name for r in ["Edgars","Woolworths","RCS"])
                              else "Vehicle Finance" if any(v in name for v in ["Finance","WesBank","MFC"])
                              else "Micro Lender" if any(m in name for m in ["Wonga","Lime24","Bayport","Boodle","Izwe"])
                              else "Insurance" if any(i in name for i in ["Old Mutual","Sanlam"])
                              else "Home Loan"),
            "ncr_registered": True,
        })
    return pd.DataFrame(rows)


def gen_counsellors():
    teams   = ["Johannesburg A","Johannesburg B","Cape Town","Durban",
               "Pretoria","Online Team A","Online Team B","Digital Team"]
    names_m = ["James","Michael","David","Robert","John","William","Richard","Thomas"]
    names_f = ["Sarah","Lisa","Karen","Michelle","Amanda","Jennifer","Angela","Nomsa"]
    rows = []
    for _ in range(120):
        fname = random.choice(names_f + names_m)
        rows.append({
            "counsellor_id":   str(uuid.uuid4()),
            "counsellor_name": f"{fname} {random.choice(['van der Merwe','Nkosi','Botha','Dlamini','Smith','Johnson','Williams','Brown'])}",
            "team":            random.choice(teams),
            "branch":          random.choice(["Sandton","Rosebank","Century City","Umhlanga","Menlyn","Remote"]),
            "ncr_number":      f"DC{random.randint(1000,9999)}",
            "active_flag":     random.choices([True,False],[0.90,0.10])[0],
            "hire_date":       rand_date(2014,2023).isoformat(),
        })
    return pd.DataFrame(rows)


def gen_products():
    rows = []
    for code, name, cat in PRODUCTS:
        rows.append({
            "product_id":       str(uuid.uuid4()),
            "product_code":     code,
            "product_name":     name,
            "product_category": cat,
            "fee_type":         "Monthly" if "Counselling" in name or "Monitoring" in name else "Once-Off",
            "active_flag":      True,
        })
    return pd.DataFrame(rows)


def gen_leads(client_ids):
    # Vectorised for speed
    n = N_LEADS
    rng = np.random.default_rng(SEED)

    start = date(2019,1,1).toordinal()
    end   = date(2025,12,31).toordinal()
    dates = [date.fromordinal(int(d)).isoformat()
             for d in rng.integers(start, end+1, n)]

    channels = rng.choice(CHANNELS, n, p=[w/sum(CHAN_W) for w in CHAN_W])
    cids     = rng.choice(client_ids, n)
    scores   = rng.integers(1, 101, n)
    costs    = rng.uniform(35, 280, n).round(2)

    # Channel conversion lift (high-intent channels convert better)
    ch_lift = {"Referral":0.12,"JustMoney Portal":0.10,"Partner":0.08,"Sanlam Referral":0.07,
               "Fincheck Referral":0.06,"SEO Organic":0.02,"Call Centre":0.01,
               "Google Ads":-0.02,"Facebook":-0.04,"Email Campaign":-0.01}
    ch_arr  = np.array([ch_lift.get(c, 0) for c in channels])

    # Conversion probability driven by lead_score + channel (causal signal)
    qual_prob  = np.clip(0.35 + scores/100 * 0.50 + ch_arr * 0.5, 0.10, 0.92)
    assess_prob= np.clip(0.25 + scores/100 * 0.55 + ch_arr * 0.4, 0.08, 0.88)
    conv_prob  = np.clip(0.10 + scores/100 * 0.50 + ch_arr * 0.6, 0.04, 0.80)

    qualified  = rng.random(n) < qual_prob
    assessed   = qualified & (rng.random(n) < assess_prob)
    converted  = assessed  & (rng.random(n) < conv_prob)

    statuses = np.where(converted, "Converted",
               np.where(assessed,  "Assessed",
               np.where(qualified, "Qualified","Unqualified")))

    return pd.DataFrame({
        "lead_id":        [str(uuid.uuid4()) for _ in range(n)],
        "client_id":      cids,
        "lead_date":      dates,
        "source_channel": channels,
        "campaign":       [f"CAM-{random.randint(1000,9999)}" for _ in range(n)],
        "utm_source":     rng.choice(["google","facebook","email","organic","partner","justmoney"],n),
        "utm_medium":     rng.choice(["cpc","social","email","referral","organic"],n),
        "lead_score":     scores,
        "lead_status":    statuses,
        "cost_per_lead":  costs,
        "qualified_flag": qualified,
        "assessed_flag":  assessed,
        "converted_flag": converted,
    })


def gen_assessments(client_ids, counsellor_ids):
    n    = N_ASSESSMENTS
    rng  = np.random.default_rng(SEED+1)
    gross = np.exp(rng.normal(math.log(18000), 0.6, n)).round(2)
    tax   = np.where(gross < 18000, 0.18, np.where(gross < 35000, 0.26, 0.31))
    net   = (gross * (1 - tax)).round(2)
    living= (gross * rng.uniform(0.25, 0.45, n)).round(2)
    inst  = (gross * rng.uniform(0.30, 0.75, n)).round(2)
    disp  = (net - living - inst).round(2)
    debt  = (inst * rng.uniform(18, 60, n)).round(2)
    dti   = np.where(net > 0, (inst / net).round(4), 0)

    start = date(2019,1,1).toordinal()
    end   = date(2025,12,31).toordinal()
    dates = [date.fromordinal(int(d)).isoformat()
             for d in rng.integers(start, end+1, n)]

    prods = ["Debt Counselling","Debt Consolidation","Debt Settlement",
             "Credit Repair","Credit Monitoring","Insurance Review"]
    pw    = [0.40,0.22,0.12,0.12,0.09,0.05]

    return pd.DataFrame({
        "assessment_id":                 [str(uuid.uuid4()) for _ in range(n)],
        "client_id":                     rng.choice(client_ids, n),
        "counsellor_id":                 rng.choice(counsellor_ids, n),
        "assessment_date":               dates,
        "gross_income":                  gross,
        "net_income":                    net,
        "living_expenses":               living,
        "total_debt_balance":            debt,
        "total_monthly_debt_instalment": inst,
        "disposable_income":             disp,
        "debt_to_income_ratio":          dti,
        "dti_band":                      np.where(dti<0.40,"< 40%",
                                          np.where(dti<0.60,"40-60%",
                                          np.where(dti<0.80,"60-80%","> 80%"))),
        "affordability_amount":          np.maximum(0, disp).round(2),
        "over_indebted_flag":            (disp < 0) | (dti > 0.70),
        # DTI-driven product recommendation with 15% noise (realistic ~85% signal)
        "recommended_product":           np.where(
            rng.random(n) < 0.85,
            np.where(dti > 0.70, "DebtBusters Debt Review",
             np.where(dti > 0.50, "Debt Consolidation Loan",
             np.where(dti > 0.35, "Budget & Affordability Plan",
             np.where(dti > 0.20, "Credit Health Monitoring",
             "Credit Builder Programme")))),
            rng.choice(prods, n, p=pw)  # 15% random override
        ),
        "number_of_creditors":           rng.integers(1, 13, n),
    })


def gen_cases(client_ids, counsellor_ids, product_ids, client_risk=None):
    n   = N_CASES
    rng = np.random.default_rng(SEED+2)
    # Index into clients so risk matches the actual client assigned to the case
    cid_indices = rng.integers(0, len(client_ids), n)
    matched_risk = (np.array(client_risk)[cid_indices]
                    if client_risk is not None
                    else np.full(n, 0.30))
    # Wider range: Withdrawn prob = 2-70% based on risk (strong signal for churn model)
    w_withdrawn = np.clip(0.02 + matched_risk * 0.68, 0.02, 0.70)
    w_completed = np.clip(0.35 - matched_risk * 0.30, 0.05, 0.35)
    # Remaining weight spread over non-terminal stages proportionally
    stage_weights_base = np.array([0.02,0.04,0.06,0.08,0.10,0.45,0.20,0.05])
    stage_idx = np.zeros(n, dtype=int)
    for i in range(n):
        w = stage_weights_base.copy()
        w[7] = w_withdrawn[i]
        w[6] = w_completed[i]
        w = np.clip(w, 0.001, 1); w /= w.sum()
        stage_idx[i] = rng.choice(range(len(CASE_STAGES)), p=w)
    stages    = np.array(CASE_STAGES)[stage_idx]

    start = date(2019,1,1).toordinal()
    end   = date(2024,12,31).toordinal()
    app_ord = rng.integers(start, end+1, n)
    app_dates = [date.fromordinal(int(d)).isoformat() for d in app_ord]

    def offset_date(ord_arr, lo, hi):
        return [date.fromordinal(int(o + random.randint(lo,hi))).isoformat()
                for o in ord_arr]

    acc_dates  = [offset_date([app_ord[i]],5,30)[0]  if stage_idx[i]>=2 else None for i in range(n)]
    court_dates= [offset_date([app_ord[i]],31,120)[0] if stage_idx[i]>=4 else None for i in range(n)]
    comp_dates = [offset_date([app_ord[i]],365,1460)[0] if stages[i]=="Completed" else None for i in range(n)]

    legal_s   = rng.choice(["Not Filed","Filed","Court Date Set","Order Granted","Order Declined"],
                            n, p=[0.10,0.20,0.20,0.40,0.10])
    ncr_s     = rng.choice(["Pending","Registered","Active","Completed","Withdrawn"],
                            n, p=[0.05,0.15,0.55,0.15,0.10])
    court_s   = rng.choice(["Pending","Granted","Declined","Not Required"],
                            n, p=[0.10,0.55,0.10,0.25])

    return pd.DataFrame({
        "case_id":              [str(uuid.uuid4()) for _ in range(n)],
        "client_id":            np.array(client_ids)[cid_indices],
        "counsellor_id":        rng.choice(counsellor_ids, n),
        "product_id":           rng.choice(product_ids, n),
        "application_date":     app_dates,
        "acceptance_date":      acc_dates,
        "court_order_date":     court_dates,
        "completion_date":      comp_dates,
        "case_stage":           stages,
        "legal_status":         legal_s,
        "ncr_status":           ncr_s,
        "court_order_status":   court_s,
        "case_open_flag":       np.isin(stages, ["Application","Review","Court Order","Active"]),
        "days_in_stage":        rng.integers(1, 731, n),
        "clearance_issued_flag":((stages=="Completed") & (rng.random(n)<0.92)),
    })


def gen_debt_accounts(client_ids, creditor_ids):
    n   = N_DEBT_ACCOUNTS
    rng = np.random.default_rng(SEED+3)

    acc_types = rng.choice(ACCOUNT_TYPES, n, p=[w/sum(ACCT_W) for w in ACCT_W])
    balances  = np.exp(rng.normal(math.log(45000), 0.8, n))
    balances  = np.clip(balances, 500, 2_500_000).round(2)
    rates     = rng.uniform(0.08, 0.285, n).round(4)
    terms     = rng.integers(6, 301, n)
    r_m       = rates/12
    inst      = np.where(terms > 0,
                         (balances * r_m) / (1 - (1 + r_m)**(-terms)),
                         balances / 12).round(2)

    statuses  = rng.choice(
        ["Current","In Arrears","Restructured","Settled","Written Off"],
        n, p=[0.38,0.25,0.22,0.12,0.03]
    )
    start = date(2015,1,1).toordinal()
    end   = date(2024,12,31).toordinal()
    dates = [date.fromordinal(int(d)).isoformat()
             for d in rng.integers(start, end+1, n)]

    arrears = np.where(statuses=="In Arrears",
                       (inst * rng.uniform(0,3,n)).round(2), 0.0)
    missed  = np.where(statuses=="In Arrears", rng.integers(1,13,n), 0)

    return pd.DataFrame({
        "account_id":                   [str(uuid.uuid4()) for _ in range(n)],
        "client_id":                    rng.choice(client_ids, n),
        "creditor_id":                  rng.choice(creditor_ids, n),
        "account_type":                 acc_types,
        "original_balance":             (balances * rng.uniform(0.8,1.5,n)).round(2),
        "current_balance":              balances,
        "interest_rate":                rates,
        "interest_rate_pct":            (rates*100).round(2),
        "current_monthly_instalment":   inst,
        "term_months":                  terms,
        "account_status":               statuses,
        "open_date":                    dates,
        "arrears_amount":               arrears,
        "missed_payments_count":        missed,
    })


def gen_repayment_plans(case_ids, creditor_ids):
    n    = N_PLANS
    rng  = np.random.default_rng(SEED+4)
    orig = rng.uniform(500, 8000, n).round(2)
    red  = rng.uniform(0.10, 0.50, n)
    prop = (orig * (1 - red)).round(2)
    acc  = rng.random(n) < 0.82
    acc_amt = np.where(acc, prop, np.nan)
    r_bef   = rng.uniform(0.10, 0.285, n).round(4)
    r_aft   = np.where(acc, (r_bef * rng.uniform(0.40,0.80,n)).round(4), np.nan)
    t_bef   = rng.integers(6, 121, n)
    t_aft   = np.where(acc, t_bef + rng.integers(0,181,n), np.nan)
    saving  = np.where(acc, (orig - prop).round(2), 0.0)
    tot_sav = np.where(acc, (saving * np.where(np.isnan(t_aft), 0, t_aft)).round(2), 0.0)

    start = date(2019,1,1).toordinal()
    end   = date(2025,12,31).toordinal()
    dates = [date.fromordinal(int(d)).isoformat()
             for d in rng.integers(start, end+1, n)]

    cr_acc = np.where(acc, "Accepted",
             rng.choice(["Rejected","Counter-Proposed","Pending"], n))

    return pd.DataFrame({
        "plan_id":                  [str(uuid.uuid4()) for _ in range(n)],
        "case_id":                  rng.choice(case_ids, n),
        "creditor_id":              rng.choice(creditor_ids, n),
        "plan_date":                dates,
        "original_instalment":      orig,
        "proposed_instalment":      prop,
        "accepted_instalment":      acc_amt,
        "accepted_flag":            acc,
        "interest_rate_before":     r_bef,
        "interest_rate_after":      r_aft,
        "term_months_before":       t_bef,
        "term_months_after":        t_aft.astype(float),
        "monthly_saving":           saving,
        "total_saving_estimated":   tot_sav,
        "reduction_pct":            (red*100).round(2),
        "creditor_acceptance_status": cr_acc,
    })


def gen_payments(case_ids, creditor_ids, client_ids, client_risk=None):
    n    = N_PAYMENTS
    rng  = np.random.default_rng(SEED+5)
    exp  = rng.uniform(300, 6500, n).round(2)
    # Index into clients so risk matches the actual client on each payment
    cid_indices  = rng.integers(0, len(client_ids), n)
    matched_risk = (np.array(client_risk)[cid_indices]
                    if client_risk is not None
                    else np.full(n, 0.12))
    miss_prob = np.clip(0.02 + matched_risk * 0.35, 0.01, 0.60)
    miss = rng.random(n) < miss_prob
    act  = np.where(miss, 0.0, (exp * rng.uniform(0.90,1.05,n)).round(2))
    arr  = np.where(act<exp, (exp-act).round(2), 0.0)
    dist = np.where(~miss, (act * rng.uniform(0.92,1.0,n)).round(2), 0.0)

    start = date(2019,1,1).toordinal()
    end   = date(2025,12,31).toordinal()
    day_ords = rng.integers(start, end+1, n)
    dates    = [date.fromordinal(int(d)) for d in day_ords]
    date_str = [d.isoformat() for d in dates]
    months   = [d.strftime("%Y-%m") for d in dates]
    years    = [d.year for d in dates]

    status = np.where(miss, "Missed",
             np.where(act < exp*0.99, "Partial", "Full"))

    return pd.DataFrame({
        "payment_id":               [str(uuid.uuid4()) for _ in range(n)],
        "case_id":                  rng.choice(case_ids, n),
        "client_id":                np.array(client_ids)[cid_indices],
        "creditor_id":              rng.choice(creditor_ids, n),
        "payment_date":             date_str,
        "payment_month":            months,
        "payment_year":             years,
        "expected_payment_amount":  exp,
        "actual_payment_amount":    act,
        "distribution_amount":      dist,
        "arrears_amount":           arr,
        "collection_rate":          np.where(exp>0, (act/exp).round(4), 0),
        "payment_status":           status,
        "missed_payment_flag":      miss,
        "pda_reference":            [f"PDA-{random.randint(1000000,9999999)}" for _ in range(n)],
    })


def gen_credit_monitoring(client_ids):
    n    = N_CREDIT
    rng  = np.random.default_rng(SEED+6)

    # Assign clients and build per-client monitoring sequences
    assigned_clients = rng.choice(client_ids, n)
    client_seq_counter: dict = {}
    seq_nums = np.zeros(n, dtype=int)
    for i, c in enumerate(assigned_clients):
        client_seq_counter[c] = client_seq_counter.get(c, 0) + 1
        seq_nums[i] = client_seq_counter[c]

    # Monthly score change: +3 pts/month trend + noise (debt review improvement)
    changes = np.clip(rng.normal(3.0, 12.0, n), -60, 80).round(0).astype(int)

    # Evolving credit score: start around 520 (high risk), improve over time
    # score[i] = initial_score + cumulative monthly changes up to seq[i]
    # Approximation without full cumsum per client: use seq * avg_change + noise
    initial_score = 520
    scores = np.clip(
        initial_score + seq_nums * 3.0 + rng.normal(0, 30, n),
        300, 850
    ).round(0).astype(int)

    start = date(2019,1,1).toordinal()
    end   = date(2025,12,31).toordinal()
    dates = [date.fromordinal(int(d)).isoformat()
             for d in rng.integers(start, end+1, n)]

    bands = np.where(scores<480, "Very High Risk",
            np.where(scores<580, "High Risk",
            np.where(scores<670, "Medium Risk",
            np.where(scores<750, "Low Risk","Very Low Risk"))))

    return pd.DataFrame({
        "monitoring_id":        [str(uuid.uuid4()) for _ in range(n)],
        "client_id":            assigned_clients,
        "monitoring_date":      dates,
        "monitoring_seq":       seq_nums,       # months in debt review (causal signal)
        "credit_score":         scores,
        "score_change":         changes,
        "credit_risk_band":     bands,
        "accounts_open":        rng.integers(1, 16, n),
        "accounts_in_arrears":  rng.integers(0, 9, n),
        "judgements_count":     rng.integers(0, 5, n),
        "defaults_count":       rng.integers(0, 6, n),
        "enquiries_count":      rng.integers(0, 21, n),
        "total_credit_limit":   rng.uniform(5000, 800000, n).round(2),
        "total_utilisation_pct":rng.uniform(0.10, 0.95, n).round(4),
        "bureau":               rng.choice(BUREAUS, n),
    })


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  DebtBusters Intelligence Platform — Data Generator")
    print(f"  Target: ~{N_CLIENTS+N_LEADS+N_ASSESSMENTS+N_CASES+N_DEBT_ACCOUNTS+N_PLANS+N_PAYMENTS+N_CREDIT:,} rows")
    print("=" * 60)

    print("\nGenerating dimension tables…")
    clients     = gen_clients();      write(clients,    "clients")
    creditors   = gen_creditors();    write(creditors,  "creditors")
    counsellors = gen_counsellors();  write(counsellors,"counsellors")
    products    = gen_products();     write(products,   "financial_products")

    client_ids     = clients["client_id"].values
    client_risk    = clients["risk_score"].values   # causal signal
    creditor_ids   = creditors["creditor_id"].values
    counsellor_ids = counsellors["counsellor_id"].values
    product_ids    = products["product_id"].values

    print("\nGenerating fact tables…")
    leads    = gen_leads(client_ids);                                      write(leads,    "leads")
    assess   = gen_assessments(client_ids, counsellor_ids);               write(assess,   "assessments")
    cases    = gen_cases(client_ids, counsellor_ids, product_ids, client_risk); write(cases,"debt_review_cases")
    accts    = gen_debt_accounts(client_ids, creditor_ids);                write(accts,   "debt_accounts")
    plans    = gen_repayment_plans(cases["case_id"].values, creditor_ids); write(plans,   "repayment_plans")
    pays     = gen_payments(cases["case_id"].values, creditor_ids, client_ids, client_risk); write(pays, "payments")
    credit   = gen_credit_monitoring(client_ids);                          write(credit,  "credit_monitoring")

    total = sum([len(clients),len(creditors),len(counsellors),len(products),
                 len(leads),len(assess),len(cases),len(accts),len(plans),len(pays),len(credit)])
    print(f"\n{'='*60}")
    print(f"  COMPLETE: {total:,} total rows written to {OUT_DIR}")
    print(f"{'='*60}")
