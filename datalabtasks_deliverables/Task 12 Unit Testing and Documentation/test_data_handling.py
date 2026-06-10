"""test_data_handling.py
=======================
Unit tests for the project's data layer (``data_handling.py``).

Run with::

    pytest test_data_handling.py -v

Design notes
------------
* Tests do **not** depend on the real ``modelling_dataset.csv``. Each test
  builds its own small, deterministic synthetic fixture, so the suite is fast,
  reproducible, and runnable anywhere.
* Pure-logic functions (``build_feature_columns``, ``compute_rsi``,
  ``compute_macd``, ``engineer_features``, ``fill_missing``,
  ``split_and_scale``) get focused unit tests.
* Functions that touch the filesystem or the real NYSE exchange calendar
  (``load_dataset``, ``align_trading_days``, ``resample_weekly``,
  ``preprocess``) are exercised by tests marked ``integration`` -- still fast,
  but flagged because they cross a boundary.
"""

import logging
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler


def _ensure_importable(module_filename: str = "data_handling.py") -> None:
    """Put the folder containing ``data_handling.py`` on ``sys.path``.

    This lets the test file live in a different directory from the module it
    tests (e.g. a dedicated ``tests/`` folder). It searches this file's own
    directory and its ancestors up to the repository root (the nearest folder
    containing ``.git``), then falls back to a bounded recursive search under
    that root. Raises ImportError if the module cannot be found.
    """
    start = Path(__file__).resolve().parent

    # Repository root = nearest ancestor with a .git folder (bounds the search
    # so we never scan the whole filesystem).
    repo_root = next(
        (p for p in (start, *start.parents) if (p / ".git").exists()),
        start,
    )

    # 1) Cheap check: the test's own directory and each ancestor up to the root.
    for parent in (start, *start.parents):
        if (parent / module_filename).exists():
            sys.path.insert(0, str(parent))
            return
        if parent == repo_root:
            break

    # 2) Fallback: bounded recursive search under the repository root.
    match = next(repo_root.rglob(module_filename), None)
    if match is not None:
        sys.path.insert(0, str(match.parent))
        return

    raise ImportError(
        f"Could not locate {module_filename} under {repo_root}. "
        "Place it in the repo, or add its folder to sys.path / a conftest.py."
    )


_ensure_importable()

import data_handling as dh  # noqa: E402  (import after sys.path setup)


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #
@pytest.fixture
def raw_daily_df() -> pd.DataFrame:
    """A synthetic *raw* daily frame with the merged-dataset schema.

    Mirrors what ``load_dataset`` expects: a lowercase ``date`` column plus
    ``msft_*`` OHLCV columns and ``<peer>_close`` / ``<peer>_volume`` columns.
    Spans ~1.5 years of business days so weekly resampling leaves enough rows
    for the longest look-back (20-week volume average).
    """
    rng = np.random.default_rng(0)
    dates = pd.bdate_range("2020-01-02", periods=400)
    n = len(dates)
    close = 100 + np.cumsum(rng.normal(0, 1, n))
    close = np.abs(close) + 10  # keep strictly positive
    frame = pd.DataFrame(
        {
            "date": dates.strftime("%Y-%m-%d"),
            "msft_open": close + rng.normal(0, 0.5, n),
            "msft_high": close + np.abs(rng.normal(0, 1, n)),
            "msft_low": close - np.abs(rng.normal(0, 1, n)),
            "msft_close": close,
            "msft_volume": rng.integers(1_000, 5_000, n).astype(float),
            "nvda_close": close * 0.4 + rng.normal(0, 1, n),
            "nvda_volume": rng.integers(2_000, 6_000, n).astype(float),
            "amzn_close": close * 0.9 + rng.normal(0, 1, n),
            "amzn_volume": rng.integers(1_500, 4_500, n).astype(float),
        }
    )
    return frame


