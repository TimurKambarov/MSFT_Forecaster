"""
MSFT Direction Predictor — Dashboard API Server
================================================
Flask backend serving the frontend dashboard and REST API endpoints.

Run:
    pip install flask flask-cors pandas numpy joblib scikit-learn xgboost
    cd frontend
    python server.py

Endpoints:
    GET /                        → dashboard
    GET /api/stock/history       → MSFT OHLCV (last ?days=90)
    GET /api/stock/latest        → meest recente MSFT datapunt
    GET /api/indicators/latest   → Gold, Oil, VIX (meest recent)
    GET /api/indicators/history  → Gold, Oil, VIX (laatste ?days=90)
    GET /api/prediction/latest   → UP/DOWN voorspelling + confidence
    GET /api/model/metrics       → model-prestaties (accuracy, F1, etc.)
"""

import os
import sqlite3
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent  # project root
DB_PATH = BASE_DIR / "db" / "stocks.db"
MODELS_DIR = BASE_DIR / "models" / "lucan"
STATIC_DIR = Path(__file__).parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

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


# ── Helpers ──────────────────────────────────────────────────────────────────


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_best_model():
    """Load the best available trained model + matching scaler."""
    for prefix in ("xgboost_lucan", "random_forest_lucan", "logistic_regression_lucan"):
        models = sorted(MODELS_DIR.glob(f"{prefix}*.pkl"))
        scalers = sorted(MODELS_DIR.glob("scaler_lucan*.pkl"))
        if models and scalers:
            try:
                model = joblib.load(models[-1])
                scaler = joblib.load(scalers[-1])
                name = models[-1].stem
                logger.info(f"Loaded model: {name}")
                return model, scaler, name
            except Exception as e:
                logger.warning(f"Could not load {prefix}: {e}")
    return None, None, None


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Wilder's RSI."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def build_features(conn, n_rows: int = 60) -> pd.DataFrame:
    """Merge the last n_rows of all tables and engineer features matching training."""
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


# ── Routes ───────────────────────────────────────────────────────────────────


@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(str(STATIC_DIR), filename)


@app.route("/api/stock/history")
def stock_history():
    days = request.args.get("days", 90, type=int)
    try:
        conn = get_conn()
        df = pd.read_sql(
            f"""
            SELECT m.date, m.open, m.high, m.low, m.close, m.volume,
                   g.gold_close, o.oil_close, v.vix
            FROM msft_daily m
            LEFT JOIN gold_prices g ON m.date = g.date
            LEFT JOIN oil_prices  o ON m.date = o.date
            LEFT JOIN vix_data    v ON m.date = v.date
            ORDER BY m.date DESC LIMIT {days}
        """,
            conn,
        ).sort_values("date")
        conn.close()
        return jsonify({"status": "ok", "data": df.to_dict(orient="records")})
    except Exception as e:
        logger.error(f"stock_history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stock/latest")
def stock_latest():
    try:
        conn = get_conn()
        row = conn.execute("SELECT * FROM msft_daily ORDER BY date DESC LIMIT 1").fetchone()
        conn.close()
        if row:
            return jsonify({"status": "ok", "data": dict(row)})
        return jsonify({"status": "error", "message": "Geen data gevonden"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/indicators/latest")
def indicators_latest():
    try:
        conn = get_conn()
        gold = conn.execute("SELECT * FROM gold_prices ORDER BY date DESC LIMIT 1").fetchone()
        oil = conn.execute("SELECT * FROM oil_prices ORDER BY date DESC LIMIT 1").fetchone()
        vix = conn.execute("SELECT * FROM vix_data ORDER BY date DESC LIMIT 1").fetchone()
        conn.close()
        return jsonify(
            {
                "status": "ok",
                "data": {
                    "gold": dict(gold) if gold else None,
                    "oil": dict(oil) if oil else None,
                    "vix": dict(vix) if vix else None,
                },
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/indicators/history")
def indicators_history():
    days = request.args.get("days", 90, type=int)
    try:
        conn = get_conn()
        gold = pd.read_sql(
            f"SELECT * FROM gold_prices ORDER BY date DESC LIMIT {days}", conn
        ).sort_values("date")
        oil = pd.read_sql(
            f"SELECT * FROM oil_prices ORDER BY date DESC LIMIT {days}", conn
        ).sort_values("date")
        vix = pd.read_sql(
            f"SELECT * FROM vix_data ORDER BY date DESC LIMIT {days}", conn
        ).sort_values("date")
        conn.close()
        return jsonify(
            {
                "status": "ok",
                "data": {
                    "gold": gold.to_dict(orient="records"),
                    "oil": oil.to_dict(orient="records"),
                    "vix": vix.to_dict(orient="records"),
                },
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/prediction/latest")
def prediction_latest():
    try:
        conn = get_conn()

        # Read from predictions table first (written by predict.py)
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
                return jsonify(
                    {
                        "status": "ok",
                        "data": {
                            "date": row["date"],
                            "direction": "UP" if row["predicted_direction"] == 1 else "DOWN",
                            "prediction": row["predicted_direction"],
                            "probability": round(row["confidence"] * 100, 1),
                            "close": row["close"],
                            "model_name": row["model_used"],
                        },
                    }
                )

        # Fallback: compute on-the-fly if predictions table is empty
        df = build_features(conn, n_rows=60)
        conn.close()

        if df.empty:
            return jsonify({"status": "error", "message": "Not enough data"}), 400

        model, scaler, model_name = load_best_model()
        if model is None:
            return (
                jsonify({"status": "model_unavailable", "message": "No trained model found."}),
                503,
            )

        X = scaler.transform(df[FEATURE_COLS].iloc[[-1]])
        pred = int(model.predict(X)[0])
        prob = float(model.predict_proba(X)[0][pred])

        return jsonify(
            {
                "status": "ok",
                "data": {
                    "date": str(df["date"].iloc[-1]),
                    "direction": "UP" if pred == 1 else "DOWN",
                    "prediction": pred,
                    "probability": round(prob * 100, 1),
                    "close": float(df["close"].iloc[-1]),
                    "model_name": model_name,
                },
            }
        )
    except Exception as e:
        logger.error("prediction_latest: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/model/metrics")
def model_metrics():
    """
    Retourneer opgeslagen model-metrics.
    Verbind de evaluatie-pipeline om dit te vullen met echte waarden.
    """
    try:
        conn = get_conn()
        tables = [
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        ]
        conn.close()

        metrics = []
        if "model_metrics" in tables:
            conn = get_conn()
            rows = pd.read_sql("SELECT * FROM model_metrics", conn)
            conn.close()
            metrics = rows.to_dict(orient="records")
        else:
            metrics = [
                {
                    "model": "XGBoost",
                    "accuracy": None,
                    "f1": None,
                    "precision": None,
                    "recall": None,
                },
                {
                    "model": "Random Forest",
                    "accuracy": None,
                    "f1": None,
                    "precision": None,
                    "recall": None,
                },
                {
                    "model": "Logistic Regression",
                    "accuracy": None,
                    "f1": None,
                    "precision": None,
                    "recall": None,
                },
            ]

        return jsonify({"status": "ok", "data": metrics})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n  Dashboard: http://localhost:5000")
    print(f"  Database:  {DB_PATH}\n")
    app.run(debug=True, port=5000, host="0.0.0.0")
