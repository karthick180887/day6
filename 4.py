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
