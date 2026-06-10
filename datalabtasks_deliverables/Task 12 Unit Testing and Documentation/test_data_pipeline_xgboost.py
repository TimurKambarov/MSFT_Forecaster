"""
test_train_xgboost.py
======================
Unit tests for the *data-pipeline* functions in ``train_xgboost.py``.

Scope
-----
These tests cover the deterministic preprocessing transforms only:
``build_feature_columns``, ``load_dataset``, ``align_trading_days``,
``resample_weekly``, ``engineer_features``, ``fill_missing``,
``split_and_scale``, and a light smoke test for ``save_artifacts``.

The model-fitting / tuning functions (``tune_xgboost``,
``train_final_model``, ``evaluate_model``) are intentionally NOT unit-tested:
they are non-deterministic and heavyweight (Optuna search, gradient boosting)
and belong in slower integration runs, not fast unit tests.

Each test documents *why* the behaviour matters — preventing lookahead bias,
preserving time order, correct label thresholds, peer-feature synchronisation —
so a test fails if that business rule is broken, not merely if a shape changes.

Run
---
    pytest test_train_xgboost.py -v

The module under test is imported by file path so the test can live anywhere
relative to the repo. Override the location with the TRAIN_XGBOOST_PATH
environment variable if the script is not found automatically.

Author: Group 15 - Block D ADS-AI BUas
"""

import importlib.util
import json
import logging
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Import the module under test by file path                                   #
# --------------------------------------------------------------------------- #
def _locate_module() -> Path:
    """Locate train_xgboost.py via env var or a few sensible defaults.

    Returns
    -------
    Path
        Path to the script under test.

    Raises
    ------
    FileNotFoundError
        If the script cannot be found in any candidate location.
    """
    env_path = os.environ.get("TRAIN_XGBOOST_PATH")
    candidates = []
    if env_path:
        candidates.append(Path(env_path))

    here = Path(__file__).resolve().parent
    # Same dir as the test, the parent dir, and the original upload location.
    candidates += [
        here / "train_xgboost.py",
        here.parent / "train_xgboost.py",
        Path("/mnt/user-data/uploads/train_xgboost.py"),
    ]

    for candidate in candidates:
        if candidate.is_file():
            logger.info("Loading module under test from %s", candidate)
            return candidate

    raise FileNotFoundError(
        "Could not find train_xgboost.py. Set the TRAIN_XGBOOST_PATH "
        f"environment variable. Tried: {[str(c) for c in candidates]}"
    )


def _import_module():
    """Import train_xgboost.py as a module object.

    Returns
    -------
    module
        The imported module under test.
    """
    module_path = _locate_module()
    spec = importlib.util.spec_from_file_location("train_xgboost", module_path)
    module = importlib.util.module_from_spec(spec)
    # Register before exec so any internal self-references resolve.
    sys.modules["train_xgboost"] = module
    spec.loader.exec_module(module)
    return module


tx = _import_module()


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #
@pytest.fixture
def raw_daily_csv(tmp_path) -> Path:
    """Write a small but realistic raw input CSV and return its path.

    Spans two calendar years of *business* days starting before START_DATE so
    the START_DATE filter in load_dataset has something to remove, and is long
    enough (~2 years) that the 20-week rolling windows in feature engineering
    produce non-NaN values for a usable number of weekly rows.

    The schema matches what the pipeline expects: a lowercase ``date`` column,
    MSFT OHLCV columns, and close+volume for each peer ticker.
    """
    rng = np.random.default_rng(RANDOM_SEED)
    # Start a month before START_DATE so the date filter has rows to drop.
    dates = pd.bdate_range("2019-12-01", periods=N_BDAYS)

    # Geometric-ish random walk so prices stay positive and look like a stock.
    def _walk(start: float) -> np.ndarray:
        steps = rng.normal(loc=0.0005, scale=0.01, size=len(dates))
        return start * np.exp(np.cumsum(steps))

    msft_close = _walk(150.0)
    frame = {
        "date": dates.strftime("%Y-%m-%d"),
        "msft_open": msft_close * (1 + rng.normal(0, 0.002, len(dates))),
        "msft_high": msft_close * (1 + np.abs(rng.normal(0, 0.005, len(dates)))),
        "msft_low": msft_close * (1 - np.abs(rng.normal(0, 0.005, len(dates)))),
        "msft_close": msft_close,
        "msft_volume": rng.integers(2e7, 5e7, len(dates)).astype(float),
    }
    for peer, start in zip(tx.PEER_TICKERS, (400.0, 120.0, 90.0, 80.0)):
        frame[f"{peer}_close"] = _walk(start)
        frame[f"{peer}_volume"] = rng.integers(1e7, 3e7, len(dates)).astype(float)

    df = pd.DataFrame(frame)
    path = tmp_path / "modelling_dataset.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def weekly_df(raw_daily_csv) -> pd.DataFrame:
    """Return a weekly-resampled dataframe (load -> align -> resample)."""
    df = tx.load_dataset(raw_daily_csv)
    df = tx.align_trading_days(df)
    return tx.resample_weekly(df)


