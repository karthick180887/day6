from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import pandas as pd
from pydantic import BaseModel, Field, ValidationError

RAW_CUSTOMERS_PATH = Path("data/customers_raw.csv")
RAW_USAGE_PATH = Path("data/usage_events.json")
CORRUPTED_PATH = Path("data/customers_corrupted_batch.csv")
==================================================================================
raw_customers = pd.read_csv(RAW_CUSTOMERS_PATH)
with open(RAW_USAGE_PATH, "r", encoding="utf-8") as f:
    raw_usage = pd.DataFrame(json.load(f))

print(f"Raw customers rows : {len(raw_customers)} (unique customer_id: {raw_customers['customer_id'].nunique()})")
print(f"Raw usage rows     : {len(raw_usage)} (unique customer_id: {raw_usage['customer_id'].nunique()})")
print("\nRaw plan_tier values (notice messy casing & spaces!):")
print(raw_customers["plan_tier"].value_counts(dropna=False))
print("\nRaw country values:")
print(raw_customers["country"].value_counts(dropna=False))
========================================================================================================
def compute_file_sha256(path: Path) -> str:
    """Return a short SHA-256 fingerprint for data lineage tracking."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:12]


def ingest_streampulse_data(customers_csv: Path, usage_json: Path) -> tuple[pd.DataFrame, dict]:
    """Load, standardize, deduplicate, and join StreamPulse customer + usage data."""
    cust_df = pd.read_csv(customers_csv)
    with open(usage_json, "r", encoding="utf-8") as f:
        usage_df = pd.DataFrame(json.load(f))

    raw_row_count = len(cust_df)

    # 1. Standardize column names (lowercase, stripped)
    cust_df.columns = [c.strip().lower() for c in cust_df.columns]
    usage_df.columns = [c.strip().lower() for c in usage_df.columns]

    # 2. Clean whitespace & casing on string categories (preserving NaN as NaN!)
    if "plan_tier" in cust_df.columns:
        cust_df["plan_tier"] = cust_df["plan_tier"].apply(
            lambda x: x.strip().lower() if isinstance(x, str) else x
        )
    if "country" in cust_df.columns:
        cust_df["country"] = cust_df["country"].apply(
            lambda x: x.strip().upper() if isinstance(x, str) else x
        )
    if "payment_method" in cust_df.columns:
        cust_df["payment_method"] = cust_df["payment_method"].apply(
            lambda x: x.strip().lower() if isinstance(x, str) else x
        )

    # 3. Deduplicate on primary key customer_id
    duplicates_removed = int(cust_df.duplicated(subset=["customer_id"]).sum())
    cust_df = cust_df.drop_duplicates(subset=["customer_id"], keep="first")

    # 4. Left join usage metrics onto customers (drop orphan usage IDs with no billing profile)
    merged_df = cust_df.merge(usage_df, on="customer_id", how="left", validate="one_to_one")

    metadata = {
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "customers_source": str(customers_csv),
        "customers_sha256": compute_file_sha256(customers_csv),
        "usage_source": str(usage_json),
        "usage_sha256": compute_file_sha256(usage_json),
        "raw_customer_rows": raw_row_count,
        "duplicates_removed": duplicates_removed,
        "final_rows": len(merged_df),
        "final_columns": list(merged_df.columns),
    }
    return merged_df, metadata


ingested_df, ingest_meta = ingest_streampulse_data(RAW_CUSTOMERS_PATH, RAW_USAGE_PATH)
print("Ingestion Metadata:")
print(json.dumps(ingest_meta, indent=2))
print("\nCleaned plan_tier values:")
print(ingested_df["plan_tier"].value_counts(dropna=False))
===========================================================================================================================
REQUIRED_COLUMNS = [
    "customer_id", "age", "plan_tier", "country", "payment_method",
    "auto_pay", "tenure_months", "monthly_charges", "churned",
]
ALLOWED_PLANS = {"basic", "standard", "premium"}
ALLOWED_COUNTRIES = {"US", "IN", "UK", "CA", "DE"}


def validate_customer_dataframe(df: pd.DataFrame, max_missing_ratio: float = 0.15) -> dict:
    """Run schema and data-quality checks. Returns a structured validation report."""
    errors = []
    warnings = []

    # Check 1: Required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return {"passed": False, "row_count": len(df), "errors": errors, "warnings": warnings}

    # Check 2: Primary key uniqueness & non-null
    null_ids = int(df["customer_id"].isna().sum())
    dup_ids = int(df["customer_id"].duplicated().sum())
    if null_ids > 0:
        errors.append(f"Found {null_ids} null customer_id values.")
    if dup_ids > 0:
        errors.append(f"Found {dup_ids} duplicate customer_id values.")

    # Check 3: Missingness threshold per column
    for col in REQUIRED_COLUMNS:
        ratio = float(df[col].isna().mean())
        if ratio > max_missing_ratio:
            errors.append(f"Column '{col}' missing ratio {ratio:.1%} exceeds limit {max_missing_ratio:.1%}.")
        elif ratio > 0:
            warnings.append(f"Column '{col}' has {ratio:.1%} missing values (will be imputed in pipeline).")

    # Check 4: Numeric range checks (ignoring NaNs which are checked above)
    bad_age = df["age"].dropna().pipe(lambda s: ~s.between(18, 100)).sum()
    if bad_age > 0:
        errors.append(f"Found {int(bad_age)} rows with age outside [18, 100].")

    bad_tenure = (df["tenure_months"].dropna() < 0).sum()
    if bad_tenure > 0:
        errors.append(f"Found {int(bad_tenure)} rows with negative tenure_months.")

    bad_charges = df["monthly_charges"].dropna().pipe(lambda s: ~s.between(0, 100)).sum()
    if bad_charges > 0:
        errors.append(f"Found {int(bad_charges)} rows with monthly_charges outside [0, 100].")

    # Check 5: Allowed categorical values
    bad_plans = set(df["plan_tier"].dropna().unique()) - ALLOWED_PLANS
    if bad_plans:
        errors.append(f"Unexpected plan_tier values: {sorted(bad_plans)}")

    bad_countries = set(df["country"].dropna().unique()) - ALLOWED_COUNTRIES
    if bad_countries:
        errors.append(f"Unexpected country values: {sorted(bad_countries)}")

    # Check 6: Target label integrity
    bad_targets = set(df["churned"].dropna().unique()) - {0, 1}
    if bad_targets:
        errors.append(f"Invalid churned target values: {sorted(bad_targets)}")

    return {
        "passed": len(errors) == 0,
        "row_count": int(len(df)),
        "error_count": len(errors),
        "errors": errors,
        "warnings": warnings,
    }


clean_report = validate_customer_dataframe(ingested_df)
print("=== Validation Report: Clean Ingested Dataset ===")
print(json.dumps(clean_report, indent=2))
assert clean_report["passed"] is True

