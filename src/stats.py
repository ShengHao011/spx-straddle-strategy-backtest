"""Summary statistics for the dashboard. Each function does one calculation."""
import numpy as np

TRADING_DAYS = 252      # trading days per year, used to annualise daily numbers


def daily_returns(equity):
    """% change in equity from one close to the next."""
    return equity.pct_change().dropna()


def total_return(equity):
    """Final equity / starting equity - 1."""
    return equity.iloc[-1] / equity.iloc[0] - 1


def cagr(equity):
    """Compound annual growth rate: the constant yearly return that gives the same end result."""
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    return (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1


def annual_volatility(returns):
    """Standard deviation of daily returns, scaled to a year."""
    return returns.std() * np.sqrt(TRADING_DAYS)


def sharpe(returns):
    """Mean daily return / std of daily returns, scaled to a year. 0% risk-free rate.
    Returns NaN when returns never vary (std = 0) instead of dividing by zero."""
    std = returns.std()
    if np.isnan(std) or np.isclose(std, 0):
        return np.nan
    return returns.mean() / std * np.sqrt(TRADING_DAYS)


def drawdown(equity):
    """For each day: % below the highest equity reached so far (0 at a new high)."""
    return equity / equity.cummax() - 1


def max_drawdown(equity):
    """Worst (most negative) drawdown over the whole period."""
    return drawdown(equity).min()


def summary(equity_df, trades):
    """All dashboard stats in one dict. Trade stats use closed trades only."""
    equity = equity_df["equity"]
    returns = daily_returns(equity)
    closed = trades[trades["exit_reason"] != "open"]
    wins = closed[closed["pnl"] > 0]
    losses = closed[closed["pnl"] <= 0]
    return {
        "Total return": total_return(equity),
        "CAGR": cagr(equity),
        "Annual volatility": annual_volatility(returns),
        "Sharpe (rf = 0%)": sharpe(returns),
        "Max drawdown": max_drawdown(equity),
        "Closed trades": len(closed),
        "Win rate": len(wins) / len(closed),
        "Average win %": wins["pnl_pct"].mean(),
        "Average loss %": losses["pnl_pct"].mean(),
        "Best trade %": closed["pnl_pct"].max(),
        "Worst trade %": closed["pnl_pct"].min(),
        "Total costs paid": trades["costs"].sum(),
        "% of days in a position": equity_df["in_position"].mean(),
    }
