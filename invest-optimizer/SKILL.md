---
name: invest-optimizer
description: Posture portfolio to market regime and goals. Triggers: portfolio review, market timing, goal alignment.
---

# Invest Optimizer

Calibrate portfolio **posture** — the portfolio's overall stance expressed as concrete allocation shifts — to the current market **regime** through the lens of personal investment goals.

The regime is the market's state, read from objective metrics. Posture is what you do about it given who you are.

Reference files:
- [`METRICS.md`](METRICS.md) — market metric thresholds and synthesis rules
- [`POSTURE.md`](POSTURE.md) — posture × goals calibration matrix
## Prerequisite — goal profile

This skill needs a **goal profile**: a structured record of the user's investment objectives. If the system has a goal intake (e.g. Quinn's `/goal-intake`), load the latest confirmed profile from it. Otherwise infer from context or ask the user.

Never proceed without a goal anchor: a growth profile and a preservation profile read the same market data and reach different postures.

## Phase 1 — Anchor to goals

Load the profile. Extract at minimum the critical axes that determine which posture fits:

| Axis | Values | Why it matters |
|---|---|---|
| Primary objective | income / growth / balanced / preservation | Sets the top-line compass — every downstream posture decision recalibrates against this axis |
| Risk tolerance | conservative / moderate / aggressive | How far from neutral the posture can deviate |
| Investor type | day trader / swing trader / income investor / growth holder | Determines recommendation granularity — traders need entry/exit levels and stops; income investors need yield safety checks; growth holders need macro-driven allocation shifts |
| Time horizon | <1 / 1-5 / 5-15 / 15+ years | Short horizons can't wait out recession; long ones average through |
| Income cadence | weekly / monthly / quarterly / annual / none | Determines whether recommendations prioritize dividend safety and yield vs total-return reinvestment |
| Concentration | concentrated / balanced / broad | Concentrated tolerates sector risk; broad needs diversification |

**Completion criterion:** All critical axes loaded and noted. The anchor is the fixed reference every downstream assessment measures against.

## Phase 2 — Read the regime

Assess current market conditions across three axes using the thresholds in [`METRICS.md`](METRICS.md). For each axis produce a verdict, then synthesize a single **market pulse**.

### 2A — Valuation: how expensive are stocks vs fundamentals?

Check: **Shiller CAPE**, **Buffett Indicator**, **Tobin's Q**, **S&P 500 ÷ M2**.

Verdict: CHEAP / FAIR / RICH / EXTREME / BUBBLE

### 2B — Complacency & credit: is everyone pricing in zero risk?

Check: **VIX**, **high-yield credit spread**.

Verdict: COMPLACENT / NEUTRAL / CONCERN / FEAR / PANIC

### 2C — Macro: is a recession brewing underneath?

Check: **Yield curve (10y − 2y)**.

Verdict: EXPANSION / WARNING / RECESSION / CRISIS

Weight all three axes. Add market microstructure as a **modifier axis** (see 2D).

AI trading agents now compose >60% of daily equity volume. Their herding creates vertical parabolic surges followed by random liquidity vacuums and flash crashes — a "parabolic-and-drop" regime that breaks traditional option strategies.

Check: **AI trading volume share**, **intraday tail frequency** (days with >3% single-stock intraday reversals), **flash crash count** (rolling 30-day).

| Metric | Estimate (mid-2026) | Signal |
|--------|--------------------|--------|
| AI trading agent volume share | 60–70%+ | AGENT-DOMINATED |
| Intraday >3% V-reversals per week | 3–8 | HIGH REGIME NOISE |
| Flash crash events (30d) | 1–4 | STRUCTURAL FRAGILITY |

Verdict: AGENT-DOMINATED / HUMAN-MIXED / HUMAN-DOMINATED

### Event/Prediction (2E)

Use Polymarket to anchor probability-driven verdicts that complement the four
structural axes. Live prediction-market prices on recessions, rate moves, and
sector outcomes are a harder signal than any VIX read.

Measures: Polymarket-implied probability of recession within 12m, rate-hike
probability, sector-outcome markets.

Verdict: [RECESSION p≥0.30 / NEUTRAL p0.10–0.29 / BULLISH p<0.10]

Fold this into the synthesis table as a fifth column. A RICH + COMPLACENT +
RECESSION p≥0.30 is LATE CYCLE with extra conviction; a FAIR + ANXIOUS +
BULLISH p<0.10 warns the market is pricing tail risk lower than your structural
read — flag the tension.

### Synthesis

Weight all five axes (valuation, complacency, macro, microstructure, prediction markets). Add market microstructure as a **modifier axis** — it amplifies or mutes the standard pulse based on who is trading:

- AGENT-DOMINATED + high valuation → crash severity elevated (flash crashes become structural, not one-off)
- AGENT-DOMINATED + LATE CYCLE → rotation severity elevated (agents herd exits faster than humans)
- AGENT-DOMINATED × any pulse → **monthly ATM covered calls structurally underperform** (strikes get run over by intraday agent-driven spikes)

**Completion criterion:** Five axis verdicts (valuation, complacency, macro, microstructure, prediction markets) plus a synthesized market pulse.

## Phase 3 — Calibrate posture

Map the market pulse against the goal anchor using **[the posture matrix](POSTURE.md)**. The matrix is the cross-product: same pulse × different goals → different postures.

