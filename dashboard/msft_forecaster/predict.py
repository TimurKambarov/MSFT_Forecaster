"""
dashboard/msft_forecaster/predict.py
=====================================
Generates the next-week directional prediction for MSFT using
Timur's XGBoost weekly model and stores it in the predictions table.

Run weekly after market close (Friday):
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
MODEL_PATH = Path(__file__).parent / "pipeline" / "models" / "xgboost_weekly.joblib"

DIRECTION_LABELS = {0: "DOWN", 1: "UP", 2: "SAME"}
PEER_TICKERS = ["nvda", "amzn"]


def _rsi_weekly(series: pd.Series) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, min_periods=14).mean()
    avg_loss = loss.ewm(com=13, min_periods=14).mean()
    return 100 - (100 / (1 + avg_gain / avg_loss))


def load_model():
    try:
        bundle = joblib.load(MODEL_PATH)
        logger.info("Loaded model: xgboost_weekly")
        return bundle["model"], bundle["scaler"], bundle["feature_columns"], "xgboost_weekly"
    except Exception as exc:
        logger.error("Could not load model from %s: %s", MODEL_PATH, exc)
        return None, None, None, None


def build_features(conn: sqlite3.Connection, n_daily_rows: int = 400) -> pd.DataFrame:
    """Fetch daily MSFT + peer data, resample to weekly, compute all 20 features."""
    msft = pd.read_sql(
        f"SELECT date, open, high, low, close, volume FROM msft_daily ORDER BY date DESC LIMIT {n_daily_rows}",
        conn,
    ).sort_values("date")
    msft["date"] = pd.to_datetime(msft["date"])
    msft = msft.set_index("date")

    weekly = (
        msft.resample("W-FRI")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna(subset=["close"])
    )

    close = weekly["close"]
    high = weekly["high"]
    low = weekly["low"]
    vol = weekly["volume"]

    weekly["return_1w"] = close.pct_change(1) * 100
    weekly["return_4w"] = close.pct_change(4) * 100
    weekly["return_8w"] = close.pct_change(8) * 100
    weekly["lag_return_1"] = weekly["return_1w"].shift(1)
    weekly["lag_return_2"] = weekly["return_1w"].shift(2)
    weekly["rsi_14"] = _rsi_weekly(close)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    weekly["macd"] = ema12 - ema26
    weekly["macd_signal"] = weekly["macd"].ewm(span=9, adjust=False).mean()
    weekly["macd_hist"] = weekly["macd"] - weekly["macd_signal"]

    weekly["price_range_pct"] = (high - low) / close * 100
    weekly["rolling_std_5"] = close.rolling(5).std()
    weekly["volume_ratio"] = vol / vol.rolling(20).mean()

    msft_return_1w = weekly["return_1w"]

    for peer in PEER_TICKERS:
        close_col = f"{peer}_close"
        volume_col = f"{peer}_volume"
        try:
            peer_df = pd.read_sql(
                f"SELECT date, {close_col}, {volume_col} FROM {peer}_daily ORDER BY date DESC LIMIT {n_daily_rows}",
                conn,
            ).sort_values("date")
            peer_df["date"] = pd.to_datetime(peer_df["date"])
            peer_df = peer_df.set_index("date")

            peer_w = peer_df.resample("W-FRI").agg({close_col: "last", volume_col: "sum"})
            weekly[close_col] = peer_w[close_col]
            weekly[volume_col] = peer_w[volume_col]

            peer_close = weekly[close_col]
            peer_volume = weekly[volume_col]

            weekly[f"{peer}_return_1w"] = peer_close.pct_change(1) * 100
            weekly[f"{peer}_lag_return_1"] = weekly[f"{peer}_return_1w"].shift(1)
            weekly[f"{peer}_rel_strength"] = msft_return_1w - weekly[f"{peer}_return_1w"]
            weekly[f"{peer}_volume_ratio"] = peer_volume / peer_volume.rolling(20).mean()
        except Exception as e:
            logger.warning(
                "Could not build peer features for %s: %s — filling with defaults", peer, e
            )
            weekly[f"{peer}_return_1w"] = 0.0
            weekly[f"{peer}_lag_return_1"] = 0.0
            weekly[f"{peer}_rel_strength"] = 0.0
            weekly[f"{peer}_volume_ratio"] = 1.0

    return weekly.dropna().reset_index()


def run_prediction(db_path: Path = DB_PATH) -> dict | None:
    conn = sqlite3.connect(str(db_path))

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

    model, scaler, feature_cols, model_name = load_model()
    if model is None:
        logger.error("No trained model found at %s", MODEL_PATH)
        conn.close()
        return None

    row = df.iloc[[-1]]
    date_str = str(row["date"].iloc[0].date())
    close_price = float(row["close"].iloc[0])

    X = scaler.transform(row[feature_cols])
    pred = int(model.predict(X)[0])
    prob = float(model.predict_proba(X)[0][pred])

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
        "direction": DIRECTION_LABELS.get(pred, str(pred)),
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
            "Done — %s %s (%.1f%% confidence)",
            result["date"],
            result["direction"],
            result["probability"],
        )
    else:
        logger.error("Prediction failed")
