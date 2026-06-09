"""
train_xgboost.py
================
Train the tuned XGBoost model for weekly MSFT direction prediction.

This script reproduces the EXACT preprocessing pipeline used by
train_random_forests.py (load -> align -> weekly resample -> feature
engineering with peer-stock indicators -> split/scale), then trains and
tunes ONLY an XGBoost classifier. It is one of three sibling scripts
(Random Forest, XGBoost, LSTM) that share identical preprocessing so the
three model types are compared on the same footing.

Peer-stock features
-------------------
On top of the 12 MSFT base features, each peer ticker in PEER_TICKERS adds
four scale-invariant features (own return, lagged return, relative strength
vs MSFT, volume ratio). Edit PEER_TICKERS to add or remove peers; the feature
list, model, and saved artifacts all follow automatically.

Usage
-----
    python train_xgboost.py
    python train_xgboost.py --data path/to/modelling_dataset.csv \\
        --n-trials 40 --output-dir models

Author: Group 15 - Block D ADS-AI BUas
"""

import argparse
import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import optuna
import pandas_market_calendars as mcal
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.preprocessing import RobustScaler
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

# -- Logging -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

optuna.logging.set_verbosity(optuna.logging.WARNING)

# ── Constants (mirrors the notebook) ──────────────────────────────────────────
DEFAULT_DATA_PATH = Path("../../../dashboard/data/processed/modelling_dataset.csv")
DEFAULT_OUTPUT_DIR = Path("models")

START_DATE = "2020-01-01"
NEUTRAL_THRESHOLD = 0.01  # ±1% weekly move is labelled NEUTRAL
TEST_SIZE = 0.15
N_SPLITS = 3
RANDOM_STATE = 42

# MSFT carries full OHLCV; every other ticker is close + volume.
MSFT_AGG = {
    "msft_open": "first",
    "msft_high": "max",
    "msft_low": "min",
    "msft_close": "last",
    "msft_volume": "sum",
}

# Peer / micro-indicator tickers (each has <ticker>_close and <ticker>_volume).
# These sit alongside MSFT in the merged dataset and are turned into
# scale-invariant features in engineer_features().
PEER_TICKERS = ["nvda", "amzn"]

# Base MSFT-derived features. Peer features are appended at runtime by
# build_feature_columns() so the two stay in sync automatically.
BASE_FEATURE_COLUMNS = [
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
]


def build_feature_columns(peers=PEER_TICKERS):
    """Return the full feature list: MSFT base features plus peer features.

    For every peer ticker, engineer_features() creates four columns:
    ``<ticker>_return_1w`` (its own weekly return), ``<ticker>_lag_return_1``
    (that return shifted one week), ``<ticker>_rel_strength`` (MSFT's weekly
    return minus the peer's — a cross-sectional co-movement signal), and
    ``<ticker>_volume_ratio`` (weekly volume vs its 20-week average).

    Parameters
    ----------
    peers : list[str]
        Peer ticker prefixes.

    Returns
    -------
    list[str]
        Ordered feature-column names used for training and inference.
    """
    cols = list(BASE_FEATURE_COLUMNS)
    for peer in peers:
        cols.extend(
            [
                f"{peer}_return_1w",
                f"{peer}_lag_return_1",
                f"{peer}_rel_strength",
                f"{peer}_volume_ratio",
            ]
        )
    return cols


# Concrete feature list used throughout the script.
FEATURE_COLUMNS = build_feature_columns()


