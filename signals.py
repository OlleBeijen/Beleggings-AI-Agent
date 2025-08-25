from typing import Dict
import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.momentum import RSIIndicator

def indicators(df: pd.DataFrame, ma_short=20, ma_long=50, rsi_period=14) -> pd.DataFrame:
    out = df.copy()
    out["SMA_S"] = SMAIndicator(close=out["Close"], window=ma_short).sma_indicator()
    out["SMA_L"] = SMAIndicator(close=out["Close"], window=ma_long).sma_indicator()
    out["RSI"] = RSIIndicator(close=out["Close"], window=rsi_period).rsi()
    macd = MACD(close=out["Close"])
    out["MACD"] = macd.macd()
    out["MACD_SIG"] = macd.macd_signal()
    return out.dropna()

def signal_from_row(row, rsi_buy=35, rsi_sell=65):
    sig = "HOLD"
    if row["SMA_S"] > row["SMA_L"] and row["RSI"] < rsi_sell and row["MACD"] > row["MACD_SIG"]:
        sig = "BUY"
    if row["SMA_S"] < row["SMA_L"] and row["RSI"] > rsi_buy and row["MACD"] < row["MACD_SIG"]:
        sig = "SELL"
    return sig

def generate_signals(prices: Dict[str, pd.DataFrame], params: Dict) -> Dict[str, Dict]:
    out = {}
    for t, df in prices.items():
        ind = indicators(df, params["ma_short"], params["ma_long"], params["rsi_period"])
        if ind.empty: continue
        last = ind.iloc[-1]
        sig = signal_from_row(last, params["rsi_buy"], params["rsi_sell"])
        out[t] = {
            "signal": sig,
            "close": float(last["Close"]),
            "sma_s": float(last["SMA_S"]),
            "sma_l": float(last["SMA_L"]),
            "rsi": float(last["RSI"]),
            "macd": float(last["MACD"]),
            "macd_sig": float(last["MACD_SIG"]),
        }
    return out
