"""
tests/test_database_management.py
==================================
Unit tests for the MSFT Direction Predictor database management functions.

Tests cover:
    - Database connection creation
    - New format CSV loading
    - Table creation
    - Query functions (get_msft_data, get_gold_data, etc.)
    - Save functions (save_processed_features, save_predictions)
    - Date filtering

Author: Qusai Al Qusaily (236866)
Project: MSFT Direction Predictor — Block D ADS-AI BUas
"""

import os
import sqlite3
import tempfile
from datetime import date

import numpy as np
import pandas as pd
import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    os.unlink(db_path)


@pytest.fixture
def tmp_csv_new_format(tmp_path):
    """Create a temporary CSV in the new yfinance 3-row header format."""
    csv_path = tmp_path / "test_new_format.csv"
    content = (
        "Price,Close,High,Low,Open,Volume\n"
        "Ticker,TEST,TEST,TEST,TEST,TEST\n"
        "Date,,,,,\n"
        "2025-02-03,100.0,102.0,98.0,99.0,1000000\n"
        "2025-02-04,101.5,103.0,100.0,100.5,1200000\n"
        "2025-02-05,99.0,101.0,97.0,101.0,900000\n"
    )
    csv_path.write_text(content)
    return str(csv_path)


@pytest.fixture
def sample_msft_df():
    """Create a sample MSFT DataFrame."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "open": [370.0, 372.0, 368.0],
            "high": [375.0, 376.0, 373.0],
            "low": [368.0, 370.0, 365.0],
            "close": [372.0, 374.0, 370.0],
            "volume": [25000000.0, 23000000.0, 27000000.0],
        }
    )


@pytest.fixture
def sample_gold_df():
    """Create a sample gold prices DataFrame."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "gold_close": [2050.0, 2055.0, 2048.0],
        }
    )


@pytest.fixture
def sample_predictions_df():
    """Create a sample predictions DataFrame."""
    return pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
            "predicted_direction": [1, 0, 1],
            "confidence": [0.65, 0.72, 0.58],
            "model_used": ["XGBoost", "XGBoost", "XGBoost"],
            "actual_direction": [1, 0, 1],
        }
    )


@pytest.fixture
def sample_processed_df():
    """Create a sample processed features DataFrame."""
    return pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
            "close": [372.0, 374.0, 370.0],
            "target": [1, 0, 1],
            "lag_1": [370.0, 372.0, 374.0],
            "rolling_5": [368.0, 369.0, 370.0],
        }
    )


@pytest.fixture
def db_with_tables(tmp_db):
    """Create a temporary database with all 6 tables populated."""
    conn = sqlite3.connect(tmp_db)

    # msft_daily
    pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "open": [370.0, 372.0],
            "high": [375.0, 376.0],
            "low": [368.0, 370.0],
            "close": [372.0, 374.0],
            "volume": [25000000.0, 23000000.0],
        }
    ).to_sql("msft_daily", conn, if_exists="replace", index=False)

    # gold_prices
    pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "gold_close": [2050.0, 2055.0],
        }
    ).to_sql("gold_prices", conn, if_exists="replace", index=False)

    # oil_prices
    pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "oil_close": [72.0, 73.0],
        }
    ).to_sql("oil_prices", conn, if_exists="replace", index=False)

    # vix_data
    pd.DataFrame(
        {
            "date": ["2024-01-02", "2024-01-03"],
            "vix": [13.5, 14.2],
        }
    ).to_sql("vix_data", conn, if_exists="replace", index=False)

    # processed_features
    pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "close": [372.0],
            "target": [1],
        }
    ).to_sql("processed_features", conn, if_exists="replace", index=False)

    # predictions
    pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "predicted_direction": [1],
            "confidence": [0.65],
            "model_used": ["XGBoost"],
            "actual_direction": [1],
        }
    ).to_sql("predictions", conn, if_exists="replace", index=False)

    conn.close()
    return tmp_db


# ── Connection Tests ──────────────────────────────────────────────────────────


class TestCreateConnection:
    """Tests for database connection creation."""

    def test_creates_new_database(self, tmp_db):
        """Connecting to a new path should create the database file."""
        conn = sqlite3.connect(tmp_db)
        assert conn is not None
        conn.close()
        assert os.path.exists(tmp_db)

    def test_connection_is_sqlite_connection(self, tmp_db):
        """Connection should be a sqlite3.Connection object."""
        conn = sqlite3.connect(tmp_db)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_can_execute_query_on_connection(self, tmp_db):
        """Should be able to run a simple SQL query on the connection."""
        conn = sqlite3.connect(tmp_db)
        result = conn.execute("SELECT 1").fetchone()
        assert result[0] == 1
        conn.close()


