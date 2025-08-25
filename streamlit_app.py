import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st
import pandas as pd
import yaml

from agent import run_day
from backtest import backtest_ticker, backtest_portfolio
from data_sources import fetch_prices
from report import make_report_md, send_slack, send_email

st.set_page_config(page_title="Beleggings AI Agent", layout="wide")
st.title("Beleggings AI Agent (No‑Code)")

cfg_path = "config.yaml"
st.caption("Pas tickers/sectoren aan via de GitHub web‑editor.")

if st.button("Run nu"):
    rep = run_day(cfg_path)
    st.session_state["report"] = rep

rep = st.session_state.get("report")
if rep:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("Tijd"); st.write(rep["timestamp"])
    with c2:
        st.subheader("Tickers"); st.write(", ".join(sorted(rep["last_prices"].keys())))
    with c3:
        st.subheader("Risico"); st.json(rep["risk"])

    st.subheader("Sectorrapport"); st.dataframe(pd.DataFrame(rep["sector_report"]))
    st.subheader("Signalen"); st.dataframe(pd.DataFrame(rep["signals"]).T)
    st.subheader("5-daagse forecast"); st.dataframe(pd.DataFrame.from_dict(rep["forecast_5d"], orient="index", columns=["forecast_price"]).round(2))

    st.subheader("Kansen per sector (screener)")
    opp_rows = []
    for sec, items in rep["opportunities"].items():
        for t, score in items:
            opp_rows.append({"sector": sec, "ticker": t, "score": round(float(score), 3)})
    if opp_rows:
        st.dataframe(pd.DataFrame(opp_rows).sort_values(["sector","score"], ascending=[True, False]))
    else:
        st.info("Geen resultaten uit de screener.")

    st.markdown("### Rapport")
    md = make_report_md(rep)
    st.download_button("Download Markdown rapport", data=md, file_name="daily_report.md")
    if st.button("Verstuur (Slack/E-mail)"):
        sent_any = False
        slack_env = os.getenv("SLACK_WEBHOOK_URL")
        email_env = os.getenv("EMAIL_TO")
        if slack_env:
            ok, msg = send_slack(md); st.write("Slack:", "OK" if ok else f"FOUT: {msg}"); sent_any = sent_any or ok
        if email_env and os.getenv("SMTP_HOST"):
            ok, msg = send_email("Dagrapport Beleggings Agent", md); st.write("E-mail:", "OK" if ok else f"FOUT: {msg}"); sent_any = sent_any or ok
        if not sent_any:
            st.warning("Zet env vars (SLACK_WEBHOOK_URL of SMTP_* + EMAIL_TO).")

st.markdown("---")
st.header("Quick Backtest")
ticker = st.text_input("Ticker (bijv. ASML.AS, AAPL)", value="ASML.AS")
ma_s = st.number_input("MA kort", 5, 200, 20)
ma_l = st.number_input("MA lang", 10, 400, 50)
rsi_p = st.number_input("RSI periode", 5, 30, 14)
rsi_buy = st.number_input("RSI koop drempel", 5, 60, 35)
rsi_sell = st.number_input("RSI verkoop drempel", 40, 95, 65)
cost_bps = st.number_input("Transactiekosten (bps)", 0, 50, 5)

if st.button("Backtest draaien"):
    prices = fetch_prices([ticker])
    if ticker in prices:
        res = backtest_ticker(prices[ticker], {
            "ma_short": ma_s, "ma_long": ma_l, "rsi_period": rsi_p, "rsi_buy": rsi_buy, "rsi_sell": rsi_sell
        }, cost_bps=cost_bps)
        st.subheader("Metrics")
        st.json({k: (round(v,4) if isinstance(v, float) else v) for k, v in res["metrics"].items()})
        st.subheader("Equity curve"); st.line_chart(res["equity"])
    else:
        st.error("Geen data voor deze ticker.")

st.markdown("---")
st.header("Portfolio Backtest")
if Path(cfg_path).exists():
    cfg = yaml.safe_load(Path(cfg_path).read_text(encoding="utf-8"))
    tickers = cfg["portfolio"]["tickers"]
    weights = cfg["portfolio"].get("weights")
    st.write("Tickers:", ", ".join(tickers))
    custom_w = st.text_input("Gewichten (bijv. ASML.AS=0.3,AAPL=0.2,...). Leeg = equal weight.", value="")
    def parse_w(s):
        if not s: return None
        parts = [p.strip() for p in s.split(",") if p.strip()]
        w = {}
        for p in parts:
            t, v = p.split("="); w[t.strip()] = float(v)
        tot = sum(w.values()); 
        if abs(tot-1.0) > 1e-6: w = {k: v/tot for k, v in w.items()}
        return w
    if st.button("Portfolio backtest draaien"):
        prices = fetch_prices(tickers, lookback_days=cfg["data"]["lookback_days"])
        res = backtest_portfolio(prices, cfg["signals"], weights=parse_w(custom_w) or weights, cost_bps=5)
        st.subheader("Metrics"); st.json({k: (round(v,4) if isinstance(v, float) else v) for k, v in res["metrics"].items()})
        st.subheader("Equity curve (portfolio)"); st.line_chart(res["equity"])
else:
    st.info("config.yaml niet gevonden.")
