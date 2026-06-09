"""
database_management.py
=======================
Database management script for the MSFT Direction Predictor project.

This module handles all database operations including:
    - Creating and connecting to the SQLite database
    - Loading raw market data from CSV files into the database
    - Creating output tables for processed features and predictions
    - Providing query functions for all six database tables
    - Saving processed features and model predictions

The database contains six tables:
    - msft_daily          : MSFT daily OHLCV stock data
    - gold_prices         : Daily gold closing prices
    - oil_prices          : Daily crude oil closing prices
    - vix_data            : Daily VIX volatility index values
    - processed_features  : Engineered features (filled by pipeline)
    - predictions         : Model predictions (filled by model)

Usage:
    python database_management.py

Author: Qusai Al Qusaily (236866)
Project: MSFT Direction Predictor — Block D ADS-AI BUas
Group: Group 15
"""

import logging
import os
import sqlite3

import pandas as pd

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# Original CSV files (2015-2025)
MSFT_CSV_PATH = "../../../data/raw/MSFT.csv"
GOLD_CSV_PATH = "../../../data/raw/Gold.csv"
OIL_CSV_PATH = "../../../data/raw/CrudeOil.csv"
MACRO_CSV_PATH = "../../../data/raw/MacroEconomicIndicators.csv"

# New CSV files (2025-2026)
MSFT_NEW_PATH = "../../../data/raw/Microsoft_2025-2026.csv"
GOLD_NEW_PATH = "../../../data/raw/Gold_2025-2026.csv"
OIL_NEW_PATH = "../../../data/raw/Oil_2025-2026.csv"
VIX_NEW_PATH = "../../../data/raw/VIX_2025-2026.csv"

# Database path
DB_PATH = "../../../db/stocks.db"

# Date filter — only keep data from this date onwards
START_DATE = "2019-01-01"


# ── Connection ────────────────────────────────────────────────────────────────


def create_connection(db_path: str) -> sqlite3.Connection:
    """
    Create a connection to the SQLite database.
    Creates the database file if it does not exist.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: Active database connection.
    """
    conn = sqlite3.connect(db_path)
    logger.info(f"Connected to database: {db_path}")
    return conn


# ── CSV Loading ───────────────────────────────────────────────────────────────


