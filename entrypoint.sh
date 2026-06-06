#!/bin/sh
set -e

# Build the database on first run (requires internet for yfinance)
if [ ! -f /app/db/stocks.db ]; then
    echo "First run: building database from Yahoo Finance..."
    python /app/dashboard/setup_db.py
else
    echo "Database found, fetching latest data..."
    python /app/dashboard/msft_forecaster/data/fetch_latest.py
fi

# Generate today's prediction and store in DB
echo "Running prediction..."
python /app/dashboard/msft_forecaster/predict.py

# Start the dashboard server
echo "Starting dashboard on http://0.0.0.0:5000"
exec python /app/dashboard/server.py
