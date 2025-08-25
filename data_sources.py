from typing import List, Dict
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def fetch_prices(tickers: List[str], lookback_days: int = 365) -> Dict[str, pd.DataFrame]:
    start = datetime.today() - timedelta(days=lookback_days*2)
    data = {}
    for t in tickers:
        try:
            df = yf.download(t, start=start.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
            if not df.empty:
                df = df.rename(columns=str.title)
                data[t] = df.dropna()
        except Exception as e:
            print(f"[WARN] Kon data niet ophalen voor {t}: {e}")
    return data

def latest_close(prices: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    return {t: float(df["Close"].iloc[-1]) for t, df in prices.items() if not df.empty}
