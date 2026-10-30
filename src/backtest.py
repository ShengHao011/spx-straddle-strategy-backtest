"""Day-by-day backtest of the long ATM straddle. Rules: STRATEGY.md."""
import pandas as pd

from src.expiries import atm_strike, monthly_expiries, pick_expiry
from src.pricing import straddle_mid

LEGS = 2  # a straddle has two legs: one call and one put


def straddle_value(spx, vix, date, expiry, strike, cfg):
    """Model mid price of the straddle (index points) at the close of `date`."""
    T = (expiry - date).days / cfg.DAYS_PER_YEAR
    return straddle_mid(spx, strike, T, cfg.RISK_FREE_RATE, cfg.DIVIDEND_YIELD, vix / 100)


def close_trade(trade, cfg):
    """Add P&L in dollars (after costs) and as % of entry premium to a finished trade."""
    size = cfg.CONTRACT_MULTIPLIER * cfg.CONTRACTS_PER_LEG
    premium_paid = trade["entry_mid"] * size
    trade["pnl"] = (trade["exit_mid"] - trade["entry_mid"]) * size - trade["costs"]
    trade["pnl_pct"] = 100 * trade["pnl"] / premium_paid
    return trade


def run_backtest(data, cfg):
    """Loop over trading days in order. Returns (trades, equity) DataFrames."""
    days = data.index
    expiries = monthly_expiries(days)
    size = cfg.CONTRACT_MULTIPLIER * cfg.CONTRACTS_PER_LEG      # $ per index point of straddle
    # Cost of one fill (buy or sell): half spread + commission on each of the 2 legs.
    fill_cost = LEGS * cfg.CONTRACTS_PER_LEG * (cfg.HALF_SPREAD * cfg.CONTRACT_MULTIPLIER
                                                + cfg.COMMISSION_PER_CONTRACT)

    cash = cfg.ACCOUNT_SIZE
    position = None     # the open trade (a dict), or None when flat
    pending = None      # a signal from yesterday's close, filled at today's close
    trades = []
    equity_rows = []

    for i, t in enumerate(days):
        spx = data.at[t, "spx"]
        vix = data.at[t, "vix"]

        # A. Fill yesterday's signal at today's close (t+1 relative to the signal).
        if pending is not None:
            if pending["action"] == "buy":
                mid = straddle_value(spx, vix, t, pending["expiry"], pending["strike"], cfg)
                cash -= mid * size + fill_cost
                position = {
                    "signal_date": pending["signal_date"],
                    "entry_date": t,
                    "expiry": pending["expiry"],
                    "strike": pending["strike"],
                    "entry_dte": (pending["expiry"] - t).days,
                    "entry_mid": mid,
                    "costs": fill_cost,
                }
            else:  # "sell"
                mid = straddle_value(spx, vix, t, position["expiry"], position["strike"], cfg)
                cash += mid * size - fill_cost
                position["exit_date"] = t
                position["exit_mid"] = mid
                position["costs"] += fill_cost
                trades.append(close_trade(position, cfg))
                position = None
            pending = None

        # Value of the open straddle at today's close (used for exits and equity).
        mid_t = 0.0
        if position is not None:
            mid_t = straddle_value(spx, vix, t, position["expiry"], position["strike"], cfg)

        # B. Exit check: only for a position that was not bought today.
        if position is not None and t != position["entry_date"]:
            change = mid_t / position["entry_mid"] - 1       # e.g. +0.50 = up 50%
            dte = (position["expiry"] - t).days
            reason = None
            if change >= cfg.PROFIT_TARGET:
                reason = "profit"
            elif change <= -cfg.STOP_LOSS:
                reason = "stop"
            elif dte <= cfg.EXIT_DTE:
                reason = "time"
            if reason is not None:
                position["exit_signal_date"] = t
                position["exit_reason"] = reason
                pending = {"action": "sell"}

        # C. Entry check: only when flat, nothing pending, and there is a next day to fill on.
        if position is None and pending is None and i + 1 < len(days):
            expiry = pick_expiry(days[i + 1], expiries)     # DTE measured at the fill date
            if expiry is not None:
                pending = {"action": "buy", "signal_date": t,
                           "expiry": expiry, "strike": atm_strike(spx)}

        # D. Daily mark-to-market equity.
        position_value = mid_t * size
        equity_rows.append({"date": t, "cash": cash, "position_value": position_value,
                            "equity": cash + position_value, "in_position": position is not None})

    # End of data: a trade still open is marked at mid on the last day, without exit costs.
    if position is not None:
        position.setdefault("exit_signal_date", None)
        position["exit_reason"] = "open"
        position["exit_date"] = days[-1]
        position["exit_mid"] = mid_t
        trades.append(close_trade(position, cfg))

    columns = ["signal_date", "entry_date", "expiry", "strike", "entry_dte", "entry_mid",
               "exit_signal_date", "exit_date", "exit_reason", "exit_mid", "costs", "pnl", "pnl_pct"]
    trades = pd.DataFrame(trades, columns=columns)
    equity = pd.DataFrame(equity_rows).set_index("date")
    return trades, equity
