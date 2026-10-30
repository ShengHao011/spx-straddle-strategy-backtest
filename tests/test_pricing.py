from math import exp, sqrt

import pytest

from src.pricing import bs_price, straddle_mid

# Typical inputs used by most tests
S, K, T, r, q, sigma = 5800.0, 5800.0, 45 / 365, 0.04, 0.015, 0.15


# Proves call and put formulas are consistent with each other (a model-free identity).
@pytest.mark.parametrize("strike", [5000.0, 5800.0, 6500.0])
def test_put_call_parity(strike):
    call = bs_price(S, strike, T, r, q, sigma, "call")
    put = bs_price(S, strike, T, r, q, sigma, "put")
    assert call - put == pytest.approx(S * exp(-q * T) - strike * exp(-r * T), abs=1e-8)


# Proves the expiry branch returns payoff, not time value (and avoids dividing by zero).
def test_expiry_equals_intrinsic():
    assert bs_price(5900, 5800, 0, r, q, sigma, "call") == 100
    assert bs_price(5900, 5800, 0, r, q, sigma, "put") == 0
    assert bs_price(5700, 5800, 0, r, q, sigma, "put") == 100
    assert bs_price(5700, 5800, 0, r, q, sigma, "call") == 0


# Proves a straddle (long vol) gains value when implied vol rises and when time to expiry rises.
def test_straddle_increases_with_sigma_and_time():
    base = straddle_mid(S, K, T, r, q, sigma)
    assert straddle_mid(S, K, T, r, q, sigma + 0.05) > base
    assert straddle_mid(S, K, T + 30 / 365, r, q, sigma) > base


# Proves the price level is sensible: matches the trader's rule of thumb 0.8 * S * sigma * sqrt(T).
def test_atm_straddle_rule_of_thumb():
    approx = 0.8 * S * sigma * sqrt(T)            # about 244 points
    assert straddle_mid(S, K, T, r, q, sigma) == pytest.approx(approx, rel=0.05)


# Proves a typo in kind raises an error instead of silently returning a put price (also at expiry).
@pytest.mark.parametrize("T_", [T, 0.0])
def test_invalid_kind_raises(T_):
    with pytest.raises(ValueError):
        bs_price(S, K, T_, r, q, sigma, "Call")


# Proves a deep in-the-money call is worth its discounted forward intrinsic value (no time value left).
def test_deep_itm_call():
    strike = 3000.0
    call = bs_price(S, strike, T, r, q, sigma, "call")
    assert call == pytest.approx(S * exp(-q * T) - strike * exp(-r * T), abs=1e-6)
