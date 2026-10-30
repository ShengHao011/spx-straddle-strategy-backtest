"""Monthly SPX expiry dates, entry expiry selection and ATM strike."""
import math

import pandas as pd

import config


def monthly_expiries(trading_days):
    """3rd Friday of every month in the data (plus 2 months after it), moved to the
    previous trading day if that Friday was a market holiday. Returns a sorted list."""
    days = pd.DatetimeIndex(trading_days)
    day_set = set(days)
    last_day = days[-1]

    # Go 2 months past the data so trades entered near the end still have an expiry.
    months = pd.period_range(days[0], last_day + pd.DateOffset(months=2), freq="M")

    expiries = []
    for month in months:
        first = month.start_time
        first_friday = first + pd.Timedelta(days=(4 - first.weekday()) % 7)  # weekday 4 = Friday
        expiry = first_friday + pd.Timedelta(weeks=2)
        # Holidays can only be checked for dates our data covers; future dates are kept as-is.
        if expiry <= last_day:
            while expiry not in day_set:
                expiry -= pd.Timedelta(days=1)
        expiries.append(expiry)
    return expiries


def pick_expiry(fill_date, expiries):
    """Expiry with the largest DTE in [ENTRY_DTE_MIN, DTE_MAX] measured from fill_date, else None."""
    eligible = [e for e in expiries
                if config.ENTRY_DTE_MIN <= (e - fill_date).days <= config.DTE_MAX]
    if not eligible:
        return None
    return max(eligible)          # latest date = largest DTE


def atm_strike(spx_close):
    """SPX close rounded to the nearest STRIKE_ROUNDING points; exact ties round up."""
    # floor(x + 0.5) always rounds .5 up. Python's round() would round .5 to the
    # nearest even number instead (round(2.5) == 2), which is not our rule.
    step = config.STRIKE_ROUNDING
    return step * math.floor(spx_close / step + 0.5)
