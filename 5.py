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
====================================================================================================================================
# Small synthetic illustration of leakage when test distribution has higher values
rng = np.random.default_rng(42)
X_demo = np.concatenate([rng.normal(10, 2, size=80), rng.normal(25, 2, size=20)]).reshape(-1, 1)

# WRONG: fit scaler on ALL data before splitting
leaky_scaler = StandardScaler().fit(X_demo)

# RIGHT: split FIRST, then fit scaler ONLY on training fold
X_tr, X_te = X_demo[:80], X_demo[80:]
clean_scaler = StandardScaler().fit(X_tr)

print(f"Leaky scaler mean (peeked at test!): {leaky_scaler.mean_[0]:.2f}")
print(f"Clean scaler mean (train only)     : {clean_scaler.mean_[0]:.2f}")
print("\nRule: ALWAYS split train/test FIRST. Call .fit() ONLY on X_train, and .transform() on X_test!")
====================================================================================================================================
def add_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create stateless, row-level domain features for StreamPulse churn prediction."""
    out = df.copy()
    # Add +1 in denominators to prevent division-by-zero when login_days_30d == 0
    out["charges_per_login"] = out["monthly_charges"] / (out["login_days_30d"] + 1.0)
    out["tickets_per_tenure_month"] = out["support_tickets_30d"] / (out["tenure_months"] + 1.0)
    out["watch_hours_per_login"] = out["watch_hours_30d"] / (out["login_days_30d"] + 1.0)
    out["is_new_customer"] = (out["tenure_months"] <= 3).astype(int)
    return out


df_fe = add_domain_features(df)

# Quick sanity check: compare average engineered features for Churned vs Retained customers!
check_cols = ["charges_per_login", "tickets_per_tenure_month", "watch_hours_per_login", "is_new_customer"]
print("Mean engineered features grouped by churned (0 = Retained, 1 = Churned):")
df_fe.groupby("churned")[check_cols].mean().round(3)
==========================================================================================================================================
NUMERIC_FEATURES = [
    "age", "tenure_months", "monthly_charges",
    "login_days_30d", "watch_hours_30d", "support_tickets_30d",
    "auto_pay", "charges_per_login", "tickets_per_tenure_month",
    "watch_hours_per_login", "is_new_customer",
]
CATEGORICAL_FEATURES = ["plan_tier", "country", "payment_method", "last_active_device"]

X = df_fe[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
y = df_fe["churned"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

numeric_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ]
)

categorical_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("num", numeric_transformer, NUMERIC_FEATURES),
        ("cat", categorical_transformer, CATEGORICAL_FEATURES),
    ]
)

# Fit ONLY on X_train, then transform both train and test
X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed = preprocessor.transform(X_test)

feature_names = preprocessor.get_feature_names_out()
print(f"Original columns    : {X_train.shape[1]}")
print(f"Transformed features: {X_train_processed.shape[1]}")
print(f"Any NaNs remaining? : train={np.isnan(X_train_processed).any()}, test={np.isnan(X_test_processed).any()}")
print("\nSample transformed feature names:", list(feature_names[:10]))



