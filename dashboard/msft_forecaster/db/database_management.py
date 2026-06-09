"""
database_management.py
======================
Build `stocks.db` — MSFT Direction Predictor, Group 15, Block D ADS-AI BUas.

Merge the per-ticker CSV files produced by the data-fetch script (`data/raw/`)
and load them into a single SQLite database (`db/stocks.db`). One table per
ticker.

This script performs the **initial / full build** of the database. The *daily*
rolling update (append newest trading day, drop oldest row) is handled by the
separate automated fetch script, not here.

Sections
--------
1. Connection      — open / create `stocks.db`
2. CSV merging     — read and normalise all raw CSVs
3. Adding/creating — write each ticker to its own table
4. Testing         — `SELECT *` checks and row counts
5. CSV export      — join all tables into one wide modelling dataset
6. Saving          — commit and close

Tables
------
    msft_daily  : date, open, high, low, close, volume
    gold_prices : date, close, volume
    vix_data    : date, close, volume
    asml_data   : date, close, volume
    nvda_data   : date, close, volume
    amd_data    : date, close, volume
    amzn_data   : date, close, volume
    crm_data    : date, close, volume
    pltr_data   : date, close, volume

Note: ^VIX is an index and has no trading volume; its `volume` column will be
empty/zero and is kept only for schema consistency.

Usage
-----
    python database_management.py

Author: Group 15 — Block D ADS-AI BUas
"""

import logging
import sqlite3
from pathlib import Path

import pandas as pd

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────────────────
def _find_project_root(marker: str = "data/raw") -> Path:
    """Walk upwards from the cwd until *marker* is found.

    Args:
        marker (str): Relative path that marks the project root.

    Returns:
        Path: The resolved project root directory.
    """
    here = Path.cwd().resolve()
    for candidate in [here, *here.parents]:
        if (candidate / marker).exists():
            return candidate
    # Fallback: assume three levels up (notebooks/<x>/<y>/)
    return here.parents[2] if len(here.parents) >= 3 else here


BASE_DIR = _find_project_root()
RAW_DIR = BASE_DIR / "data" / "raw"
DB_PATH = BASE_DIR / "db" / "stocks.db"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELLING_CSV = PROCESSED_DIR / "modelling_dataset.csv"

# file stem -> (table name, list of columns to keep besides 'date')
TICKER_CONFIG = {
    "MSFT": ("msft_daily", ["open", "high", "low", "close", "volume"]),
    "GOLD": ("gold_prices", ["close", "volume"]),
    "VIX": ("vix_data", ["close", "volume"]),
    "ASML": ("asml_data", ["close", "volume"]),
    "NVDA": ("nvda_data", ["close", "volume"]),
    "AMD": ("amd_data", ["close", "volume"]),
    "AMZN": ("amzn_data", ["close", "volume"]),
    "CRM": ("crm_data", ["close", "volume"]),
    "PLTR": ("pltr_data", ["close", "volume"]),
}


# ── 1. Connection ─────────────────────────────────────────────────────────────
def create_connection(db_path: Path) -> sqlite3.Connection:
    """
    Open a connection to the SQLite database, creating it if needed.

    Args:
        db_path (Path): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: Active database connection.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    logger.info("Connected to database: %s", db_path)
    return conn


# ── 2. CSV merging ────────────────────────────────────────────────────────────
def load_raw_csv(csv_path: Path, keep_cols: list[str]) -> pd.DataFrame:
    """
    Read a single raw CSV and return a tidy DataFrame.

    Args:
        csv_path (Path): Path to the raw CSV file.
        keep_cols (list[str]): Columns to keep alongside 'date'
            (e.g. ['close', 'volume'] or the full OHLCV list).

    Returns:
        pd.DataFrame: Tidy frame with 'date' plus the requested columns,
        sorted ascending by date and de-duplicated.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Normalise column names to lowercase for consistent access
    df.columns = [c.strip().lower() for c in df.columns]

    if "date" not in df.columns:
        raise ValueError(f"{csv_path.name}: no 'date' column found")

    # Parse and standardise the date to YYYY-MM-DD strings
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    # Warn if any requested column is missing, then keep what we can
    missing = [c for c in keep_cols if c not in df.columns]
    if missing:
        logger.warning("%s: missing columns %s", csv_path.name, missing)
    available = [c for c in keep_cols if c in df.columns]

    df = df[["date", *available]]
    df = df.dropna(subset=["date"])
    df = df.drop_duplicates(subset="date")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def merge_all_csvs(raw_dir: Path, config: dict) -> dict:
    """
    Load every configured CSV into a tidy DataFrame.

    Args:
        raw_dir (Path): Directory containing the raw CSV files.
        config (dict): Mapping of file stem -> (table, keep_cols).

    Returns:
        dict: Mapping of table name -> tidy DataFrame.
    """
    frames = {}
    for stem, (table, keep_cols) in config.items():
        csv_path = raw_dir / f"{stem}.csv"
        df = load_raw_csv(csv_path, keep_cols)
        frames[table] = df
        logger.info(
            "%-12s -> %-12s | %4d rows | %s to %s",
            stem,
            table,
            len(df),
            df["date"].min() if not df.empty else "-",
            df["date"].max() if not df.empty else "-",
        )
    return frames


