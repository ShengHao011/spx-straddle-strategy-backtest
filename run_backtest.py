"""Run the backtest, save results/trades.csv, results/equity.csv and
results/cost_sensitivity.csv, print a summary.

Run from the project root:  python run_backtest.py
"""
import os
from types import SimpleNamespace

import pandas as pd

import config
from src.backtest import run_backtest
from src.stats import daily_returns, sharpe

data = pd.read_csv(config.DATA_PATH, index_col="date", parse_dates=True)
trades, equity = run_backtest(data, config)

os.makedirs("results", exist_ok=True)
trades.to_csv("results/trades.csv", index=False, float_format="%.2f")
equity.to_csv("results/equity.csv", float_format="%.2f")

pd.set_option("display.width", 200)
show = ["entry_date", "expiry", "strike", "entry_dte", "entry_mid",
        "exit_date", "exit_reason", "exit_mid", "costs", "pnl", "pnl_pct"]
closed = trades[trades["exit_reason"] != "open"]      # open trade excluded from win/loss stats

print(f"Trades: {len(trades)} ({len(closed)} closed, {len(trades) - len(closed)} open)")
print("By exit reason:")
print(trades["exit_reason"].value_counts().to_string())
print(f"\nTotal P&L (after costs): ${trades['pnl'].sum():,.0f}")
print(f"Total costs paid:        ${trades['costs'].sum():,.0f}")
print(f"Days in a position:      {equity['in_position'].mean():.1%}")
print(f"Final equity:            ${equity['equity'].iloc[-1]:,.0f}")
print(f"Check: equity change - sum of trade P&L = "
      f"${equity['equity'].iloc[-1] - config.ACCOUNT_SIZE - trades['pnl'].sum():,.2f}")

print("\nFirst 5 trades:")
print(trades[show].head().round(2).to_string(index=False))
print("\n5 best closed trades:")
print(closed.nlargest(5, "pnl")[show].round(2).to_string(index=False))
print("\n5 worst closed trades:")
print(closed.nsmallest(5, "pnl")[show].round(2).to_string(index=False))

# --- Cost sensitivity: same rules, different trading costs ---
# Copy every setting from config, then override only the cost parameters.
base = {k: v for k, v in vars(config).items() if k.isupper()}
cases = [(0.0, 0.0), (0.25, config.COMMISSION_PER_CONTRACT), (0.5, config.COMMISSION_PER_CONTRACT),
         (1.0, config.COMMISSION_PER_CONTRACT), (2.0, config.COMMISSION_PER_CONTRACT)]
rows = []
for half_spread, commission in cases:
    cfg = SimpleNamespace(**{**base, "HALF_SPREAD": half_spread, "COMMISSION_PER_CONTRACT": commission})
    t, e = run_backtest(data, cfg)
    rows.append({"half_spread": half_spread, "commission": commission,
                 "total_costs": t["costs"].sum(), "total_pnl": t["pnl"].sum(),
                 "sharpe": sharpe(daily_returns(e["equity"]))})
sensitivity = pd.DataFrame(rows)
sensitivity.to_csv("results/cost_sensitivity.csv", index=False, float_format="%.2f")
print("\nCost sensitivity:")
print(sensitivity.round(2).to_string(index=False))