@pytest.fixture
def weekly_df() -> pd.DataFrame:
    """A synthetic *weekly* frame ready for ``engineer_features``.

    Has the renamed MSFT OHLCV columns plus peer close/volume columns, and
    enough weeks (60) that feature warm-up periods still leave usable rows.
    The close path mixes up, down, and flat moves so all three target classes
    can appear.
    """
    rng = np.random.default_rng(1)
    dates = pd.date_range("2020-01-03", periods=60, freq="W-FRI")
    n = len(dates)
    trend = np.linspace(0, 10, n)
    wave = 5 * np.sin(np.linspace(0, 6 * np.pi, n))
    close = 100 + trend + wave + rng.normal(0, 1, n)
    frame = pd.DataFrame(
        {
            "Date": dates,
            "Open": close + rng.normal(0, 0.3, n),
            "High": close + np.abs(rng.normal(0, 1, n)),
            "Low": close - np.abs(rng.normal(0, 1, n)),
            "Close": close,
            "Volume": rng.integers(1_000, 5_000, n).astype(float),
            "nvda_close": close * 0.4 + rng.normal(0, 1, n),
            "nvda_volume": rng.integers(2_000, 6_000, n).astype(float),
            "amzn_close": close * 0.9 + rng.normal(0, 1, n),
            "amzn_volume": rng.integers(1_500, 4_500, n).astype(float),
        }
    )
    return frame


@pytest.fixture
def engineered_df(weekly_df) -> pd.DataFrame:
    """Feature-engineered frame (all FEATURE_COLUMNS + Direction, no NaN)."""
    return dh.engineer_features(weekly_df)


@pytest.fixture
def csv_path(tmp_path, raw_daily_df):
    """Write the raw frame to a temporary CSV and return its path."""
    path = tmp_path / "modelling_dataset.csv"
    raw_daily_df.to_csv(path, index=False)
    return path


# --------------------------------------------------------------------------- #
# build_feature_columns                                                        #
# --------------------------------------------------------------------------- #
class TestBuildFeatureColumns:
    def test_default_count(self):
        """12 base features + 4 per default peer ticker."""
        cols = dh.build_feature_columns()
        expected = len(dh.BASE_FEATURE_COLUMNS) + 4 * len(dh.PEER_TICKERS)
        assert len(cols) == expected
        assert len(dh.BASE_FEATURE_COLUMNS) == 12

    def test_custom_single_peer_names_and_order(self):
        """Base features come first, then the four peer features in order."""
        cols = dh.build_feature_columns(peers=["xyz"])
        assert cols[: len(dh.BASE_FEATURE_COLUMNS)] == dh.BASE_FEATURE_COLUMNS
        assert cols[len(dh.BASE_FEATURE_COLUMNS) :] == [
            "xyz_return_1w",
            "xyz_lag_return_1",
            "xyz_rel_strength",
            "xyz_volume_ratio",
        ]

    def test_no_peers_returns_base_only(self):
        assert dh.build_feature_columns(peers=[]) == dh.BASE_FEATURE_COLUMNS

    def test_base_override(self):
        cols = dh.build_feature_columns(peers=["a"], base=["f1", "f2"])
        assert cols == [
            "f1",
            "f2",
            "a_return_1w",
            "a_lag_return_1",
            "a_rel_strength",
            "a_volume_ratio",
        ]

    def test_returns_new_list_not_alias(self):
        """The base list must not be mutated/aliased by the function."""
        cols = dh.build_feature_columns(peers=[])
        cols.append("injected")
        assert "injected" not in dh.BASE_FEATURE_COLUMNS


# --------------------------------------------------------------------------- #
# compute_rsi                                                                  #
# --------------------------------------------------------------------------- #
class TestComputeRsi:
    def test_length_and_bounds(self):
        s = pd.Series(np.linspace(10, 50, 40) + np.sin(np.arange(40)))
        rsi = dh.compute_rsi(s, window=14)
        assert len(rsi) == len(s)
        valid = rsi.dropna()
        assert ((valid >= 0) & (valid <= 100)).all()

    def test_warmup_is_nan(self):
        """Wilder smoothing needs `window` observations before a value."""
        s = pd.Series(np.arange(1, 31, dtype=float))
        rsi = dh.compute_rsi(s, window=14)
        assert rsi.iloc[:13].isna().all()
        assert not np.isnan(rsi.iloc[-1])

    def test_monotonic_increasing_approaches_100(self):
        s = pd.Series(np.arange(1, 41, dtype=float))  # only gains
        assert dh.compute_rsi(s, window=14).iloc[-1] == pytest.approx(100.0)

    def test_monotonic_decreasing_approaches_0(self):
        s = pd.Series(np.arange(40, 0, -1, dtype=float))  # only losses
        assert dh.compute_rsi(s, window=14).iloc[-1] == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# compute_macd                                                                 #
