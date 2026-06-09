"""
2025-26d-fai1-adsai-group_15/data/raw/fetch_latest.py
=====================================================
Weekly incremental updater for the per-ticker raw CSV files.

Unlike a full re-download, this script maintains a fixed-size rolling window
of daily market data per ticker, stored as one CSV per ticker in `data/raw/`.
Those CSVs are the persistent store (committed back to the repo by the GitHub
Actions workflow), so each run:

    1. Reads the existing CSV for each ticker (if present).
    2. Checks the latest date already stored.
    3. Fetches only the trading days newer than that date.
    4. Appends the new rows (de-duplicated, sorted).
    5. Trims the CSV back to the newest WINDOW_ROWS rows (drops the oldest).

If a CSV does not yet exist, the script seeds it with the last WINDOW_ROWS
trading days so the first run bootstraps the full window.

Tickers maintained (one CSV each):
    MSFT  -> MSFT.csv     GC=F -> GOLD.csv     ^VIX -> VIX.csv
    ASML  -> ASML.csv     NVDA -> NVDA.csv     AMD  -> AMD.csv
    AMZN  -> AMZN.csv     CRM  -> CRM.csv      PLTR -> PLTR.csv

Usage:

    python data/raw/fetch_latest.py
    python data/raw/fetch_latest.py --window 1863 --raw-dir data/raw

Author: Group 15 — Block D ADS-AI BUas
"""

import argparse
import logging
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
# Project root: 2025-26d-fai1-adsai-group_15  (this file is at data/raw/)
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"

# ── Rolling-window config ─────────────────────────────────────────────────────
# Number of most-recent trading days to keep per ticker. Roughly the count of
# NYSE trading days in the original 2019-01-01 → 2026-06-01 seed range.
WINDOW_ROWS = 1863

# How far back to look when seeding a brand-new CSV or catching up. Generous so
# we never miss days after a long gap; extra rows are trimmed by the window.
SEED_PERIOD = "10y"

# ── Ticker config ─────────────────────────────────────────────────────────────
# yfinance symbol → output CSV file stem
TICKERS = {
    "MSFT": "MSFT",
    "GC=F": "GOLD",
    "^VIX": "VIX",
    "ASML": "ASML",
    "NVDA": "NVDA",
    "AMD": "AMD",
    "AMZN": "AMZN",
    "CRM": "CRM",
    "PLTR": "PLTR",
}