When 2D verdict is AGENT-DOMINATED or AGENT-SATURATED, apply the **[Agent-Market Microstructure Addendum](POSTURE.md#agent-market-microstructure-addendum)** as a modifier on all income instrument recommendations. Standard allocation templates remain valid for broad asset-class posture but individual income vehicles must be filtered through the addendum's preference hierarchy.

For each area the portfolio touches, produce:

1. **Current posture** — what the portfolio looks like now
2. **Target posture** — per the matrix, given the pulse and goals
3. **Actions** — specific trades or shifts to close the gap
4. **Risk gate** — the observable condition that would break the thesis and trigger a revert

**Completion criterion:** At least one concrete recommendation per affected portfolio area, each with target posture, specific actions, and a reversal condition.

### Individual stock screening

When the posture recommends sector or asset-class shifts that imply individual stock picks, filter candidates through three technical gates. This is a **research list**, not a buy list — every stock that passes still needs manual analysis.

| Gate | Criterion | Why |
|---|---|---|
| Proximity to 52-week low | Price ≥ 70% above 52-week low | Screens out stocks trying to recover; requires stocks already proving they can trend higher |
| Average Daily Range | ADR ≥ 4.5% | Big winners need room to run. Low-volatility stocks rarely become home runs |
| Momentum structure | Above EMA 8 *and* EMA 21 | Confirms institutional accumulation and strong near-term momentum |

**Manual analysis** (applied post-screener, not automated):
- [ ] EPS ≥ +50% YoY **or** sales ≥ +20% YoY
- [ ] Compelling growth story
- [ ] Clean price action
- [ ] Proper base
- [ ] Tight risk
- [ ] Industry leadership

If the posture recommends a market-wide shift (e.g. "rotate to defensive" or "increase fixed income"), the screener applies to the **instruments used to execute the shift** — e.g. which defensive equities, not whether to go defensive.

**Completion criterion:** At least one concrete stock-level example per affected portfolio area that passes all three technical gates, or an explicit note that no candidates survive the filter.
## Data layer — consult, don't recompute

The posture logic above is judgment, not math. Pull the hard quantitative
work from dedicated tools instead of hand-estimating:

- **Market regime & macro** — `qlib` (microsoft/qlib) for factor/return
  backtests; `timesfm` (google-research/timesfm) for time-series forecasting
  of the metrics in METRICS.md. Use them to sanity-check the valuation /
  macro verdicts, not to override them.
- **Agent-flow signal** — `TradingAgents` (TauricResearch) for multi-agent
  market narrative; cross-read its output against the 2D microstructure axis.
- **Event / probability** — `polymarket-cli` for live prediction-market
  prices on recessions, rate moves, and sector outcomes. A Polymarket price
  of 0.30 on "US recession in 12m" is a harder microstructure signal than any
  VIX read; fold it into the 2C/2D verdicts as an external probability anchor.

These are references and CLIs, not dependencies of this skill. If a tool is
unavailable, fall back to the manual metric checks in METRICS.md and state
the gap. Never block a posture brief on a missing data source.


## Phase 4 — Risk check

Before outputting, validate recommendations against system risk constraints. If system values aren't available, use defaults:

- [ ] Position size within goal-appropriate limits
- [ ] Sector concentration under ceiling (≤30% per sector default)
- [ ] Leverage under cap (≤1.25× default)
- [ ] Polymarket-implied probability of recession within 12m matches the posture level (LATE CYCLE → ≥0.30; HEDGE → ≥0.15; BULLISH → <0.10)
- [ ] Drawdown within loss tolerance from goal profile

If any recommendation violates a limit, downgrade the posture to the next safe rung. State the violation and the downgrade explicitly.

**Completion criterion:** Every recommendation checked against risk limits. Violations blocked or downgraded with reason.

## Output format

Present as a structured posture brief. The format adapts to **investor type** — traders get levels, stops, and position sizing; holders get allocation shifts and review cadence.

```markdown
## Posture brief — {date}

### Profile
- Primary: growth · Trader type: long-term holder · Horizon: 10+ years
- *Why this matters:* long-term holder tolerates late-cycle drawdowns and averages through; a day trader would tighten stops and halve position size.

### Market pulse
| Axis | Verdict |
|---|---|
| Valuation | RICH |
| Complacency | COMPLACENT |
| Macro | RECESSION WARNING |
| **Overall** | **LATE CYCLE** |

### Posture
| Area | Current | Target | Action | Risk gate |
|---|---|---|---|---|
| Equity allocation | 80% | 65% | Trim 15% → cash/short bonds | Redeploy if CAPE < 25 |
| Sector tilt | Tech-heavy | Add defensive | Buy XLP, XLU | Exit if VIX > 30 |
| Duration | 5yr | 2yr | Shorten bond portfolio | — |

### Stock picks (screener pass)
| Ticker | 52W low | ADR | EMA8/21 | Gate status |
|---|---|---|---|---|
| ABC | +75% | 5.2% | Above both | PASS |
| DEF | +40% | 3.1% | Above EMA8 only | FAIL (low 52W, low ADR) |
```

**Completion criterion:** Every area in Phase 3 has a corresponding row in the posture table. Every stock-level example shows which gates it passes or fails.

## Branch: Quick pulse

When only market conditions are requested (no portfolio recommendations), run Phase 2 only. Output a compact table of three axes and overall pulse. Skip Phases 1, 3, and 4.
