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
