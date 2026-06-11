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
MODEL_PATH = (
    Path(__file__).parent / "msft_forecaster" / "pipeline" / "models" / "xgboost_weekly.joblib"
)
STATIC_DIR = Path(__file__).parent / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


@app.after_request
def no_cache(response):
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


FEATURE_COLS = [
    "return_1w",
    "return_4w",
    "return_8w",
    "lag_return_1",
    "lag_return_2",
    "rsi_14",
    "macd",
    "macd_signal",
    "macd_hist",
    "price_range_pct",
    "rolling_std_5",
    "volume_ratio",
    "nvda_return_1w",
    "nvda_lag_return_1",
    "nvda_rel_strength",
    "nvda_volume_ratio",
    "amzn_return_1w",
    "amzn_lag_return_1",
    "amzn_rel_strength",
    "amzn_volume_ratio",
]

PEER_TICKERS = ["nvda", "amzn"]

DIRECTION_LABELS = {0: "DOWN", 1: "UP", 2: "SAME"}


# ── Helpers ──────────────────────────────────────────────────────────────────


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_model():
    """Load Timur's XGBoost weekly bundle (model + scaler + feature list)."""
    try:
        bundle = joblib.load(MODEL_PATH)
        logger.info("Loaded model: xgboost_weekly")
        return bundle["model"], bundle["scaler"], bundle["feature_columns"], "xgboost_weekly"
    except Exception as e:
        logger.error("Could not load model from %s: %s", MODEL_PATH, e)
        return None, None, None, None


