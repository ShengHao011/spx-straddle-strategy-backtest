# Strategy: Long ATM SPX Straddle (buying volatility)

All numbers in *italics* are parameters in [config.py](config.py).
Ambiguities found while writing the rules, and how each was decided, are listed in §12.

## 1. Data
- Daily closes of SPX (`^GSPC`) and VIX (`^VIX`) from Yahoo Finance. Interest rate and dividend yield are set to 0 (no rate data needed).
- Trading calendar = days on which SPX has a close. Period: *START_DATE* (2018-01-01) to latest available.
- VIX gaps of up to *MAX_FFILL_DAYS* (3) consecutive SPX trading days are forward-filled; longer gaps are dropped.

## 2. Definitions
- **t** = a trading day; **t+1** = the next trading day in the calendar.
- **Monthly expiry** = 3rd Friday of each calendar month. If that Friday is not a trading day, expiry = the previous trading day (e.g. Good Friday 2025-04-18 -> 2025-04-17).
- **DTE(d, E)** = calendar days between date d and expiry date E (`(E - d).days`).
- **Straddle** = *CONTRACTS_PER_LEG* (1) call + 1 put, same strike, same expiry. Multiplier *CONTRACT_MULTIPLIER* (100).

## 3. Entry
At the close of day t, if **no position is open** (see §6 for the exact meaning):
1. **Expiry:** an expiry E is eligible only if its DTE measured at the **fill date** t+1 satisfies *ENTRY_DTE_MIN* (30) <= DTE(t+1, E) <= *DTE_MAX* (45). Choose the eligible expiry with the largest DTE. If no expiry is eligible, no trade is signalled that day.
   - *Why 30, not 21:* prevents entering at ~22 DTE and being forced out by the 21 DTE exit a day later.
   - *Why measured at t+1:* guarantees every trade opens inside the assignment's 21–45 DTE window, even when a weekend or holiday sits between signal and fill. The date t+1 is known at t from the published exchange calendar, so this is not lookahead.
   - Consequence: monthlies are 28 or 35 days apart and the window is 16 days wide, so on some days no expiry is eligible and the strategy waits.
2. **Strike:** K = SPX close(t) rounded to the nearest *STRIKE_ROUNDING* (5) points; exact ties (e.g. 5,002.50) round up.
3. A **buy signal** is generated. Expiry and strike are fixed at t (at the t+1 fill the strike may no longer be exactly ATM).

## 4. Execution (no lookahead)
- Every signal (entry or exit) observed at close t is **filled at close t+1**, using SPX and VIX of t+1.
- Buy fills: pay model mid + half spread per leg + commission per leg.
- Sell fills: receive model mid − half spread per leg − commission per leg.

## 5. Exits
Checked at each close t while a position is open (not on the fill day itself), in this order — first hit wins:
1. **Profit target:** straddle mid value(t) >= entry premium × (1 + *PROFIT_TARGET*) (i.e. +50%).
2. **Stop loss:** straddle mid value(t) <= entry premium × (1 − *STOP_LOSS*) (i.e. −50%).
3. **Time exit:** DTE(t, E) <= *EXIT_DTE* (21), i.e. the first close with DTE ≤ 21 (covers 21 DTE falling on a weekend/holiday).

"Entry premium" = straddle **mid** price at the entry fill (excluding costs).
The exit is filled at close t+1, so realised P&L can be beyond ±50%.

Expected behaviour: with no move and flat VIX, an ATM straddle's value scales with sqrt(time), so holding to 21 DTE loses about 1 - sqrt(21/DTE_entry). Most entries occur at ~43-45 DTE (the next expiry enters the window from above), so a typical calm-market trade exits at 21 DTE with ~-30%. Re-entries after early exits can start nearer 30 DTE and lose less (~-16%). Profit and stop exits mainly occur during volatility shifts.

## 6. Position state and re-entry
- A position is open from the close of its entry fill day until the close of its exit fill day.
- When an exit fills at close t+1, the account is flat at that close. An entry signal may be generated at that same close (§3) and fills at close t+2.
- No same-day exit-and-entry: an exit fill and an entry fill never happen on the same close.
- A position still open at the end of the data is marked at mid on the last day, shown in the trade log as 'open', and excluded from win/loss statistics.

