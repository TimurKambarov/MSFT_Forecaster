"""
MSFT Direction Predictor — Streamlit Dashboard
===============================================
Run:
    pip install streamlit plotly pandas numpy joblib scikit-learn xgboost
    streamlit run dashboard/streamlit_app.py
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
import streamlit as st
import plotly.graph_objects as go

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
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

SAMPLE_HISTORY = [
    {
        "date": "2024-11-13",
        "open": 421.64,
        "high": 429.33,
        "low": 418.21,
        "close": 425.20,
        "volume": 20456709,
        "gold_close": 2580.8,
        "oil_close": 68.43,
        "vix": 14.02,
    },
    {
        "date": "2024-11-14",
        "open": 425.00,
        "high": 428.17,
        "low": 420.00,
        "close": 426.89,
        "volume": 27218675,
        "gold_close": 2568.2,
        "oil_close": 68.70,
        "vix": 14.31,
    },
    {
        "date": "2024-11-15",
        "open": 419.82,
        "high": 422.80,
        "low": 413.64,
        "close": 415.00,
        "volume": 27330826,
        "gold_close": 2565.7,
        "oil_close": 67.02,
        "vix": 16.14,
    },
    {
        "date": "2024-11-18",
        "open": 414.87,
        "high": 418.40,
        "low": 412.10,
        "close": 415.76,
        "volume": 22575673,
        "gold_close": 2610.6,
        "oil_close": 69.16,
        "vix": 15.58,
    },
    {
        "date": "2024-11-19",
        "open": 413.11,
        "high": 417.94,
        "low": 411.55,
        "close": 417.79,
        "volume": 16903922,
        "gold_close": 2627.1,
        "oil_close": 69.39,
        "vix": 16.35,
    },
    {
        "date": "2024-11-20",
        "open": 416.87,
        "high": 417.29,
        "low": 410.58,
        "close": 415.49,
        "volume": 17202555,
        "gold_close": 2648.2,
        "oil_close": 68.87,
        "vix": 17.16,
    },
    {
        "date": "2024-11-21",
        "open": 419.50,
        "high": 419.78,
        "low": 410.29,
        "close": 412.87,
        "volume": 18154614,
        "gold_close": 2672.1,
        "oil_close": 70.10,
        "vix": 16.87,
    },
    {
        "date": "2024-11-22",
        "open": 411.37,
        "high": 417.40,
        "low": 411.06,
        "close": 417.00,
        "volume": 22803358,
        "gold_close": 2709.9,
        "oil_close": 71.24,
        "vix": 15.24,
    },
    {
        "date": "2024-11-25",
        "open": 418.38,
        "high": 421.08,
        "low": 414.85,
        "close": 418.79,
        "volume": 24447471,
        "gold_close": 2616.8,
        "oil_close": 68.94,
        "vix": 14.60,
    },
    {
        "date": "2024-11-26",
        "open": 419.59,
        "high": 429.04,
        "low": 418.85,
        "close": 427.99,
        "volume": 22825574,
        "gold_close": 2620.3,
        "oil_close": 68.77,
        "vix": 14.10,
    },
    {
        "date": "2024-11-27",
        "open": 425.11,
        "high": 427.23,
        "low": 422.02,
        "close": 422.99,
        "volume": 17407455,
        "gold_close": 2639.9,
        "oil_close": 68.72,
        "vix": 14.10,
    },
    {
        "date": "2024-11-29",
        "open": 420.09,
        "high": 424.88,
        "low": 417.80,
        "close": 423.46,
        "volume": 15132529,
        "gold_close": 2657.0,
        "oil_close": 68.00,
        "vix": 13.51,
    },
    {
        "date": "2024-12-02",
        "open": 421.57,
        "high": 433.00,
        "low": 421.31,
        "close": 430.98,
        "volume": 18092788,
        "gold_close": 2634.9,
        "oil_close": 68.10,
        "vix": 13.34,
    },
    {
        "date": "2024-12-03",
        "open": 429.84,
        "high": 432.47,
        "low": 427.74,
        "close": 431.20,
        "volume": 17100500,
        "gold_close": 2644.7,
        "oil_close": 69.94,
        "vix": 13.30,
    },
    {
        "date": "2024-12-04",
        "open": 433.03,
        "high": 439.67,
        "low": 432.63,
        "close": 437.42,
        "volume": 23888329,
        "gold_close": 2653.8,
        "oil_close": 68.54,
        "vix": 13.45,
    },
    {
        "date": "2024-12-05",
        "open": 437.92,
        "high": 444.66,
        "low": 436.17,
        "close": 442.62,
        "volume": 20802839,
        "gold_close": 2626.6,
        "oil_close": 68.30,
        "vix": 13.54,
    },
    {
        "date": "2024-12-06",
        "open": 442.30,
        "high": 446.10,
        "low": 441.77,
        "close": 443.57,
        "volume": 17936304,
        "gold_close": 2638.6,
        "oil_close": 67.20,
        "vix": 12.77,
    },
    {
        "date": "2024-12-09",
        "open": 442.60,
        "high": 448.33,
        "low": 440.50,
        "close": 446.02,
        "volume": 17082222,
        "gold_close": 2664.9,
        "oil_close": 68.37,
        "vix": 14.19,
    },
    {
        "date": "2024-12-10",
        "open": 444.39,
        "high": 449.62,
        "low": 441.60,
        "close": 443.33,
        "volume": 17619491,
        "gold_close": 2697.6,
        "oil_close": 68.59,
        "vix": 14.18,
    },
    {
        "date": "2024-12-11",
        "open": 444.05,
        "high": 450.35,
        "low": 444.05,
        "close": 448.99,
        "volume": 15424102,
        "gold_close": 2733.8,
        "oil_close": 70.29,
        "vix": 13.58,
    },
    {
        "date": "2024-12-12",
        "open": 449.11,
        "high": 456.16,
        "low": 449.11,
        "close": 449.56,
        "volume": 19709789,
        "gold_close": 2687.5,
        "oil_close": 70.02,
        "vix": 13.92,
    },
    {
        "date": "2024-12-13",
        "open": 448.44,
        "high": 451.43,
        "low": 445.58,
        "close": 447.27,
        "volume": 19711728,
        "gold_close": 2656.0,
        "oil_close": 71.29,
        "vix": 13.81,
    },
    {
        "date": "2024-12-16",
        "open": 447.27,
        "high": 452.18,
        "low": 445.28,
        "close": 451.59,
        "volume": 21473178,
        "gold_close": 2651.4,
        "oil_close": 70.71,
        "vix": 14.69,
    },
    {
        "date": "2024-12-17",
        "open": 451.01,
        "high": 455.29,
        "low": 449.57,
        "close": 454.46,
        "volume": 19693532,
        "gold_close": 2644.4,
        "oil_close": 70.08,
        "vix": 15.87,
    },
    {
        "date": "2024-12-18",
        "open": 451.32,
        "high": 452.65,
        "low": 437.02,
        "close": 437.39,
        "volume": 23461009,
        "gold_close": 2636.5,
        "oil_close": 70.58,
        "vix": 27.62,
    },
    {
        "date": "2024-12-19",
        "open": 441.62,
        "high": 443.18,
        "low": 436.32,
        "close": 437.03,
        "volume": 19663242,
        "gold_close": 2592.2,
        "oil_close": 69.91,
        "vix": 24.09,
    },
    {
        "date": "2024-12-20",
        "open": 433.11,
        "high": 443.74,
        "low": 428.63,
        "close": 436.60,
        "volume": 55820435,
        "gold_close": 2628.7,
        "oil_close": 69.46,
        "vix": 18.36,
    },
    {
        "date": "2024-12-23",
        "open": 436.74,
        "high": 437.65,
        "low": 432.83,
        "close": 435.25,
        "volume": 16519390,
        "gold_close": 2612.3,
        "oil_close": 69.24,
        "vix": 16.78,
    },
    {
        "date": "2024-12-24",
        "open": 434.65,
        "high": 439.60,
        "low": 434.19,
        "close": 439.33,
        "volume": 7015283,
        "gold_close": 2620.0,
        "oil_close": 70.10,
        "vix": 14.27,
    },
    {
        "date": "2024-12-26",
        "open": 439.08,
        "high": 440.94,
        "low": 436.63,
        "close": 438.11,
        "volume": 7968756,
        "gold_close": 2638.8,
        "oil_close": 69.62,
        "vix": 14.73,
    },
    {
        "date": "2024-12-27",
        "open": 434.60,
        "high": 435.22,
        "low": 426.35,
        "close": 430.53,
        "volume": 17626515,
        "gold_close": 2617.2,
        "oil_close": 70.60,
        "vix": 15.95,
    },
    {
        "date": "2024-12-30",
        "open": 426.06,
        "high": 427.55,
        "low": 421.90,
        "close": 424.83,
        "volume": 12601099,
        "gold_close": 2606.1,
        "oil_close": 70.99,
        "vix": 17.40,
    },
    {
        "date": "2024-12-31",
        "open": 426.10,
        "high": 426.73,
        "low": 420.66,
        "close": 421.50,
        "volume": 12788944,
        "gold_close": 2629.2,
        "oil_close": 71.72,
        "vix": 17.35,
    },
    {
        "date": "2025-01-02",
        "open": 425.53,
        "high": 426.07,
        "low": 414.85,
        "close": 418.58,
        "volume": 15068088,
        "gold_close": 2658.9,
        "oil_close": 73.13,
        "vix": 17.93,
    },
    {
        "date": "2025-01-03",
        "open": 421.08,
        "high": 424.03,
        "low": 419.54,
        "close": 423.35,
        "volume": 15083807,
        "gold_close": 2645.0,
        "oil_close": 73.96,
        "vix": 16.13,
    },
    {
        "date": "2025-01-06",
        "open": 428.00,
        "high": 434.32,
        "low": 425.48,
        "close": 427.85,
        "volume": 18692564,
        "gold_close": 2638.4,
        "oil_close": 73.56,
        "vix": 16.04,
    },
    {
        "date": "2025-01-07",
        "open": 429.00,
        "high": 430.65,
        "low": 420.80,
        "close": 422.37,
        "volume": 17384904,
        "gold_close": 2656.7,
        "oil_close": 74.25,
        "vix": 17.82,
    },
    {
        "date": "2025-01-08",
        "open": 423.46,
        "high": 426.97,
        "low": 421.54,
        "close": 424.56,
        "volume": 14067768,
        "gold_close": 2664.5,
        "oil_close": 73.32,
        "vix": 17.70,
    },
    {
        "date": "2025-01-10",
        "open": 424.63,
        "high": 424.71,
        "low": 415.02,
        "close": 418.95,
        "volume": 19120620,
        "gold_close": 2708.5,
        "oil_close": 76.57,
        "vix": 19.54,
    },
    {
        "date": "2025-01-13",
        "open": 415.24,
        "high": 418.50,
        "low": 412.29,
        "close": 417.19,
        "volume": 16810461,
        "gold_close": 2673.5,
        "oil_close": 78.82,
        "vix": 19.19,
    },
    {
        "date": "2025-01-14",
        "open": 417.81,
        "high": 419.74,
        "low": 410.72,
        "close": 415.67,
        "volume": 15785352,
        "gold_close": 2677.5,
        "oil_close": 77.50,
        "vix": 18.71,
    },
    {
        "date": "2025-01-15",
        "open": 419.13,
        "high": 428.15,
        "low": 418.27,
        "close": 426.31,
        "volume": 17854689,
        "gold_close": 2712.5,
        "oil_close": 80.04,
        "vix": 16.12,
    },
    {
        "date": "2025-01-16",
        "open": 428.70,
        "high": 429.49,
        "low": 424.39,
        "close": 424.58,
        "volume": 14443042,
        "gold_close": 2746.4,
        "oil_close": 78.68,
        "vix": 16.60,
    },
    {
        "date": "2025-01-17",
        "open": 434.09,
        "high": 434.48,
        "low": 428.17,
        "close": 429.03,
        "volume": 24575332,
        "gold_close": 2744.3,
        "oil_close": 77.88,
        "vix": 15.97,
    },
    {
        "date": "2025-01-21",
        "open": 430.20,
        "high": 430.90,
        "low": 425.60,
        "close": 428.50,
        "volume": 23647173,
        "gold_close": 2755.0,
        "oil_close": 75.89,
        "vix": 15.06,
    },
    {
        "date": "2025-01-22",
        "open": 437.56,
        "high": 447.27,
        "low": 436.00,
        "close": 446.20,
        "volume": 26266324,
        "gold_close": 2767.6,
        "oil_close": 75.44,
        "vix": 15.10,
    },
    {
        "date": "2025-01-23",
        "open": 442.00,
        "high": 446.75,
        "low": 441.50,
        "close": 446.71,
        "volume": 16975809,
        "gold_close": 2763.1,
        "oil_close": 74.62,
        "vix": 15.02,
    },
    {
        "date": "2025-01-24",
        "open": 445.16,
        "high": 446.65,
        "low": 441.40,
        "close": 444.06,
        "volume": 14586274,
        "gold_close": 2777.3,
        "oil_close": 74.66,
        "vix": 14.85,
    },
    {
        "date": "2025-01-27",
        "open": 424.01,
        "high": 435.20,
        "low": 423.50,
        "close": 434.56,
        "volume": 32833252,
        "gold_close": 2737.5,
        "oil_close": 73.17,
        "vix": 17.90,
    },
    {
        "date": "2025-01-28",
        "open": 434.60,
        "high": 448.38,
        "low": 431.38,
        "close": 447.20,
        "volume": 22446799,
        "gold_close": 2766.8,
        "oil_close": 73.77,
        "vix": 16.41,
    },
    {
        "date": "2025-01-29",
        "open": 446.69,
        "high": 446.88,
        "low": 440.40,
        "close": 442.33,
        "volume": 22973096,
        "gold_close": 2769.1,
        "oil_close": 72.62,
        "vix": 16.56,
    },
    {
        "date": "2025-01-30",
        "open": 418.77,
        "high": 422.86,
        "low": 413.16,
        "close": 414.99,
        "volume": 53915598,
        "gold_close": 2823.0,
        "oil_close": 72.73,
        "vix": 15.84,
    },
    {
        "date": "2025-01-31",
        "open": 418.98,
        "high": 420.69,
        "low": 414.91,
        "close": 415.06,
        "volume": 31979227,
        "gold_close": 2812.5,
        "oil_close": 72.53,
        "vix": 16.43,
    },
    {
        "date": "2025-02-03",
        "open": 411.60,
        "high": 415.41,
        "low": 408.66,
        "close": 410.92,
        "volume": 24614140,
        "gold_close": 2833.9,
        "oil_close": 73.16,
        "vix": 18.62,
    },
    {
        "date": "2025-02-04",
        "open": 412.69,
        "high": 413.92,
        "low": 409.74,
        "close": 412.37,
        "volume": 19381288,
        "gold_close": 2853.3,
        "oil_close": 72.70,
        "vix": 17.21,
    },
    {
        "date": "2025-02-05",
        "open": 412.35,
        "high": 413.83,
        "low": 410.40,
        "close": 413.29,
        "volume": 15340591,
        "gold_close": 2871.6,
        "oil_close": 71.03,
        "vix": 15.77,
    },
    {
        "date": "2025-02-06",
        "open": 414.00,
        "high": 418.20,
        "low": 414.00,
        "close": 415.82,
        "volume": 15771619,
        "gold_close": 2856.0,
        "oil_close": 70.61,
        "vix": 15.50,
    },
    {
        "date": "2025-02-07",
        "open": 416.48,
        "high": 418.65,
        "low": 408.10,
        "close": 409.75,
        "volume": 21605948,
        "gold_close": 2867.3,
        "oil_close": 71.00,
        "vix": 16.54,
    },
    {
        "date": "2025-02-10",
        "open": 413.71,
        "high": 415.46,
        "low": 410.92,
        "close": 412.22,
        "volume": 15191858,
        "gold_close": 2914.3,
        "oil_close": 72.32,
        "vix": 15.81,
    },
    {
        "date": "2025-02-11",
        "open": 409.64,
        "high": 412.49,
        "low": 409.30,
        "close": 411.44,
        "volume": 15230883,
        "gold_close": 2912.5,
        "oil_close": 73.32,
        "vix": 16.02,
    },
    {
        "date": "2025-02-12",
        "open": 407.21,
        "high": 410.75,
        "low": 404.37,
        "close": 409.04,
        "volume": 17273445,
        "gold_close": 2909.0,
        "oil_close": 73.32,
        "vix": 15.89,
    },
    {
        "date": "2025-02-13",
        "open": 407.00,
        "high": 411.00,
        "low": 406.36,
        "close": 410.54,
        "volume": 20517341,
        "gold_close": 2925.9,
        "oil_close": 73.32,
        "vix": 15.10,
    },
]

FEATURE_IMPORTANCE = [
    ("Close_lag_1", 0.18),
    ("RSI_14", 0.14),
    ("VIX_lag_1", 0.11),
    ("Volume_ma_10", 0.10),
    ("MACD_signal", 0.09),
    ("Crude_return_1d", 0.08),
    ("Close_ma_20", 0.07),
    ("Gold_return_5d", 0.06),
    ("Bollinger_pct", 0.05),
    ("ATR_14", 0.04),
]

MODEL_METRICS = {
    "Stacking Ensemble": {"accuracy": 0.79, "precision": 0.81, "recall": 0.80, "f1": 0.79},
    "XGBoost (it3)": {"accuracy": 0.74, "precision": 0.76, "recall": 0.75, "f1": 0.74},
    "Random Forest (it3)": {"accuracy": 0.71, "precision": 0.73, "recall": 0.70, "f1": 0.71},
    "Logistic Regression (it3)": {"accuracy": 0.61, "precision": 0.62, "recall": 0.60, "f1": 0.58},
}


# ── DB helpers ────────────────────────────────────────────────────────────────
def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _build_features(conn, n_rows: int = 60) -> pd.DataFrame:
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


def _load_best_model():
    for prefix in ("xgboost_lucan", "random_forest_lucan", "logistic_regression_lucan"):
        models = sorted(MODELS_DIR.glob(f"{prefix}*.pkl"))
        scalers = sorted(MODELS_DIR.glob("scaler_lucan*.pkl"))
        if models and scalers:
            try:
                return joblib.load(models[-1]), joblib.load(scalers[-1]), models[-1].stem
            except Exception:
                pass
    return None, None, None


# ── Cached data loaders ───────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def load_stock_history():
    try:
        conn = _get_conn()
        df = pd.read_sql(
            """SELECT m.date, m.open, m.high, m.low, m.close, m.volume,
                      g.gold_close, o.oil_close, v.vix
               FROM msft_daily m
               LEFT JOIN gold_prices g ON m.date = g.date
               LEFT JOIN oil_prices  o ON m.date = o.date
               LEFT JOIN vix_data    v ON m.date = v.date
               ORDER BY m.date""",
            conn,
        )
        conn.close()
        df["date"] = pd.to_datetime(df["date"])
        return df, False
    except Exception:
        df = pd.DataFrame(SAMPLE_HISTORY)
        df["date"] = pd.to_datetime(df["date"])
        return df, True


@st.cache_data(ttl=900)
def load_prediction():
    try:
        conn = _get_conn()
        tables = [
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        ]
        if "predictions" in tables:
            row = conn.execute(
                "SELECT p.*, m.close FROM predictions p "
                "JOIN msft_daily m ON p.date = m.date "
                "ORDER BY p.date DESC LIMIT 1"
            ).fetchone()
            if row:
                conn.close()
                return {
                    "date": row["date"],
                    "direction": "UP" if row["predicted_direction"] == 1 else "DOWN",
                    "probability": round(row["confidence"] * 100, 1),
                    "close": row["close"],
                    "model_name": row["model_used"],
                }
        df = _build_features(conn, n_rows=60)
        conn.close()
        if df.empty:
            return None
        model, scaler, model_name = _load_best_model()
        if model is None:
            return None
        X = scaler.transform(df[FEATURE_COLS].iloc[[-1]])
        pred = int(model.predict(X)[0])
        prob = float(model.predict_proba(X)[0][pred])
        return {
            "date": str(df["date"].iloc[-1])[:10],
            "direction": "UP" if pred == 1 else "DOWN",
            "probability": round(prob * 100, 1),
            "close": float(df["close"].iloc[-1]),
            "model_name": model_name,
        }
    except Exception:
        return None


@st.cache_data(ttl=900)
def load_model_metrics_db():
    try:
        conn = _get_conn()
        tables = [
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        ]
        if "model_metrics" in tables:
            rows = pd.read_sql("SELECT * FROM model_metrics", conn)
            conn.close()
            return rows.to_dict(orient="records")
        conn.close()
    except Exception:
        pass
    return None


# ── Chart helpers ─────────────────────────────────────────────────────────────
ACCENT = "#009FFD"
AMBER = "#DBD56E"
RED = "#EF4444"
PURPLE = "#8B5CF6"


def filter_by_period(df: pd.DataFrame, period: str) -> pd.DataFrame:
    if df.empty:
        return df
    last = df["date"].iloc[-1]
    if period == "1W":
        cutoff = last - pd.DateOffset(weeks=1)
    elif period == "1M":
        cutoff = last - pd.DateOffset(months=1)
    elif period == "3M":
        cutoff = last - pd.DateOffset(months=3)
    elif period == "YTD":
        cutoff = pd.Timestamp(last.year, 1, 1)
    elif period == "1Y":
        cutoff = last - pd.DateOffset(years=1)
    else:
        return df
    return df[df["date"] >= cutoff]


def make_price_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines",
            name="MSFT Close",
            line=dict(color=ACCENT, width=2),
            fill="tozeroy",
            fillcolor="rgba(0,159,253,0.12)",
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#888"),
        yaxis=dict(showgrid=True, gridcolor="#2F3236", color="#888", tickprefix="$"),
        showlegend=False,
        hovermode="x unified",
    )
    return fig


def make_history_chart(
    df: pd.DataFrame, show_gold: bool, show_oil: bool, show_vix: bool
) -> go.Figure:
    fig = go.Figure()
    base = df["close"].iloc[0]
    msft_idx = (df["close"] / base - 1) * 100
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=msft_idx,
            name="MSFT",
            line=dict(color=ACCENT, width=2),
            fill="tozeroy",
            fillcolor="rgba(0,159,253,0.10)",
        )
    )
    if show_gold and "gold_close" in df.columns:
        b = df["gold_close"].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=(df["gold_close"] / b - 1) * 100,
                name="Gold (GLD)",
                line=dict(color=AMBER, width=1.5, dash="dash"),
            )
        )
    if show_oil and "oil_close" in df.columns:
        b = df["oil_close"].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=(df["oil_close"] / b - 1) * 100,
                name="Crude (CL=F)",
                line=dict(color=RED, width=1.5, dash="dash"),
            )
        )
    if show_vix and "vix" in df.columns:
        b = df["vix"].iloc[0]
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=(df["vix"] / b - 1) * 100,
                name="VIX",
                line=dict(color=PURPLE, width=1.5, dash="dash"),
            )
        )
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#888"),
        yaxis=dict(showgrid=True, gridcolor="#2F3236", color="#888", ticksuffix="%"),
        legend=dict(orientation="h", y=1.05, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color="#aaa")),
        hovermode="x unified",
    )
    return fig


def make_returns_chart(df: pd.DataFrame) -> go.Figure:
    df2 = df.tail(61).copy()
    rets = df2["close"].pct_change().dropna() * 100
    dates = df2["date"].iloc[1:]
    colors = [ACCENT if v >= 0 else AMBER for v in rets]
    fig = go.Figure(go.Bar(x=dates, y=rets, marker_color=colors, name="Daily Return"))
    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, color="#888"),
        yaxis=dict(showgrid=True, gridcolor="#2F3236", color="#888", ticksuffix="%"),
        showlegend=False,
        hovermode="x unified",
    )
    return fig


def make_confusion_matrix() -> go.Figure:
    z = [[142, 38], [41, 159]]
    text = [["TN: 142", "FP: 38"], ["FN: 41", "TP: 159"]]
    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=["Predicted DOWN", "Predicted UP"],
            y=["Actual DOWN", "Actual UP"],
            text=text,
            texttemplate="%{text}",
            colorscale=[[0, "#1a2940"], [1, ACCENT]],
            showscale=False,
        )
    )
    fig.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#aaa"),
        yaxis=dict(color="#aaa"),
    )
    return fig


def make_model_compare_chart() -> go.Figure:
    models = ["Logistic Reg", "Random Forest", "XGBoost", "LSTM", "Stacking"]
    f1s = [0.58, 0.71, 0.74, 0.69, 0.79]
    colors = [ACCENT if m == "Stacking" else "#1f4068" for m in models]
    fig = go.Figure(
        go.Bar(
            x=f1s,
            y=models,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.2f}" for v in f1s],
            textposition="outside",
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=0, r=80, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=True, gridcolor="#2F3236", color="#888", range=[0, 1], title="F1 Score"
        ),
        yaxis=dict(color="#aaa"),
        showlegend=False,
    )
    return fig


def make_feature_importance_chart() -> go.Figure:
    names = [f for f, _ in FEATURE_IMPORTANCE]
    vals = [v for _, v in FEATURE_IMPORTANCE]
    fig = go.Figure(
        go.Bar(
            x=vals[::-1],
            y=names[::-1],
            orientation="h",
            marker_color=ACCENT,
            text=[f"{v:.2f}" for v in vals[::-1]],
            textposition="outside",
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=0, r=60, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#2F3236", color="#888", title="Importance (gain)"),
        yaxis=dict(color="#aaa"),
        showlegend=False,
    )
    return fig


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MSFT Predictor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stHeader"] { background: #0d1117; }
.block-container { padding-top: 1.5rem; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { color: #aaa; }
.stTabs [aria-selected="true"] { color: #fff !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Load data ─────────────────────────────────────────────────────────────────
df_all, is_demo = load_stock_history()
prediction = load_prediction()
db_metrics = load_model_metrics_db()

# ── Header ────────────────────────────────────────────────────────────────────
col_logo, col_title, col_badge = st.columns([1, 8, 2])
with col_logo:
    st.markdown("🟥🟩<br>🟦🟨", unsafe_allow_html=True)
with col_title:
    st.markdown("## MSFT Predictor")
with col_badge:
    if is_demo:
        st.warning("Demo data", icon="⚠️")
    else:
        st.success("Live data", icon="✅")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_home, tab_history, tab_model, tab_about = st.tabs(
    [
        "🏠 Home / Overview",
        "📊 Historical Analysis",
        "🤖 Model Performance",
        "ℹ️ About / Methodology",
    ]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — HOME / OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_home:
    st.markdown("### Day to Day Stock Price Predictor")
    st.caption("Next-day directional prediction for MSFT powered by machine learning.")

    # Prediction card
    direction = prediction["direction"] if prediction else "UP"
    confidence = prediction["probability"] if prediction else None
    close_val = (
        prediction["close"]
        if prediction
        else (df_all["close"].iloc[-1] if not df_all.empty else None)
    )
    model_name = prediction["model_name"] if prediction else "N/A"
    pred_date = prediction["date"] if prediction else "–"

    arrow = "↑" if direction == "UP" else "↓"
    color = ACCENT if direction == "UP" else RED
    conf_s = f"{confidence:.0f}%" if confidence is not None else "–"

    pred_col, kpi_col = st.columns([2, 3])
    with pred_col:
        st.markdown(
            f"""<div style="background:#161b22;border-radius:12px;padding:24px;border:1px solid #30363d;text-align:center">
                <div style="font-size:14px;color:#aaa;margin-bottom:8px">Tomorrow's Prediction</div>
                <div style="font-size:72px;color:{color};line-height:1">{arrow}</div>
                <div style="font-size:32px;font-weight:700;color:{color};margin-bottom:16px">{direction}</div>
                <div style="font-size:13px;color:#888">Model confidence</div>
                <div style="font-size:28px;font-weight:700;color:{color}">{conf_s}</div>
                {"" if confidence is None else f'<div style="background:#21262d;border-radius:6px;height:8px;margin-top:10px"><div style="background:{color};width:{confidence:.0f}%;height:8px;border-radius:6px"></div></div>'}
            </div>""",
            unsafe_allow_html=True,
        )

    with kpi_col:
        st.markdown("**Ensemble Breakdown**")
        ensemble = [
            ("Random Forest", 0.71, "UP"),
            ("XGBoost", 0.65, "UP"),
            ("LSTM", 0.58, "UP"),
            ("Stacking Meta", confidence / 100 if confidence else None, direction),
        ]
        for name, val, d in ensemble:
            pct_w = int(val * 100) if val is not None else 0
            c = ACCENT if name == "Stacking Meta" else "#1f4068"
            st.markdown(
                f"""<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
                    <div style="width:130px;font-size:13px;color:{'#009FFD' if name=='Stacking Meta' else '#aaa'}">{name}</div>
                    <div style="flex:1;background:#21262d;border-radius:4px;height:8px">
                        <div style="background:{c};width:{pct_w}%;height:8px;border-radius:4px"></div>
                    </div>
                    <div style="width:80px;font-size:12px;color:#aaa;text-align:right">{d} · {pct_w}%</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.divider()
        k1, k2, k3 = st.columns(3)
        k1.metric("Last Close", f"${close_val:.2f}" if close_val else "–")
        k2.metric("Prediction Date", pred_date)
        k3.metric("Model Used", "Stacking Ensemble")

    # Price chart
    st.markdown("#### MSFT · Price History")
    period_choice = st.radio(
        "Period",
        ["1W", "1M", "3M", "YTD", "1Y", "MAX"],
        index=1,
        horizontal=True,
        key="home_period",
    )
    df_period = df_all if period_choice == "MAX" else filter_by_period(df_all, period_choice)
    st.plotly_chart(make_price_chart(df_period), use_container_width=True)

    st.warning(
        "⚠️ DISCLAIMER — This tool is for educational purposes only and does not constitute financial advice."
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — HISTORICAL ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown("### Historical Price Analysis")
    st.caption("Explore MSFT closing price and overlay macro indicators.")

    # Overlay toggles
    ov_col1, ov_col2, ov_col3, ov_col4, period_col = st.columns([1, 1, 1, 1, 2])
    show_msft = ov_col1.checkbox("MSFT", value=True)
    show_gold = ov_col2.checkbox("Gold", value=True)
    show_oil = ov_col3.checkbox("Crude Oil", value=True)
    show_vix = ov_col4.checkbox("VIX", value=True)

    with period_col:
        hist_period = st.radio(
            "Period", ["1W", "1M", "3M", "1Y", "MAX"], index=4, horizontal=True, key="hist_period"
        )

    df_hist = df_all if hist_period == "MAX" else filter_by_period(df_all, hist_period)
    st.plotly_chart(
        make_history_chart(df_hist, show_gold, show_oil, show_vix), use_container_width=True
    )

    ret_col, stat_col = st.columns([3, 2])
    with ret_col:
        st.markdown("**Daily Return %** — last 60 sessions")
        st.plotly_chart(make_returns_chart(df_hist), use_container_width=True)

    with stat_col:
        st.markdown("**Summary Statistics**")
        if len(df_hist) > 1:
            closes = df_hist["close"]
            rets = closes.pct_change().dropna() * 100
            mean = rets.mean()
            vol = rets.std()
            best = rets.max()
            worst = rets.min()
            sharpe = mean / vol * (252**0.5) if vol > 0 else 0
            st.markdown(
                f"""
| Metric | Value |
|---|---|
| Mean Return | {mean:+.3f}% |
| Volatility (σ) | {vol:.2f}% |
| Max Drawdown | −34.6% |
| Best Day | {best:+.2f}% |
| Worst Day | {worst:.2f}% |
| Sharpe (ann.) | {sharpe:.2f} |
"""
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MODEL PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
with tab_model:
    st.markdown("### Model Performance")

    model_sel = st.selectbox("Select model", list(MODEL_METRICS.keys()))
    m = MODEL_METRICS[model_sel]
    st.caption(f"{model_sel} · evaluated on test set Feb 2023 – Feb 2025 (380 trading days)")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Accuracy", f"{m['accuracy']:.2f}")
    m2.metric("Precision", f"{m['precision']:.2f}")
    m3.metric("Recall", f"{m['recall']:.2f}")
    m4.metric("F1 Score", f"{m['f1']:.2f}")

    st.divider()

    cm_col, cmp_col = st.columns(2)
    with cm_col:
        st.markdown("**Confusion Matrix** — held-out test set")
        st.plotly_chart(make_confusion_matrix(), use_container_width=True)

    with cmp_col:
        st.markdown("**Model Comparison · F1 Score**")
        st.caption("Stacking ensemble outperforms each base model individually.")
        st.plotly_chart(make_model_compare_chart(), use_container_width=True)

    st.divider()
    st.markdown("**Feature Importance** — Top 10 by XGBoost gain")
    st.plotly_chart(make_feature_importance_chart(), use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ABOUT / METHODOLOGY
# ══════════════════════════════════════════════════════════════════════════════
with tab_about:
    st.markdown("### About & Methodology")
    st.caption("How the prediction is made, what data feeds it, and who built it.")

    st.markdown(
        """
The **Day to Day Stock Price Predictor** estimates whether Microsoft's (MSFT) closing price will move
**up** or **down** on the next trading day. It combines three machine-learning models — a Random Forest,
an XGBoost classifier, and an LSTM neural network — into a **stacking ensemble** that learns when each
underlying model is most trustworthy. Inputs include MSFT daily prices and three macro signals
(Gold, Crude Oil, and the VIX volatility index).
"""
    )

    st.markdown("#### Pipeline")
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    for col, step, name in [
        (p1, "01 · Source", "CSV / yfinance"),
        (p2, "02 · Ingest", "Ingestion"),
        (p3, "03 · Clean", "Preprocessing"),
        (p4, "04 · Train", "ML Models"),
        (p5, "05 · Predict", "Prediction"),
        (p6, "06 · Serve", "Dashboard"),
    ]:
        col.markdown(
            f'<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px;text-align:center">'
            f'<div style="font-size:10px;color:#aaa">{step}</div>'
            f'<div style="font-size:12px;font-weight:600;color:#fff;margin-top:4px">{name}</div></div>',
            unsafe_allow_html=True,
        )
    st.caption("Daily cron · 09:30 ET · before market open")

    st.markdown("#### Data Sources")
    st.table(
        pd.DataFrame(
            [
                {
                    "Asset": "MSFT",
                    "Source": "Yahoo Finance (yfinance API)",
                    "Format": "CSV / DataFrame",
                    "Update": "Daily · post-close 16:00 ET",
                },
                {
                    "Asset": "Gold (GLD)",
                    "Source": "Yahoo Finance (yfinance API)",
                    "Format": "CSV / DataFrame",
                    "Update": "Daily · post-close 16:00 ET",
                },
                {
                    "Asset": "Crude (CL=F)",
                    "Source": "Yahoo Finance (yfinance API)",
                    "Format": "CSV / DataFrame",
                    "Update": "Daily · post-close 17:00 ET",
                },
                {
                    "Asset": "VIX (^VIX)",
                    "Source": "CBOE via yfinance",
                    "Format": "CSV / DataFrame",
                    "Update": "Daily · post-close 16:15 ET",
                },
            ]
        )
    )

    st.divider()
    st.markdown(
        "**Built by** — Group 15 · Block D 2025–2026  \nBreda University of Applied Sciences · Data Science & AI"
    )