# ── 3. Adding / creating the database ─────────────────────────────────────────
def write_tables(conn: sqlite3.Connection, frames: dict) -> None:
    """
    Write each DataFrame to its table, replacing any existing table.

    Args:
        conn (sqlite3.Connection): Active database connection.
        frames (dict): Mapping of table name -> DataFrame.
    """
    for table, df in frames.items():
        df.to_sql(table, conn, if_exists="replace", index=False)
        logger.info("Wrote %-12s (%d rows)", table, len(df))
    conn.commit()


# ── 4. Testing ────────────────────────────────────────────────────────────────
def list_tables(conn: sqlite3.Connection) -> list[str]:
    """Return the names of all tables in the database."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def verify_database(conn: sqlite3.Connection) -> None:
    """Print each table with its row count and a null-value check."""
    print("Tables in database:")
    for table in list_tables(conn):
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        nulls = int(df.isnull().sum().sum())
        status = "clean" if nulls == 0 else f"{nulls} missing values"
        print(f"  {table:<14} {len(df):>5} rows | {status}")


def preview_table(conn: sqlite3.Connection, table: str, limit: int = 5) -> None:
    """Print the most recent rows of a table as a sample `SELECT *`.

    Args:
        conn (sqlite3.Connection): Active database connection.
        table (str): Table name to preview.
        limit (int): Number of most-recent rows to show.
    """
    sample = pd.read_sql(f"SELECT * FROM {table} ORDER BY date DESC LIMIT {limit}", conn)
    print(f"\nSample SELECT * FROM {table} (most recent {limit} rows):")
    print(sample.to_string(index=False))


# ── 5. Export combined modelling dataset (CSV) ────────────────────────────────
def build_modelling_dataset(conn: sqlite3.Connection, config: dict) -> pd.DataFrame:
    """
    Join every ticker table into one wide, forward-filled DataFrame.

    Args:
        conn (sqlite3.Connection): Active database connection.
        config (dict): Mapping of stem -> (table, keep_cols).

    Returns:
        pd.DataFrame: One row per date; each ticker's value columns are
        prefixed with its stem (lowercased). Sorted ascending by date.
    """
    merged = None
    for stem, (table, _keep) in config.items():
        df = pd.read_sql(f"SELECT * FROM {table}", conn)

        # Prefix every column except 'date' with the ticker stem
        prefix = stem.lower()
        df = df.rename(columns={c: f"{prefix}_{c}" for c in df.columns if c != "date"})

        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, on="date", how="outer")

    # Sort chronologically, then forward-fill, then back-fill leading gaps
    merged = merged.sort_values("date").reset_index(drop=True)
    value_cols = [c for c in merged.columns if c != "date"]
    merged[value_cols] = merged[value_cols].ffill().bfill()

    logger.info(
        "Modelling dataset: %d rows x %d columns (%s to %s)",
        len(merged),
        merged.shape[1],
        merged["date"].min(),
        merged["date"].max(),
    )
    return merged


def export_modelling_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """Write the modelling dataset to *csv_path*."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    logger.info("Modelling dataset saved to %s", csv_path)


# ── 6. Orchestration ──────────────────────────────────────────────────────────
def main() -> None:
    """Run the full build: connect, merge, write, test, export, save."""
    logger.info("Libraries imported successfully")
    logger.info("Project root : %s", BASE_DIR)
    logger.info("Raw CSV dir  : %s", RAW_DIR)
    logger.info("Database     : %s", DB_PATH)

    # 1. Connection
    conn = create_connection(DB_PATH)

    try:
        # 2. CSV merging
        frames = merge_all_csvs(RAW_DIR, TICKER_CONFIG)
        print(f"Loaded {len(frames)} ticker tables from {RAW_DIR}")

        # Quick preview of the MSFT frame to confirm the schema looks correct
        print("\nMSFT frame preview:")
        print(frames["msft_daily"].head(3).to_string(index=False))

        # 3. Adding / creating the database
        write_tables(conn, frames)
        print("All ticker tables written to the database.")

        # 4. Testing
        verify_database(conn)
        preview_table(conn, "msft_daily")  # full OHLCV
        preview_table(conn, "nvda_data")  # close + volume only

        # 5. Export combined modelling dataset
        modelling_df = build_modelling_dataset(conn, TICKER_CONFIG)
        export_modelling_csv(modelling_df, MODELLING_CSV)
        print(
            f"Modelling dataset: {modelling_df.shape[0]} rows x " f"{modelling_df.shape[1]} columns"
        )
        print("\nModelling dataset preview:")
        print(modelling_df.head(3).to_string(index=False))

        # 6. Saving
        conn.commit()
    finally:
        conn.close()

    logger.info("Database committed and connection closed.")
    print(f"stocks.db saved at: {DB_PATH}")
    print(f"Tables: {', '.join(t for t, _ in TICKER_CONFIG.values())}")


if __name__ == "__main__":
    main()
