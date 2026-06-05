"""
dashboard/msft_forecaster/predict.py
================================
Generates the next-day directional prediction for MSFT and stores
it in the predictions table of the SQLite database.

Run daily after market close:
    python dashboard/msft_forecaster/predict.py

Author: Group 15 — Block D ADS-AI BUas
"""

import logging
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "db" / "stocks.db"
MODELS_DIR = BASE_DIR / "models" / "lucan"

FEATURE_COLS = [
    "rsi_14",
    "momentum_5",
    "momentum_10",
    "daily_return",
    "price_range_pct",
    "close_to_sma5_pct",
    "close_to_sma10_pct",
    "sma_crossover",
    "rolling_std_5",
    "volume_ratio",
    "lag_gold_return",
    "lag_oil_return",
    "lag_vix_1",
    "lag_spy_return",
]


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def load_best_model():
    """Load the best available trained model and matching scaler."""
    import re

    for prefix in ("xgboost_lucan", "random_forest_lucan", "logistic_regression_lucan"):
        models = sorted(MODELS_DIR.glob(f"{prefix}*.pkl"))
        if not models:
            continue
        model_path = models[-1]
        # Extract iteration tag (e.g. "it3") from model filename to find matching scaler
        match = re.search(r"(it\d+)", model_path.stem)
        if match:
            scaler_path = MODELS_DIR / f"scaler_lucan_{match.group(1)}.pkl"
            if not scaler_path.exists():
                scaler_path = sorted(MODELS_DIR.glob("scaler_lucan*.pkl"))[-1]
        else:
            scaler_path = sorted(MODELS_DIR.glob("scaler_lucan*.pkl"))[-1]
        try:
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            name = model_path.stem
            logger.info("Loaded model: %s with scaler: %s", name, scaler_path.stem)
            return model, scaler, name
        except Exception as exc:
            logger.warning("Could not load %s: %s", prefix, exc)
    return None, None, None


def build_features(conn: sqlite3.Connection, n_rows: int = 60) -> pd.DataFrame:
    """Merge the last n_rows of all tables and engineer features."""
    msft = pd.read_sql(
        f"SELECT * FROM msft_daily ORDER BY date DESC LIMIT {n_rows}", conn
    ).sort_values("date")
    gold = pd.read_sql(
        f"SELECT * FROM gold_prices ORDER BY date DESC LIMIT {n_rows}", conn
    ).sort_values("date")
    oil = pd.read_sql(
        f"SELECT * FROM oil_prices ORDER BY date DESC LIMIT {n_rows}", conn
    ).sort_values("date")
    vix = pd.read_sql(
        f"SELECT * FROM vix_data ORDER BY date DESC LIMIT {n_rows}", conn
    ).sort_values("date")
    spy = pd.read_sql(
        f"SELECT * FROM spy_data ORDER BY date DESC LIMIT {n_rows}", conn
    ).sort_values("date")

    df = (
        msft.merge(gold, on="date", how="left")
        .merge(oil, on="date", how="left")
        .merge(vix, on="date", how="left")
        .merge(spy, on="date", how="left")
    )
    df[["gold_close", "oil_close", "vix", "spy_close"]] = df[
        ["gold_close", "oil_close", "vix", "spy_close"]
    ].ffill()

    close = df["close"]
    sma5 = close.rolling(5).mean()
    sma10 = close.rolling(10).mean()

    df["rsi_14"] = _rsi(close)
    df["daily_return"] = close.pct_change() * 100
    df["momentum_5"] = close.pct_change(5) * 100
    df["momentum_10"] = close.pct_change(10) * 100
    df["close_to_sma5_pct"] = (close - sma5) / sma5 * 100
    df["close_to_sma10_pct"] = (close - sma10) / sma10 * 100
    df["sma_crossover"] = sma5 / sma10
    df["price_range_pct"] = (df["high"] - df["low"]) / close * 100
    df["rolling_std_5"] = close.rolling(5).std()
    df["volume_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
    df["lag_gold_return"] = df["gold_close"].pct_change().shift(1) * 100
    df["lag_oil_return"] = df["oil_close"].pct_change().shift(1) * 100
    df["lag_vix_1"] = df["vix"].shift(1)
    df["lag_spy_return"] = df["spy_close"].pct_change().shift(1) * 100

    return df.dropna().reset_index(drop=True)


def run_prediction(db_path: Path = DB_PATH) -> dict | None:
    """
    Generate a prediction for the latest available trading day and
    store it in the predictions table. Returns the prediction dict
    or None if it failed.
    """
    conn = sqlite3.connect(str(db_path))

    # Create predictions table if it doesn't exist
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            date               TEXT PRIMARY KEY,
            predicted_direction INTEGER NOT NULL,
            confidence         REAL NOT NULL,
            model_used         TEXT NOT NULL,
            actual_direction   INTEGER
        )
    """
    )

    df = build_features(conn)
    if df.empty:
        logger.error("Not enough data to generate prediction")
        conn.close()
        return None

    model, scaler, model_name = load_best_model()
    if model is None:
        logger.error("No trained model found in %s", MODELS_DIR)
        conn.close()
        return None

    row = df.iloc[[-1]]
    date_str = str(row["date"].iloc[0])
    close_price = float(row["close"].iloc[0])

    X = scaler.transform(row[FEATURE_COLS])
    pred = int(model.predict(X)[0])
    prob = float(model.predict_proba(X)[0][pred])

    # Upsert — replace if prediction for this date already exists
    conn.execute(
        """
        INSERT OR REPLACE INTO predictions
            (date, predicted_direction, confidence, model_used, actual_direction)
        VALUES (?, ?, ?, ?, NULL)
        """,
        (date_str, pred, round(prob, 4), model_name),
    )
    conn.commit()
    conn.close()

    result = {
        "date": date_str,
        "direction": "UP" if pred == 1 else "DOWN",
        "prediction": pred,
        "probability": round(prob * 100, 1),
        "close": close_price,
        "model_name": model_name,
    }
    logger.info("Prediction stored: %s", result)
    return result


if __name__ == "__main__":
    result = run_prediction()
    if result:
        logger.info(
            "Done — %s %s %.1f%%",
            result["date"],
            result["direction"],
            result["probability"],
        )
    else:
        logger.error("Prediction failed")
