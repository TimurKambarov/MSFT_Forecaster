"""
Build db/stocks.db from data/processed/msft_merged.csv.
Run once from the msft-forecaster directory:
    python setup_db.py
"""

import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).parent
CSV_PATH = BASE_DIR / "data" / "processed" / "msft_merged.csv"
DB_PATH = BASE_DIR / "db" / "stocks.db"

df = pd.read_csv(CSV_PATH)
df.columns = [c.lower() for c in df.columns]
df = df.rename(columns={"date": "date"})
df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

conn = sqlite3.connect(str(DB_PATH))

df[["date", "open", "high", "low", "close", "volume"]].to_sql(
    "msft_daily", conn, if_exists="replace", index=False
)
df[["date", "gold_close"]].to_sql("gold_prices", conn, if_exists="replace", index=False)
df[["date", "oil_close"]].to_sql("oil_prices", conn, if_exists="replace", index=False)
df[["date", "vix"]].to_sql("vix_data", conn, if_exists="replace", index=False)

conn.commit()
conn.close()
print(f"Database created at {DB_PATH} ({len(df)} rows)")
