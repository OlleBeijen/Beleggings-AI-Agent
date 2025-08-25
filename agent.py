from typing import Dict
import yaml
from pathlib import Path
from .data_sources import fetch_prices, latest_close
from .signals import generate_signals
from .forecasting import simple_forecast
from .portfolio import sector_report
from .scanner import screen_universe
from .utils import now_ams

def run_day(config_path: str = "config.yaml") -> Dict:
    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    tickers = cfg["portfolio"]["tickers"]
    lookback = cfg["data"]["lookback_days"]

    prices = fetch_prices(tickers, lookback_days=lookback)
    last = latest_close(prices)
    sigs = generate_signals(prices, cfg["signals"])
    fc = simple_forecast(prices, horizon_days=5)
    sector_df = sector_report(cfg["sectors"], last)
    opps = screen_universe(cfg["sectors"])

    return {
        "timestamp": now_ams(),
        "last_prices": last,
        "signals": sigs,
        "forecast_5d": fc,
        "sector_report": sector_df.to_dict(orient="records"),
        "opportunities": opps,
        "risk": cfg["risk"],
    }
