"""Download daily closes for SPX and VIX, clean them, save to CSV.

Run from the project root:  python -m src.fetch_data
"""
import pandas as pd
import yfinance as yf

import config


def download() -> pd.DataFrame:
    """Download raw daily closes from Yahoo. Columns: spx, vix. Index: date."""
    tickers = list(config.TICKERS.values())
    raw = yf.download(tickers, start=config.START_DATE, end=config.END_DATE,
                      auto_adjust=False, progress=False)
    closes = raw["Close"]                                   # keep only closing prices
    rename = {yahoo: ours for ours, yahoo in config.TICKERS.items()}
    closes = closes.rename(columns=rename)[list(config.TICKERS)]
    closes.index = pd.to_datetime(closes.index).tz_localize(None)
    closes.index.name = "date"
    return closes


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Align on SPX trading days and forward-fill small VIX gaps."""
    # 1. Our trading calendar = days SPX has a close. Drop days where only VIX traded.
    df = raw[raw["spx"].notna()].copy()
    print(f"Rows dropped because SPX had no close: {len(raw) - len(df)}")

    # 2. Report gaps before filling, so data issues are visible.
    missing = df.isna()
    print("Missing values on SPX trading days (before fill):")
    print(missing.sum().to_string())
    dates = df.index[missing["vix"]]
    if len(dates):
        print(f"  vix missing on: {', '.join(d.strftime('%Y-%m-%d') for d in dates)}")

    # 3. Forward-fill: use the last known value, but only for short gaps.
    #    Only past values are used, so this cannot introduce lookahead.
    df["vix"] = df["vix"].ffill(limit=config.MAX_FFILL_DAYS)

    # 4. Anything still missing is a gap too long to fill safely: drop and report it.
    still_missing = df[df.isna().any(axis=1)]
    if len(still_missing):
        print(f"Dropping {len(still_missing)} rows still missing after fill:")
        print(still_missing.to_string())
    df = df.dropna()
    return df


def main() -> None:
    raw = download()
    df = clean(raw)
    df.to_csv(config.DATA_PATH, float_format="%.6f")

    print(f"\nSaved {len(df)} rows to {config.DATA_PATH}")
    print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
    print(f"Missing values after cleaning: {int(df.isna().sum().sum())}")


if __name__ == "__main__":
    main()
