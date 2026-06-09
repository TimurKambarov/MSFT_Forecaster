"""
Unit tests for the MSFT Direction Predictor dashboard.
Task 12 — Unit Testing and Documentation | ILO 9.2C

Modules tested:
  - dashboard/msft_forecaster/pipeline/preprocess.py
  - dashboard/msft_forecaster/predict.py
  - dashboard/server.py

Run with:
  python unit_tests_dashboard.py
  pytest unit_tests_dashboard.py -v
  pytest unit_tests_dashboard.py --cov=dashboard --cov-report=term-missing
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
for candidate in [
    os.path.dirname(__file__),
    os.path.join(os.path.dirname(__file__), "..", "..", ".."),
    os.getcwd(),
]:
    candidate = os.path.abspath(candidate)
    if os.path.isdir(os.path.join(candidate, "dashboard")):
        PROJECT_ROOT = candidate
        break

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Shared test helpers
# ---------------------------------------------------------------------------


def make_msft_df(n=200):
    rng = np.random.default_rng(42)
    base = date(2022, 1, 3)
    dates = [base + timedelta(days=i) for i in range(n)]
    close = np.abs(400.0 + np.cumsum(rng.normal(0, 5, n)))
    return pd.DataFrame(
        {
            "date": pd.to_datetime(dates),
            "open": close * 0.99,
            "high": close * 1.015,
            "low": close * 0.975,
            "close": close,
            "volume": rng.integers(20_000_000, 40_000_000, n).astype(float),
        }
    )


def make_gold_df(n=200):
    rng = np.random.default_rng(1)
    base = date(2022, 1, 3)
    dates = [base + timedelta(days=i) for i in range(n)]
    return pd.DataFrame(
        {"date": pd.to_datetime(dates), "gold_close": 1900.0 + np.cumsum(rng.normal(0, 5, n))}
    )


def make_oil_df(n=200):
    rng = np.random.default_rng(2)
    base = date(2022, 1, 3)
    dates = [base + timedelta(days=i) for i in range(n)]
    return pd.DataFrame(
        {"date": pd.to_datetime(dates), "oil_close": 75.0 + np.cumsum(rng.normal(0, 1, n))}
    )


def make_vix_df(n=200):
    rng = np.random.default_rng(3)
    base = date(2022, 1, 3)
    dates = [base + timedelta(days=i) for i in range(n)]
    return pd.DataFrame({"date": pd.to_datetime(dates), "vix": np.abs(15.0 + rng.normal(0, 2, n))})


def make_temp_db(n=200):
    tmp = tempfile.mktemp(suffix=".db")
    rng = np.random.default_rng(99)
    base = date(2022, 1, 3)
    dates = [(base + timedelta(days=i)).isoformat() for i in range(n)]
    close = np.abs(400.0 + np.cumsum(rng.normal(0, 5, n)))
    conn = sqlite3.connect(tmp)
    pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.99,
            "high": close * 1.015,
            "low": close * 0.975,
            "close": close,
            "volume": rng.integers(20_000_000, 40_000_000, n).astype(float),
        }
    ).to_sql("msft_daily", conn, if_exists="replace", index=False)
    pd.DataFrame({"date": dates, "gold_close": 1900 + np.cumsum(rng.normal(0, 5, n))}).to_sql(
        "gold_prices", conn, if_exists="replace", index=False
    )
    pd.DataFrame({"date": dates, "oil_close": 75 + np.cumsum(rng.normal(0, 1, n))}).to_sql(
        "oil_prices", conn, if_exists="replace", index=False
    )
    pd.DataFrame({"date": dates, "vix": np.abs(15 + rng.normal(0, 2, n))}).to_sql(
        "vix_data", conn, if_exists="replace", index=False
    )
    pd.DataFrame({"date": dates, "spy_close": 450 + np.cumsum(rng.normal(0, 3, n))}).to_sql(
        "spy_data", conn, if_exists="replace", index=False
    )
    conn.close()
    return tmp


# ---------------------------------------------------------------------------
# 1. Preprocessing pipeline tests
# ---------------------------------------------------------------------------

from dashboard.msft_forecaster.pipeline.preprocess import (
    FEATURE_COLS,
    MSFTRecord,
    ExternalRecord,
    validate_schema,
    validate_dataframe,
    validate_all_tables,
    merge_datasets,
    handle_missing_values,
    create_target,
    engineer_features,
    scale_features,
    train_test_split_timeseries,
    load_all_tables,
    save_processed_features,
)


class TestValidateSchema(unittest.TestCase):
    def test_valid_msft_passes(self):
        validate_schema(make_msft_df(), "msft_daily")

    def test_missing_column_raises(self):
        with self.assertRaises(ValueError):
            validate_schema(make_msft_df().drop(columns=["volume"]), "msft_daily")

    def test_unknown_table_passes(self):
        validate_schema(make_msft_df(), "unknown")

    def test_gold_schema_valid(self):
        validate_schema(make_gold_df(), "gold_prices")

    def test_oil_schema_valid(self):
        validate_schema(make_oil_df(), "oil_prices")

    def test_vix_schema_valid(self):
        validate_schema(make_vix_df(), "vix_data")


class TestMergeDatasets(unittest.TestCase):
    def _merged(self):
        return merge_datasets(make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df())

    def test_returns_dataframe(self):
        self.assertIsInstance(self._merged(), pd.DataFrame)

    def test_preserves_all_msft_rows(self):
        self.assertEqual(len(self._merged()), 200)

    def test_contains_all_source_columns(self):
        df = self._merged()
        for col in ["close", "gold_close", "oil_close", "vix"]:
            self.assertIn(col, df.columns)

    def test_sorted_by_date(self):
        self.assertTrue(self._merged()["date"].is_monotonic_increasing)

    def test_partial_gold_creates_nan(self):
        df = merge_datasets(
            make_msft_df(), make_gold_df().iloc[10:].copy(), make_oil_df(), make_vix_df()
        )
        self.assertGreater(df["gold_close"].isna().sum(), 0)


class TestHandleMissingValues(unittest.TestCase):
    def _clean(self):
        df = merge_datasets(make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df())
        return handle_missing_values(df)

    def test_no_nan_after_handling(self):
        self.assertEqual(self._clean().isna().sum().sum(), 0)

    def test_row_count_does_not_increase(self):
        raw = merge_datasets(make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df())
        self.assertLessEqual(len(self._clean()), len(raw))

    def test_returns_dataframe(self):
        self.assertIsInstance(self._clean(), pd.DataFrame)


class TestCreateTarget(unittest.TestCase):
    def _base(self):
        df = merge_datasets(make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df())
        return handle_missing_values(df)

    def test_target_column_created(self):
        self.assertIn("target", create_target(self._base()).columns)

    def test_target_only_zero_or_one(self):
        self.assertTrue(set(create_target(self._base())["target"].unique()).issubset({0, 1}))

    def test_up_day_encoded_as_one(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5),
                "close": [100.0, 102.0, 104.0, 106.0, 108.0],
                "open": [99.0] * 5,
                "high": [110.0] * 5,
                "low": [95.0] * 5,
                "gold_close": [1900.0] * 5,
                "oil_close": [75.0] * 5,
                "vix": [15.0] * 5,
            }
        )
        self.assertTrue((create_target(df, threshold=0.005)["target"] == 1).all())

    def test_neutral_rows_removed(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=3),
                "close": [100.0, 100.001, 100.002],
                "open": [99.0] * 3,
                "high": [101.0] * 3,
                "low": [98.0] * 3,
                "gold_close": [1900.0] * 3,
                "oil_close": [75.0] * 3,
                "vix": [15.0] * 3,
            }
        )
        self.assertEqual(len(create_target(df, threshold=0.005)), 0)

    def test_higher_threshold_fewer_rows(self):
        b = self._base()
        self.assertGreaterEqual(len(create_target(b, 0.001)), len(create_target(b, 0.02)))


class TestEngineerFeatures(unittest.TestCase):
    def _base(self):
        df = merge_datasets(make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df())
        return create_target(handle_missing_values(df))

    def test_lag_columns_created(self):
        df = engineer_features(self._base())
        self.assertIn("lag_1", df.columns)
        self.assertIn("lag_2", df.columns)

    def test_rolling_columns_created(self):
        df = engineer_features(self._base())
        self.assertIn("rolling_5", df.columns)
        self.assertIn("rolling_10", df.columns)

    def test_return_columns_created(self):
        df = engineer_features(self._base())
        for col in ["daily_return", "gold_return", "oil_return", "price_range"]:
            self.assertIn(col, df.columns)

    def test_no_nan_after_engineering(self):
        self.assertEqual(engineer_features(self._base()).isna().sum().sum(), 0)

    def test_row_count_reduced(self):
        b = self._base()
        self.assertLess(len(engineer_features(b)), len(b))


class TestPydanticModels(unittest.TestCase):
    def test_msft_record_valid(self):
        r = MSFTRecord(
            date=date(2024, 1, 2), open=399.0, high=405.0, low=397.0, close=403.0, volume=25e6
        )
        self.assertEqual(r.close, 403.0)

    def test_msft_negative_price_rejected(self):
        with self.assertRaises(Exception):
            MSFTRecord(
                date=date(2024, 1, 2), open=-1.0, high=405.0, low=397.0, close=403.0, volume=25e6
            )

    def test_msft_zero_close_rejected(self):
        with self.assertRaises(Exception):
            MSFTRecord(
                date=date(2024, 1, 2), open=399.0, high=405.0, low=397.0, close=0.0, volume=25e6
            )

    def test_msft_negative_volume_rejected(self):
        with self.assertRaises(Exception):
            MSFTRecord(
                date=date(2024, 1, 2), open=399.0, high=405.0, low=397.0, close=403.0, volume=-1.0
            )

    def test_msft_zero_volume_accepted(self):
        r = MSFTRecord(
            date=date(2024, 1, 2), open=399.0, high=405.0, low=397.0, close=403.0, volume=0.0
        )
        self.assertEqual(r.volume, 0.0)

    def test_external_record_valid(self):
        self.assertEqual(ExternalRecord(date=date(2024, 1, 2), value=1900.0).value, 1900.0)

    def test_external_negative_rejected(self):
        with self.assertRaises(Exception):
            ExternalRecord(date=date(2024, 1, 2), value=-5.0)

    def test_external_zero_rejected(self):
        with self.assertRaises(Exception):
            ExternalRecord(date=date(2024, 1, 2), value=0.0)

    def test_validate_dataframe_keeps_valid_rows(self):
        self.assertEqual(len(validate_dataframe(make_msft_df(10), MSFTRecord, "msft_daily")), 10)

    def test_validate_dataframe_drops_invalid_rows(self):
        df = make_msft_df(5)
        df.loc[0, "close"] = -1.0
        self.assertEqual(len(validate_dataframe(df, MSFTRecord, "msft_daily")), 4)


class TestValidateAllTables(unittest.TestCase):
    def test_returns_four_dataframes(self):
        self.assertEqual(
            len(validate_all_tables(make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df())),
            4,
        )

    def test_valid_data_unchanged(self):
        m, *_ = validate_all_tables(make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df())
        self.assertEqual(len(m), 200)

    def test_invalid_msft_row_dropped(self):
        bad = make_msft_df()
        bad.loc[0, "close"] = -1.0
        m, *_ = validate_all_tables(bad, make_gold_df(), make_oil_df(), make_vix_df())
        self.assertEqual(len(m), 199)

    def test_column_names_restored(self):
        _, g, o, v = validate_all_tables(
            make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df()
        )
        self.assertIn("gold_close", g.columns)
        self.assertIn("oil_close", o.columns)


class TestLoadAllTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = make_temp_db()

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.db)
        except OSError:
            pass

    def test_returns_four_dataframes(self):
        self.assertEqual(len(load_all_tables(self.db)), 4)

    def test_msft_columns_present(self):
        msft, *_ = load_all_tables(self.db)
        for col in ["date", "open", "high", "low", "close", "volume"]:
            self.assertIn(col, msft.columns)

    def test_dates_parsed_as_datetime(self):
        msft, *_ = load_all_tables(self.db)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(msft["date"]))

    def test_missing_db_raises(self):
        with self.assertRaises(AssertionError):
            load_all_tables("/nonexistent/db.sqlite")


class TestScaleAndSplit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import shutil

        cls.tmp = tempfile.mkdtemp()
        df = merge_datasets(make_msft_df(), make_gold_df(), make_oil_df(), make_vix_df())
        df = engineer_features(create_target(handle_missing_values(df)))
        sp = os.path.join(cls.tmp, "scaler.pkl")
        cls.df, _ = scale_features(df, FEATURE_COLS, scaler_path=sp)
        cls.sp = sp

    @classmethod
    def tearDownClass(cls):
        import shutil

        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_scaled_columns_added(self):
        for col in FEATURE_COLS:
            self.assertIn(f"{col}_scaled", self.df.columns)

    def test_scaler_file_created(self):
        self.assertTrue(os.path.exists(self.sp))

    def test_split_returns_six_items(self):
        self.assertEqual(len(train_test_split_timeseries(self.df, FEATURE_COLS, 0.8)), 6)

    def test_split_ratio_correct(self):
        X_tr, X_te, *_ = train_test_split_timeseries(self.df, FEATURE_COLS, 0.8)
        self.assertAlmostEqual(len(X_tr) / (len(X_tr) + len(X_te)), 0.8, delta=0.05)

    def test_no_data_leakage(self):
        *_, tr, te = train_test_split_timeseries(self.df, FEATURE_COLS, 0.8)
        self.assertLess(tr["date"].max(), te["date"].min())

    def test_save_processed_features(self):
        db = os.path.join(self.tmp, "test.db")
        save_processed_features(self.df, FEATURE_COLS, db_path=db)
        conn = sqlite3.connect(db)
        count = conn.execute("SELECT COUNT(*) FROM processed_features").fetchone()[0]
        conn.close()
        self.assertEqual(count, len(self.df))


# ---------------------------------------------------------------------------
# 2. Prediction module tests
# ---------------------------------------------------------------------------

from dashboard.msft_forecaster.predict import (
    _rsi,
    build_features,
    load_best_model,
    FEATURE_COLS as PRED_FC,
)


def _mem_conn(n=60):
    rng = np.random.default_rng(99)
    base = date(2023, 1, 2)
    dates = [(base + timedelta(days=i)).isoformat() for i in range(n)]
    close = np.abs(400.0 + np.cumsum(rng.normal(0, 5, n)))
    conn = sqlite3.connect(":memory:")
    pd.DataFrame(
        {
            "date": dates,
            "open": close * 0.99,
            "high": close * 1.015,
            "low": close * 0.975,
            "close": close,
            "volume": [25e6] * n,
        }
    ).to_sql("msft_daily", conn, if_exists="replace", index=False)
    pd.DataFrame({"date": dates, "gold_close": 1900 + np.cumsum(rng.normal(0, 5, n))}).to_sql(
        "gold_prices", conn, if_exists="replace", index=False
    )
    pd.DataFrame({"date": dates, "oil_close": 75 + np.cumsum(rng.normal(0, 1, n))}).to_sql(
        "oil_prices", conn, if_exists="replace", index=False
    )
    pd.DataFrame({"date": dates, "vix": np.abs(15 + rng.normal(0, 2, n))}).to_sql(
        "vix_data", conn, if_exists="replace", index=False
    )
    pd.DataFrame({"date": dates, "spy_close": 450 + np.cumsum(rng.normal(0, 3, n))}).to_sql(
        "spy_data", conn, if_exists="replace", index=False
    )
    return conn


class TestRSI(unittest.TestCase):
    def test_length_matches_input(self):
        s = pd.Series([100.0 + i for i in range(30)])
        self.assertEqual(len(_rsi(s)), 30)

    def test_values_between_0_and_100(self):
        s = pd.Series(400.0 + np.cumsum(np.random.default_rng(42).normal(0, 2, 50)))
        result = _rsi(s).dropna()
        self.assertTrue((result >= 0).all() and (result <= 100).all())

    def test_high_rsi_on_gains(self):
        self.assertGreater(
            _rsi(pd.Series([100.0 + i * 2 for i in range(40)])).dropna().iloc[-1], 70
        )

    def test_low_rsi_on_losses(self):
        self.assertLess(_rsi(pd.Series([200.0 - i * 2 for i in range(40)])).dropna().iloc[-1], 30)

    def test_returns_series(self):
        self.assertIsInstance(_rsi(pd.Series([100.0 + i for i in range(20)])), pd.Series)

    def test_custom_window(self):
        self.assertGreater(
            len(_rsi(pd.Series([100.0 + i for i in range(30)]), window=7).dropna()), 0
        )


class TestBuildFeatures(unittest.TestCase):
    def setUp(self):
        self.conn = _mem_conn()

    def tearDown(self):
        self.conn.close()

    def test_returns_dataframe(self):
        self.assertIsInstance(build_features(self.conn), pd.DataFrame)

    def test_all_feature_cols_present(self):
        df = build_features(self.conn)
        for col in PRED_FC:
            self.assertIn(col, df.columns)

    def test_no_nan_in_features(self):
        self.assertEqual(build_features(self.conn)[PRED_FC].isna().sum().sum(), 0)

    def test_rsi_in_valid_range(self):
        df = build_features(self.conn)
        self.assertTrue((df["rsi_14"] >= 0).all() and (df["rsi_14"] <= 100).all())

    def test_volume_ratio_positive(self):
        self.assertTrue((build_features(self.conn)["volume_ratio"] > 0).all())

    def test_fewer_rows_than_input(self):
        self.assertLess(len(build_features(self.conn, n_rows=60)), 60)


class TestLoadBestModel(unittest.TestCase):
    def test_returns_none_when_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("dashboard.msft_forecaster.predict.MODELS_DIR", Path(tmp)):
                m, s, n = load_best_model()
        self.assertIsNone(m)
        self.assertIsNone(s)
        self.assertIsNone(n)

    def test_loads_model_when_pkl_present(self):
        import joblib
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import RobustScaler

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            joblib.dump(LogisticRegression(), p / "xgboost_lucan_it3.pkl")
            joblib.dump(RobustScaler(), p / "scaler_lucan_it3.pkl")
            with patch("dashboard.msft_forecaster.predict.MODELS_DIR", p):
                m, s, n = load_best_model()
        self.assertIsNotNone(m)
        self.assertEqual(n, "xgboost_lucan_it3")


# ---------------------------------------------------------------------------
# 3. Flask API tests
# ---------------------------------------------------------------------------

from dashboard.server import app


class TestFlaskAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.db_path = make_temp_db(n=100)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(cls.db_path)
        except OSError:
            pass

    def _patch(self):
        return patch("dashboard.server.DB_PATH", Path(self.db_path))

    def test_stock_history_status_200(self):
        with self._patch():
            r = self.client.get("/api/stock/history")
        self.assertEqual(r.status_code, 200)

    def test_stock_history_has_data_key(self):
        with self._patch():
            r = self.client.get("/api/stock/history")
        self.assertIn(b"data", r.data)

    def test_stock_history_custom_days(self):
        with self._patch():
            r = self.client.get("/api/stock/history?days=10")
        self.assertLessEqual(len(json.loads(r.data)["data"]), 10)

    def test_stock_latest_status_200(self):
        with self._patch():
            r = self.client.get("/api/stock/latest")
        self.assertEqual(r.status_code, 200)

    def test_stock_latest_has_close(self):
        with self._patch():
            r = self.client.get("/api/stock/latest")
        self.assertIn("close", json.loads(r.data)["data"])

    def test_indicators_latest_status_200(self):
        with self._patch():
            r = self.client.get("/api/indicators/latest")
        self.assertEqual(r.status_code, 200)

    def test_indicators_latest_has_gold_oil_vix(self):
        with self._patch():
            r = self.client.get("/api/indicators/latest")
        for key in ["gold", "oil", "vix"]:
            self.assertIn(key, json.loads(r.data)["data"])

    def test_indicators_history_status_200(self):
        with self._patch():
            r = self.client.get("/api/indicators/history")
        self.assertEqual(r.status_code, 200)

    def test_model_metrics_status_200(self):
        with self._patch():
            r = self.client.get("/api/model/metrics")
        self.assertEqual(r.status_code, 200)

    def test_model_metrics_returns_list(self):
        with self._patch():
            r = self.client.get("/api/model/metrics")
        self.assertIsInstance(json.loads(r.data)["data"], list)

    def test_prediction_history_status_200(self):
        with self._patch():
            r = self.client.get("/api/prediction/history")
        self.assertEqual(r.status_code, 200)

    def test_prediction_history_has_accuracy(self):
        with self._patch():
            r = self.client.get("/api/prediction/history")
        self.assertIn("accuracy", json.loads(r.data))

    def test_no_cache_header_on_api(self):
        with self._patch():
            r = self.client.get("/api/stock/latest")
        self.assertEqual(r.headers.get("Cache-Control"), "no-store")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [
        TestValidateSchema,
        TestMergeDatasets,
        TestHandleMissingValues,
        TestCreateTarget,
        TestEngineerFeatures,
        TestPydanticModels,
        TestValidateAllTables,
        TestLoadAllTables,
        TestScaleAndSplit,
        TestRSI,
        TestBuildFeatures,
        TestLoadBestModel,
        TestFlaskAPI,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f'\n{"=" * 60}')
    print(f"Tests run:  {result.testsRun}")
    print(f"Passed:     {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures:   {len(result.failures)}")
    print(f"Errors:     {len(result.errors)}")
    print(f'{"=" * 60}')

    sys.exit(0 if result.wasSuccessful() else 1)
