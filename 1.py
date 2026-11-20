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
