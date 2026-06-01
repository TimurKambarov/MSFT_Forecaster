[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/stHFpEyM)

# Day to Day Stock Price Predictor

**Group 15 · Block D 2025–2026 · Breda University of Applied Sciences**

A binary classification tool that predicts whether the Microsoft (MSFT) stock will go **UP** or **DOWN** on the next trading day. The prediction is powered by an XGBoost model trained on historical MSFT price data combined with exogenous macro signals (Gold, Crude Oil, VIX). Results are displayed in an interactive web dashboard.

---

## Team

| Name | Student ID | Task |
|------|-----------|------|
| Dekker, Lucan den | 251285 | Application development, Design document |
| Gádor, Gergely | 250713 | Legal & ethical compliance |
| Kambarov, Timur | 250596 | Data processing pipelines |
| Qusaily, Qusai Al | 236866 | Database management |

---

## Project Structure

```
├── dashboard/              # Flask API server + frontend
│   ├── server.py           # REST API endpoints
│   ├── requirements.txt    # Dashboard dependencies
│   └── static/             # HTML, CSS, JavaScript
├── src/msft_forecaster/
│   ├── data/
│   │   └── fetch_latest.py # Fetch daily data from Yahoo Finance
│   └── predict.py          # Run model and store prediction in DB
├── models/lucan/           # Trained .pkl model files (not in git)
├── db/                     # SQLite database (not in git)
├── data/processed/         # Historical CSV data
├── setup_db.py             # Build database from Yahoo Finance
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## Quick Start — Docker (Recommended)

**Prerequisites:** Docker Desktop installed and running.

```bash
# Clone the repository
git clone https://github.com/BredaUniversityADSAI/2025-26d-fai1-adsai-group_15.git
cd 2025-26d-fai1-adsai-group_15

# Start the application
docker compose up
```

Open **http://localhost:5000** in your browser.

On first run the container automatically fetches all historical data from Yahoo Finance and builds the database (~30 seconds). Subsequent starts skip this step.

To rebuild after code changes:

```bash
docker compose up --build
```

---

## Quick Start — Local (Without Docker)

**Prerequisites:** Python 3.11+

### 1. Install dependencies

Using Poetry (recommended):

```bash
poetry install
poetry shell
```

Or using pip:

```bash
pip install -r dashboard/requirements.txt
pip install yfinance
```

### 2. Build the database

```bash
python setup_db.py
```

This fetches MSFT, Gold (GC=F), Crude Oil (CL=F), VIX (^VIX) and SPY data from Yahoo Finance and stores it in `db/stocks.db`.

### 3. Generate today's prediction

```bash
python src/msft_forecaster/predict.py
```

### 4. Start the dashboard

```bash
python dashboard/server.py
```

Open **http://localhost:5000** in your browser.

---

## Daily Data Update

To refresh the database with the latest market data and update the prediction:

```bash
python src/msft_forecaster/data/fetch_latest.py
python src/msft_forecaster/predict.py
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard UI |
| `GET /api/stock/history?days=90` | MSFT OHLCV history |
| `GET /api/stock/latest` | Latest MSFT data point |
| `GET /api/indicators/history` | Gold, Oil, VIX history |
| `GET /api/prediction/latest` | UP/DOWN prediction + confidence |
| `GET /api/model/metrics` | Model accuracy, F1, precision, recall |

---

## Running Tests

```bash
pytest tests/ -v --cov=src --cov=dashboard --cov-report=term-missing
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Data storage | SQLite |
| Data fetching | yfinance |
| Machine learning | scikit-learn, XGBoost |
| Dashboard backend | Flask, Flask-CORS |
| Dashboard frontend | HTML, CSS, Vanilla JS |
| Containerisation | Docker, Docker Compose |
| Dependency management | Poetry |

---

## Disclaimer

This tool is for **educational purposes only** and does not constitute financial advice. Predictions are based on historical patterns and do not guarantee future results.
