# Individual Stock Screening

When posture recommends sector or asset-class shifts that imply individual stock picks, source candidates then filter through five technical gates.

## Candidate sourcing

The screener is a filter, not a generator — candidates must come from somewhere first. Source per the target posture's tilt:

| Posture tilt | Where to source candidates |
|---|---|
| Sector rotation (e.g. defensive, value) | ETF holdings in the target sector (e.g. XLP constituents for defensive) — pull top 20 by weight, filter |
| Small cap / emerging markets | ETF holdings (IWM, EEM) screened for liquidity and momentum |
| Quality growth | User's existing holdings + ETF holdings in VUG/QQQ — supplement with sector leaders |
| Income / dividend | ETF holdings in SCHD, VYM — screen for dividend safety (payout ratio < 60%, consistent dividend growth) |
| Thematic — energy/power | ETF holdings / constituents in the AI-load-growth complex (nuclear/SMR, utilities, transmission, turbines). Source from thematic ETFs (e.g. NUKZ, GRID, utilities indices); screen for liquidity + momentum |
| Thematic — digital assets / crypto | Crypto-forward sleeve (BTC/ETH proxy ETFs like IBIT/ETHE, miners, stablecoin-exposed equities). Source from spot-crypto ETFs and miner constituents; screen for volatility tolerance and NAV premium/discount |
| Broad market shift | User's existing holdings are the universe — screen each for hold/trim/add |

If the user holds individual stocks, always include current holdings in the candidate pool for the relevant areas — a posture shift may mean trimming, not new buys.

Generate 15–30 raw candidates per affected area before applying technical gates. The filter exists to narrow, not to search.

## Technical gates

| Gate | Criterion | Why |
|---|---|---|
| Proximity to 52-week low | Price ≥ 70% above 52-week low | Screens out stocks trying to recover; requires stocks already proving they can trend higher |
| Average Daily Range | ADR ≥ 4.5% | Big winners need room to run. Low-volatility stocks rarely become home runs |
| Momentum structure | Above EMA 8 *and* EMA 21 | Confirms institutional accumulation and strong near-term momentum |
| Secular trend | Price above 200-day MA | Long-cycle gate — separates secular bull from secular bear; EMA8/21 is traders' momentum, this is the cycle. (The 200-week MA is a *regime-level* signal — Phase 2K/2L — that applies to bitcoin/crypto, not individual stocks.) |
| Lindy durability | Long operating history / franchise age | Durability filter — biases toward long-surviving franchises. Apply only when the posture is defensive/preservation; skip for growth postures (it systematically misses newly-dominant companies) |

**Conditional gates:** Secular trend applies to every candidate — it is the long-cycle floor. Lindy applies only when the target posture is defensive/preservation; a growth or aggressive posture omits the Lindy gate because it would filter out exactly the newly-dominant companies the regime favors.

## Manual analysis (applied post-screener, not automated)

- [ ] EPS ≥ +50% YoY **or** sales ≥ +20% YoY
- [ ] Compelling growth story
- [ ] Clean price action
- [ ] Proper base
- [ ] Tight risk
- [ ] Industry leadership

## Correlation gate (portfolio-level)

When adding a pick to an existing book, check pairwise correlation to the current equity sleeve (60–90d). If Phase 2F is ELEVATED or CRISIS-CORR, reject names with ρ > 0.75 to the sleeve average unless they are an explicit hedge or the only liquid vehicle in a mandated sector. Diversification is measured by effective N and factor exposure, not ticker count.

If the posture recommends a market-wide shift (e.g. "rotate to defensive" or "increase fixed income"), the screener applies to the **instruments used to execute the shift** — e.g. which defensive equities, not whether to go defensive.

**Completion criterion:** At least one concrete stock-level example per affected portfolio area that passes all *applicable* technical gates (five for defensive postures; four — omitting Lindy — for growth postures), or an explicit note that no candidates survive the filter.
