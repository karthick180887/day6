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
======================================================================================================
## Part 2: Mapping Every ML Lifecycle Stage to Its Code Owner

A clean project structure mirrors the **ML Lifecycle** stage by stage:

| Lifecycle Stage | Folder | Responsibility | Day 6 Notebook |
| --- | --- | --- | --- |
| 1. Problem Framing & Config | `configs/` | Business KPI, target definition, config parameters | Notebook 01 & 08 |
| 2. Data Ingestion | `src/ingestion/` | Pull CSV/JSON/SQL sources into immutable raw snapshot | Notebook 02 & 03 |
| 3. Data Validation | `src/validation/` | Check schema, nulls, ranges, categories before training | Notebook 02 & 03 |
| 4. Feature Engineering | `src/features/` | Transform raw columns into leak-free ML features | Notebook 04 & 05 |
| 5. Model Training & Testing | `src/training/` | Split, cross-validate, evaluate on unseen test set | Notebook 06 & 07 |
| 6. Artifact Packaging & Inference | `src/inference/` & `artifacts/` | Save `Pipeline` + metadata, verify prediction contract | Notebook 06 & 07 |
| 7. Tracking, Config & Monitoring | `artifacts/reports/` | Log experiments, ensure reproducibility, monitor drift (Day 7!) | Notebook 08 & 09 |
=====================================================================================================================================================
# Let's write a tiny reusable Python module into our scaffolded project and import it!
module_code = '''
from pathlib import Path
import pandas as pd

def summarize_dataset(csv_path: str | Path) -> dict:
    df = pd.read_csv(csv_path)
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }
'''

helper_file = PROJECT_ROOT / "src/ingestion/inspector.py"
helper_file.write_text(module_code.strip() + "\n", encoding="utf-8")

# Import and run the modular helper cleanly
import sys
if str(PROJECT_ROOT.resolve()) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.resolve()))

from src.ingestion.inspector import summarize_dataset

summary = summarize_dataset("data/customers_raw.csv")
print("Output from modular src.ingestion.inspector.summarize_dataset():")
print(json.dumps(summary, indent=2))


