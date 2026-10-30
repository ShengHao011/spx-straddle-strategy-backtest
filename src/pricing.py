"""Black-Scholes prices for European options on an index that pays a continuous dividend yield.

Inputs (same for every function):
    S      spot price of the index (SPX close)
    K      strike
    T      time to expiry in years (calendar days / 365)
    r      risk-free rate, decimal (0.04 = 4%)
    q      dividend yield, decimal (0.015 = 1.5%)
    sigma  implied volatility, decimal (0.15 = 15%)
"""
from math import exp, log, sqrt

from scipy.stats import norm


def bs_price(S, K, T, r, q, sigma, kind):
    """Black-Scholes price of one European call or put (kind = "call" or "put")."""
    # Fail loudly on a typo like "Call" instead of silently pricing a put.
    if kind not in ("call", "put"):
        raise ValueError(f'kind must be "call" or "put", got {kind!r}')

    # At or after expiry there is no time value left: the option is worth what it pays now.
    if T <= 0:
        if kind == "call":
            return max(S - K, 0.0)
        return max(K - S, 0.0)

    # d1 and d2 measure how far the strike is from the expected future index level,
    # in units of volatility over the option's life (sigma * sqrt(T)).
    d1 = (log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    # N(x) = norm.cdf(x): probability that a standard normal variable is below x.
    # N(d2) is the (risk-neutral) probability the call finishes in the money;
    # e^(-qT) * N(d1) is the call's delta: points it moves per 1-point move in the index.
    if kind == "call":
        return S * exp(-q * T) * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    return K * exp(-r * T) * norm.cdf(-d2) - S * exp(-q * T) * norm.cdf(-d1)


def straddle_mid(S, K, T, r, q, sigma):
    """Model mid price of a straddle: one call plus one put, same strike and expiry."""
    return bs_price(S, K, T, r, q, sigma, "call") + bs_price(S, K, T, r, q, sigma, "put")
