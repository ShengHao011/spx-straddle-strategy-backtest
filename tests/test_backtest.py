import pandas as pd

import config
from src.backtest import run_backtest

DATA = pd.read_csv(config.DATA_PATH, index_col="date", parse_dates=True)
TRADES, EQUITY = run_backtest(DATA, config)


# Proves one straddle at a time: each entry fills strictly after the previous exit (never the same day).
def test_no_overlap_and_no_same_day_exit_entry():
    trades = TRADES.sort_values("entry_date").reset_index(drop=True)
    for prev, nxt in zip(trades.iloc[:-1].itertuples(), trades.iloc[1:].itertuples()):
        assert nxt.entry_date > prev.exit_date


# Proves no lookahead: cutting off future data must not change any trade completed before the cutoff.
def test_no_lookahead():
    cutoff = pd.Timestamp("2022-12-30")
    cut_trades, _ = run_backtest(DATA.loc[:cutoff], config)
    full_done = TRADES[TRADES["exit_date"] <= cutoff].reset_index(drop=True)
    cut_done = cut_trades[(cut_trades["exit_date"] <= cutoff)
                          & (cut_trades["exit_reason"] != "open")].reset_index(drop=True)
    assert len(full_done) > 0
    pd.testing.assert_frame_equal(full_done, cut_done)


# Proves every trade opens inside the 30-45 DTE entry window, measured at the fill date.
def test_entry_dte_in_window():
    dte = (TRADES["expiry"] - TRADES["entry_date"]).dt.days
    assert dte.between(config.ENTRY_DTE_MIN, config.DTE_MAX).all()
