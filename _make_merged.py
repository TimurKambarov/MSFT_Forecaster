"""One-off script to create msft_merged.csv from raw CSV files."""

import pandas as pd
import yfinance as yf
from pathlib import Path

RAW = Path(r"C:\Users\lucan\OneDrive - BUas\GitHub\2025-26d-fai1-adsai-group_15\data\raw")
OUT = Path(
    r"C:\Users\lucan\OneDrive - BUas\GitHub\2025-26d-fai1-adsai-group_15\msft-forecaster\data\processed\msft_merged.csv"
)


def _parse_date(series: pd.Series) -> pd.Series:
    """Parse dates robustly, stripping timezone info."""
    parsed = pd.to_datetime(series, utc=True).dt.tz_localize(None).dt.normalize()
    return parsed


# ── MSFT ──────────────────────────────────────────────────────────────────────
msft = pd.read_csv(RAW / "MSFT.csv")
msft["Date"] = _parse_date(msft["Date"])
msft = msft[["Date", "Open", "High", "Low", "Close", "Volume"]]
msft.columns = ["date", "open", "high", "low", "close", "volume"]

msft2 = pd.read_csv(
    RAW / "Microsoft_2025-2026.csv",
    skiprows=3,
    header=None,
    names=["date", "close", "high", "low", "open", "volume"],
)
msft2["date"] = _parse_date(msft2["date"])
msft2 = msft2[["date", "open", "high", "low", "close", "volume"]]

msft_all = (
    pd.concat([msft, msft2], ignore_index=True)
    .drop_duplicates("date")
    .sort_values("date")
    .reset_index(drop=True)
)
print(
    f"MSFT: {len(msft_all)} rows | {msft_all['date'].min().date()} - {msft_all['date'].max().date()}"
)

# ── Gold → gold_close ────────────────────────────────────────────────────────
gold = pd.read_csv(RAW / "Gold.csv", usecols=["Date", "Close"])
gold["date"] = _parse_date(gold["Date"])
gold = gold[["date", "Close"]].rename(columns={"Close": "gold_close"})

gold2 = pd.read_csv(
    RAW / "Gold_2025-2026.csv",
    skiprows=3,
    header=None,
    names=["date", "close", "high", "low", "open", "volume"],
)
gold2["date"] = _parse_date(gold2["date"])
gold2 = gold2[["date", "close"]].rename(columns={"close": "gold_close"})

gold_all = (
    pd.concat([gold, gold2], ignore_index=True)
    .drop_duplicates("date")
    .sort_values("date")
    .reset_index(drop=True)
)
print(
    f"Gold: {len(gold_all)} rows | {gold_all['date'].min().date()} - {gold_all['date'].max().date()}"
)

# ── Oil → oil_close ──────────────────────────────────────────────────────────
oil = pd.read_csv(RAW / "CrudeOil.csv", usecols=["Date", "Close"])
oil["date"] = _parse_date(oil["Date"])
oil = oil[["date", "Close"]].rename(columns={"Close": "oil_close"})
print(f"Oil : {len(oil)} rows | {oil['date'].min().date()} - {oil['date'].max().date()}")

# ── VIX — daily data via yfinance ────────────────────────────────────────────
start_date = msft_all["date"].min().strftime("%Y-%m-%d")
end_date = msft_all["date"].max().strftime("%Y-%m-%d")
print(f"Downloading ^VIX from yfinance ({start_date} to {end_date})...")
vix_raw = yf.download("^VIX", start=start_date, end=end_date, auto_adjust=True, progress=False)
vix_all = vix_raw[["Close"]].rename(columns={"Close": "vix"}).reset_index()
vix_all.columns = ["date", "vix"]
vix_all["date"] = pd.to_datetime(vix_all["date"]).dt.normalize()
print(
    f"VIX : {len(vix_all)} rows | {vix_all['date'].min().date()} - {vix_all['date'].max().date()}"
)

# ── SPY — daily close via yfinance ────────────────────────────────────────────
print(f"Downloading SPY from yfinance ({start_date} to {end_date})...")
spy_raw = yf.download("SPY", start=start_date, end=end_date, auto_adjust=True, progress=False)
spy_all = spy_raw[["Close"]].rename(columns={"Close": "spy_close"}).reset_index()
spy_all.columns = ["date", "spy_close"]
spy_all["date"] = pd.to_datetime(spy_all["date"]).dt.normalize()
print(
    f"SPY : {len(spy_all)} rows | {spy_all['date'].min().date()} - {spy_all['date'].max().date()}"
)

# ── Merge ─────────────────────────────────────────────────────────────────────
df = (
    msft_all.merge(gold_all, on="date", how="left")
    .merge(oil, on="date", how="left")
    .merge(vix_all, on="date", how="left")
    .merge(spy_all, on="date", how="left")
)

df[["gold_close", "oil_close", "vix", "spy_close"]] = df[
    ["gold_close", "oil_close", "vix", "spy_close"]
].ffill()
df = df.dropna().sort_values("date").reset_index(drop=True)

# Rename date to Date for notebook compatibility
df = df.rename(
    columns={
        "date": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
)

df.to_csv(OUT, index=False)
print(f"\nSaved: {OUT}")
print(f"Shape: {df.shape}")
print(df.head(3).to_string())
