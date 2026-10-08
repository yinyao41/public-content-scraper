import os
import pandas as pd
from datetime import datetime

def ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def save_dataframe(df: pd.DataFrame, prefix: str) -> str:
    ensure_data_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"data/{prefix}_{timestamp}.csv"
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return filepath
