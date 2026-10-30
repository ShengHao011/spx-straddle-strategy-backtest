# SPX Long Straddle Backtest

A backtest of a long at-the-money SPX straddle (buying volatility), January 2018 to October 2026.
Option prices are **modeled** with Black-Scholes using VIX as the implied volatility, not taken
from real quotes. Results are shown in a Streamlit dashboard: equity curve, drawdowns, VIX,
trade list, summary statistics and cost sensitivity.

## Quick start (tested on Python 3.12)
```bash
pip install -r requirements.txt
python run_backtest.py
streamlit run app.py --server.address localhost
```
`data/market_data.csv` is included so results reproduce exactly. To re-download SPX and VIX
from Yahoo Finance instead, run `python -m src.fetch_data` (results will then include newer days).

## Project structure
```
config.py              every tunable number (DTE window, exits, costs, account size)
run_backtest.py        runs the backtest, saves results/, prints a summary
app.py                 Streamlit dashboard
src/fetch_data.py      downloads SPX and VIX closes from Yahoo Finance
src/pricing.py         Black-Scholes call/put and straddle prices
src/expiries.py        monthly expiry dates, expiry selection, ATM strike
src/backtest.py        day-by-day loop: signals, fills, trade log, daily equity
src/stats.py           return, CAGR, volatility, Sharpe, drawdown
data/market_data.csv   cached daily SPX and VIX closes
results/               trades.csv, equity.csv, cost_sensitivity.csv
tests/                 pytest tests for pricing, expiries, backtest and stats
STRATEGY.md            full rules and assumptions
WRITEUP.md             results, findings and limitations
```

## Tests
```bash
pytest
```
(`pytest.ini` adds the project root to the import path, so the tests can import `src` and `config`.)

## More
- [STRATEGY.md](STRATEGY.md): full rules, precise enough to reproduce every trade.
- [WRITEUP.md](WRITEUP.md): results, key findings and limitations.
