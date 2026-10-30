import pandas as pd

import config
from src.expiries import atm_strike, monthly_expiries, pick_expiry

DATA = pd.read_csv(config.DATA_PATH, index_col="date", parse_dates=True)
EXPIRIES = monthly_expiries(DATA.index)


# Proves the holiday rule: Good Friday 2025-04-18 was closed, so expiry moves back to Thursday.
def test_good_friday_2025_moves_to_thursday():
    april = [e for e in EXPIRIES if e.year == 2025 and e.month == 4]
    assert april == [pd.Timestamp("2025-04-17")]


# Proves the largest eligible DTE is picked, including an expiry beyond the end of the data.
def test_pick_expiry_45_dte():
    assert pick_expiry(pd.Timestamp("2026-10-06"), EXPIRIES) == pd.Timestamp("2026-11-20")


# Proves no entry when nothing is in the window (Oct 16 is 11 DTE, Nov 20 is 46 DTE).
def test_pick_expiry_none_in_window():
    assert pick_expiry(pd.Timestamp("2026-10-05"), EXPIRIES) is None


# Proves rounding to the nearest 5 with exact ties rounded up (not to even).
def test_atm_strike():
    assert atm_strike(5812) == 5810
    assert atm_strike(5812.5) == 5815
    assert atm_strike(5817.6) == 5820