# --------------------------------------------------------------------------- #
class TestComputeMacd:
    def test_returns_three_aligned_series(self):
        s = pd.Series(np.linspace(10, 30, 50))
        macd, signal, hist = dh.compute_macd(s)
        assert len(macd) == len(signal) == len(hist) == len(s)

    def test_histogram_identity(self):
        """hist must equal macd - signal exactly."""
        s = pd.Series(np.random.default_rng(2).normal(100, 5, 60))
        macd, signal, hist = dh.compute_macd(s)
        pd.testing.assert_series_equal(hist, macd - signal, check_names=False)

    def test_constant_series_gives_zero_macd(self):
        s = pd.Series([42.0] * 50)
        macd, _, _ = dh.compute_macd(s)
        assert np.allclose(macd.values, 0.0)


# --------------------------------------------------------------------------- #
# load_dataset (integration: filesystem)                                       #
# --------------------------------------------------------------------------- #
@pytest.mark.integration
class TestLoadDataset:
    def test_renames_date_and_filters(self, csv_path):
        df = dh.load_dataset(csv_path, start_date="2020-06-01")
        assert "Date" in df.columns and "date" not in df.columns
        assert (df["Date"] >= "2020-06-01").all()

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            dh.load_dataset(tmp_path / "nope.csv")

    def test_no_date_column_raises(self, tmp_path):
        bad = tmp_path / "bad.csv"
        pd.DataFrame({"x": [1, 2]}).to_csv(bad, index=False)
        with pytest.raises(KeyError):
            dh.load_dataset(bad)

    def test_accepts_capitalised_date(self, tmp_path):
        path = tmp_path / "cap.csv"
        pd.DataFrame({"Date": ["2021-01-01", "2021-01-02"], "msft_close": [1.0, 2.0]}).to_csv(
            path, index=False
        )
        df = dh.load_dataset(path, start_date="2020-01-01")
        assert len(df) == 2


# --------------------------------------------------------------------------- #
# align_trading_days (integration: NYSE calendar)                              #
# --------------------------------------------------------------------------- #
@pytest.mark.integration
class TestAlignTradingDays:
    @pytest.fixture
    def aligned(self):
        # Trading days only in the raw feed; alignment fills the calendar.
        raw = pd.DataFrame(
            {
                "Date": ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-21", "2020-01-31"],
                "msft_close": [1.0, 2.0, 3.0, 4.0, 5.0],
            }
        )
        return dh.align_trading_days(raw)

    def test_daily_frequency_and_flags_exist(self, aligned):
        # 2020-01-02 .. 2020-01-31 inclusive == 30 calendar days.
        assert len(aligned) == 30
        for col in ("is_trading_day", "is_weekend", "is_holiday"):
            assert col in aligned.columns
            assert aligned[col].dtype == bool

    def test_flag_consistency(self, aligned):
        """A day is a holiday iff it is neither a trading day nor a weekend."""
        expected = (~aligned["is_trading_day"]) & (~aligned["is_weekend"])
        assert (aligned["is_holiday"] == expected).all()

    def test_weekend_detected(self, aligned):
        sat = aligned.loc[aligned["Date"] == "2020-01-04"].iloc[0]
        assert sat["is_weekend"] and not sat["is_trading_day"]

    def test_holiday_detected(self, aligned):
        # 2020-01-20 is MLK Day: a non-trading weekday -> holiday.
        mlk = aligned.loc[aligned["Date"] == "2020-01-20"].iloc[0]
        assert mlk["is_holiday"] and not mlk["is_trading_day"]

    def test_forward_fill_no_gaps(self, aligned):
        assert aligned["msft_close"].isna().sum() == 0


