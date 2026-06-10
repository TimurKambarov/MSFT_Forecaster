"""
Build db/stocks.db entirely from Yahoo Finance (yfinance).
Run once from the project root:
    python dashboard/setup_db.py

All historical data from 2015-01-01 to today is fetched fresh from
yfinance so every table uses a single consistent data source.
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent  # project root (dashboard/ → root)
DB_PATH = BASE_DIR / "db" / "stocks.db"
START = "2015-01-01"

TICKERS = {
    "MSFT": "msft_daily",
    "GC=F": "gold_prices",
    "CL=F": "oil_prices",
    "^VIX": "vix_data",
    "SPY": "spy_data",
    "NVDA": "nvda_daily",
    "AMZN": "amzn_daily",
}

COL_MAP = {
    "msft_daily": {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    },
    "gold_prices": {"Close": "gold_close"},
    "oil_prices": {"Close": "oil_close"},
    "vix_data": {"Close": "vix"},
    "spy_data": {"Close": "spy_close"},
    "nvda_daily": {"Close": "nvda_close", "Volume": "nvda_volume"},
    "amzn_daily": {"Close": "amzn_close", "Volume": "amzn_volume"},
}


def fetch(ticker: str) -> pd.DataFrame:
    """Download full history for a ticker from yfinance."""
    logger.info("Fetching %s from %s", ticker, START)
    df = yf.download(ticker, start=START, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.reset_index()
    df = df.rename(columns={"Date": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


def build():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))

    for ticker, table in TICKERS.items():
        df = fetch(ticker)
        col_map = COL_MAP[table]
        keep = ["date"] + list(col_map.keys())
        df = df[[c for c in keep if c in df.columns]].rename(columns=col_map)
        df.to_sql(table, conn, if_exists="replace", index=False)
        logger.info("%s → %s (%d rows)", ticker, table, len(df))

    # Model metrics from it3 evaluation (XGBoost, test set Jan 2024 – Apr 2026)
    metrics = pd.DataFrame(
        [
            {
                "model": "XGBoost",
                "accuracy": 0.5223,
                "precision": 0.5272,
                "recall": 0.5223,
                "f1": 0.5222,
            },
            {
                "model": "Random Forest",
                "accuracy": 0.4841,
                "precision": 0.4827,
                "recall": 0.4841,
                "f1": 0.4832,
            },
            {
                "model": "Logistic Regression",
                "accuracy": 0.4862,
                "precision": 0.4983,
                "recall": 0.4862,
                "f1": 0.4737,
            },
        ]
    )
    metrics.to_sql("model_metrics", conn, if_exists="replace", index=False)
    logger.info("model_metrics written")

    conn.commit()
    conn.close()
    logger.info("Database ready at %s", DB_PATH)


if __name__ == "__main__":
    build()