## 7. Pricing model
- Black-Scholes European call/put (the formula supports a dividend yield and interest rate; both set to 0 here, see §10 #4).
- Spot S = SPX close; volatility σ = VIX/100 for every strike and expiry; r = *RISK_FREE_RATE* (0); q = *DIVIDEND_YIELD* (0).
- Time T = DTE / *DAYS_PER_YEAR* (365).

## 8. Costs
Per option leg, per fill (entry and exit):
- Commission: *COMMISSION_PER_CONTRACT* ($1.50) per contract. IBKR $0.65 + Cboe SPX fee ~$0.45 + surcharge/regulatory ≈ $1.10-1.35 per contract; rounded up to be conservative.
- Half bid-ask spread: flat *HALF_SPREAD* (0.50 index points) per contract, regardless of market conditions. Cost in USD = half spread × multiplier ($50 per leg).

## 9. Sizing and equity
- One straddle at a time, account *ACCOUNT_SIZE* ($1,000,000).
- Equity(t) = cash + mark-to-market value of open position at **mid** (costs already deducted from cash when paid).
- Cash earns no interest; no margin (a long straddle is fully paid).

## 10. Assumptions (simplifications we disclose)
1. Option prices are **modeled**, not real quotes.
2. VIX is used as the IV for the ATM option at any tenor 21–45 DTE: no skew, no term structure. VIX is a 30-day, variance-swap-style measure that is usually a bit **above** ATM IV, so modeled straddles are likely somewhat overpriced (bad for a long-vol strategy).
3. Real SPX monthlies are AM-settled (last trade Thursday); we model settlement at Friday's close. This never binds because the 21 DTE exit closes every trade weeks before expiry.
4. Interest rate and dividend yield set to 0. Checked: a 45 DTE ATM straddle at VIX 15 (S=5800) prices 243.3 with r=4%, q=1.5% vs 243.7 with r=q=0 (~0.2%), because the effects offset between call and put.
5. European exercise (correct for SPX).
6. Fills at the closing model price ± half spread; no slippage beyond that, no market impact.
7. Commission estimated from IBKR/Cboe published fees; half spread is an illustrative estimate.
8. The half spread is flat, but real spreads widen sharply in volatility spikes (e.g. March 2020), so costs are understated in exactly the periods that matter most for a long-vol strategy.
9. Yahoo Finance data assumed correct apart from the small gaps handled in §1.
10. Account size $1M: one 45 DTE ATM SPX straddle cost ~$7k (calm 2018) to ~$73k (April 2025 spike) over the period, i.e. ~1-7% of a $1M account. With $100k, a single trade could be 70% of capital and sizing would dominate the drawdowns.
11. Signals at close t fill at close t+1: a one-day reaction delay versus live trading, which could signal and trade before the same close.
12. Idle cash earns no interest, to isolate strategy returns; Sharpe is therefore computed with a 0% risk-free rate.

## 11. Outputs
- **Trade log:** one row per trade with entry/exit dates, expiry, strike, entry/exit premium, costs, and P&L both **in dollars** and **as % of premium paid**.
- Daily equity curve, drawdown series and summary statistics (built in later steps).
- % of trading days with a position open.
- Total costs paid (commissions + half spreads).

## 12. Ambiguities (all resolved)
| # | Ambiguity | Decision |
|---|-----------|----------|
| 1 | "Closest to 45 DTE, only if within 21–45" | **RESOLVED:** largest DTE with 30 <= DTE(t+1) <= 45; if none, no signal (§3) |
| 2 | Strike/expiry chosen at signal day t or fill day t+1? | **RESOLVED:** fixed at t; strike rounds to nearest 5, ties up (§3) |
| 3 | Do exit signals also wait one day? | **RESOLVED:** filled at t+1, consistent with entries (§5) |
| 4 | 21 DTE falls on a weekend/holiday | **RESOLVED:** trigger at first close with DTE ≤ 21 (§5) |
| 5 | Is ±50% measured on mid premium or on cost-inclusive premium? | **RESOLVED:** mid premium; costs only hit equity (§5) |
| 6 | Re-entry timing after an exit | **RESOLVED:** flat at the exit-fill close; entry may be signalled at that close, fills next day (§6) |
| 7 | 3rd Friday is a market holiday (e.g. Good Friday 2019-04-19, 2022-04-15, 2025-04-18) | **RESOLVED:** expiry = previous trading day (§2) |
| 8 | ^IRX is a discount-basis yield, BS needs a continuous rate | **SUPERSEDED:** r = q = 0, IRX no longer used (§7, §10) |
