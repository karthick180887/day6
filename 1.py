import importlib
import os
import platform
import sys
from pathlib import Path

print(f"Python version : {sys.version.split()[0]}")
print(f"Platform       : {platform.platform()}")
print(f"Working folder : {Path.cwd()}")

REQUIRED_PACKAGES = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("sklearn", "scikit-learn"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("yaml", "pyyaml"),
    ("joblib", "joblib"),
    ("pydantic", "pydantic"),
    ("dotenv", "python-dotenv"),
]

missing = []
for import_name, pip_name in REQUIRED_PACKAGES:
    try:
        mod = importlib.import_module(import_name)
        version = getattr(mod, "__version__", "installed")
        print(f"  [PASS] {pip_name:<15} -> {version}")
    except ImportError:
        print(f"  [FAIL] {pip_name:<15} -> NOT INSTALLED")
        missing.append(pip_name)

assert not missing, f"Missing packages: {missing}. Run pip install -r ../docker-jupyterlab/requirements.txt"
print("\nAll required libraries imported successfully!")
#############################################################################################################################
# Ensure data files exist (auto-generate cleanly if missing)
data_dir = Path("data")
expected_files = [
    data_dir / "customers_raw.csv",
    data_dir / "usage_events.json",
    data_dir / "customers_corrupted_batch.csv",
    data_dir / "incoming_batch_exercise.csv",
]

if not all(p.exists() for p in expected_files):
    print("Some data files are missing — running data/generate_data.py...")
    from data.generate_data import generate_all_datasets
    generate_all_datasets(data_dir)

for p in expected_files:
    assert p.exists(), f"Missing dataset: {p}"
    print(f"  [PASS] Found {p} ({p.stat().st_size:,} bytes)")

config_path = Path("configs/train_config.yaml")
assert config_path.exists(), f"Missing config: {config_path}"
print(f"  [PASS] Found {config_path} ({config_path.stat().st_size:,} bytes)")