# ── Data loading & preprocessing ──────────────────────────────────────────────
def load_dataset(data_path: Path) -> pd.DataFrame:
    """Load the merged modelling dataset and standardise the date column.

    Parameters
    ----------
    data_path : Path
        Path to the merged multi-stock CSV (one row per date).

    Returns
    -------
    pd.DataFrame
        Raw dataframe filtered to START_DATE onward, with a 'Date' column.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    df = df.rename(columns={"date": "Date"})
    df = df[df["Date"] >= START_DATE]
    logger.info("Loaded %d rows from %s (>= %s)", len(df), data_path, START_DATE)
    return df


def align_trading_days(df: pd.DataFrame) -> pd.DataFrame:
    """Reindex to a full daily calendar, forward-fill, and flag trading days.

    Parameters
    ----------
    df : pd.DataFrame
        Raw dataframe with a 'Date' column.

    Returns
    -------
    pd.DataFrame
        Daily-frequency dataframe with is_trading_day / is_weekend /
        is_holiday flags. Non-trading values are forward-filled.
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    df = df.sort_values("Date")

    calendar = mcal.get_calendar("NYSE")
    full_range = pd.date_range(df["Date"].min(), df["Date"].max(), freq="D")

    trading_days = calendar.valid_days(
        start_date=full_range.min(),
        end_date=full_range.max(),
    )
    trading_days = pd.DatetimeIndex(trading_days.date)  # date-only, no tz

    df = df.set_index("Date").reindex(full_range)
    df.index.name = "Date"
    df = df.sort_index().ffill()

    df["is_trading_day"] = df.index.isin(trading_days)
    df["is_weekend"] = df.index.dayofweek >= 5
    df["is_holiday"] = (~df["is_trading_day"]) & (~df["is_weekend"])

    df = df.reset_index()
    logger.info("Aligned to NYSE calendar: %d daily rows", len(df))
    return df


