"""Generate deterministic synthetic datasets for Day 6: StreamPulse Subscription Churn.

Run directly:
    python generate_data.py

Produces four files in the same directory:
  1. customers_raw.csv            - Main customer profile table (with realistic messy values)
  2. usage_events.json            - 30-day product usage & support metrics (JSON records)
  3. customers_corrupted_batch.csv - Intentionally broken batch to demo Data Validation
  4. incoming_batch_exercise.csv  - Fresh incoming batch for Exercise 1 (Ingestion & Validation)
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd


def generate_all_datasets(output_dir: Path | None = None, seed: int = 42) -> dict[str, Path]:
    """Create all Day 6 datasets deterministically and return their file paths."""
    out = Path(output_dir) if output_dir is not None else Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(seed)
    n_customers = 1000

    customer_ids = [f"CUST-{10001 + i}" for i in range(n_customers)]
    ages = rng.integers(18, 68, size=n_customers).astype(float)
    plan_tiers = rng.choice(["basic", "standard", "premium"], size=n_customers, p=[0.45, 0.35, 0.20])
    countries = rng.choice(["US", "IN", "UK", "CA", "DE"], size=n_customers, p=[0.35, 0.30, 0.15, 0.10, 0.10])
    payment_methods = rng.choice(
        ["credit_card", "upi", "debit_card", "bank_transfer"],
        size=n_customers,
        p=[0.40, 0.25, 0.20, 0.15],
    )
    auto_pay = rng.choice([0, 1], size=n_customers, p=[0.35, 0.65])
    tenure_months = rng.integers(1, 49, size=n_customers).astype(float)

    base_price_map = {"basic": 9.99, "standard": 15.99, "premium": 24.99}
    monthly_charges = np.array([base_price_map[p] for p in plan_tiers]) + rng.normal(0, 1.2, size=n_customers)
    monthly_charges = np.round(np.clip(monthly_charges, 6.99, 32.00), 2)

    # Usage & support metrics (stored separately in JSON to teach multi-source ingestion)
    login_days_30d = np.clip(
        rng.normal(loc=16, scale=7, size=n_customers) + (tenure_months * 0.08),
        0,
        30,
    ).round(0).astype(int)
    watch_hours_30d = np.round(np.clip(login_days_30d * rng.uniform(0.6, 2.4, size=n_customers), 0.0, 90.0), 1)
    support_tickets_30d = rng.poisson(lam=1.2, size=n_customers)

    # Realistic churn signal (~30% churn rate, ~0.84-0.88 ROC-AUC across models)
    churn_logit = (
        1.15
        - 0.055 * tenure_months
        - 0.14 * login_days_30d
        + 0.72 * support_tickets_30d
        - 0.90 * auto_pay
        + 0.06 * monthly_charges
        + np.where(plan_tiers == "basic", 0.45, np.where(plan_tiers == "premium", -0.35, 0.0))
        + rng.normal(0, 0.65, size=n_customers)
    )
    churn_prob = 1.0 / (1.0 + np.exp(-churn_logit))
    churned = (rng.random(n_customers) < churn_prob).astype(int)

    # Build raw customer table with realistic messiness (missing values, casing, duplicates, bad outliers)
    customers_df = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "age": ages,
            "plan_tier": plan_tiers.astype(object),
            "country": countries.astype(object),
            "payment_method": payment_methods.astype(object),
            "auto_pay": auto_pay,
            "tenure_months": tenure_months,
            "monthly_charges": monthly_charges,
            "churned": churned,
        }
    )

    # Inject small, realistic real-world data flaws for Ingestion & Validation lessons
    customers_df.loc[[5, 29, 104, 210, 355], "age"] = np.nan
    customers_df.loc[[12, 88, 199, 412], "monthly_charges"] = np.nan
    customers_df.loc[[17, 140, 305], "plan_tier"] = np.nan
    customers_df.loc[[3, 44, 150], "plan_tier"] = [" Basic ", "PREMIUM", " Standard"]
    customers_df.loc[[71, 280], "country"] = [" us ", "in"]
    # Add 3 exact duplicate rows to teach deduplication
    duplicates = customers_df.iloc[[10, 50, 120]].copy()
    customers_df = pd.concat([customers_df, duplicates], ignore_index=True)

    customers_raw_path = out / "customers_raw.csv"
    customers_df.to_csv(customers_raw_path, index=False)

    # Build JSON usage events (one record per customer, plus 2 extra orphan IDs to show join behavior)
    usage_records = [
        {
            "customer_id": cid,
            "login_days_30d": int(ld),
            "watch_hours_30d": float(wh),
            "support_tickets_30d": int(st),
            "last_active_device": str(dev),
        }
        for cid, ld, wh, st, dev in zip(
            customer_ids,
            login_days_30d,
            watch_hours_30d,
            support_tickets_30d,
            rng.choice(["mobile", "web", "smart_tv", "tablet"], size=n_customers, p=[0.45, 0.25, 0.20, 0.10]),
        )
    ]
    usage_records.append(
        {
            "customer_id": "CUST-99998",
            "login_days_30d": 4,
            "watch_hours_30d": 3.5,
            "support_tickets_30d": 0,
            "last_active_device": "web",
        }
    )
    usage_json_path = out / "usage_events.json"
    usage_json_path.write_text(json.dumps(usage_records, indent=2), encoding="utf-8")

    # Build intentionally corrupted batch to demonstrate Data Validation catching bad feeds
    corrupted_df = customers_df.head(40).copy()
    corrupted_df.loc[2, "age"] = -12.0                 # Impossible negative age
    corrupted_df.loc[7, "age"] = 185.0                 # Impossible high age
    corrupted_df.loc[11, "tenure_months"] = -5.0       # Negative tenure
    corrupted_df.loc[15, "monthly_charges"] = 999.99   # Out-of-bounds price
    corrupted_df.loc[20, "plan_tier"] = "ultra_vip"    # Unexpected category
    corrupted_df.loc[25, "churned"] = 2                # Invalid target label
    # Drop a required column in a copy? Keep columns intact here so multiple rules trigger,
    # and we test missing-column rejection in-code during the demo.
    corrupted_path = out / "customers_corrupted_batch.csv"
    corrupted_df.to_csv(corrupted_path, index=False)

    # Build fresh incoming batch for Exercise 1 (mix of cleanable noise + 4 invalid rows to quarantine)
    n_ex = 120
    ex_ids = [f"CUST-{20001 + i}" for i in range(n_ex)]
    ex_tiers = rng.choice(["basic", "standard", "premium"], size=n_ex, p=[0.4, 0.4, 0.2]).astype(object)
    ex_charges = np.round([base_price_map[t] + float(rng.normal(0, 1.0)) for t in ex_tiers], 2)
    ex_df = pd.DataFrame(
        {
            "customer_id": ex_ids,
            "age": rng.integers(19, 65, size=n_ex).astype(float),
            "plan_tier": ex_tiers,
            "country": rng.choice(["US", "IN", "UK", "CA", "DE"], size=n_ex),
            "payment_method": rng.choice(["credit_card", "upi", "debit_card", "bank_transfer"], size=n_ex),
            "auto_pay": rng.choice([0, 1], size=n_ex, p=[0.3, 0.7]),
            "tenure_months": rng.integers(1, 40, size=n_ex).astype(float),
            "monthly_charges": ex_charges,
            "login_days_30d": rng.integers(0, 31, size=n_ex),
            "watch_hours_30d": np.round(rng.uniform(0.5, 65.0, size=n_ex), 1),
            "support_tickets_30d": rng.poisson(1.1, size=n_ex),
            "churned": rng.choice([0, 1], size=n_ex, p=[0.68, 0.32]),
        }
    )
    # Messy but fixable strings + 2 duplicates
    ex_df.loc[[1, 14], "plan_tier"] = [" BASIC ", "Premium"]
    ex_df.loc[[4, 22], "country"] = ["uk", " in "]
    # 4 invalid rows that must be flagged/quarantined by the student's validator
    ex_df.loc[9, "age"] = 10.0                  # Under 18
    ex_df.loc[33, "tenure_months"] = -3.0       # Negative tenure
    ex_df.loc[57, "monthly_charges"] = -15.0    # Negative charge
    ex_df.loc[84, "plan_tier"] = "enterprise"   # Unknown plan tier
    ex_df = pd.concat([ex_df, ex_df.iloc[[0, 5]]], ignore_index=True)

    ex_path = out / "incoming_batch_exercise.csv"
    ex_df.to_csv(ex_path, index=False)

    return {
        "customers_raw": customers_raw_path,
        "usage_events": usage_json_path,
        "customers_corrupted": corrupted_path,
        "incoming_batch_exercise": ex_path,
    }


if __name__ == "__main__":
    paths = generate_all_datasets()
    for name, path in paths.items():
        print(f"Generated {name}: {path}")
