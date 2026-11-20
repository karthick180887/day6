import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def load_clean_streampulse() -> pd.DataFrame:
    cust = pd.read_csv("data/customers_raw.csv")
    with open("data/usage_events.json", "r", encoding="utf-8") as f:
        usage = pd.DataFrame(json.load(f))
    cust["plan_tier"] = cust["plan_tier"].apply(lambda x: x.strip().lower() if isinstance(x, str) else x)
    cust["country"] = cust["country"].apply(lambda x: x.strip().upper() if isinstance(x, str) else x)
    cust = cust.drop_duplicates(subset=["customer_id"], keep="first")
    return cust.merge(usage, on="customer_id", how="left")


df = load_clean_streampulse()
print("Merged dataset shape:", df.shape)
print("Missing values before preprocessing:")
print(df.isna().sum()[df.isna().sum() > 0])