def resample_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Resample daily bars into weekly (week-ending-Friday) bars.

    MSFT keeps full OHLCV; other tickers get summed volume and last close.
    MSFT columns are renamed to plain OHLCV so feature engineering is generic.

    Parameters
    ----------
    df : pd.DataFrame
        Daily dataframe produced by :func:`align_trading_days`.

    Returns
    -------
    pd.DataFrame
        Weekly dataframe with Open, High, Low, Close, Volume (MSFT) plus any
        other tickers' weekly columns.
    """
    daily = df.set_index("Date")
    trading_only = daily[daily["is_trading_day"]]

    agg = dict(MSFT_AGG)
    ohlcv_cols = set(agg)
    extra_cols = [
        c for c in trading_only.select_dtypes(include="number").columns if c not in ohlcv_cols
    ]
    for col in extra_cols:
        agg[col] = "sum" if col.endswith("_volume") else "last"

    weekly = trading_only.resample("W-FRI").agg(agg)
    weekly = weekly.dropna(subset=["msft_close"]).reset_index()

    weekly = weekly.rename(
        columns={
            "msft_open": "Open",
            "msft_high": "High",
            "msft_low": "Low",
            "msft_close": "Close",
            "msft_volume": "Volume",
        }
    )
    logger.info(
        "Resampled to %d weekly bars (%s to %s)",
        len(weekly),
        weekly["Date"].min().date(),
        weekly["Date"].max().date(),
    )
    return weekly


def engineer_features(df: pd.DataFrame, threshold: float = NEUTRAL_THRESHOLD) -> pd.DataFrame:
    """Engineer scale-invariant weekly features and the 3-class target.

    All features use only data available at the close of week t, preventing
    lookahead bias into week t+1. The target is the direction of the following
    week's close relative to this week's.

    Parameters
    ----------
    df : pd.DataFrame
        Weekly dataframe with Date, Open, High, Low, Close, Volume columns.
    threshold : float
        Neutral-zone threshold for target creation (default 1%).

    Returns
    -------
    pd.DataFrame
        Feature-engineered dataframe with an integer 'Direction' target
        (0 = DOWN, 1 = UP, 2 = NEUTRAL). Rows with NaNs are dropped.
    """
    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Fractional changes over 1, 4 and 8 weeks (scale-invariant)
    df["return_1w"] = close.pct_change(1) * 100
    df["return_4w"] = close.pct_change(4) * 100
    df["return_8w"] = close.pct_change(8) * 100

    # Lagged weekly returns (last week and two weeks ago)
    df["lag_return_1"] = df["return_1w"].shift(1)
    df["lag_return_2"] = df["return_1w"].shift(2)

    # RSI(14 weeks): overbought/oversold oscillator
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, min_periods=14).mean()
    avg_loss = loss.ewm(com=13, min_periods=14).mean()
    df["rsi_14"] = 100 - (100 / (1 + avg_gain / avg_loss))

    # MACD on weekly closes: trend-following momentum oscillator
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]  # > 0 = bullish

    # Volatility
    df["price_range_pct"] = (high - low) / close * 100
    df["rolling_std_5"] = close.rolling(5).std()  # 5-week rolling std

    # Volume signal (vs 20-week average)
    df["volume_ratio"] = volume / volume.rolling(20).mean()

    # --- Peer / micro-indicator features (ASML, NVDA, AMD, AMZN, CRM, PLTR) ---
    # Each peer contributes scale-invariant signals built ONLY from data
    # available at the close of week t, so there is no lookahead into t+1.
    # Raw price levels are non-stationary and are deliberately NOT used.
    msft_return_1w = df["return_1w"]
    for peer in PEER_TICKERS:
        close_col = f"{peer}_close"
        volume_col = f"{peer}_volume"

        if close_col not in df.columns:
            logger.warning("Peer close column missing, skipping: %s", close_col)
            continue

        peer_close = df[close_col]

        # Peer's own weekly return (scale-invariant momentum).
        df[f"{peer}_return_1w"] = peer_close.pct_change(1) * 100
        # Last week's peer return — usable to predict MSFT's next week.
        df[f"{peer}_lag_return_1"] = df[f"{peer}_return_1w"].shift(1)
        # Relative strength: MSFT return minus peer return this week.
        # Captures whether MSFT is leading or lagging the tech complex.
        df[f"{peer}_rel_strength"] = msft_return_1w - df[f"{peer}_return_1w"]

        # Peer volume pressure vs its own 20-week average.
        if volume_col in df.columns:
            peer_volume = df[volume_col]
            df[f"{peer}_volume_ratio"] = peer_volume / peer_volume.rolling(20).mean()
        else:
            logger.warning(
                "Peer volume column missing, filling ratio with 1.0: %s",
                volume_col,
            )
            df[f"{peer}_volume_ratio"] = 1.0

    # 3-class target: UP (1), DOWN (0), NEUTRAL (2) for NEXT week
    next_return = (close.shift(-1) - close) / close * 100
    threshold_pct = threshold * 100
    df["Direction"] = np.where(
        next_return > threshold_pct,
        1,
        np.where(next_return < -threshold_pct, 0, 2),
    )

    df = df.dropna(subset=["Direction"]).copy()
    df["Direction"] = df["Direction"].astype(int)
    df = df.dropna()

    counts = df["Direction"].value_counts().sort_index()
    logger.info(
        "Target balance — DOWN(0): %d | UP(1): %d | NEUTRAL(2): %d",
        counts.get(0, 0),
        counts.get(1, 0),
        counts.get(2, 0),
    )
    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill any residual missing values (numeric median, categorical mode).

    Parameters
    ----------
    df : pd.DataFrame
        Feature-engineered dataframe.

    Returns
    -------
    pd.DataFrame
        Dataframe with no missing values.
    """
    missing_total = int(df.isna().sum().sum())
    logger.info("Total missing values: %d", missing_total)
    if missing_total == 0:
        return df

    df = df.copy()
    numeric_cols = df.select_dtypes(include="number").columns
    non_numeric_cols = df.columns.difference(numeric_cols)
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    for col in non_numeric_cols:
        mode_value = df[col].mode(dropna=True)
        if not mode_value.empty:
            df[col] = df[col].fillna(mode_value.iloc[0])
    logger.info("Missing values filled.")
    return df


