"This script is used to download the latest stock data for Microsoft, Gold, Oil, and VIX from Yahoo Finance and save it as CSV files. The data is downloaded for the period from February 1, 2025, to May 1, 2026."

import yfinance as yf # pip install yfinance

# Downloading the latest data for Microsoft, Gold, Oil, and VIX from Yahoo Finance
data_msft = yf.download("MSFT", start="2025-02-01", end="2026-05-01")
data_msft.to_csv("Microsoft_2025-2026.csv")

data_gld = yf.download("GLD", start="2025-02-01", end="2026-05-01")
data_gld.to_csv("Gold_2025-2026.csv")

data_oil = yf.download("^OVX", start="2025-02-01", end="2026-05-01")
data_oil.to_csv("Oil_2025-2026.csv")

data_vix = yf.download("^VIX", start="2025-02-01", end="2026-05-01")
data_vix.to_csv("VIX_2025-2026.csv")
