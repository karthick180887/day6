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
======================================================================================================================
PROJECT_ROOT = Path("artifacts/streampulse_project_demo")

# Define a clean, industry-standard ML project folder structure
FOLDERS = [
    "configs",          # YAML configs (hyperparameters, paths, validation rules)
    "data/raw",         # Immutable raw snapshots (NEVER overwrite!)
    "data/processed",   # Validated & cleaned tables ready for modeling
    "notebooks",        # Short EDA / presentation notebooks only
    "src/ingestion",    # Data loading & multi-source merging
    "src/validation",   # Schema & data quality checks
    "src/features",     # Feature engineering & transformers
    "src/training",     # Training, cross-validation, evaluation
    "src/inference",    # Loading saved pipeline & predicting on new data
    "artifacts/models", # Serialized pipelines (.joblib) + model cards (.json)
    "artifacts/reports",# Validation reports, metrics, confusion matrices
    "tests",            # Automated pytest unit tests for data & pipeline
]

for rel in FOLDERS:
    (PROJECT_ROOT / rel).mkdir(parents=True, exist_ok=True)

# Write small placeholder __init__.py files so src is a valid Python package
for pkg in ["src", "src/ingestion", "src/validation", "src/features", "src/training", "src/inference"]:
    (PROJECT_ROOT / pkg / "__init__.py").write_text('"""StreamPulse ML package."""\n', encoding="utf-8")

def print_tree(root: Path, prefix: str = ""):
    entries = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name))
    for idx, entry in enumerate(entries):
        connector = "└── " if idx == len(entries) - 1 else "├── "
        print(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if idx == len(entries) - 1 else "│   "
            print_tree(entry, prefix + extension)

print(f"Scaffolded ML project at: {PROJECT_ROOT}\n")
print_tree(PROJECT_ROOT)

