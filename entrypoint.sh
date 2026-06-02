#!/bin/sh
set -e

# Build the database on first run (requires internet for yfinance)
if [ ! -f /app/db/stocks.db ]; then
    echo "First run: building database from Yahoo Finance..."
    python /app/setup_db.py
else
    echo "Database found, skipping setup."
fi

# Generate today's prediction and store in DB
echo "Running prediction..."
python /app/src/msft_forecaster/predict.py

# Start the dashboard server
echo "Starting dashboard on http://0.0.0.0:5000"
exec python /app/dashboard/server.py
