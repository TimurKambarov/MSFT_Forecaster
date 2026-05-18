"""
pipeline/preprocess.py
======================
Data preprocessing pipeline for the MSFT Direction Predictor project.

This module provides reusable functions for loading, merging, cleaning,
and transforming stock market data from the SQLite database into a
machine-learning-ready dataset.

Author: Qusai Al Qusaily
Project: MSFT Direction Predictor — Block D ADS-AI BUas
"""

import sqlite3
import logging
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
DB_PATH = "data/stocks.db"
SCALER_PATH = "models/scaler.pkl"
TARGET_THRESHOLD = 0.005  # 0.5% minimum move to classify as UP or DOWN
TRAIN_SIZE = 0.8          # 80% training, 20% testing
FEATURE_COLS = [
    "open", "high", "low", "close", "volume",
    "gold_close", "oil_close", "vix",
    "lag_1", "lag_2", "rolling_5", "rolling_10",
    "daily_return", "price_range", "gold_return", "oil_return",
]


# ── Data Loading ─────────────────────────────────────────────────────────────

def load_all_tables(db_path: str = DB_PATH) -> tuple:
    """
    Load all four raw data tables from the SQLite database.

    Args:
        db_path (str): Path to the SQLite database file.

    Returns:
        tuple: msft_df, gold_df, oil_df, vix_df as pandas DataFrames.

    Raises:
        AssertionError: If the database file does not exist.
    """
    assert os.path.exists(db_path), f"Database not found at: {db_path}"

    conn = sqlite3.connect(db_path)

    msft_df = pd.read_sql("SELECT * FROM msft_daily ORDER BY date", conn)
    gold_df = pd.read_sql("SELECT * FROM gold_prices ORDER BY date", conn)
    oil_df = pd.read_sql("SELECT * FROM oil_prices ORDER BY date", conn)
    vix_df = pd.read_sql("SELECT * FROM vix_data ORDER BY date", conn)

    conn.close()

    # convert date columns to datetime
    for df in [msft_df, gold_df, oil_df, vix_df]:
        df["date"] = pd.to_datetime(df["date"])

    logger.info(
        f"Loaded from database: msft={len(msft_df)}, gold={len(gold_df)}, "
        f"oil={len(oil_df)}, vix={len(vix_df)}"
    )
    return msft_df, gold_df, oil_df, vix_df


# ── Merging ─────────────────────────────────────────────────────────────