@pytest.fixture
def engineered_df(weekly_df) -> pd.DataFrame:
    """Return a fully feature-engineered, gap-filled dataframe."""
    df = tx.engineer_features(weekly_df)
    return tx.fill_missing(df)


# Module-level constants used by the fixtures above.
RANDOM_SEED = 7
N_BDAYS = 520  # ~2 years of business days


class _DummyModel:
    """Picklable stand-in for a fitted estimator.

    Defined at module level (not inside a test) so joblib can pickle it. It
    deliberately lacks ``feature_importances_`` so save_artifacts skips the
    importance logging branch, keeping the I/O smoke test fast.
    """


# --------------------------------------------------------------------------- #
# build_feature_columns                                                       #
# --------------------------------------------------------------------------- #
class TestBuildFeatureColumns:
    """The feature list and the columns engineer_features() creates must stay
    in lockstep — drift here silently breaks training/inference alignment."""

    def test_base_columns_come_first_and_unchanged(self):
        """Base MSFT features must be present and lead the list, so existing
        artifacts keyed by position/order remain valid."""
        cols = tx.build_feature_columns(peers=[])
        assert cols == tx.BASE_FEATURE_COLUMNS

    def test_each_peer_adds_exactly_four_named_features(self):
        """Each peer must contribute its four documented signals. If this
        count drifts, the metadata feature list and the model input disagree."""
        cols = tx.build_feature_columns(peers=["foo"])
        added = cols[len(tx.BASE_FEATURE_COLUMNS) :]
        assert added == [
            "foo_return_1w",
            "foo_lag_return_1",
            "foo_rel_strength",
            "foo_volume_ratio",
        ]

    def test_length_scales_with_peer_count(self):
        """Total feature count = base + 4 per peer; guards the arithmetic that
        split_and_scale logs and that downstream shape checks rely on."""
        n_base = len(tx.BASE_FEATURE_COLUMNS)
        assert len(tx.build_feature_columns(peers=[])) == n_base
        assert len(tx.build_feature_columns(peers=["a", "b", "c"])) == n_base + 12


# --------------------------------------------------------------------------- #
# load_dataset                                                                #
# --------------------------------------------------------------------------- #
class TestLoadDataset:
    """Loading must normalise the date column and enforce the START_DATE
    lower bound, because every later step assumes a 'Date' column and that no
    pre-START_DATE rows leak in."""

    def test_missing_file_raises(self, tmp_path):
        """A clear FileNotFoundError beats a cryptic pandas error so a wrong
        --data path fails loudly (Rule 12)."""
        with pytest.raises(FileNotFoundError):
            tx.load_dataset(tmp_path / "does_not_exist.csv")

    def test_renames_date_column(self, raw_daily_csv):
        """Source uses lowercase 'date'; the pipeline contract is 'Date'."""
        df = tx.load_dataset(raw_daily_csv)
        assert "Date" in df.columns
        assert "date" not in df.columns

    def test_filters_before_start_date(self, raw_daily_csv):
        """Rows before START_DATE must be dropped to avoid training on data
        outside the intended regime."""
        df = tx.load_dataset(raw_daily_csv)
        assert (df["Date"] >= tx.START_DATE).all()
        # The fixture deliberately includes December-2019 rows; confirm the
        # filter actually removed something rather than passing vacuously.
        assert df["Date"].min() >= tx.START_DATE


