# Write-up: Long ATM SPX Straddle, 2018–2026

## Summary
Buying a 45-day ATM SPX straddle every month lost 29% over 2018-2026 (Sharpe -0.84), and still lost about 27% before trading costs. Options are usually priced for more movement than actually follows (the volatility risk premium), so the buyer pays a little on most trades and only recovers it in sharp volatility spikes. The backtest is built to avoid lookahead, includes costs, and its main limits are modeled prices and strike drift in large gaps.

## Strategy (full spec in [STRATEGY.md](STRATEGY.md))
- **Entry:** when flat, buy 1 SPX call + 1 put on the monthly expiry (3rd Friday) with the most days left within 30–45 DTE at the fill date.
- **Strike:** SPX close on the signal day, rounded to the nearest 5 points.
- **Exits:** first of +50% or −50% of the premium paid (at mid), or 21 days to expiry.
- **Execution:** every signal at close t fills at close t+1, so no decision uses a price it trades at.
- **Costs:** $50 half spread (0.50 points) + $1.50 commission per leg per fill, about $206 per round trip.

Prices: Black-Scholes with VIX/100 as volatility, interest rate and dividends 0. Account $1M, one straddle at a time.

## Results (2018-01-02 to 2026-10-28)
| Total return | CAGR | Sharpe (rf 0%) | Max drawdown | Closed trades | Win rate | Avg win | Avg loss |
|---|---|---|---|---|---|---|---|
| −28.9% | −3.8% | −0.84 | −30.7% | 112 | 25% | +44.8% | −25.4% |

## Key findings
- **Why it loses:** implied volatility, which sets the option price, has usually been higher than the volatility that actually followed. A straddle buyer pays that gap on most trades. Using VIX (which sits above ATM implied vol) likely makes this cost somewhat larger in the backtest than it was in reality.
- **It loses about 29% over 8.8 years.** It wins 25% of the time. The average win is about 1.8× the average loss, but breaking even at a 25% win rate needs about 3×.
- **Profits come in bursts around volatility spikes.** The equity curve jumps in Feb 2018, Feb 2020 and Apr 2025. The largest profit exits were Apr 2025 (+$44.8k), Apr 2026 (+$28.6k), Jan 2022 (+$22.0k) and Feb 2020 (+$19.2k). In between, time decay erodes the account steadily.
- **The two largest losses were re-entries straight after a profit exit, at peak VIX.**
  - Mar 2020: bought at VIX 82.7 (its record close), lost $28.6k (−51%).
  - Apr 2025: bought at VIX 52.3, lost $19.8k (−29%).
  - Feb 2018 shows the same pattern on a smaller scale (VIX 27.7, −46%).

  This is buying insurance when it is most expensive. It is a tail effect, though, not an average one: across all 17 re-entries after a profit exit the mean result (−8.2%) is close to the other trades (−7.8%).
- **The loss is not from costs.** With zero spread and commission the strategy still loses $266k. Costs ($23k) add about 8% to the loss.
- **The stop-loss never triggered.** Time decay alone costs about 30% from 45 to 21 DTE, so the 21 DTE exit always comes before −50%. The worst result (−51%) came from the one-day fill delay after a time exit signalled at −37%.

## Validation
- **Pricer tests:** put-call parity at three strikes, payoff at expiry, price rises with volatility and time, ATM rule of thumb 0.8·S·σ·√T, deep in-the-money call, invalid input.
- **Hand-checked trade:** every input and intermediate value of the worst trade (Mar 2020) recomputed by hand and matched to the trade log.
- **Lookahead test:** re-running on data cut at 2022-12-30 gives identical results for all 65 trades finished by then. Limit: it cannot catch a one-day peek (using tomorrow's close today), because tomorrow exists in both runs. That is prevented by the loop structure: a signal can only fill at the next day's step.
- **Cost sensitivity:** half spread 0 to 2 points; the conclusion holds at every level (Sharpe −0.77 to −1.02).
- **Clean-environment reproduction:** a fresh virtual environment from `requirements.txt` passes all tests and reproduces the results files exactly.

## Limitations (most important first)
1. **Modeled prices.** VIX is used as the volatility for every option: no skew, no term structure. VIX is usually above ATM implied vol, so straddles are probably priced too high, which hurts a buyer.
2. **The strike is fixed at the signal close, so after large gaps it is far from ATM.** In Mar 2020 it was 324 points from spot at the fill. Fix: choose the strike at execution.
3. **The flat spread understates costs in volatility spikes,** the periods that matter most for a long-vol strategy.
4. **One-day fill delay** versus live trading, which could act before the same close.
5. **Monthly expiries only and one position at a time,** so results depend on when each entry happened to fall.
6. **Interest rate and dividends set to 0.** The effect is about 0.2% of the straddle price.

## What I'd do next
- Re-run on real historical SPX option chain data (bid/ask, skew, term structure) instead of modeled prices.
- Choose the strike at execution instead of at the signal close.
- Test a filter against re-entering at extreme VIX, judged on out-of-sample data only, since the evidence so far rests on a few trades.