def load_new_format_csv(csv_path: str, close_col_name: str) -> pd.DataFrame:
    """
    Load a new format CSV file with 3-row header (yfinance format).
    Skips the first 3 rows and reads date and close columns only.

    Args:
        csv_path (str): Path to the new format CSV file.
        close_col_name (str): Name to give the close column.

    Returns:
        pd.DataFrame: DataFrame with date and close columns.
    """
    # skip the 3-row yfinance header and assign column names manually
    df = pd.read_csv(
        csv_path,
        skiprows=3,
        header=None,
        names=["date", "close", "high", "low", "open", "volume"],
    )

    # drop empty or non-date rows
    df = df.dropna(subset=["date"])
    df = df[df["date"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")]

    # parse date column
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # keep only date and close columns
    df = df[["date", "close"]]
    df.columns = ["date", close_col_name]

    df = df.drop_duplicates(subset="date")
    df = df.sort_values("date").reset_index(drop=True)

    logger.info(f"Loaded new format CSV: {csv_path} — {len(df)} rows")
    return df


# ── Data Loaders ──────────────────────────────────────────────────────────────


def load_msft_data(
    conn: sqlite3.Connection,
    original_path: str,
    new_path: str,
    start_date: str,
) -> pd.DataFrame:
    """
    Load and combine original and new MSFT data into the database.
    Filters to start_date onwards and saves to msft_daily table.

    Args:
        conn (sqlite3.Connection): Active database connection.
        original_path (str): Path to original MSFT CSV file.
        new_path (str): Path to new 2025-2026 MSFT CSV file.
        start_date (str): Date filter — keep rows from this date onwards.

    Returns:
        pd.DataFrame: Combined and filtered MSFT DataFrame.
    """
    # load original format
    df_old = pd.read_csv(original_path)
    df_old["Date"] = pd.to_datetime(df_old["Date"]).dt.date
    df_old = df_old[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df_old.columns = ["date", "open", "high", "low", "close", "volume"]

    # load new format (3-row header)
    df_new = pd.read_csv(
        new_path,
        skiprows=3,
        header=None,
        names=["date", "close", "high", "low", "open", "volume"],
    )
    df_new = df_new.dropna(subset=["date"])
    df_new = df_new[df_new["date"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")]
    df_new["date"] = pd.to_datetime(df_new["date"]).dt.date
    df_new = df_new[["date", "open", "high", "low", "close", "volume"]]

    # combine old and new
    df = pd.concat([df_old, df_new], ignore_index=True)
    df = df.drop_duplicates(subset="date")
    df = df.sort_values("date").reset_index(drop=True)

    # apply date filter
    df = df[df["date"] >= pd.to_datetime(start_date).date()]
    df = df.reset_index(drop=True)

    # save to database
    df.to_sql("msft_daily", conn, if_exists="replace", index=False)
    logger.info(f"msft_daily loaded: {len(df)} rows")
    return df


def load_gold_data(
    conn: sqlite3.Connection,
    original_path: str,
    new_path: str,
    start_date: str,
) -> pd.DataFrame:
    """
    Load and combine original and new Gold price data into the database.
    Filters to start_date onwards and saves to gold_prices table.

    Args:
        conn (sqlite3.Connection): Active database connection.
        original_path (str): Path to original Gold CSV file.
        new_path (str): Path to new 2025-2026 Gold CSV file.
        start_date (str): Date filter.

    Returns:
        pd.DataFrame: Combined and filtered gold DataFrame.
    """
    # load original format
    df_old = pd.read_csv(original_path)
    df_old["Date"] = pd.to_datetime(df_old["Date"], utc=True).dt.date
    df_old = df_old[["Date", "Close"]]
    df_old.columns = ["date", "gold_close"]

    # load new format
    df_new = load_new_format_csv(new_path, "gold_close")

    # combine
    df = pd.concat([df_old, df_new], ignore_index=True)
    df = df.drop_duplicates(subset="date")
    df = df.sort_values("date").reset_index(drop=True)

    # apply date filter
    df = df[df["date"] >= pd.to_datetime(start_date).date()]
    df = df.reset_index(drop=True)

    # save to database
    df.to_sql("gold_prices", conn, if_exists="replace", index=False)
    logger.info(f"gold_prices loaded: {len(df)} rows")
    return df


def load_oil_data(
    conn: sqlite3.Connection,
    original_path: str,
    new_path: str,
    start_date: str,
) -> pd.DataFrame:
    """
    Load and combine original and new Crude Oil price data into the database.
    Filters to start_date onwards and saves to oil_prices table.

    Args:
        conn (sqlite3.Connection): Active database connection.
        original_path (str): Path to original CrudeOil CSV file.
        new_path (str): Path to new 2025-2026 Oil CSV file.
        start_date (str): Date filter.

    Returns:
        pd.DataFrame: Combined and filtered oil DataFrame.
    """
    # load original format
    df_old = pd.read_csv(original_path)
    df_old["Date"] = pd.to_datetime(df_old["Date"]).dt.date
    df_old = df_old[["Date", "Close"]]
    df_old.columns = ["date", "oil_close"]

    # load new format
    df_new = load_new_format_csv(new_path, "oil_close")

    # combine
    df = pd.concat([df_old, df_new], ignore_index=True)
    df = df.drop_duplicates(subset="date")
    df = df.sort_values("date").reset_index(drop=True)

    # apply date filter
    df = df[df["date"] >= pd.to_datetime(start_date).date()]
    df = df.reset_index(drop=True)

    # save to database
    df.to_sql("oil_prices", conn, if_exists="replace", index=False)
    logger.info(f"oil_prices loaded: {len(df)} rows")
    return df


def load_vix_data(
    conn: sqlite3.Connection,
    macro_path: str,
    new_path: str,
    start_date: str,
) -> pd.DataFrame:
    """
    Load and combine original VIX from macro file and new 2025-2026 VIX data.
    Filters to start_date onwards and saves to vix_data table.

    Args:
        conn (sqlite3.Connection): Active database connection.
        macro_path (str): Path to MacroEconomicIndicators CSV file.
        new_path (str): Path to new 2025-2026 VIX CSV file.
        start_date (str): Date filter.

    Returns:
        pd.DataFrame: Combined and filtered VIX DataFrame.
    """
    # load original VIX from macro file
    df_old = pd.read_csv(macro_path, index_col=0)
    df_old = df_old[["Stock Market Volatility (VIX Index)"]]
    df_old.columns = ["vix"]
    df_old = df_old.reset_index()
    df_old.columns = ["date", "vix"]
    df_old["date"] = pd.to_datetime(df_old["date"]).dt.date
    df_old = df_old.dropna(subset=["vix"])

    # load new format
    df_new = load_new_format_csv(new_path, "vix")

    # combine
    df = pd.concat([df_old, df_new], ignore_index=True)
    df = df.drop_duplicates(subset="date")
    df = df.sort_values("date").reset_index(drop=True)

    # apply date filter
    df = df[df["date"] >= pd.to_datetime(start_date).date()]
    df = df.reset_index(drop=True)

    # save to database
    df.to_sql("vix_data", conn, if_exists="replace", index=False)
    logger.info(f"vix_data loaded: {len(df)} rows")
    return df


# ── Table Creation ────────────────────────────────────────────────────────────


def create_output_tables(conn: sqlite3.Connection) -> None:
    """
    Create empty output tables for processed features and model predictions.
    These tables are populated by the pipeline and model notebooks.
    If the tables already exist they are left unchanged.

    Args:
        conn (sqlite3.Connection): Active database connection.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_features (
            date          TEXT PRIMARY KEY,
            open          REAL,
            high          REAL,
            low           REAL,
            close         REAL,
            volume        REAL,
            gold_close    REAL,
            oil_close     REAL,
            vix           REAL,
            lag_1         REAL,
            lag_2         REAL,
            rolling_5     REAL,
            rolling_10    REAL,
            daily_return  REAL,
            price_range   REAL,
            gold_return   REAL,
            oil_return    REAL,
            target        INTEGER
        )
    """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            date                TEXT PRIMARY KEY,
            predicted_direction INTEGER,
            confidence          REAL,
            model_used          TEXT,
            actual_direction    INTEGER
        )
    """
    )

    conn.commit()
    logger.info("Output tables created: processed_features, predictions")


# ── Verification ──────────────────────────────────────────────────────────────


def verify_database(conn: sqlite3.Connection) -> None:
    """
    Verify all expected tables exist in the database with correct row counts.
    Logs a summary of all tables and their row counts.

    Args:
        conn (sqlite3.Connection): Active database connection.
    """
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    logger.info("Database verification:")
    for table in tables["name"]:
        count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
        rows = count["count"].values[0]
        status = "(empty — fills later)" if rows == 0 else f"{rows} rows"
        logger.info(f"  {table:<25} {status}")


# ── Query Functions ───────────────────────────────────────────────────────────


def get_msft_data(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Query all MSFT daily stock data from the database.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        pd.DataFrame: MSFT daily data sorted by date.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM msft_daily ORDER BY date", conn)
    conn.close()
    return df


def get_gold_data(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Query all Gold price data from the database.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        pd.DataFrame: Gold price data sorted by date.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM gold_prices ORDER BY date", conn)
    conn.close()
    return df


def get_oil_data(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Query all Crude Oil price data from the database.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        pd.DataFrame: Oil price data sorted by date.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM oil_prices ORDER BY date", conn)
    conn.close()
    return df


def get_vix_data(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Query all VIX volatility index data from the database.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        pd.DataFrame: VIX data sorted by date.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM vix_data ORDER BY date", conn)
    conn.close()
    return df


def get_processed_features(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Query all processed features from the database.
    This table is populated by the pipeline notebook (Task 9).

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        pd.DataFrame: Processed features sorted by date.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM processed_features ORDER BY date", conn)
    conn.close()
    return df


def get_predictions(db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Query all model predictions from the database.
    This table is populated by the model notebook (Task 10).

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        pd.DataFrame: Model predictions sorted by date.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM predictions ORDER BY date", conn)
    conn.close()
    return df


# ── Save Functions ────────────────────────────────────────────────────────────


def save_processed_features(df: pd.DataFrame, db_path: str = DB_PATH) -> None:
    """
    Save processed features DataFrame to the database.
    Replaces any existing data in the processed_features table.
    Called by the pipeline notebook after preprocessing is complete.

    Args:
        df (pd.DataFrame): Processed features DataFrame.
        db_path (str): Path to the SQLite database file.
    """
    conn = sqlite3.connect(db_path)
    df.to_sql("processed_features", conn, if_exists="replace", index=False)
    conn.close()
    logger.info(f"Saved {len(df)} rows to processed_features")


def save_predictions(df: pd.DataFrame, db_path: str = DB_PATH) -> None:
    """
    Save model predictions DataFrame to the database.
    Replaces any existing data in the predictions table.
    Called by the model notebook after predictions are generated.

    Args:
        df (pd.DataFrame): Predictions DataFrame with columns:
            date, predicted_direction, confidence, model_used, actual_direction.
        db_path (str): Path to the SQLite database file.
    """
    conn = sqlite3.connect(db_path)
    df.to_sql("predictions", conn, if_exists="replace", index=False)
    conn.close()
    logger.info(f"Saved {len(df)} rows to predictions")


# ── Main Pipeline ─────────────────────────────────────────────────────────────


def run_database_setup(
    db_path: str = DB_PATH,
    start_date: str = START_DATE,
) -> None:
    """
    Run the full database setup pipeline.

    Steps:
        1. Verify all CSV files exist
        2. Create database connection
        3. Load MSFT, Gold, Oil, VIX data from CSV files
        4. Create output tables (processed_features, predictions)
        5. Remove legacy macro_indicators table
        6. Verify database integrity

    Args:
        db_path (str): Path to the SQLite database file.
        start_date (str): Date filter — keep rows from this date onwards.
    """
    logger.info("Starting database setup...")
    logger.info(f"Database  : {db_path}")
    logger.info(f"Start date: {start_date}")

    # step 1 — verify all CSV files exist
    all_paths = [
        MSFT_CSV_PATH,
        GOLD_CSV_PATH,
        OIL_CSV_PATH,
        MACRO_CSV_PATH,
        MSFT_NEW_PATH,
        GOLD_NEW_PATH,
        OIL_NEW_PATH,
        VIX_NEW_PATH,
    ]
    for path in all_paths:
        assert os.path.exists(path), f"File not found: {path}"
        logger.info(f"  Found: {path}")

    # step 2 — create connection
    conn = create_connection(db_path)

    # step 3 — load raw data
    msft_df = load_msft_data(conn, MSFT_CSV_PATH, MSFT_NEW_PATH, start_date)
    gold_df = load_gold_data(conn, GOLD_CSV_PATH, GOLD_NEW_PATH, start_date)
    oil_df = load_oil_data(conn, OIL_CSV_PATH, OIL_NEW_PATH, start_date)
    vix_df = load_vix_data(conn, MACRO_CSV_PATH, VIX_NEW_PATH, start_date)

    # step 4 — create output tables
    create_output_tables(conn)

    # step 5 — remove legacy tables
    conn.execute("DROP TABLE IF EXISTS macro_indicators")
    conn.commit()
    logger.info("Legacy macro_indicators table removed")

    # step 6 — verify
    verify_database(conn)

    # missing values check
    for name, df in [
        ("msft_daily", msft_df),
        ("gold_prices", gold_df),
        ("oil_prices", oil_df),
        ("vix_data", vix_df),
    ]:
        nulls = df.isnull().sum().sum()
        status = "Clean" if nulls == 0 else f"{nulls} missing values"
        logger.info(f"  {name:<25} {status}")

    conn.close()
    logger.info("Database setup complete.")
    logger.info("Next step: run pipeline notebook to fill processed_features")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_database_setup()
