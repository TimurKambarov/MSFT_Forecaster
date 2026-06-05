"""
dashboard/msft_forecaster/data/fetch_latest.py
=========================================
Fetches the latest daily market data from Yahoo Finance and appends
new rows to the SQLite database. Existing dates are never overwritten.

Tickers fetched:
    MSFT  → msft_daily  (open, high, low, close, volume)
    GC=F  → gold_prices (gold_close)
    CL=F  → oil_prices  (oil_close)
    ^VIX  → vix_data    (vix)
    SPY   → spy_data    (spy_close)

Usage:
    
    python dashboard/msft_forecaster/data/fetch_latest.py

Author: Group 15 — Block D ADS-AI BUas
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd
import yfinance as yf

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[3]  # project root
DB_PATH = BASE_DIR / "db" / "stocks.db"

# ── Ticker config ─────────────────────────────────────────────────────────────
TICKERS = {
    "MSFT": "msft_daily",
    "GC=F": "gold_prices",
    "CL=F": "oil_prices",
    "^VIX": "vix_data",
    "SPY": "spy_data",
}

# Column mapping: yfinance column → database column name
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
}


def _get_latest_date(conn: sqlite3.Connection, table: str) -> str | None:
    """Return the most recent date stored in a table, or None if empty."""
    try:
        row = conn.execute(f"SELECT MAX(date) FROM {table}").fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None


def _fetch_ticker(ticker: str, start: str) -> pd.DataFrame:
    """Download daily OHLCV data from yfinance from *start* date onwards."""
    logger.info("Fetching %s from %s", ticker, start)
    df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
    if df.empty:
        logger.warning("No data returned for %s", ticker)
    return df


def _append_to_table(
    conn: sqlite3.Connection,
    df: pd.DataFrame,
    table: str,
    col_map: dict,
) -> int:
    """
    Append new rows to *table*, skipping any dates already present.
    Returns the number of rows inserted.
    """
    if df.empty:
        return 0

    # Flatten MultiIndex columns produced by yfinance when downloading one ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df = df.rename(columns={"Date": "date", "Datetime": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # Keep only the columns we need
    keep = ["date"] + list(col_map.keys())
    df = df[[c for c in keep if c in df.columns]].rename(columns=col_map)

    # Load dates already in the table to avoid duplicates
    try:
        existing = pd.read_sql(f"SELECT date FROM {table}", conn)["date"].tolist()
    except Exception:
        existing = []

    new_rows = df[~df["date"].isin(existing)]
    if new_rows.empty:
        logger.info("%s — already up to date", table)
        return 0

    new_rows.to_sql(table, conn, if_exists="append", index=False)
    logger.info("%s — inserted %d new rows", table, len(new_rows))
    return len(new_rows)


def fetch_and_update(db_path: Path = DB_PATH) -> dict:
    """
    Fetch latest data for all tickers and append to the database.
    Returns a summary dict with rows inserted per table.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    summary = {}

    for ticker, table in TICKERS.items():
        try:
            latest_date = _get_latest_date(conn, table)

            # Start one day after the latest stored date, or fetch from 2015
            if latest_date:
                start = pd.Timestamp(latest_date) + pd.Timedelta(days=1)
                if start > pd.Timestamp.today():
                    logger.info("%s — already up to date", table)
                    summary[table] = 0
                    continue
                start = start.strftime("%Y-%m-%d")
            else:
                start = "2015-01-01"

            df = _fetch_ticker(ticker, start)
            inserted = _append_to_table(conn, df, table, COL_MAP[table])
            summary[table] = inserted

        except Exception as exc:
            logger.error("Failed to update %s (%s): %s", table, ticker, exc)
            summary[table] = 0

    conn.commit()
    conn.close()
    return summary


if __name__ == "__main__":
    logger.info("Starting data fetch — DB: %s", DB_PATH)
    results = fetch_and_update()
    total = sum(results.values())
    logger.info("Done. Rows inserted: %s | Total: %d", results, total)