# --------------------------------------------------------------------------- #
# resample_weekly (integration)                                                #
# --------------------------------------------------------------------------- #
@pytest.mark.integration
class TestResampleWeekly:
    def test_ohlcv_aggregation(self):
        """One full trading week aggregates to one weekly bar correctly."""
        days = pd.to_datetime(
            ["2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09", "2020-01-10"]  # Mon..Fri
        )
        daily = pd.DataFrame(
            {
                "Date": days,
                "msft_open": [1.0, 2.0, 3.0, 4.0, 5.0],
                "msft_high": [11, 12, 19, 14, 15],
                "msft_low": [9, 1, 7, 6, 5],
                "msft_close": [10.0, 11.0, 12.0, 13.0, 14.0],
                "msft_volume": [100.0] * 5,
                "is_trading_day": [True] * 5,
            }
        )
        weekly = dh.resample_weekly(daily)
        assert len(weekly) == 1
        row = weekly.iloc[0]
        assert row["Open"] == 1.0  # first
        assert row["High"] == 19  # max
        assert row["Low"] == 1  # min
        assert row["Close"] == 14.0  # last
        assert row["Volume"] == 500.0  # sum
        assert row["Date"].weekday() == 4  # week-ending Friday

    def test_renames_msft_columns(self, raw_daily_df):
        aligned = dh.align_trading_days(raw_daily_df.rename(columns={"date": "Date"}))
        weekly = dh.resample_weekly(aligned)
        for col in ("Open", "High", "Low", "Close", "Volume"):
            assert col in weekly.columns
        assert "msft_close" not in weekly.columns

    def test_peer_volume_summed_close_last(self):
        days = pd.to_datetime(
            ["2020-01-06", "2020-01-07", "2020-01-08", "2020-01-09", "2020-01-10"]
        )
        daily = pd.DataFrame(
            {
                "Date": days,
                "msft_open": [1.0] * 5,
                "msft_high": [1.0] * 5,
                "msft_low": [1.0] * 5,
                "msft_close": [1.0] * 5,
                "msft_volume": [1.0] * 5,
                "nvda_close": [10.0, 20.0, 30.0, 40.0, 50.0],
                "nvda_volume": [7.0] * 5,
                "is_trading_day": [True] * 5,
            }
        )
        weekly = dh.resample_weekly(daily)
        assert weekly.iloc[0]["nvda_close"] == 50.0  # last
        assert weekly.iloc[0]["nvda_volume"] == 35.0  # sum


# --------------------------------------------------------------------------- #
# engineer_features                                                            #
# --------------------------------------------------------------------------- #
class TestEngineerFeatures:
    def test_all_feature_columns_present(self, engineered_df):
        for col in dh.build_feature_columns():
            assert col in engineered_df.columns

    def test_target_is_valid_integer_class(self, engineered_df):
        assert engineered_df["Direction"].dtype.kind in "iu"
        assert set(engineered_df["Direction"].unique()).issubset({0, 1, 2})

    def test_no_missing_values(self, engineered_df):
        assert engineered_df.isna().sum().sum() == 0

    def test_target_labelling_rule_no_lookahead(self, weekly_df):
        """Direction must equal the next-week move classified by threshold."""
        out = dh.engineer_features(weekly_df).set_index("Date")
        close = weekly_df.set_index("Date")["Close"]
        nxt = (close.shift(-1) - close) / close * 100
        thr = dh.NEUTRAL_THRESHOLD * 100
        expected = pd.Series(np.where(nxt > thr, 1, np.where(nxt < -thr, 0, 2)), index=close.index)
        assert (out["Direction"] == expected.loc[out.index]).all()

    def test_last_week_dropped_as_unlabelled(self, weekly_df):
        """The final week has no `t+1`, so it must not survive."""
        out = dh.engineer_features(weekly_df)
        assert weekly_df["Date"].max() not in set(out["Date"])

    def test_wider_threshold_yields_more_neutral(self, weekly_df):
        narrow = dh.engineer_features(weekly_df, threshold=0.001)
        wide = dh.engineer_features(weekly_df, threshold=0.05)
        n_neutral = (narrow["Direction"] == 2).sum()
        w_neutral = (wide["Direction"] == 2).sum()
        assert w_neutral >= n_neutral

    def test_missing_peer_close_skips_peer(self, weekly_df, caplog):
        df = weekly_df.drop(columns=["nvda_close", "nvda_volume"])
        with caplog.at_level(logging.WARNING):
            out = dh.engineer_features(df, peers=["nvda"])
        assert "nvda_return_1w" not in out.columns
        assert any("nvda_close" in r.message for r in caplog.records)

    def test_missing_peer_volume_fills_ratio_one(self, weekly_df):
        df = weekly_df.drop(columns=["nvda_volume"])
        out = dh.engineer_features(df, peers=["nvda"])
        assert (out["nvda_volume_ratio"] == 1.0).all()

    def test_input_not_mutated(self, weekly_df):
        before = weekly_df.copy()
        dh.engineer_features(weekly_df)
        pd.testing.assert_frame_equal(weekly_df, before)


