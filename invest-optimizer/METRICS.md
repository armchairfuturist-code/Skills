# Market Metrics Reference

Thresholds and interpretation for the market axes the Invest Optimizer reads. All values are current-snapshot checks; a metric outside the range for its axis contributes to the synthesized **market pulse**.

## Valuation

### Shiller CAPE Ratio
Price ÷ 10-year average inflation-adjusted earnings. Long-run mean ~17.

| Range | Verdict | Forward return implication |
|---|---|---|
| < 10 | CHEAP | Historically strong 10-year returns |
| 10–17 | FAIR | Near long-run mean |
| 17–25 | RICH | Below-average forward returns |
| 25–35 | EXTREME | Historically very weak forward returns |
| > 35 | BUBBLE | Only exceeded pre-1929 and 1999-2000 |

High CAPE is the single best long-run return predictor — it has historically meant weak returns over the following decade, not the next week.

### Buffett Indicator
Total US stock market value ÷ GDP. "Probably the best single measure of where valuations stand" — Warren Buffett.

| Threshold | Verdict |
|---|---|
| < 80% | CHEAP |
| 80–120% | FAIR |
| 120–150% | RICH |
| 150–200% | PLAYING WITH FIRE |
| > 200% | EXTREME |

### Tobin's Q
Market value of companies ÷ replacement cost. Long-run mean ~0.75. Above 1 means the market prices companies above their tangible worth.

| Range | Verdict |
|---|---|
| < 0.5 | VERY CHEAP |
| 0.5–0.75 | CHEAP |
| 0.75–1.0 | FAIR |
| 1.0–1.5 | RICH |
| > 1.5 | VERY RICH |

### S&P 500 ÷ M2
Valuation adjusted for the money supply. Filters out "record highs" that are really just monetary inflation.

No fixed thresholds — compare to the series' own history. A reading in the 90th+ percentile = RICH.

## Complacency

### VIX — CBOE Volatility Index
Implied volatility of S&P 500 options. Sustained low VIX is a more dangerous tell than a spike: low VIX means no one is hedging.

| Range | Verdict | Meaning |
|---|---|---|
| < 12 | COMPLACENT | Investors pricing in no risk — classic late-cycle tell |
| 12–18 | NEUTRAL | Normal range |
| 18–25 | CONCERN | Elevated fear |
| 25–35 | FEAR | High fear, late stages of sell-off |
| > 35 | PANIC | Crisis-level fear, historically a buying signal |

### High-Yield Credit Spread
Junk bond yield over Treasuries.

| Spread | Verdict | Meaning |
|---|---|---|
| < 3% | TIGHT | Froth — lenders pricing in almost no risk |
| 3–5% | NORMAL | Typical range |
| 5–8% | WIDENING | Stress building |
| > 8% | DISTRESS | Crisis — credit markets seizing |

## Macro

### Yield Curve — 10y − 2y

| State | Verdict | Meaning |
|---|---|---|
| > +0.5% | EXPANSION | Normal growth — steep curve |
| 0% to +0.5% | WARNING | Late cycle — flattening, slowing growth |
| < 0% (inverted) | RECESSION | Recession warning — most reliable lead indicator |
| Recently un-inverted | CRISIS | Recession typically hits after un-inversion, not during |

The recession usually arrives 6–18 months after the curve un-inverts.

## Market Microstructure and Liquidity

Use observable inputs; never infer AI causality from price shape alone. Report the instrument universe, sampling interval, lookback, and data source.

### Liquidity stress composite

Combine available measures: quoted/effective spread percentile, depth, volume participation, Amihud price impact, gap frequency, and realized-versus-implied volatility. Compare each with its own history rather than universal cutoffs.

| State | Evidence | Portfolio implication |
|---|---|---|
| LIQUID | most measures below 50th historical percentile | normal sizing and execution assumptions |
| NORMAL | measures broadly 50th–80th percentile | standard cost model; monitor |
| FRAGILE | two or more measures above 80th percentile | reduce size; stage trades; raise impact/slippage stress |
| DISLOCATED | spread/impact/gaps above 95th percentile or trading impairment | preserve liquidity; bounded-loss hedges; manual review |

### Intraday tail proxy

`tools/market_pulse.py` counts SMH days with >3% high-low range. This is a sector-ETF range proxy—not a V-reversal measure, flash-crash count, market-wide statistic, or estimate of AI participation. Use it only as corroborating evidence and state those limitations.

### AI/automation attribution

Only report AI or automated-volume share when a dated source defines the venue, asset class, sampling method, and whether it measures order submissions, trades, or notional volume. Otherwise mark attribution **UNKNOWN**. Automated execution, systematic trading, high-frequency trading, and AI are not interchangeable.

## Correlation Regime

Pairwise equity correlations and equity–credit/bond linkage determine whether diversification in the posture matrix is real or illusory. A book of 20 tech names with pairwise ρ > 0.8 is one bet.

### Average pairwise equity correlation

SPX constituents or the portfolio's own names; state window (default 60–90 trading days).

| Level | Verdict | Meaning |
|---|---|---|
| < 0.30 | DIVERSIFIED | Idiosyncratic risk dominates — stock picks and sector tilts earn their keep |
| 0.30–0.50 | NORMAL | Standard multi-asset assumptions hold |
| 0.50–0.70 | ELEVATED | Diversification decaying — prefer factor/risk-parity over name count |
| > 0.70 | CRISIS-CORR | Correlations collapsing to 1 — equity book = one risk factor; hedges must sit outside equities |

### Equity–bond correlation

60-day rolling, SPY (or portfolio equity beta) vs TLT / IEF / duration proxy.

| Level | Verdict | Meaning |
|---|---|---|
| < −0.2 | BALLAST-OK | Bonds hedge equities — standard stock/bond math works |
| −0.2 to +0.2 | WEAK-BALLAST | Hedge unreliable — prefer cash, managed futures, or collars over long duration alone |
| > +0.2 | CO-CRASH | Bonds will not save an equity drawdown — raise T-bill/cash share; avoid balanced complacency |

### Modifier rules

CRISIS-CORR or CO-CRASH modifies the pulse alongside liquidity stress:

- ELEVATED/CRISIS-CORR + equity-heavy posture → raise cash/non-equity hedge floors; ban "diversified by name count" language
- CO-CRASH + LATE CYCLE → duration is not the hedge; prefer T-bills, collars, or trend/alt premia
- DIVERSIFIED + EXPANSION → stock-level [`SCREENING.md`](SCREENING.md) picks and sector tilts are justified

## Statistical Regime Confirmation (optional)

When regime tools are available, use them as an ensemble confirmation layer—not a replacement. Compare HMM/Markov-switching with a different family such as change-point detection or volatility clustering. Follow [`AI_RISK.md`](AI_RISK.md).

| Output | How to use |
|---|---|
| Current regime (Bull / Sideways / Bear) | Must not violently contradict the pulse (e.g. structural LATE CYCLE + HMM Bull is tension to flag, not auto-override) |
| Persistence diagonal P(stay) | High Bear persistence → slower mean-reversion assumption; widen risk gates |
| Stationary distribution | Long-run Bear share > ~0.35 → structural tail-heaviness; size down aggressive postures |
| Signal (bull_prob − bear_prob) | Confirmation filter on tactical tilts only |

Graceful degrade: if the tool is missing, skip this block and state the gap. Structural axes (2A–2E + correlation) still produce the pulse.
