# Posture Calibration Matrix

How market pulse maps to portfolio posture through the lens of personal goals. Same pulse × different goals → different postures; the matrix makes the mapping explicit.

## The matrix

Cells marked **(default)** are the allocation the goal profile would produce on its own — they exist for completeness. Focus calibration effort on the non-obvious intersections where the pulse materially changes the default behavior.

| Market pulse | Growth / Aggressive | Balanced / Moderate | Income / Conservative | Preservation |
|---|---|---|---|---|
| **EXPANSION** — cheap valuations, bull market, low fear | Maximum equities. Small/value tilt. Emerging markets. Full risk budget. | **(default)** Neutral weight, drift to equity. Maintain targets. | Income tilt. High quality, preferreds, dividend growers. | **(default)** Standard allocation. Quality bias. |
| **LATE CYCLE** — rich valuations, complacency, macro warnings | Reduce to neutral. Trim winners, raise cash 15–20%. Quality rotation. Prefer HRP/CVaR over max-Sharpe in 3.5. | Shift defensive. +5–10% bonds (or T-bills if CO-CRASH). Quality, low vol equities. | Short duration, high credit quality. Trim HY exposure. | Reduce equity to minimum target. Short Treasuries core. |
| **CONTRACTION** — fear, recession, crash | Average down systematically. Extend duration. Scale into weakness. | Rebalance. Sell bonds into equity strength at targets. | **(default)** Hold income. Dividends safe; yield quality only. | **(default)** Maintain. Equity at floor. Duration extended. |
| **CRISIS** — panic, credit freeze, policy emergency | Aggressive buy. Full deployment into panic. Go barbell. | Systematic rebalance only. | Hold course. Income from best credits. | **(default)** Hold. This is what the allocation is for. |

## Allocation templates by posture

### Aggressive
Equities 80–100% · Fixed income 0–10% · Cash 0–10%<br>
Tilt: small cap, value, emerging markets, thematic

### Growth
Equities 65–80% · Fixed income 10–25% · Cash 5–15%<br>
Tilt: quality growth, broad market, sector rotation

### Balanced
Equities 50–65% · Fixed income 25–40% · Cash 5–10%<br>
Tilt: total market, core bonds, low correlation

### Conservative
Equities 30–50% · Fixed income 40–60% · Cash 5–10%<br>
Tilt: large cap, dividend, investment grade bonds

### Income
Equities 20–40% · Fixed income 50–70% · Cash 5–10%<br>
Tilt: dividend aristocrats, preferreds, REITs, high quality corporates

### Preservation
Equities 10–30% · Fixed income 60–80% · Cash 5–10%<br>
Tilt: short duration Treasuries, TIPS, money market

## Microstructure and Liquidity Addendum

When Phase 2D is FRAGILE or DISLOCATED, implementation risk changes even if strategic allocation bands do not.

- Size orders from observed volume and spread; stage execution and stress market impact.
- Keep a liquidity reserve sized to withdrawals, margin, and stressed liquidation time.
- For options, compare tenor/strike structures on net total return, implied-versus-realized volatility, skew, gap loss, turnover, tax, and assignment—not a presumed AI regime.
- Short-dated options carry high gamma, path, spread, and execution risk; monthly calls carry more time exposure and cap upside. Neither structurally dominates across regimes.
- Prefer bounded-loss spreads or collars when the mandate values drawdown control; verify liquidity in every leg.
- Separate distribution yield from total return and test NAV erosion.

Completion criterion: instrument choice is supported by strategy-specific evidence after costs and stress, with liquidity assumptions and contrary evidence stated.

## Correlation Regime Addendum

When Phase 2F reads ELEVATED, CRISIS-CORR, WEAK-BALLAST, or CO-CRASH, the matrix cells still pick the direction — but hedge *composition* changes.

| 2F verdict | Posture adjustment |
|---|---|
| ELEVATED | Keep equity band; inside equities prefer risk-parity / factor-balanced weights over equal stock count. State effective-N, not ticker count. |
| CRISIS-CORR | Treat the equity sleeve as one risk factor. Raise cash or true diversifiers (managed futures, collars, T-bills) to at least the template cash ceiling. Stock-picking alpha claims require extraordinary evidence. |
| WEAK-BALLAST | Do not count long duration as a full equity hedge. Split the fixed-income band toward T-bills / short Treasuries unless the goal is pure income carry. |
| CO-CRASH | Bonds co-move with equities — duration extension is not the LATE CYCLE / CONTRACTION hedge. Prefer cash, T-bills, collars, or non-correlated alts. Balanced templates must disclose the broken stock/bond assumption. |