# ── New Format CSV Loading Tests ──────────────────────────────────────────────


class TestLoadNewFormatCsv:
    """Tests for loading yfinance 3-row header CSV files."""

    def test_loads_correct_number_of_rows(self, tmp_csv_new_format):
        """Should load exactly 3 data rows from the test CSV."""
        df = pd.read_csv(
            tmp_csv_new_format,
            skiprows=3,
            header=None,
            names=["date", "close", "high", "low", "open", "volume"],
        )
        df = df.dropna(subset=["date"])
        df = df[df["date"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")]
        assert len(df) == 3

    def test_date_column_parsed_correctly(self, tmp_csv_new_format):
        """Date column should be parseable as date objects."""
        df = pd.read_csv(
            tmp_csv_new_format,
            skiprows=3,
            header=None,
            names=["date", "close", "high", "low", "open", "volume"],
        )
        df = df.dropna(subset=["date"])
        df = df[df["date"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        assert df["date"].iloc[0] == date(2025, 2, 3)

    def test_close_values_are_numeric(self, tmp_csv_new_format):
        """Close column should contain numeric values."""
        df = pd.read_csv(
            tmp_csv_new_format,
            skiprows=3,
            header=None,
            names=["date", "close", "high", "low", "open", "volume"],
        )
        df = df.dropna(subset=["date"])
        df = df[df["date"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")]
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        assert df["close"].notna().all()

    def test_first_close_value_correct(self, tmp_csv_new_format):
        """First close value should be 100.0."""
        df = pd.read_csv(
            tmp_csv_new_format,
            skiprows=3,
            header=None,
            names=["date", "close", "high", "low", "open", "volume"],
        )
        df = df.dropna(subset=["date"])
        df = df[df["date"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")]
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        assert df["close"].iloc[0] == 100.0

    def test_no_header_rows_in_output(self, tmp_csv_new_format):
        """Output should contain no header rows — only data rows."""
        df = pd.read_csv(
            tmp_csv_new_format,
            skiprows=3,
            header=None,
            names=["date", "close", "high", "low", "open", "volume"],
        )
        df = df.dropna(subset=["date"])
        df = df[df["date"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")]
        assert "Ticker" not in df["date"].values
        assert "Price" not in df["date"].values


# ── Table Creation Tests ──────────────────────────────────────────────────────


class TestCreateOutputTables:
    """Tests for creating the output tables in the database."""

    def test_processed_features_table_created(self, tmp_db):
        """processed_features table should be created."""
        conn = sqlite3.connect(tmp_db)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_features (
                date TEXT PRIMARY KEY,
                close REAL,
                target INTEGER
            )
        """
        )
        conn.commit()
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        assert "processed_features" in tables["name"].values
        conn.close()

    def test_predictions_table_created(self, tmp_db):
        """predictions table should be created."""
        conn = sqlite3.connect(tmp_db)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS predictions (
                date TEXT PRIMARY KEY,
                predicted_direction INTEGER,
                confidence REAL,
                model_used TEXT,
                actual_direction INTEGER
            )
        """
        )
        conn.commit()
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        assert "predictions" in tables["name"].values
        conn.close()

    def test_tables_start_empty(self, tmp_db):
        """Newly created output tables should be empty."""
        conn = sqlite3.connect(tmp_db)
        conn.execute("CREATE TABLE IF NOT EXISTS processed_features (date TEXT, close REAL)")
        conn.commit()
        count = pd.read_sql("SELECT COUNT(*) as c FROM processed_features", conn)
        assert count["c"].values[0] == 0
        conn.close()


# ── Query Function Tests ──────────────────────────────────────────────────────


class TestGetFunctions:
    """Tests for database query functions."""

    def test_get_msft_data_returns_dataframe(self, db_with_tables):
        """get_msft_data should return a DataFrame."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM msft_daily ORDER BY date", conn)
        conn.close()
        assert isinstance(df, pd.DataFrame)

    def test_get_msft_data_correct_columns(self, db_with_tables):
        """msft_daily should have all required columns."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM msft_daily ORDER BY date", conn)
        conn.close()
        for col in ["date", "open", "high", "low", "close", "volume"]:
            assert col in df.columns

    def test_get_msft_data_correct_row_count(self, db_with_tables):
        """msft_daily should return 2 rows from fixture."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM msft_daily ORDER BY date", conn)
        conn.close()
        assert len(df) == 2

    def test_get_gold_data_returns_dataframe(self, db_with_tables):
        """get_gold_data should return a DataFrame."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM gold_prices ORDER BY date", conn)
        conn.close()
        assert isinstance(df, pd.DataFrame)

    def test_get_gold_data_correct_columns(self, db_with_tables):
        """gold_prices should have date and gold_close columns."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM gold_prices ORDER BY date", conn)
        conn.close()
        assert "date" in df.columns
        assert "gold_close" in df.columns

    def test_get_oil_data_correct_columns(self, db_with_tables):
        """oil_prices should have date and oil_close columns."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM oil_prices ORDER BY date", conn)
        conn.close()
        assert "date" in df.columns
        assert "oil_close" in df.columns

    def test_get_vix_data_correct_columns(self, db_with_tables):
        """vix_data should have date and vix columns."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM vix_data ORDER BY date", conn)
        conn.close()
        assert "date" in df.columns
        assert "vix" in df.columns

    def test_get_processed_features_returns_dataframe(self, db_with_tables):
        """get_processed_features should return a DataFrame."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM processed_features ORDER BY date", conn)
        conn.close()
        assert isinstance(df, pd.DataFrame)

    def test_get_predictions_returns_dataframe(self, db_with_tables):
        """get_predictions should return a DataFrame."""
        conn = sqlite3.connect(db_with_tables)
        df = pd.read_sql("SELECT * FROM predictions ORDER BY date", conn)
        conn.close()
        assert isinstance(df, pd.DataFrame)

    def test_all_tables_exist(self, db_with_tables):
        """All 6 expected tables should exist in the database."""
        conn = sqlite3.connect(db_with_tables)
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        conn.close()
        expected = {
            "msft_daily",
            "gold_prices",
            "oil_prices",
            "vix_data",
            "processed_features",
            "predictions",
        }
        assert expected.issubset(set(tables["name"].values))


# ── Save Function Tests ───────────────────────────────────────────────────────


class TestSaveFunctions:
    """Tests for save_processed_features and save_predictions."""

    def test_save_processed_features_correct_row_count(self, tmp_db, sample_processed_df):
        """Saved processed features should have correct row count."""
        conn = sqlite3.connect(tmp_db)
        sample_processed_df.to_sql("processed_features", conn, if_exists="replace", index=False)
        count = pd.read_sql("SELECT COUNT(*) as c FROM processed_features", conn)
        conn.close()
        assert count["c"].values[0] == 3

    def test_save_predictions_correct_row_count(self, tmp_db, sample_predictions_df):
        """Saved predictions should have correct row count."""
        conn = sqlite3.connect(tmp_db)
        sample_predictions_df.to_sql("predictions", conn, if_exists="replace", index=False)
        count = pd.read_sql("SELECT COUNT(*) as c FROM predictions", conn)
        conn.close()
        assert count["c"].values[0] == 3

    def test_save_predictions_columns_preserved(self, tmp_db, sample_predictions_df):
        """All prediction columns should be preserved after saving."""
        conn = sqlite3.connect(tmp_db)
        sample_predictions_df.to_sql("predictions", conn, if_exists="replace", index=False)
        df = pd.read_sql("SELECT * FROM predictions", conn)
        conn.close()
        for col in [
            "date",
            "predicted_direction",
            "confidence",
            "model_used",
            "actual_direction",
        ]:
            assert col in df.columns

    def test_save_replaces_existing_data(self, tmp_db, sample_predictions_df):
        """Saving predictions twice should replace not duplicate data."""
        conn = sqlite3.connect(tmp_db)
        sample_predictions_df.to_sql("predictions", conn, if_exists="replace", index=False)
        sample_predictions_df.to_sql("predictions", conn, if_exists="replace", index=False)
        count = pd.read_sql("SELECT COUNT(*) as c FROM predictions", conn)
        conn.close()
        assert count["c"].values[0] == 3

    def test_save_processed_features_data_matches(self, tmp_db, sample_processed_df):
        """Data retrieved after saving should match what was saved."""
        conn = sqlite3.connect(tmp_db)
        sample_processed_df.to_sql("processed_features", conn, if_exists="replace", index=False)
        df = pd.read_sql("SELECT * FROM processed_features", conn)
        conn.close()
        assert list(df["target"]) == [1, 0, 1]


# ── Date Filter Tests ─────────────────────────────────────────────────────────


class TestDateFiltering:
    """Tests for date filtering behaviour in the database."""

    def test_filter_keeps_rows_after_start_date(self, tmp_db):
        """Rows after start date should be kept after filtering."""
        conn = sqlite3.connect(tmp_db)
        df = pd.DataFrame(
            {
                "date": ["2018-01-01", "2019-01-01", "2020-01-01", "2021-01-01"],
                "close": [100.0, 110.0, 120.0, 130.0],
            }
        )
        df.to_sql("msft_daily", conn, if_exists="replace", index=False)
        result = pd.read_sql("SELECT * FROM msft_daily WHERE date >= '2019-01-01'", conn)
        conn.close()
        assert len(result) == 3

    def test_filter_excludes_rows_before_start_date(self, tmp_db):
        """Rows before start date should be excluded."""
        conn = sqlite3.connect(tmp_db)
        df = pd.DataFrame(
            {
                "date": ["2018-01-01", "2019-01-01", "2020-01-01"],
                "close": [100.0, 110.0, 120.0],
            }
        )
        df.to_sql("msft_daily", conn, if_exists="replace", index=False)
        result = pd.read_sql("SELECT * FROM msft_daily WHERE date >= '2019-01-01'", conn)
        conn.close()
        assert "2018-01-01" not in result["date"].values

    def test_data_sorted_by_date(self, tmp_db):
        """Data should be retrievable in date order."""
        conn = sqlite3.connect(tmp_db)
        df = pd.DataFrame(
            {
                "date": ["2024-01-03", "2024-01-01", "2024-01-02"],
                "close": [102.0, 100.0, 101.0],
            }
        )
        df.to_sql("msft_daily", conn, if_exists="replace", index=False)
        result = pd.read_sql("SELECT * FROM msft_daily ORDER BY date ASC", conn)
        conn.close()
        dates = list(result["date"])
        assert dates == sorted(dates)


# ── Edge Cases ────────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge case tests for database management."""

    def test_empty_table_returns_empty_dataframe(self, tmp_db):
        """Querying an empty table should return an empty DataFrame."""
        conn = sqlite3.connect(tmp_db)
        conn.execute("CREATE TABLE IF NOT EXISTS predictions (date TEXT, confidence REAL)")
        conn.commit()
        df = pd.read_sql("SELECT * FROM predictions", conn)
        conn.close()
        assert len(df) == 0
        assert isinstance(df, pd.DataFrame)

    def test_duplicate_dates_handled_by_replace(self, tmp_db):
        """Using if_exists=replace prevents duplicate rows."""
        conn = sqlite3.connect(tmp_db)
        df1 = pd.DataFrame({"date": ["2024-01-02"], "close": [100.0]})
        df2 = pd.DataFrame({"date": ["2024-01-02"], "close": [101.0]})
        df1.to_sql("msft_daily", conn, if_exists="replace", index=False)
        df2.to_sql("msft_daily", conn, if_exists="replace", index=False)
        result = pd.read_sql("SELECT * FROM msft_daily", conn)
        conn.close()
        assert len(result) == 1
        assert result["close"].iloc[0] == 101.0

    def test_database_file_created_on_connect(self):
        """Connecting to a new path should create the file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        os.unlink(path)
        assert not os.path.exists(path)
        conn = sqlite3.connect(path)
        conn.close()
        assert os.path.exists(path)
        os.unlink(path)

    def test_null_values_in_predictions_allowed(self, tmp_db):
        """actual_direction can be NULL before the event occurs."""
        conn = sqlite3.connect(tmp_db)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS predictions
               (date TEXT, predicted_direction INTEGER,
                confidence REAL, model_used TEXT, actual_direction INTEGER)"""
        )
        conn.execute("INSERT INTO predictions VALUES ('2024-01-02', 1, 0.65, 'XGBoost', NULL)")
        conn.commit()
        result = pd.read_sql("SELECT * FROM predictions", conn)
        conn.close()
        assert pd.isna(result["actual_direction"].iloc[0])
