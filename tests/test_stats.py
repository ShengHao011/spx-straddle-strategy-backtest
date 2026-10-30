import numpy as np
import pandas as pd
import pytest

from src.stats import max_drawdown, sharpe


# Proves drawdown is measured from the running peak (120 -> 90), not from the start (100).
def test_max_drawdown():
    equity = pd.Series([100.0, 120.0, 90.0, 110.0])
    assert max_drawdown(equity) == pytest.approx(-0.25)


# Proves Sharpe returns NaN instead of dividing by zero when returns never vary.
def test_sharpe_constant_returns():
    returns = pd.Series([0.001] * 100)
    assert np.isnan(sharpe(returns))