CRISIS-CORR + CO-CRASH together: maximum caution on any “diversified 60/40” language; preservation and conservative columns win ties.

## Optimizer hook

Phase 3.5 reads bands from the templates above and the model × goal map in [`OPTIMIZATION.md`](OPTIMIZATION.md). Pulse → view encoding (BL / Entropy Pooling) also lives there. This file owns *what band*; OPTIMIZATION.md owns *how weights fill the band*.

## Thematic Tilt Overlay

A **secular/sector supercycle** (e.g. an "AI macro nexus" — token demand, compute, power/energy, digital assets) can run *inside* a broad-market Late Cycle or Contraction. The 1999 precedent applies: broad valuations were late-cycle even as networking/semis compounded. The overlay lets a thesis tilt the **offense sleeve only**, without touching regime-level hedges.

**Rules:**
- A thematic tilt is a *modifier on the offense band*, never a substitute for the regime read. The market pulse (Phase 2) always wins on defense.
- The tilt may overweight specific sectors/themes *within* the equities allocation already permitted by the pulse — it does **not** grant extra equity weight beyond the matrix bands.
- It **cannot** override the Phase 4 risk gate. If the pulse is LATE CYCLE / CONTRACTION, the hedge layers (duration, non-correlated, cash) stay at their minimum regardless of conviction.
- Treat any secular narrative as *one strategist's thesis to weight*, not doctrine. State the source and the condition that would falsify it (e.g. "token demand growth decelerates below compute supply growth").
- Common overlay candidates: AI/semiconductor infrastructure, energy/power (grid, nuclear/SMR, utilities feeding load growth), digital assets / crypto-forward (BTC, stablecoin legislation, Treasury digital-asset posture). Source candidates per SCREENING.md's thematic buckets.

## Axis → Posture Wiring (structural axes 2H–2M)

The matrix maps the core pulse (2A–2E) to posture. The six structural/thematic axes (2H–2M) are wired directly — every verdict has a defined consequence. No axis is read without a defined portfolio consequence.

**Risk-budget axis** (secular trend, 2L) caps *total* equity.
**Defense axes** (fiscal 2H, currency 2I, money-creation 2J) set the *floor* on hedges.
**Offense axes** (digital-asset 2K, AI-financing 2M) set the *ceiling* on the thematic tilt.

### Fiscal (2H) → defense floor
| Verdict | Consequence |
|---|---|
| HEALTHY | Standard duration |
| WATCH | Bias short duration |
| STRESSED | Short duration + TIPS + gold/BTC sleeve |
| FISCAL DOMINANCE | Hard floor on hedges; real assets (gold/BTC/commodities) become core, not satellite |

### Currency (2I) → real-asset tilt
| Verdict | Consequence |
|---|---|
| DOLLAR STRONG | Foreign exposure unhedged OK |
| NEUTRAL | Maintain |
| DEBASEMENT | Overweight gold/BTC/real assets; underweight nominal long bonds |

### Money creation (2J) → cash & risk posture
| Verdict | Consequence |
|---|---|
| DRAIN | De-risk; raise cash; expect vol |
| NEUTRAL | Maintain |
| PRINTING | Real-asset tilt; nominal cash is the liability |

### Digital-asset (2K) → crypto sleeve
| Verdict | Consequence |
|---|---|
| SECULAR BULL | BTC/ETH sleeve at full permitted weight |
| INFLECTION | Halve crypto sleeve; wait for the 200w MA to resolve |
| SECULAR BEAR | Crypto sleeve to zero; no dip-buying |

### Secular trend (2L) → risk budget
| Verdict | Consequence |
|---|---|
| SECULAR BULL | Full equity budget; buy dips |
| LATE-CYCLE BULL | Reduce equity; add defense |
| SECULAR BEAR | Minimum equity; capital preservation |