# --------------------------------------------------------------------------- #
# fill_missing                                                                 #
# --------------------------------------------------------------------------- #
class TestFillMissing:
    def test_no_missing_returns_complete_frame(self):
        df = pd.DataFrame({"a": [1.0, 2.0], "b": [3.0, 4.0]})
        out = dh.fill_missing(df)
        assert out.isna().sum().sum() == 0
        assert out.shape == df.shape

    def test_numeric_filled_with_median(self):
        df = pd.DataFrame({"a": [1.0, np.nan, 3.0]})  # median == 2.0
        out = dh.fill_missing(df)
        assert out.isna().sum().sum() == 0
        assert out["a"].iloc[1] == pytest.approx(2.0)

    def test_categorical_filled_with_mode(self):
        df = pd.DataFrame({"num": [1.0, 2.0, np.nan], "cat": ["x", "x", None]})
        out = dh.fill_missing(df)
        assert out.isna().sum().sum() == 0
        assert out["cat"].iloc[2] == "x"


# --------------------------------------------------------------------------- #
# split_and_scale                                                              #
# --------------------------------------------------------------------------- #
class TestSplitAndScale:
    def test_shapes_partition_rows(self, engineered_df):
        feats = dh.build_feature_columns()
        x_tr, x_te, y_tr, y_te, _ = dh.split_and_scale(engineered_df, feats, test_size=0.2)
        assert x_tr.shape[0] + x_te.shape[0] == len(engineered_df)
        assert x_tr.shape[1] == x_te.shape[1] == len(feats)
        # sklearn rounds the test count up (ceil), not down.
        assert x_te.shape[0] == math.ceil(len(engineered_df) * 0.2)

    def test_time_order_preserved(self, engineered_df):
        """No shuffle: the test split is the chronological tail."""
        feats = dh.build_feature_columns()
        _, _, _, y_te, _ = dh.split_and_scale(engineered_df, feats, test_size=0.2)
        tail = engineered_df["Direction"].iloc[-len(y_te) :]
        assert list(y_te.values) == list(tail.values)

    def test_scaler_fit_on_train_only(self, engineered_df):
        """RobustScaler centres on the median -> train medians ~ 0."""
        feats = dh.build_feature_columns()
        x_tr, _, _, _, _ = dh.split_and_scale(engineered_df, feats)
        assert np.allclose(np.median(x_tr, axis=0), 0.0, atol=1e-9)

    def test_returns_numpy_and_fitted_scaler(self, engineered_df):
        feats = dh.build_feature_columns()
        x_tr, x_te, _, _, scaler = dh.split_and_scale(engineered_df, feats)
        assert isinstance(x_tr, np.ndarray) and isinstance(x_te, np.ndarray)
        assert hasattr(scaler, "center_")  # RobustScaler fitted attribute

    def test_custom_scaler_is_used_and_fitted(self, engineered_df):
        feats = dh.build_feature_columns()
        custom = StandardScaler()
        _, _, _, _, scaler = dh.split_and_scale(engineered_df, feats, scaler=custom)
        assert scaler is custom
        assert hasattr(scaler, "mean_")  # StandardScaler fitted attribute

    def test_missing_feature_column_raises(self, engineered_df):
        with pytest.raises(KeyError):
            dh.split_and_scale(engineered_df, ["does_not_exist"])


# --------------------------------------------------------------------------- #
# preprocess (integration: full pipeline)                                      #
# --------------------------------------------------------------------------- #
@pytest.mark.integration
class TestPreprocess:
    def test_end_to_end_shape_and_target(self, csv_path):
        df = dh.preprocess(csv_path)
        assert len(df) > 0
        assert df.isna().sum().sum() == 0
        for col in dh.build_feature_columns():
            assert col in df.columns
        assert set(df["Direction"].unique()).issubset({0, 1, 2})

    def test_threshold_passthrough(self, csv_path):
        wide = dh.preprocess(csv_path, threshold=0.05)
        narrow = dh.preprocess(csv_path, threshold=0.001)
        assert (wide["Direction"] == 2).sum() >= (narrow["Direction"] == 2).sum()