def _tidy_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten yfinance MultiIndex columns and expose the date as a column.

    Args:
        df (pd.DataFrame): Raw frame returned by ``yfinance.download``.

    Returns:
        pd.DataFrame: Clean frame with a 'date' column (YYYY-MM-DD strings).
    """
    # Flatten MultiIndex columns produced by yfinance for a single ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df = df.rename(columns={"Date": "date", "Datetime": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


def _read_existing_csv(csv_path: Path) -> pd.DataFrame:
    """Read an existing ticker CSV, or return an empty frame if absent.

    Args:
        csv_path (Path): Path to the ticker's CSV file.

    Returns:
        pd.DataFrame: Existing data (possibly empty), date-sorted.
    """
    if not csv_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(csv_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        df = df.sort_values("date").reset_index(drop=True)
    return df


def _fetch_since(ticker: str, start: str) -> pd.DataFrame:
    """Download daily OHLCV from *start* (inclusive) to today.

    Args:
        ticker (str): yfinance ticker symbol.
        start (str): Start date (YYYY-MM-DD).

    Returns:
        pd.DataFrame: Tidied frame of new rows (may be empty).
    """
    logger.info("Fetching %s from %s", ticker, start)
    df = yf.download(ticker, start=start, auto_adjust=True, progress=False)
    if df.empty:
        logger.warning("No data returned for %s", ticker)
        return pd.DataFrame()
    return _tidy_dataframe(df)


def _fetch_seed(ticker: str) -> pd.DataFrame:
    """Download a long history to seed a new CSV (first run / missing file).

    Args:
        ticker (str): yfinance ticker symbol.

    Returns:
        pd.DataFrame: Tidied frame (may be empty).
    """
    logger.info("Seeding %s (period=%s)", ticker, SEED_PERIOD)
    df = yf.download(ticker, period=SEED_PERIOD, auto_adjust=True, progress=False)
    if df.empty:
        logger.warning("No seed data returned for %s", ticker)
        return pd.DataFrame()
    return _tidy_dataframe(df)


def update_ticker(
    ticker: str,
    stem: str,
    raw_dir: Path,
    window_rows: int,
) -> dict:
    """Update one ticker's CSV: append new trading days, trim to the window.

    Args:
        ticker (str): yfinance ticker symbol.
        stem (str): Output CSV file stem (e.g. 'MSFT').
        raw_dir (Path): Directory holding the raw CSVs.
        window_rows (int): Max rows to keep (drops oldest beyond this).

    Returns:
        dict: Summary with rows added, rows dropped, and final row count.
    """
    csv_path = raw_dir / f"{stem}.csv"
    existing = _read_existing_csv(csv_path)

    if existing.empty:
        # No file yet → seed the full window
        new_data = _fetch_seed(ticker)
        combined = new_data
        added = len(new_data)
    else:
        latest_date = existing["date"].max()
        # Start the day after the latest stored date
        start = (pd.Timestamp(latest_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

        if pd.Timestamp(start) > pd.Timestamp.today().normalize():
            logger.info("%s — already up to date (latest %s)", stem, latest_date)
            return {
                "added": 0,
                "dropped": 0,
                "rows": len(existing),
                "up_to_date": True,
            }

        new_data = _fetch_since(ticker, start)
        # Keep only genuinely new dates, then append
        if not new_data.empty:
            new_data = new_data[~new_data["date"].isin(existing["date"])]
        combined = pd.concat([existing, new_data], ignore_index=True)
        added = len(new_data)

    if combined.empty:
        logger.warning("%s — no data available, nothing written", stem)
        return {"added": 0, "dropped": 0, "rows": 0, "up_to_date": False}

    # De-duplicate, sort ascending by date
    combined = combined.drop_duplicates(subset="date").sort_values("date").reset_index(drop=True)

    # Trim to the fixed window: keep the newest *window_rows* rows
    rows_before_trim = len(combined)
    if rows_before_trim > window_rows:
        combined = combined.iloc[-window_rows:].reset_index(drop=True)
    dropped = rows_before_trim - len(combined)

    combined.to_csv(csv_path, index=False)
    logger.info(
        "%-6s — +%d new, -%d oldest | %d rows (%s to %s)",
        stem,
        added,
        dropped,
        len(combined),
        combined["date"].min(),
        combined["date"].max(),
    )
    return {
        "added": added,
        "dropped": dropped,
        "rows": len(combined),
        "up_to_date": added == 0,
    }


def update_all(
    raw_dir: Path = RAW_DIR,
    window_rows: int = WINDOW_ROWS,
) -> dict:
    """Update every configured ticker's CSV.

    Args:
        raw_dir (Path): Directory holding the raw CSVs.
        window_rows (int): Max rows to keep per ticker.

    Returns:
        dict: Mapping of CSV filename → per-ticker summary dict.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    summary = {}

    for ticker, stem in TICKERS.items():
        try:
            summary[f"{stem}.csv"] = update_ticker(ticker, stem, raw_dir, window_rows)
        except Exception as exc:  # keep going even if one ticker fails
            logger.error("Failed to update %s (%s): %s", stem, ticker, exc)
            summary[f"{stem}.csv"] = {
                "added": 0,
                "dropped": 0,
                "rows": 0,
                "error": str(exc),
            }

    return summary


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Weekly incremental updater for raw ticker CSVs.")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=RAW_DIR,
        help="Directory holding the raw CSV files.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=WINDOW_ROWS,
        help="Number of most-recent trading days to keep per ticker.",
    )
    return parser.parse_args()


def main() -> None:
    """Script entry point."""
    args = parse_args()
    logger.info(
        "Starting weekly update — dir: %s | window: %d rows",
        args.raw_dir,
        args.window,
    )
    results = update_all(args.raw_dir, args.window)

    total_added = sum(r.get("added", 0) for r in results.values())
    total_dropped = sum(r.get("dropped", 0) for r in results.values())
    logger.info(
        "Done. Added %d rows, dropped %d oldest across %d tickers.",
        total_added,
        total_dropped,
        len(results),
    )
    for name, r in results.items():
        logger.info("  %-10s %s", name, r)


if __name__ == "__main__":
    main()