def split_and_scale(df: pd.DataFrame):
    """Time-order split (no shuffle) and fit a RobustScaler on the train set.

    Parameters
    ----------
    df : pd.DataFrame
        Fully preprocessed dataframe containing FEATURE_COLUMNS and 'Direction'.

    Returns
    -------
    tuple
        (X_train_scaled, X_test_scaled, y_train, y_test, scaler).
    """
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(
            f"Expected feature columns are missing from the dataframe: {missing}. "
            "Check that every peer ticker in PEER_TICKERS has a <ticker>_close "
            "column in the source dataset."
        )

    X = df[FEATURE_COLUMNS]
    y = df["Direction"]
    logger.info(
        "Training on %d features (%d peer-derived).",
        len(FEATURE_COLUMNS),
        len(FEATURE_COLUMNS) - len(BASE_FEATURE_COLUMNS),
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, shuffle=False  # preserve time order
    )

    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info(
        "Split — train: %d samples | test: %d samples",
        X_train_scaled.shape[0],
        X_test_scaled.shape[0],
    )
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler


# -- Tuning --------------------------------------------------------------------
def tune_xgboost(X_train_scaled, y_train, n_trials):
    """Tune XGBoost hyper-parameters with Optuna and TimeSeriesSplit CV.

    Class imbalance is handled with per-sample weights (XGBoost has no
    ``class_weight`` argument), computed as "balanced" on each training fold.
    The optimisation target is mean macro-F1 across folds, with ``labels``
    pinned to the global class set so early time slices missing a class do
    not distort the score.

    Parameters
    ----------
    X_train_scaled : np.ndarray
        Scaled training features.
    y_train : pd.Series
        Training labels.
    n_trials : int
        Number of Optuna trials.

    Returns
    -------
    tuple
        (best_params, best_cv_macro_f1).
    """
    tscv = TimeSeriesSplit(n_splits=N_SPLITS)
    global_classes = np.unique(y_train)

    def xgb_objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 500),
            "max_depth": trial.suggest_int("max_depth", 2, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "objective": "multi:softmax",
            "num_class": 3,
            "eval_metric": "mlogloss",
            "random_state": RANDOM_STATE,
            "n_jobs": -1,
        }

        scores = []
        for step, (train_idx, val_idx) in enumerate(tscv.split(X_train_scaled)):
            y_fold = y_train.iloc[train_idx]
            sample_weight = compute_sample_weight("balanced", y_fold)
            model = XGBClassifier(**params)
            model.fit(
                X_train_scaled[train_idx],
                y_fold,
                sample_weight=sample_weight,
            )
            preds = model.predict(X_train_scaled[val_idx]).astype(int)
            fold_f1 = f1_score(y_train.iloc[val_idx], preds, average="macro", labels=global_classes)
            scores.append(fold_f1)
            trial.report(float(np.mean(scores)), step=step)
            if trial.should_prune():
                raise optuna.TrialPruned()
        return float(np.mean(scores))

    study = optuna.create_study(
        direction="maximize", pruner=optuna.pruners.MedianPruner(n_startup_trials=5)
    )
    study.optimize(xgb_objective, n_trials=n_trials)

    logger.info("Best CV macro-F1: %.4f", study.best_value)
    logger.info("Best params: %s", study.best_params)
    return study.best_params, study.best_value


# -- Train, evaluate, save -----------------------------------------------------
def train_final_model(best_params, X_train_scaled, y_train):
    """Refit XGBoost with tuned params on the full training split.

    Parameters
    ----------
    best_params : dict
        Hyper-parameters from :func:`tune_xgboost`.
    X_train_scaled : np.ndarray
        Scaled training features.
    y_train : pd.Series
        Training labels.

    Returns
    -------
    XGBClassifier
        Fitted model.
    """
    sample_weight = compute_sample_weight("balanced", y_train)
    model = XGBClassifier(
        **best_params,
        objective="multi:softmax",
        num_class=3,
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train, sample_weight=sample_weight)
    logger.info("Final XGBoost refit on full training split.")
    return model