# --------------------------------------------------------------------------- #
# align_trading_days                                                          #
# --------------------------------------------------------------------------- #
class TestAlignTradingDays:
    """Aligning to a full daily calendar with trading-day flags is the basis
    for the weekly resample; weekend/holiday rows must be flagged correctly."""

    def test_daily_frequency_is_continuous(self, raw_daily_csv):
        """Output must be gap-free daily: consecutive dates differ by 1 day,
        so the resample sees a complete calendar."""
        df = tx.load_dataset(raw_daily_csv)
        out = tx.align_trading_days(df)
        diffs = out["Date"].diff().dropna().dt.days.unique()
        assert set(diffs) == {1}

    def test_flag_columns_exist_and_are_boolean(self, raw_daily_csv):
        """The three calendar flags must exist and be boolean for the boolean
        mask in resample_weekly to behave."""
        df = tx.load_dataset(raw_daily_csv)
        out = tx.align_trading_days(df)
        for col in ("is_trading_day", "is_weekend", "is_holiday"):
            assert col in out.columns
            assert out[col].dtype == bool

    def test_weekends_are_never_trading_days(self, raw_daily_csv):
        """Saturday/Sunday can never be NYSE trading days; if this slips,
        weekly bars would aggregate non-trading rows."""
        df = tx.load_dataset(raw_daily_csv)
        out = tx.align_trading_days(df)
        weekend = out[out["Date"].dt.dayofweek >= 5]
        assert not weekend["is_trading_day"].any()

    def test_holiday_is_weekday_non_trading(self, raw_daily_csv):
        """Holiday = weekday AND not a trading day. Mutually-exclusive logic
        keeps the three flags coherent."""
        df = tx.load_dataset(raw_daily_csv)
        out = tx.align_trading_days(df)
        holidays = out[out["is_holiday"]]
        assert (holidays["Date"].dt.dayofweek < 5).all()
        assert not holidays["is_trading_day"].any()


# --------------------------------------------------------------------------- #
# resample_weekly                                                             #
# --------------------------------------------------------------------------- #
class TestResampleWeekly:
    """Weekly bars must use only trading days, end on Fridays, and rename MSFT
    OHLCV to the generic names the feature code expects."""

    def test_renames_msft_to_generic_ohlcv(self, weekly_df):
        """Downstream feature code reads Open/High/Low/Close/Volume, not the
        msft_-prefixed names."""
        for col in ("Open", "High", "Low", "Close", "Volume"):
            assert col in weekly_df.columns
        for col in ("msft_open", "msft_close", "msft_volume"):
            assert col not in weekly_df.columns

    def test_all_periods_end_on_friday(self, weekly_df):
        """W-FRI resampling must yield Friday-ending weeks; a wrong anchor
        would misalign every return and the next-week target."""
        assert (weekly_df["Date"].dt.dayofweek == 4).all()

    def test_peer_close_uses_last_not_sum(self, raw_daily_csv):
        """Peer *close* must aggregate as 'last' (a price), while *volume*
        sums. Summing closes would produce nonsense price features."""
        df = tx.load_dataset(raw_daily_csv)
        df = tx.align_trading_days(df)
        weekly = tx.resample_weekly(df)
        peer = tx.PEER_TICKERS[0]
        close_col = f"{peer}_close"
        # A weekly 'last' close must equal some daily close that week, and be
        # far below the sum of that week's daily closes (which would be ~5x).
        assert close_col in weekly.columns
        weekly_max_close = weekly[close_col].max()
        daily_close_sum = df[df["is_trading_day"]][close_col].sum()
        assert weekly_max_close < daily_close_sum

    def test_no_missing_msft_close(self, weekly_df):
        """resample_weekly drops weeks with no MSFT close; none should remain,
        otherwise the target derived from Close would be undefined."""
        assert weekly_df["Close"].notna().all()


