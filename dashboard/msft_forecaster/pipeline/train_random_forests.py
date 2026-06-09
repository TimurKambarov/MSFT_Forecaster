"""
train_random_forest.py
======================
Train the tuned Random Forest model for weekly MSFT direction prediction.

This script reproduces the exact preprocessing pipeline from the weekly model
training notebook, then trains ONLY the Random Forest classifier — selected
because its Optuna-tuned version yielded the best results among the candidate
models (Random Forest, XGBoost, LSTM, ARIMA).

Pipeline
--------
1. Load the merged multi-stock dataset.
2. Filter to 2020-01-01 onward and align to NYSE trading days.
3. Resample daily bars into weekly (week-ending-Friday) bars.
4. Engineer scale-invariant weekly features and the 3-class target.
5. Handle missing values, time-order split (no shuffle), RobustScaler.
6. Tune Random Forest hyper-parameters with Optuna (TimeSeriesSplit CV).
7. Refit the best model on the full training split and evaluate on the test set.
8. Save the fitted model, the scaler, the feature list, and the best params.

Usage
-----
    python train_random_forest.py
    python train_random_forest.py --data path/to/modelling_dataset.csv \\
        --n-trials 40 --output-dir models

Author: Group 15 — Block D ADS-AI BUas
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.preprocessing import RobustScaler

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Quieten Optuna's per-trial chatter; the script logs its own summary.
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

FEATURE_COLUMNS = [
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
    X = df[FEATURE_COLUMNS]
    y = df["Direction"]

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


# optuna tuning
import numpy as np
import pandas as pd
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score


def tune_random_forest(
    X_train_scaled: np.ndarray,
    y_train: pd.Series,
    n_trials: int,
) -> tuple:

    tscv = TimeSeriesSplit(n_splits=N_SPLITS)
    # Get all unique classes globally to protect small time windows
    global_classes = np.unique(y_train)

    def rf_objective(trial: optuna.Trial) -> float:
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 32),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 10),
            "class_weight": "balanced",
            "random_state": RANDOM_STATE,
            "n_jobs": -1,  # Speed up Random Forest training
        }

        scores = []

        # Enumerate to track the fold step index for pruning
        for step, (train_idx, val_idx) in enumerate(tscv.split(X_train_scaled)):
            model = RandomForestClassifier(**params)
            model.fit(X_train_scaled[train_idx], y_train.iloc[train_idx])
            preds = model.predict(X_train_scaled[val_idx])

            # CRUCIAL: Pass 'labels' to handle missing classes in early time slices
            fold_f1 = f1_score(y_train.iloc[val_idx], preds, average="macro", labels=global_classes)
            scores.append(fold_f1)

            # OPTIONAL: Report intermediate running mean macro-F1 to Optuna
            running_mean = np.mean(scores)
            trial.report(running_mean, step=step)

            # Handle pruning (stop trial early if results are terrible)
            if trial.should_prune():
                raise optuna.TrialPruned()

        return float(np.mean(scores))

    # Add a pruner to the study to leverage the trial.report() steps
    study = optuna.create_study(
        direction="maximize", pruner=optuna.pruners.MedianPruner(n_startup_trials=5)
    )
    study.optimize(rf_objective, n_trials=n_trials)

    logger.info("Best CV macro-F1: %.4f", study.best_value)
    logger.info("Best params: %s", study.best_params)
    return study.best_params, study.best_value


# ── Train, evaluate, save ─────────────────────────────────────────────────────
def train_final_model(
    best_params: dict,
    X_train_scaled: np.ndarray,
    y_train: pd.Series,
) -> RandomForestClassifier:
    """Refit a Random Forest with the tuned params on the full training split.

    Parameters
    ----------
    best_params : dict
        Hyper-parameters from :func:`tune_random_forest`.
    X_train_scaled : np.ndarray
        Scaled training features.
    y_train : pd.Series
        Training labels.

    Returns
    -------
    RandomForestClassifier
        Fitted model.
    """
    model = RandomForestClassifier(
        **best_params,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )
    model.fit(X_train_scaled, y_train)
    logger.info("Final Random Forest refit on full training split.")
    return model


def evaluate_model(
    model: RandomForestClassifier,
    X_test_scaled: np.ndarray,
    y_test: pd.Series,
) -> dict:
    """Evaluate the model on the held-out test set.

    Parameters
    ----------
    model : RandomForestClassifier
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
    pred = model.predict(X_test_scaled)
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
    return metrics


def save_artifacts(
    model: RandomForestClassifier,
    scaler: RobustScaler,
    best_params: dict,
    metrics: dict,
    output_dir: Path,
) -> Path:
    """Persist the model, scaler, feature list, and metadata.

    Parameters
    ----------
    model : RandomForestClassifier
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
        Path to the saved model file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "random_forest_weekly.joblib"
    scaler_path = output_dir / "robust_scaler.joblib"
    meta_path = output_dir / "random_forest_weekly_metadata.json"

    # Bundle model + scaler + feature order together for safe inference.
    joblib.dump(
        {
            "model": model,
            "scaler": scaler,
            "feature_columns": FEATURE_COLUMNS,
        },
        model_path,
    )
    joblib.dump(scaler, scaler_path)

    metadata = {
        "model_type": "RandomForestClassifier",
        "prediction": "weekly MSFT direction (0=DOWN, 1=UP, 2=NEUTRAL)",
        "neutral_threshold": NEUTRAL_THRESHOLD,
        "feature_columns": FEATURE_COLUMNS,
        "best_params": best_params,
        "test_metrics": metrics,
    }
    with meta_path.open("w", encoding="utf-8") as fh:
        json.dump(metadata, fh, indent=2)

    logger.info("Saved model   -> %s", model_path)
    logger.info("Saved scaler  -> %s", scaler_path)
    logger.info("Saved metadata-> %s", meta_path)
    return model_path


# ── Orchestration ─────────────────────────────────────────────────────────────
def run_pipeline(data_path: Path, output_dir: Path, n_trials: int) -> None:
    """Run the full load → preprocess → tune → train → evaluate → save pipeline.

    Parameters
    ----------
    data_path : Path
        Path to the merged modelling dataset.
    output_dir : Path
        Directory for saved artifacts.
    n_trials : int
        Number of Optuna trials.
    """
    df = load_dataset(data_path)
    df = align_trading_days(df)
    df = resample_weekly(df)
    df = engineer_features(df)
    df = fill_missing(df)

    X_train_scaled, X_test_scaled, y_train, y_test, scaler = split_and_scale(df)

    best_params, _ = tune_random_forest(X_train_scaled, y_train, n_trials)
    model = train_final_model(best_params, X_train_scaled, y_train)
    metrics = evaluate_model(model, X_test_scaled, y_test)
    save_artifacts(model, scaler, best_params, metrics, output_dir)
    logger.info("Done.")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Train the tuned Random Forest for weekly MSFT direction."
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
    parser.add_argument(
        "--n-trials",
        type=int,
        default=40,
        help="Number of Optuna trials",
    )
    return parser.parse_args()


def main() -> None:
    """Script entry point."""
    args = parse_args()
    run_pipeline(args.data, args.output_dir, args.n_trials)


if __name__ == "__main__":
    main()
