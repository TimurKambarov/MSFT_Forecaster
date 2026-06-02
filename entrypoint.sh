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

# Start the Streamlit dashboard
echo "Starting dashboard on http://0.0.0.0:8501"
exec streamlit run /app/dashboard/streamlit_app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
