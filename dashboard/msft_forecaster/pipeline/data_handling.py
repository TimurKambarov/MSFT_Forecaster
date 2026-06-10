"""data_handling.py
=================
Data layer for the weekly MSFT direction-prediction project.

This module contains *everything related to working with the data*: loading
the merged multi-stock dataset, aligning it to the NYSE trading calendar,
resampling daily bars to weekly bars, engineering scale-invariant features
(including peer-stock indicators), filling residual missing values, and
producing a time-ordered, scaled train/test split.

It is deliberately kept separate from the model-training code (which lives in
``model_training_notebook_<student_number>.ipynb``). Every function here is a
small, deterministic, side-effect-free transformation (input ``DataFrame`` ->
output ``DataFrame``/arrays) so that the module is straightforward to cover
with unit tests. Configuration values (peer tickers, thresholds, feature
lists, ...) are exposed both as module-level defaults *and* as function
arguments, so tests can override them without monkey-patching globals.

The feature contract mirrors the three sibling training scripts
(Random Forest, XGBoost, LSTM) so the model types are compared on identical
inputs.

Author: Group 15 - Block D ADS-AI BUas
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Configuration defaults (overridable per function call for testing)          #
# --------------------------------------------------------------------------- #
START_DATE: str = "2020-01-01"
NEUTRAL_THRESHOLD: float = 0.01  # +/-1% weekly move is labelled NEUTRAL
TEST_SIZE: float = 0.15
RANDOM_STATE: int = 42

# MSFT carries full OHLCV; every other ticker is close + volume.
MSFT_AGG = {
    "msft_open": "first",
    "msft_high": "max",
    "msft_low": "min",
    "msft_close": "last",
    "msft_volume": "sum",
}

# Peer / micro-indicator tickers. Each has ``<ticker>_close`` and
# ``<ticker>_volume`` in the merged dataset and is turned into four
# scale-invariant features by :func:`engineer_features`.
PEER_TICKERS = ["nvda", "amzn"]

# Base MSFT-derived features. Peer features are appended at runtime by
# :func:`build_feature_columns` so the two lists stay in sync automatically.
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

TARGET_COLUMN = "Direction"

# Human-readable class names indexed by the integer label.
CLASS_NAMES = {0: "DOWN", 1: "UP", 2: "NEUTRAL"}


# --------------------------------------------------------------------------- #
# Feature bookkeeping                                                         #
# --------------------------------------------------------------------------- #
def build_feature_columns(
    peers: Optional[list[str]] = None,
    base: Optional[list[str]] = None,
) -> list[str]:
    """Return the full ordered feature list: base features plus peer features.

    For every peer ticker, :func:`engineer_features` creates four columns:
    ``<ticker>_return_1w`` (its own weekly return), ``<ticker>_lag_return_1``
    (that return shifted one week), ``<ticker>_rel_strength`` (MSFT's weekly
    return minus the peer's -- a co-movement signal), and
    ``<ticker>_volume_ratio`` (weekly volume vs its 20-week average).

    Parameters
    ----------
    peers : list of str, optional
        Peer ticker prefixes. Defaults to :data:`PEER_TICKERS`.
    base : list of str, optional
        Base MSFT feature names. Defaults to :data:`BASE_FEATURE_COLUMNS`.

    Returns
    -------
    list of str
        Ordered feature-column names used for training and inference.
    """
    peers = PEER_TICKERS if peers is None else peers
    base = BASE_FEATURE_COLUMNS if base is None else base

    cols = list(base)
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


# --------------------------------------------------------------------------- #
# Loading                                                                     #
# --------------------------------------------------------------------------- #
def load_dataset(
    data_path: Path | str,
    start_date: str = START_DATE,
) -> pd.DataFrame:
    """Load the merged modelling dataset and standardise the date column.

    Parameters
    ----------
    data_path : Path or str
        Path to the merged multi-stock CSV (one row per date).
    start_date : str
        ISO date string; rows strictly before this date are dropped. This
        keeps the history aligned with the rest of the pipeline.

    Returns
    -------
    pandas.DataFrame
        Raw dataframe filtered to ``start_date`` onward, with a ``Date``
        column.

    Raises
    ------
    FileNotFoundError
        If ``data_path`` does not exist.
    """
    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)

    # Accept either 'date' or 'Date' from upstream and normalise to 'Date'.
    if "date" in df.columns:
        df = df.rename(columns={"date": "Date"})
    if "Date" not in df.columns:
        raise KeyError(f"No date column found. Columns present: {list(df.columns)}")

    df = df[df["Date"] >= start_date]
    logger.info("Loaded %d rows from %s (>= %s)", len(df), data_path, start_date)
    return df


# --------------------------------------------------------------------------- #
# Calendar alignment                                                          #
# --------------------------------------------------------------------------- #
def align_trading_days(
    df: pd.DataFrame,
    calendar_name: str = "NYSE",
) -> pd.DataFrame:
    """Reindex to a full daily calendar, forward-fill, and flag trading days.

    The raw feed only contains trading days. We expand to a complete daily
    range, forward-fill prices across gaps, and add boolean flags so the
    weekly resampler can ignore non-trading days.

    Parameters
    ----------
    df : pandas.DataFrame
        Raw dataframe with a ``Date`` column.
    calendar_name : str
        Name of the exchange calendar understood by
        ``pandas_market_calendars`` (default ``"NYSE"``).

    Returns
    -------
    pandas.DataFrame
        Daily-frequency dataframe with ``is_trading_day`` / ``is_weekend`` /
        ``is_holiday`` flags. Non-trading values are forward-filled.
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    df = df.sort_values("Date")

    calendar = mcal.get_calendar(calendar_name)
    full_range = pd.date_range(df["Date"].min(), df["Date"].max(), freq="D")

    trading_days = calendar.valid_days(
        start_date=full_range.min(),
        end_date=full_range.max(),
    )
    # Drop tz/time information so the membership test below is exact.
    trading_days = pd.DatetimeIndex(trading_days.date)

    df = df.set_index("Date").reindex(full_range)
    df.index.name = "Date"
    df = df.sort_index().ffill()

    df["is_trading_day"] = df.index.isin(trading_days)
    df["is_weekend"] = df.index.dayofweek >= 5
    df["is_holiday"] = (~df["is_trading_day"]) & (~df["is_weekend"])

    df = df.reset_index()
    logger.info("Aligned to %s calendar: %d daily rows", calendar_name, len(df))
    return df


# --------------------------------------------------------------------------- #
# Weekly resampling                                                           #
# --------------------------------------------------------------------------- #
def resample_weekly(
    df: pd.DataFrame,
    msft_agg: Optional[dict] = None,
) -> pd.DataFrame:
    """Resample daily bars into weekly (week-ending-Friday) bars.

    MSFT keeps full OHLCV; every other ticker gets summed volume and last
    close. MSFT columns are renamed to plain OHLCV afterwards so that feature
    engineering can stay generic.

    Parameters
    ----------
    df : pandas.DataFrame
        Daily dataframe produced by :func:`align_trading_days`.
    msft_agg : dict, optional
        Mapping of MSFT OHLCV columns to aggregation functions. Defaults to
        :data:`MSFT_AGG`.

    Returns
    -------
    pandas.DataFrame
        Weekly dataframe with ``Open, High, Low, Close, Volume`` (MSFT) plus
        any peer tickers' weekly columns.
    """
    msft_agg = dict(MSFT_AGG if msft_agg is None else msft_agg)

    daily = df.set_index("Date")
    trading_only = daily[daily["is_trading_day"]]

    # Build the aggregation map: MSFT OHLCV as specified, every other numeric
    # column summed if it is a volume series, otherwise carried as last value.
    agg = dict(msft_agg)
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


# --------------------------------------------------------------------------- #
# Technical-indicator helpers (small + individually testable)                 #
# --------------------------------------------------------------------------- #
def compute_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index using Wilder's exponential smoothing.

    Values above ~70 indicate overbought conditions and below ~30 oversold.

    Parameters
    ----------
    close : pandas.Series
        Close-price series.
    window : int
        Look-back period (default 14).

    Returns
    -------
    pandas.Series
        RSI values in the range [0, 100].
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    return 100 - (100 / (1 + avg_gain / avg_loss))


def compute_macd(
    close: pd.Series,
    span_fast: int = 12,
    span_slow: int = 26,
    span_signal: int = 9,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Moving Average Convergence Divergence (MACD) on a price series.

    Parameters
    ----------
    close : pandas.Series
        Close-price series.
    span_fast, span_slow, span_signal : int
        EMA spans for the fast line, slow line, and signal line.

    Returns
    -------
    tuple of pandas.Series
        ``(macd, macd_signal, macd_hist)`` where ``macd_hist`` is
        ``macd - macd_signal`` (positive values are bullish).
    """
    ema_fast = close.ewm(span=span_fast, adjust=False).mean()
    ema_slow = close.ewm(span=span_slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=span_signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist


# --------------------------------------------------------------------------- #
# Feature engineering + target                                                #
# --------------------------------------------------------------------------- #
def engineer_features(
    df: pd.DataFrame,
    peers: Optional[list[str]] = None,
    threshold: float = NEUTRAL_THRESHOLD,
) -> pd.DataFrame:
    """Engineer scale-invariant weekly features and the 3-class target.

    All features use only data available at the close of week ``t``, which
    prevents lookahead bias into week ``t+1``. The target is the direction of
    the *following* week's close relative to this week's:
    ``0 = DOWN``, ``1 = UP``, ``2 = NEUTRAL`` (move within +/- ``threshold``).

    Raw price levels are non-stationary and are deliberately NOT used as
    features; everything is expressed as a return, ratio, or oscillator.

    Parameters
    ----------
    df : pandas.DataFrame
        Weekly dataframe with ``Date, Open, High, Low, Close, Volume`` and any
        ``<peer>_close`` / ``<peer>_volume`` columns.
    peers : list of str, optional
        Peer ticker prefixes. Defaults to :data:`PEER_TICKERS`.
    threshold : float
        Neutral-zone half-width as a fraction (default ``0.01`` = 1%).

    Returns
    -------
    pandas.DataFrame
        Feature-engineered dataframe with an integer ``Direction`` target.
        Rows containing NaNs (warm-up periods, final unlabelled week) are
        dropped.
    """
    peers = PEER_TICKERS if peers is None else peers

    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # --- MSFT momentum: fractional changes over 1/4/8 weeks (scale-free) ---
    df["return_1w"] = close.pct_change(1) * 100
    df["return_4w"] = close.pct_change(4) * 100
    df["return_8w"] = close.pct_change(8) * 100

    # Lagged weekly returns (last week and two weeks ago).
    df["lag_return_1"] = df["return_1w"].shift(1)
    df["lag_return_2"] = df["return_1w"].shift(2)

    # --- MSFT oscillators ---
    df["rsi_14"] = compute_rsi(close, window=14)
    df["macd"], df["macd_signal"], df["macd_hist"] = compute_macd(close)

    # --- MSFT volatility + volume ---
    df["price_range_pct"] = (high - low) / close * 100
    df["rolling_std_5"] = close.rolling(5).std()
    df["volume_ratio"] = volume / volume.rolling(20).mean()

    # --- Peer / micro-indicator features ---
    # Each peer contributes scale-invariant signals built ONLY from data
    # available at the close of week t, so there is no lookahead into t+1.
    msft_return_1w = df["return_1w"]
    for peer in peers:
        close_col = f"{peer}_close"
        volume_col = f"{peer}_volume"

        if close_col not in df.columns:
            logger.warning("Peer close column missing, skipping: %s", close_col)
            continue

        peer_close = df[close_col]

        # Peer's own weekly return (scale-invariant momentum).
        df[f"{peer}_return_1w"] = peer_close.pct_change(1) * 100
        # Last week's peer return -- usable to predict MSFT next week.
        df[f"{peer}_lag_return_1"] = df[f"{peer}_return_1w"].shift(1)
        # Relative strength: MSFT return minus peer return this week. Captures
        # whether MSFT is leading or lagging the wider tech complex.
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

    # --- 3-class target for NEXT week ---
    next_return = (close.shift(-1) - close) / close * 100
    threshold_pct = threshold * 100
    direction = np.where(
        next_return > threshold_pct,
        1,  # UP
        np.where(next_return < -threshold_pct, 0, 2),  # DOWN else NEUTRAL
    )
    # The final week has no t+1, so next_return is NaN. A plain np.where would
    # let NaN fall through to the NEUTRAL branch and fabricate a label; mark it
    # NaN explicitly so the dropna below removes the genuinely unlabelled week.
    direction = np.where(next_return.isna(), np.nan, direction)
    df[TARGET_COLUMN] = direction

    # Drop the final unlabelled week, cast the target, drop warm-up NaNs.
    df = df.dropna(subset=[TARGET_COLUMN]).copy()
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)
    df = df.dropna()

    counts = df[TARGET_COLUMN].value_counts().sort_index()
    logger.info(
        "Target balance - DOWN(0): %d | UP(1): %d | NEUTRAL(2): %d",
        counts.get(0, 0),
        counts.get(1, 0),
        counts.get(2, 0),
    )
    return df


# --------------------------------------------------------------------------- #
# Missing-value handling                                                      #
# --------------------------------------------------------------------------- #
def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill any residual missing values (numeric median, categorical mode).

    After feature engineering and the ``dropna`` inside it, the frame should
    usually be complete; this is a defensive final pass so downstream model
    fitting never receives NaNs.

    Parameters
    ----------
    df : pandas.DataFrame
        Feature-engineered dataframe.

    Returns
    -------
    pandas.DataFrame
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


# --------------------------------------------------------------------------- #
# Train/test split + scaling                                                  #
# --------------------------------------------------------------------------- #
def split_and_scale(
    df: pd.DataFrame,
    feature_columns: Optional[list[str]] = None,
    target_col: str = TARGET_COLUMN,
    test_size: float = TEST_SIZE,
    scaler: Optional[object] = None,
) -> Tuple[np.ndarray, np.ndarray, pd.Series, pd.Series, object]:
    """Time-ordered split (no shuffle) and fit a scaler on the train set only.

    The split preserves chronological order (``shuffle=False``) so the test
    set is strictly in the future relative to training -- the realistic setup
    for forecasting. The scaler is fit on training data only, then applied to
    the test data, to avoid leaking test statistics.

    Parameters
    ----------
    df : pandas.DataFrame
        Fully preprocessed dataframe containing the feature columns and the
        target.
    feature_columns : list of str, optional
        Columns to use as model inputs. Defaults to
        :func:`build_feature_columns`.
    target_col : str
        Name of the target column (default ``"Direction"``).
    test_size : float
        Fraction of rows reserved for the (chronologically last) test set.
    scaler : estimator, optional
        A fresh scaler implementing ``fit_transform`` / ``transform``. Passing
        one in is convenient for testing; defaults to a new
        :class:`~sklearn.preprocessing.RobustScaler`.

    Returns
    -------
    tuple
        ``(X_train_scaled, X_test_scaled, y_train, y_test, scaler)``.

    Raises
    ------
    KeyError
        If any expected feature column is absent from ``df``.
    """
    feature_columns = build_feature_columns() if feature_columns is None else feature_columns

    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise KeyError(
            f"Expected feature columns are missing from the dataframe: "
            f"{missing}. Check that every peer ticker has a <ticker>_close "
            f"column in the source dataset."
        )

    X = df[feature_columns]
    y = df[target_col]
    logger.info("Training matrix: %d rows x %d features", *X.shape)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=False  # preserve time order
    )

    scaler = RobustScaler() if scaler is None else scaler
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logger.info(
        "Split - train: %d samples | test: %d samples",
        X_train_scaled.shape[0],
        X_test_scaled.shape[0],
    )
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler


# --------------------------------------------------------------------------- #
# Orchestration (load -> align -> resample -> engineer -> fill)               #
# --------------------------------------------------------------------------- #
def preprocess(
    data_path: Path | str,
    peers: Optional[list[str]] = None,
    threshold: float = NEUTRAL_THRESHOLD,
    start_date: str = START_DATE,
    calendar_name: str = "NYSE",
) -> pd.DataFrame:
    """Run the full data pipeline up to (but not including) the split.

    Convenience wrapper chaining :func:`load_dataset`,
    :func:`align_trading_days`, :func:`resample_weekly`,
    :func:`engineer_features`, and :func:`fill_missing`. Returns a single
    analysis-ready weekly dataframe. Kept as one call so the notebook (and
    integration tests) can obtain the modelling frame in one line.

    Parameters
    ----------
    data_path : Path or str
        Path to the merged modelling dataset CSV.
    peers : list of str, optional
        Peer ticker prefixes. Defaults to :data:`PEER_TICKERS`.
    threshold : float
        Neutral-zone half-width as a fraction (default 1%).
    start_date : str
        Earliest date to keep.
    calendar_name : str
        Exchange calendar name for trading-day alignment.

    Returns
    -------
    pandas.DataFrame
        Weekly, feature-engineered, gap-free modelling frame with the
        ``Direction`` target.
    """
    df = load_dataset(data_path, start_date=start_date)
    df = align_trading_days(df, calendar_name=calendar_name)
    df = resample_weekly(df)
    df = engineer_features(df, peers=peers, threshold=threshold)
    df = fill_missing(df)
    logger.info("Preprocessing complete: %d weekly rows ready.", len(df))
    return df