def _rsi_weekly(series: pd.Series) -> pd.Series:
    """RSI using Wilder's EWM smoothing (com=13, min_periods=14)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, min_periods=14).mean()
    avg_loss = loss.ewm(com=13, min_periods=14).mean()
    return 100 - (100 / (1 + avg_gain / avg_loss))


def build_weekly_features(conn, n_daily_rows: int = 400) -> pd.DataFrame:
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
            logger.warning("Peer features unavailable for %s: %s — using defaults", peer, e)
            weekly[f"{peer}_return_1w"] = 0.0
            weekly[f"{peer}_lag_return_1"] = 0.0
            weekly[f"{peer}_rel_strength"] = 0.0
            weekly[f"{peer}_volume_ratio"] = 1.0

    return weekly.dropna().reset_index()


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
                   g.gold_close, o.oil_close, v.vix,
                   n.nvda_close, a.amzn_close
            FROM msft_daily m
            LEFT JOIN gold_prices g ON m.date = g.date
            LEFT JOIN oil_prices  o ON m.date = o.date
            LEFT JOIN vix_data    v ON m.date = v.date
            LEFT JOIN nvda_daily  n ON m.date = n.date
            LEFT JOIN amzn_daily  a ON m.date = a.date
            ORDER BY m.date DESC LIMIT {days}
        """,
            conn,
        ).sort_values("date")
        conn.close()
        import json as _json

        return app.response_class(
            _json.dumps({"status": "ok", "data": _json.loads(df.to_json(orient="records"))}),
            mimetype="application/json",
        )
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
                "SELECT p.*, (SELECT close FROM msft_daily ORDER BY date DESC LIMIT 1) as close "
                "FROM predictions p "
                "ORDER BY p.date DESC LIMIT 1"
            ).fetchone()
            if row:
                conn.close()
                return jsonify(
                    {
                        "status": "ok",
                        "data": {
                            "date": row["date"],
                            "direction": DIRECTION_LABELS.get(
                                row["predicted_direction"], str(row["predicted_direction"])
                            ),
                            "prediction": row["predicted_direction"],
                            "probability": round(row["confidence"] * 100, 1),
                            "close": row["close"],
                            "model_name": row["model_used"],
                        },
                    }
                )

        # Fallback: compute on-the-fly if predictions table is empty
        df = build_weekly_features(conn)
        conn.close()

        if df.empty:
            return jsonify({"status": "error", "message": "Not enough data"}), 400

        model, scaler, feature_cols, model_name = load_model()
        if model is None:
            return (
                jsonify(
                    {
                        "status": "model_unavailable",
                        "message": "No trained model found.",
                    }
                ),
                503,
            )

        X = scaler.transform(df[feature_cols].iloc[[-1]])
        pred = int(model.predict(X)[0])
        prob = float(model.predict_proba(X)[0][pred])

        return jsonify(
            {
                "status": "ok",
                "data": {
                    "date": str(df["date"].iloc[-1].date()),
                    "direction": DIRECTION_LABELS.get(pred, str(pred)),
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


@app.route("/api/prediction/history")
def prediction_history():
    import hashlib, json as _json
    from datetime import timedelta

    n = request.args.get("n", 10, type=int)
    try:
        conn = get_conn()

        # Resample daily MSFT to weekly (W-FRI) — same as model training
        msft_daily = pd.read_sql(
            "SELECT date, close FROM msft_daily ORDER BY date DESC LIMIT 400",
            conn,
        ).sort_values("date")
        msft_daily["date"] = pd.to_datetime(msft_daily["date"])
        weekly = (
            msft_daily.set_index("date")
            .resample("W-FRI")
            .last()
            .dropna()
            .reset_index()
            .rename(columns={"date": "week_end"})
        )
        # Only include completed weeks (week_end in the past)
        today = pd.Timestamp.today().normalize()
        weekly = weekly[weekly["week_end"] < today].reset_index(drop=True)

        try:
            real_preds = pd.read_sql(
                "SELECT date, predicted_direction, confidence FROM predictions ORDER BY date DESC",
                conn,
            )
        except Exception:
            real_preds = pd.DataFrame(columns=["date", "predicted_direction", "confidence"])
        conn.close()

        # Dummy pattern: results in ~40% accuracy; fixed per week via hash
        _dummy_pattern = [0, 1, 0, 1, 1, 0, 1, 0, 2, 1]

        rows = []
        for i in range(1, len(weekly)):
            row = weekly.iloc[i]
            prev = weekly.iloc[i - 1]
            actual = 1 if row["close"] > prev["close"] else 0

            week_end = row["week_end"]
            monday = week_end - timedelta(days=4)
            week_num = int(week_end.isocalendar()[1])
            date_str = week_end.strftime("%Y-%m-%d")
            display = f"{monday.strftime('%Y-%m-%d')} · W{week_num:02d}"

            match = real_preds[real_preds["date"] == date_str]
            if len(match):
                pred_dir = int(match.iloc[0]["predicted_direction"])
                conf = float(match.iloc[0]["confidence"])
                is_dummy = False
            else:
                seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
                pred_dir = _dummy_pattern[seed % 10]
                conf = 0.52 + (seed % 16) / 100
                is_dummy = True

            correct = None if pred_dir == 2 else bool(pred_dir == actual)

            rows.append(
                {
                    "date": display,
                    "predicted_direction": pred_dir,
                    "confidence": round(conf * 100, 1),
                    "actual_direction": actual,
                    "correct": correct,
                    "close": round(float(row["close"]), 2),
                    "is_dummy": is_dummy,
                }
            )

        rows = list(reversed(rows[-n:]))

        # Accuracy only from verified real predictions (not dummies)
        real_decided = [r for r in rows if not r["is_dummy"] and r["correct"] is not None]
        accuracy = (
            round(sum(1 for r in real_decided if r["correct"]) / len(real_decided) * 100, 1)
            if real_decided
            else None
        )
        has_dummy = any(r["is_dummy"] for r in rows)

        return app.response_class(
            _json.dumps(
                {
                    "status": "ok",
                    "data": rows,
                    "accuracy": accuracy,
                    "has_dummy": has_dummy,
                }
            ),
            mimetype="application/json",
        )
    except Exception as e:
        logger.error("prediction_history: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n  Dashboard: http://localhost:5000")
    print(f"  Database:  {DB_PATH}\n")
    app.run(debug=True, port=5000, host="0.0.0.0")
