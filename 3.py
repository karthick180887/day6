from pathlib import Path
import json
import pandas as pd

# First, let's peek at our StreamPulse business dataset
customers = pd.read_csv("data/customers_raw.csv")
print(f"Customers raw table shape: {customers.shape}")
print("Columns:", list(customers.columns))
print("\nTarget distribution (churned):")
print(customers["churned"].value_counts(dropna=False).rename({0: "Retained (0)", 1: "Churned (1)"}))
customers.head(5)