def evaluate_model(model, X_test_scaled, y_test):
    """Evaluate the model on the held-out test set (macro-averaged metrics).

    Parameters
    ----------
    model : XGBClassifier
        Fitted model.
    X_test_scaled : np.ndarray
        Scaled test features.
    y_test : pd.Series
        Test labels.

    Returns
    -------
    dict
        Macro-averaged f1, accuracy, precision, and recall.
    """
    pred = model.predict(X_test_scaled).astype(int)
    metrics = {
        "f1": f1_score(y_test, pred, average="macro"),
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, average="macro", zero_division=0),
        "recall": recall_score(y_test, pred, average="macro"),
    }
    report = classification_report(
        y_test,
        pred,
        target_names=["DOWN", "UP", "NEUTRAL"],
        labels=[0, 1, 2],
        zero_division=0,
    )
    logger.info("Test-set performance:\n%s", report)
    logger.info("Test macro-F1: %.4f | accuracy: %.4f", metrics["f1"], metrics["accuracy"])

    if hasattr(model, "feature_importances_"):
        importances = pd.Series(model.feature_importances_, index=FEATURE_COLUMNS).sort_values(
            ascending=False
        )
        logger.info("Top 15 feature importances:\n%s", importances.head(15).to_string())
        peer_cols = [c for c in FEATURE_COLUMNS if c not in BASE_FEATURE_COLUMNS]
        logger.info(
            "Peer features account for %.1f%% of total importance.",
            100 * importances[peer_cols].sum(),
        )
    return metrics


def save_artifacts(model, scaler, best_params, metrics, output_dir):
    """Persist the model, scaler, feature list, and metadata.

    Parameters
    ----------
    model : XGBClassifier
        Fitted model.
    scaler : RobustScaler
        Scaler fitted on the training data.
    best_params : dict
        Tuned hyper-parameters.
    metrics : dict
        Test-set metrics.
    output_dir : Path
        Directory to write artifacts to (created if missing).

    Returns
    -------
    Path
        Path to the saved model bundle.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "xgboost_weekly.joblib"
    meta_path = output_dir / "xgboost_weekly_metadata.json"

    joblib.dump(
        {"model": model, "scaler": scaler, "feature_columns": FEATURE_COLUMNS},
        model_path,
    )

    metadata = {
        "model_type": "XGBClassifier",
        "prediction": "weekly MSFT direction (0=DOWN, 1=UP, 2=NEUTRAL)",
        "neutral_threshold": NEUTRAL_THRESHOLD,
        "peer_tickers": PEER_TICKERS,
        "feature_columns": FEATURE_COLUMNS,
        "best_params": best_params,
        "test_metrics": metrics,
    }
    with meta_path.open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    logger.info("Saved model   -> %s", model_path)
    logger.info("Saved metadata-> %s", meta_path)
    return model_path


# -- Orchestration -------------------------------------------------------------
def run_pipeline(data_path, output_dir, n_trials):
    """Run load -> preprocess -> tune -> train -> evaluate -> save."""
    df = load_dataset(data_path)
    df = align_trading_days(df)
    df = resample_weekly(df)
    df = engineer_features(df)
    df = fill_missing(df)

    X_train_scaled, X_test_scaled, y_train, y_test, scaler = split_and_scale(df)

    best_params, _ = tune_xgboost(X_train_scaled, y_train, n_trials)
    model = train_final_model(best_params, X_train_scaled, y_train)
    metrics = evaluate_model(model, X_test_scaled, y_test)
    save_artifacts(model, scaler, best_params, metrics, output_dir)
    logger.info("Done.")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train the tuned XGBoost for weekly MSFT direction."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Path to the merged modelling dataset CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save the model and artifacts.",
    )
    parser.add_argument("--n-trials", type=int, default=50, help="Number of Optuna trials")
    return parser.parse_args()


def main():
    """Script entry point."""
    args = parse_args()
    run_pipeline(args.data, args.output_dir, args.n_trials)


if __name__ == "__main__":
    main()