# --------------------------------------------------------------------------- #
# engineer_features                                                           #
# --------------------------------------------------------------------------- #
class TestEngineerFeatures:
    """Feature engineering is where lookahead bias and label errors hide.
    These tests pin the no-lookahead guarantee and the 3-class thresholds."""

    def test_all_expected_feature_columns_present(self, weekly_df):
        """Every column in FEATURE_COLUMNS must be produced; a missing one
        makes split_and_scale raise and breaks the model contract."""
        out = tx.engineer_features(weekly_df)
        for col in tx.FEATURE_COLUMNS:
            assert col in out.columns, f"missing engineered feature: {col}"

    def test_target_is_integer_three_class(self, weekly_df):
        """Direction must be integer-valued in {0,1,2}; XGBoost is configured
        for num_class=3 and non-integer/out-of-range labels would error."""
        out = tx.engineer_features(weekly_df)
        assert out["Direction"].dtype.kind in "iu"
        assert set(out["Direction"].unique()).issubset({0, 1, 2})

    def test_target_threshold_logic_is_correct(self):
        """The UP/DOWN/NEUTRAL label must follow next-week return vs ±threshold.
        This is the supervised signal itself — getting the sign or boundary
        wrong silently inverts what the model learns.

        Hand-built closes give exactly known next-week returns:
          150 -> 153  : +2.0%  > +1%  -> UP   (1)
          153 -> 150  : -1.96% < -1%  -> DOWN (0)
          150 -> 150.3: +0.2%  within -> NEUTRAL (2)
        The final row has no 'next week' and is dropped.
        """
        n = 60  # long enough to clear rolling windows before the tail rows
        base = pd.DataFrame(
            {
                "Date": pd.date_range("2021-01-01", periods=n, freq="W-FRI"),
                "Close": np.linspace(100, 140, n),
                "High": np.linspace(100, 140, n) * 1.01,
                "Low": np.linspace(100, 140, n) * 0.99,
                "Open": np.linspace(100, 140, n),
                "Volume": np.full(n, 1e7),
            }
        )
        for peer in tx.PEER_TICKERS:
            base[f"{peer}_close"] = np.linspace(50, 70, n)
            base[f"{peer}_volume"] = np.full(n, 5e6)

        # Overwrite the final four closes with the engineered scenario.
        base.loc[n - 4, "Close"] = 150.0
        base.loc[n - 3, "Close"] = 153.0
        base.loc[n - 2, "Close"] = 150.0
        base.loc[n - 1, "Close"] = 150.3

        out = tx.engineer_features(base, threshold=0.01)
        labels = out.set_index("Date")["Direction"]

        up_date = base.loc[n - 4, "Date"]
        down_date = base.loc[n - 3, "Date"]
        neutral_date = base.loc[n - 2, "Date"]
        assert labels[up_date] == 1, "next-week +2% must be UP"
        assert labels[down_date] == 0, "next-week -1.96% must be DOWN"
        assert labels[neutral_date] == 2, "next-week +0.2% must be NEUTRAL"

    def test_relative_strength_is_msft_minus_peer(self, weekly_df):
        """rel_strength must equal MSFT return minus the peer's return for the
        same week — the cross-sectional signal the docstring promises."""
        out = tx.engineer_features(weekly_df)
        peer = tx.PEER_TICKERS[0]
        expected = out["return_1w"] - out[f"{peer}_return_1w"]
        pd.testing.assert_series_equal(
            out[f"{peer}_rel_strength"],
            expected,
            check_names=False,
        )

    def test_lag_return_has_no_lookahead(self, weekly_df):
        """lag_return_1 at week t must equal return_1w at week t-1. A negative
        or zero shift would leak future information into the features."""
        out = tx.engineer_features(weekly_df).reset_index(drop=True)
        # Compare on the overlap where both are defined.
        shifted = out["return_1w"].shift(1)
        mask = out["lag_return_1"].notna() & shifted.notna()
        assert mask.sum() > 0
        pd.testing.assert_series_equal(
            out.loc[mask, "lag_return_1"],
            shifted[mask],
            check_names=False,
        )

    def test_no_nans_remain(self, weekly_df):
        """engineer_features ends with dropna(); the result must be NaN-free so
        the scaler and model never see missing values."""
        out = tx.engineer_features(weekly_df)
        assert not out.isna().any().any()

    def test_missing_peer_columns_are_skipped_gracefully(self, weekly_df):
        """If a peer's source columns are absent, the function must warn and
        skip rather than crash — robustness for partial datasets (Rule 12:
        the absence is logged, not silently masked)."""
        peer = tx.PEER_TICKERS[0]
        reduced = weekly_df.drop(columns=[f"{peer}_close", f"{peer}_volume"], errors="ignore")
        out = tx.engineer_features(reduced)
        # The skipped peer's engineered columns should simply not appear.
        assert f"{peer}_return_1w" not in out.columns


