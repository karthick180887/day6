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