### AI-financing (2M) → offense composition
| Verdict | Consequence |
|---|---|
| FRAGILE | AI sleeve capped; diversify within compute/energy |
| NEUTRAL | Standard AI tilt |
| REAL-GROWTH | Full AI/energy tilt permitted — the outsize-return sleeve |

### How the layers compose

1. **Base posture** = matrix[ pulse(2A–2E) × goal ].
2. **Risk budget** = the tighter cap on total equity from valuation (2A, in the pulse) and secular trend (2L). When they conflict, the more conservative wins — both are risk-reduction signals, so take the lower equity ceiling.
3. **Defense floor** = the most defensive consequence across 2H–2J. Sets the minimum duration/cash/real-asset allocation — can only raise the floor, never lower it.
4. **Offense ceiling** = the more permissive consequence across 2K and 2M. Sets the maximum thematic tilt within the equity band — can only lower the ceiling, never raise it above the risk budget.
5. **Income instrument** = 2D overrides the instrument, not the allocation.
6. **Conviction** = 2E confirms or flags tension; 2F (correlation) adjusts hedge composition.

## The Two-Truths Regime — fiscal fragility AND the AI supercycle are simultaneously true

The 2026 setup is not "bearish OR bullish." It is both, in different layers, and the skill must hold both without letting one veto the other.

**Truth 1 — the fiscal/currency layer is genuinely fragile.** $3B/day debt service, debasement as the crowd's assumed endgame, de-dollarization bid into gold/BTC. This governs **defense**: duration, cash, non-correlated assets, and hedges stay at their regime minimums regardless of AI conviction.

**Truth 2 — the AI infrastructure/energy layer is the only theme with outsize relative returns.** The market has never underestimated a growth curve the way it is underestimating AI token generation. Dell's end-2028 inference estimate moved from ~1 quadrillion to 57 quadrillion tokens/month inside a single year (a ~57× revision); Goldman projects an order of magnitude higher. And the companies are profitable — the "tokens are subsidized" assumption that powers the circular-financing bear thesis is simply wrong.

**How to hold both:**
- The regime read (Phase 2) governs **defense**. Fiscal/currency fragility keeps the hedge layers at their minimums.
- The AI supercycle governs **offense**. The equities sleeve tilts hard toward compute, power/energy, and the token economy *within* the bands the pulse already permits. The tilt spans multiple sectors (compute/semis, power/utilities, digital-assets), so it concentrates within the offense sleeve but spreads across sectors — it does not breach the per-sector ceiling.
- Do NOT let the circular-financing bear thesis veto the AI sleeve, and do NOT let AI conviction veto the fiscal hedges. They are different layers.
- The 1999 precedent is only half the story: broad valuations were late-cycle *while* networking/semis compounded — but 1999 had no $3B/day debt service and no 57× token-growth revision. The 2026 setup is more extreme on both axes.

**Falsification conditions (state explicitly, never as doctrine):**
- AI thesis breaks if token demand growth decelerates below compute supply growth, OR "profitable tokens" is disproven (a major chain player reports subsidized, loss-making tokens at scale).
- Fiscal thesis breaks if debt service as % of revenue falls back below ~15%, OR a credible fiscal-consolidation path materializes.

## Return-of-Capital & Margin-Income Note

Option-income ETFs (CHPY, AMDY, NVDY, QQQI, SPYI, Roundhill 0DTE, etc.) distribute heavily from **return of capital (ROC)** and option premium. High "distribution yield" is **not** income you keep — it is partly your own NAV handed back, and NAV can erode.

**Rules for income / margin-account goals:**
- Report **distribution yield** and **total-return yield** separately. A 28% distribution yield on an ETF losing 10% NAV is a *negative* real yield.
- **Margin survival check:** total-return yield must exceed the account margin rate (e.g. ~7%) *sustained*, or the income compounds debt. Confirm before funding.
- **ROC-erosion hedge:** pair high-ROC income sleeves with an *uncapped pure-equity growth leg* (e.g. SMH, sector index). The growth leg offsets NAV decay — it is ballast for the income sleeve, not optional upside.
- **Drawdown defense is not optional in margin accounts.** Stripping hedges to hit a distribution-yield target removes the buffer that prevents a margin call during the very drawdown the regime read warned about. State this tension explicitly when a yield target conflicts with the risk gate.