def merge_datasets(
    msft_df: pd.DataFrame,
    gold_df: pd.DataFrame,
    oil_df: pd.DataFrame,
    vix_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge MSFT stock data with Gold, Oil, and VIX data on the date column.

    Uses left joins to preserve all MSFT trading days even when external
    data is missing for a given date.

    Args:
        msft_df (pd.DataFrame): MSFT daily OHLCV stock data.
        gold_df (pd.DataFrame): Daily gold closing prices.
        oil_df (pd.DataFrame): Daily crude oil closing prices.
        vix_df (pd.DataFrame): Daily VIX market volatility values.

    Returns:
        pd.DataFrame: Single merged dataset sorted by date.
    """
    df = msft_df.merge(gold_df, on="date", how="left")
    df = df.merge(oil_df, on="date", how="left")
    df = df.merge(vix_df, on="date", how="left")
    df = df.sort_values("date").reset_index(drop=True)

    logger.info(f"Merged dataset shape: {df.shape}")
    return df


# ── Missing Values ──────────────────────────────────────────────────────

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values in the merged dataset.

    Forward fills gold, oil, and VIX columns to cover gaps caused by
    trading calendar misalignments between datasets. Any remaining rows
    with NaN values are dropped.

    Args:
        df (pd.DataFrame): Merged dataset potentially containing NaN values.

    Returns:
        pd.DataFrame: Clean dataset with no missing values.
    """
    before = len(df)

    # forward fill external data columns only
    fill_cols = ["gold_close", "oil_close", "vix"]
    df[fill_cols] = df[fill_cols].ffill()

    # drop any remaining rows with NaN
    df = df.dropna().reset_index(drop=True)
    after = len(df)

    logger.info(f"Missing values handled. Dropped {before - after} rows.")
    return df


# ── Target Column ───────────────────────────────────────────────────────

def create_target(
    df: pd.DataFrame,
    threshold: float = TARGET_THRESHOLD,
) -> pd.DataFrame:
    """
    Create binary target column for next-day price direction prediction.

    Uses a percentage threshold to filter out neutral days where the price
    movement is too small to carry meaningful predictive signal.

    Target encoding:
        1 = UP   (next day return > +threshold)
        0 = DOWN (next day return < -threshold)
        Neutral days (within threshold) are removed.

    Args:
        df (pd.DataFrame): Dataset with close prices.
        threshold (float): Minimum return magnitude to classify as UP or DOWN.
                           Default is 0.005 (0.5%).

    Returns:
        pd.DataFrame: Dataset with target column added, neutral rows removed.
    """
    df = df.copy()

    # calculate next day percentage return
    df["next_return"] = df["close"].shift(-1) / df["close"] - 1

    # apply threshold to create target
    df["target"] = np.nan
    df.loc[df["next_return"] > threshold, "target"] = 1  # UP
    df.loc[df["next_return"] < -threshold, "target"] = 0  # DOWN

    # drop neutral rows
    before = len(df)
    df = df.dropna(subset=["target"])
    df["target"] = df["target"].astype(int)
    after = len(df)

    logger.info(
        f"Target created with {threshold * 100}% threshold. "
        f"Dropped {before - after} neutral rows. "
        f"UP: {(df['target'] == 1).sum()}, DOWN: {(df['target'] == 0).sum()}"
    )
    return df


# ── Feature Engineering ─────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer additional features to capture temporal patterns in stock data.

    Features created:
        - lag_1:        Previous day closing price
        - lag_2:        Two days ago closing price
        - rolling_5:    5-day moving average of closing price
        - rolling_10:   10-day moving average of closing price
        - daily_return: Percentage change from previous closing price
        - price_range:  Difference between daily high and low prices
        - gold_return:  Daily percentage change in gold closing price
        - oil_return:   Daily percentage change in oil closing price

    Args:
        df (pd.DataFrame): Merged dataset with target column.

    Returns:
        pd.DataFrame: Dataset with all engineered features added.
    """
    df = df.copy()

    # lag features — short term price memory
    df["lag_1"] = df["close"].shift(1)
    df["lag_2"] = df["close"].shift(2)

    # rolling averages — medium term trend
    df["rolling_5"] = df["close"].rolling(window=5).mean()
    df["rolling_10"] = df["close"].rolling(window=10).mean()

    # daily return — normalised price change
    df["daily_return"] = df["close"].pct_change()

    # price range — intraday volatility
    df["price_range"] = df["high"] - df["low"]

    # external asset returns — market sentiment signals
    df["gold_return"] = df["gold_close"].pct_change()
    df["oil_return"] = df["oil_close"].pct_change()

    # drop rows with NaN from rolling window calculations
    before = len(df)
    df = df.dropna().reset_index(drop=True)
    after = len(df)

    logger.info(
        f"Feature engineering complete. "
        f"Dropped {before - after} rows from rolling windows. "
        f"Final shape: {df.shape}"
    )
    return df


# ── Scaling ─────────────────────────────────────────────────────────────

def scale_features(
    df: pd.DataFrame,
    feature_cols: list = FEATURE_COLS,
    train_size: float = TRAIN_SIZE,
    scaler_path: str = SCALER_PATH,
) -> tuple:
    """
    Scale features using RobustScaler fitted on training data only.

    RobustScaler uses median and interquartile range instead of mean and
    standard deviation, making it more resistant to extreme market events
    such as crashes or earnings surprises.

    The scaler is fitted exclusively on training data to prevent data
    leakage from the test set into the scaling parameters.

    The fitted scaler is saved to disk for reuse by the dashboard when
    scaling new incoming data at prediction time.

    Args:
        df (pd.DataFrame): Dataset with all engineered features.
        feature_cols (list): List of feature column names to scale.
        train_size (float): Proportion of data used for training. Default 0.8.
        scaler_path (str): File path to save the fitted scaler object.

    Returns:
        tuple: (df with scaled columns added, fitted RobustScaler object)
    """
    split_idx = int(len(df) * train_size)

    # fit scaler on training data only — never on test data
    scaler = RobustScaler()
    scaler.fit(df[feature_cols].iloc[:split_idx])

    # transform all data using training statistics
    scaled_values = scaler.transform(df[feature_cols])
    scaled_cols = [f"{col}_scaled" for col in feature_cols]
    df[scaled_cols] = scaled_values

    # save scaler for dashboard reuse
    os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
    joblib.dump(scaler, scaler_path)

    logger.info(
        f"RobustScaler fitted on {split_idx} training rows. "
        f"Saved to {scaler_path}."
    )
    return df, scaler


# ── Train/Test Split ────────────────────────────────────────────────────

def train_test_split_timeseries(
    df: pd.DataFrame,
    feature_cols: list = FEATURE_COLS,
    train_size: float = TRAIN_SIZE,
) -> tuple:
    """
    Split dataset into training and test sets using time-based ordering.

    No shuffling is applied to preserve the temporal structure of the
    time series. Training data contains older observations and test data
    contains the most recent observations.

    Args:
        df (pd.DataFrame): Fully processed dataset with scaled features.
        feature_cols (list): List of feature column names.
        train_size (float): Proportion of data for training. Default 0.8.

    Returns:
        tuple: X_train, X_test, y_train, y_test, train_df, test_df
    """
    scaled_cols = [f"{col}_scaled" for col in feature_cols]
    split_idx = int(len(df) * train_size)

    X_train = df[scaled_cols].iloc[:split_idx].values
    X_test = df[scaled_cols].iloc[split_idx:].values
    y_train = df["target"].iloc[:split_idx].values
    y_test = df["target"].iloc[split_idx:].values

    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    logger.info(
        f"Time-based split: train={len(X_train)} rows "
        f"({train_df['date'].iloc[0].date()} to "
        f"test={len(X_test)} rows "
        f"({test_df['date'].iloc[0].date()} to {test_df['date'].iloc[-1].date()})"
    )
    return X_train, X_test, y_train, y_test, train_df, test_df


# ── Save to Database ────────────────────────────────────────────────────

def save_processed_features(
    df: pd.DataFrame,
    feature_cols: list = FEATURE_COLS,
    db_path: str = DB_PATH,
) -> None:
    """
    Save the processed feature dataset to the processed_features table
    in the SQLite database.

    Only the original (unscaled) feature columns and the target column
    are saved. Scaled columns are not stored in the database.

    Args:
        df (pd.DataFrame): Fully processed dataset with features and target.
        feature_cols (list): List of feature column names to save.
        db_path (str): Path to the SQLite database file.
    """
    cols_to_save = ["date"] + feature_cols + ["target"]
    df_to_save = df[cols_to_save].copy()
    df_to_save["date"] = df_to_save["date"].astype(str)

    conn = sqlite3.connect(db_path)
    df_to_save.to_sql(
        "processed_features",
        conn,
        if_exists="replace",
        index=False)
    conn.close()

    logger.info(f"Saved {len(df_to_save)} rows to processed_features table.")


# ── Full Pipeline ───────────────────────────────────────────────────────

def run_pipeline(
    db_path: str = DB_PATH,
    threshold: float = TARGET_THRESHOLD,
    train_size: float = TRAIN_SIZE,
    scaler_path: str = SCALER_PATH,
) -> tuple:
    """
    Run the full preprocessing pipeline end to end.

    Executes all steps in order:
        1. Load raw data from database
        2. Merge all four datasets on date
        3. Handle missing values with forward fill
        4. Create binary target column with threshold
        5. Engineer additional features
        6. Scale features with RobustScaler
        7. Split into train and test sets
        8. Save processed features to database

    Args:
        db_path (str): Path to the SQLite database.
        threshold (float): Minimum return for UP/DOWN classification.
        train_size (float): Proportion of data for training.
        scaler_path (str): Path to save the fitted scaler.

    Returns:
        tuple: X_train, X_test, y_train, y_test, train_df, test_df, scaler
    """
    logger.info("Starting preprocessing pipeline...")

    # step 1 — load
    msft_df, gold_df, oil_df, vix_df = load_all_tables(db_path)

    # step 2 — merge
    df = merge_datasets(msft_df, gold_df, oil_df, vix_df)

    # step 3 — missing values
    df = handle_missing_values(df)

    # step 4 — target
    df = create_target(df, threshold=threshold)

    # step 5 — features
    df = engineer_features(df)

    # step 6 — scale
    df, scaler = scale_features(df, FEATURE_COLS, train_size, scaler_path)

    # step 7 — split
    X_train, X_test, y_train, y_test, train_df, test_df = train_test_split_timeseries(
        df, FEATURE_COLS, train_size)

    # step 8 — save
    save_processed_features(df, FEATURE_COLS, db_path)

    logger.info(
        f"Pipeline complete. "
        f"Train: {len(X_train)} rows, Test: {len(X_test)} rows."
    )
    return X_train, X_test, y_train, y_test, train_df, test_df, scaler


# ── Entry Point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    X_train, X_test, y_train, y_test, train_df, test_df, scaler = run_pipeline()
    print(f"Pipeline finished successfully.")
    print(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows")
