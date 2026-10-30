"""All tunable parameters for the backtest. Change numbers here, never inside the code."""

# --- Data ---
START_DATE = "2018-01-01"              # first date of data downloaded / backtested
END_DATE = None                        # None = latest available data
TICKERS = {"spx": "^GSPC", "vix": "^VIX"}  # our column name -> Yahoo ticker
DATA_PATH = "data/market_data.csv"     # where the cleaned daily data is cached
MAX_FFILL_DAYS = 3                     # max consecutive missing days we forward-fill (VIX only)

# --- Account ---
ACCOUNT_SIZE = 1_000_000               # starting equity in USD; one straddle is ~1-7% of capital
CONTRACT_MULTIPLIER = 100              # SPX option = 100 x index points
CONTRACTS_PER_LEG = 1                  # 1 call + 1 put = one straddle

# --- Entry ---
ENTRY_DTE_MIN = 30                     # expiry must be >= 30 days from the fill date (t+1) to enter
DTE_MAX = 45                           # expiry must be <= 45 days from the fill date (t+1) to enter
STRIKE_ROUNDING = 5                    # ATM strike = SPX close rounded to nearest 5 points

# --- Exits (checked every close, first hit wins) ---
PROFIT_TARGET = 0.50                   # exit when position value >= premium paid x (1 + 0.50)
STOP_LOSS = 0.50                       # exit when position value <= premium paid x (1 - 0.50)
EXIT_DTE = 21                          # exit when days to expiry <= 21

# --- Pricing ---
RISK_FREE_RATE = 0.0                   # set to 0 for simplicity; ATM straddle is nearly insensitive to r and q (~0.2% of price)
DIVIDEND_YIELD = 0.0                   # set to 0 for simplicity; ATM straddle is nearly insensitive to r and q (~0.2% of price)
DAYS_PER_YEAR = 365.0                  # calendar-day convention for time to expiry

# --- Costs (commission estimated from IBKR/Cboe published fees; half spread illustrative) ---
COMMISSION_PER_CONTRACT = 1.50         # IBKR $0.65 + Cboe SPX fee ~$0.45 + surcharge/regulatory ≈ $1.10-1.35 per contract; rounded up to be conservative
HALF_SPREAD = 0.50                     # flat half bid-ask spread per option leg, in index points ($50)