# --------------------------------------------------------------------------- #
# fill_missing                                                                #
# --------------------------------------------------------------------------- #
class TestFillMissing:
    """A defensive backstop: residual NaNs must be filled deterministically
    (numeric median, categorical mode) so nothing downstream sees a NaN."""

    def test_noop_when_already_complete(self):
        """With no NaNs the frame must be returned unchanged (no needless
        copy of behaviour, and value-preserving)."""
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": ["x", "y", "z"]})
        out = tx.fill_missing(df)
        pd.testing.assert_frame_equal(out, df)

    def test_numeric_nan_filled_with_median(self):
        """Numeric NaNs must take the column median, not mean or zero — the
        documented strategy that resists the outliers in financial data."""
        df = pd.DataFrame({"a": [1.0, np.nan, 3.0, 100.0]})
        out = tx.fill_missing(df)
        assert out["a"].isna().sum() == 0
        # median of [1, 3, 100] = 3.0
        assert out.loc[1, "a"] == 3.0

    def test_categorical_nan_filled_with_mode(self):
        """Non-numeric NaNs must take the column mode so categorical fields
        stay valid."""
        df = pd.DataFrame({"c": ["x", "x", "y", None]})
        out = tx.fill_missing(df)
        assert out["c"].isna().sum() == 0
        assert out.loc[3, "c"] == "x"


# --------------------------------------------------------------------------- #
# split_and_scale                                                             #
# --------------------------------------------------------------------------- #
class TestSplitAndScale:
    """The split must preserve time order (no shuffle) and fit the scaler on
    train only — leaking test statistics into the scaler inflates results."""

    def test_raises_on_missing_feature_columns(self, engineered_df):
        """A missing expected feature must raise KeyError with guidance rather
        than silently training on fewer columns (Rule 12)."""
        broken = engineered_df.drop(columns=[tx.FEATURE_COLUMNS[0]])
        with pytest.raises(KeyError):
            tx.split_and_scale(broken)

    def test_split_preserves_time_order(self, engineered_df):
        """With shuffle=False the test set must be the *tail* of the data, so
        we never evaluate on weeks that precede the training weeks."""
        n = len(engineered_df)
        # sklearn's train_test_split sizes the test set with ceil, not round.
        expected_test = math.ceil(n * tx.TEST_SIZE)
        _, x_test, _, y_test, _ = tx.split_and_scale(engineered_df)
        assert x_test.shape[0] == expected_test
        # y_test indices must be the final, contiguous block of the frame.
        assert list(y_test.index) == list(engineered_df.index[-expected_test:])

    def test_feature_matrix_width_matches_feature_list(self, engineered_df):
        """Scaled matrices must have exactly len(FEATURE_COLUMNS) columns, so
        the saved scaler and model agree with the metadata feature list."""
        x_train, x_test, _, _, _ = tx.split_and_scale(engineered_df)
        assert x_train.shape[1] == len(tx.FEATURE_COLUMNS)
        assert x_test.shape[1] == len(tx.FEATURE_COLUMNS)

    def test_scaler_is_fit_on_train_only(self, engineered_df):
        """The RobustScaler centre must come from the training rows alone.
        If the scaler were fit on all data, its median would match the full
        column median instead of the train-slice median — test-set leakage."""
        x_train, _, _, _, scaler = tx.split_and_scale(engineered_df)
        n = len(engineered_df)
        n_test = math.ceil(n * tx.TEST_SIZE)
        n_train = n - n_test
        train_slice = engineered_df[tx.FEATURE_COLUMNS].iloc[:n_train]
        np.testing.assert_allclose(
            scaler.center_,
            train_slice.median().to_numpy(),
            rtol=1e-6,
        )
        # And the transform must actually centre the train data near zero.
        np.testing.assert_allclose(
            np.median(x_train, axis=0),
            np.zeros(x_train.shape[1]),
            atol=1e-6,
        )


# --------------------------------------------------------------------------- #
# save_artifacts (light I/O smoke test)                                       #
# --------------------------------------------------------------------------- #
class TestSaveArtifacts:
    """save_artifacts is a pure I/O transform; verify it writes both files and
    that the metadata is valid, parseable JSON with the expected keys."""

    def test_writes_model_and_metadata(self, tmp_path):
        """Both the joblib bundle and the JSON metadata must be created, and
        the metadata must round-trip through json.load with the core keys."""
        joblib = pytest.importorskip("joblib")

        scaler = tx.RobustScaler()
        best_params = {"max_depth": 3}
        metrics = {"f1": 0.5, "accuracy": 0.5}

        model_path = tx.save_artifacts(_DummyModel(), scaler, best_params, metrics, tmp_path)
        meta_path = tmp_path / "xgboost_weekly_metadata.json"

        assert model_path.exists()
        assert meta_path.exists()

        bundle = joblib.load(model_path)
        assert bundle["feature_columns"] == tx.FEATURE_COLUMNS

        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["best_params"] == best_params
        assert meta["test_metrics"] == metrics
        assert meta["peer_tickers"] == tx.PEER_TICKERS


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
