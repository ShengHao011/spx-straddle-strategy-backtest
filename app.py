"""Dashboard for the backtest results.

Run from the project root:  python run_backtest.py   then   streamlit run app.py
"""
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import config
from src.stats import drawdown, summary

st.set_page_config(page_title="SPX Straddle Backtest", layout="wide")

st.title("Long ATM SPX Straddle Backtest")
st.write("Buys one at-the-money SPX call + put at 30-45 DTE and exits at +50%, -50% or 21 DTE. "
         "Option prices are **modeled** with Black-Scholes using VIX as implied volatility.  \n"
         "Full rules and assumptions: STRATEGY.md.")

# --- Load results ---
if not (os.path.exists("results/trades.csv") and os.path.exists("results/equity.csv")):
    st.error("Results not found. Run `python run_backtest.py` first.")
    st.stop()

trades = pd.read_csv("results/trades.csv",
                     parse_dates=["signal_date", "entry_date", "expiry", "exit_signal_date", "exit_date"])
equity = pd.read_csv("results/equity.csv", index_col="date", parse_dates=True)
market = pd.read_csv(config.DATA_PATH, index_col="date", parse_dates=True)
stats = summary(equity, trades)

# --- Stats rows ---
row1 = st.columns(5)
row1[0].metric("Total return", f"{stats['Total return']:.1%}")
row1[1].metric("CAGR", f"{stats['CAGR']:.1%}")
row1[2].metric("Annual volatility", f"{stats['Annual volatility']:.1%}")
row1[3].metric("Sharpe (rf = 0%)", f"{stats['Sharpe (rf = 0%)']:.2f}")
row1[4].metric("Max drawdown", f"{stats['Max drawdown']:.1%}")

row2 = st.columns(6)
row2[0].metric("Closed trades", stats["Closed trades"])
row2[1].metric("Win rate", f"{stats['Win rate']:.0%}")
row2[2].metric("Average win", f"{stats['Average win %']:+.1f}%")
row2[3].metric("Average loss", f"{stats['Average loss %']:+.1f}%")
row2[4].metric("Best trade", f"{stats['Best trade %']:+.1f}%")
row2[5].metric("Worst trade", f"{stats['Worst trade %']:+.1f}%")

row3 = st.columns(5)
row3[0].metric("Total costs paid", f"${stats['Total costs paid']:,.0f}")
row3[1].metric("Days in a position", f"{stats['% of days in a position']:.0%}")

# --- Cost sensitivity: same trades, different cost assumptions ---
st.subheader("Cost sensitivity")
if os.path.exists("results/cost_sensitivity.csv"):
    sensitivity = pd.read_csv("results/cost_sensitivity.csv")
    st.dataframe(sensitivity.round(2), hide_index=True)
    st.caption("Half spread in index points per leg; commission in $ per contract. "
               "First row is frictionless. Trades are identical in every row because exits trigger on mid prices.")
else:
    st.info("Run `python run_backtest.py` to create results/cost_sensitivity.csv.")

# --- Charts: three panels stacked on one shared x-axis, so dates line up ---
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                    subplot_titles=("Equity ($)", "Drawdown (% below previous peak)", "VIX"))
fig.add_trace(go.Scatter(x=equity.index, y=equity["equity"], name="Equity"), row=1, col=1)
fig.add_trace(go.Scatter(x=equity.index, y=drawdown(equity["equity"]) * 100, name="Drawdown",
                         fill="tozeroy"), row=2, col=1)
fig.add_trace(go.Scatter(x=market.index, y=market["vix"], name="VIX"), row=3, col=1)
fig.update_layout(height=800, showlegend=False, margin=dict(t=40, b=20))
fig.update_yaxes(ticksuffix="%", row=2, col=1)
st.plotly_chart(fig, use_container_width=True)

# --- Trade table (click a column header to sort) ---
st.subheader("Trades")
table = trades.copy()
for col in ["signal_date", "entry_date", "expiry", "exit_signal_date", "exit_date"]:
    table[col] = table[col].dt.date
st.dataframe(table.round(2), use_container_width=True, hide_index=True)

# --- Limitations ---
st.warning(
    "**Limitations**\n"
    "1. Option prices are modeled from VIX: no volatility skew and no term structure.\n"
    "2. A flat bid-ask spread understates trading costs in volatility spikes.\n"
    "3. Signals at a close fill at the next close: a one-day delay versus live trading.\n"
    "4. One position at a time, so results depend on when each entry happened to occur."
)
