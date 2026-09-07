---
name: invest-optimizer
description: "Portfolio posture, market pulse, dip/profit signals, risk. Use for portfolio reviews, market reads, buy-the-dip asks."
disable-model-invocation: true
---

# Invest Optimizer

Recalibrate portfolio **posture** — the portfolio's overall stance expressed as concrete allocation shifts — to the current market **regime** through the lens of personal investment goals.

Reference files:
- [`METRICS.md`](METRICS.md) — market metric thresholds and synthesis rules
- [`POSTURE.md`](POSTURE.md) — posture × goals calibration matrix
- [`OPTIMIZATION.md`](OPTIMIZATION.md) — optimizer models, views, covariance defaults
- [`SCREENING.md`](SCREENING.md) — individual stock technical gates
- [`AI_RISK.md`](AI_RISK.md) — AI/ML risk protocol, validation gates, and quant-tool landscape
- [`FORECASTS.md`](FORECASTS.md) — probability ledger with Brier scoring and quarterly calibration review
- [`INCOME.md`](INCOME.md) — income-sleeve dashboard with distribution/ROC/NAV tripwires

## Phase 1 — Anchor to goals

Load a **goal profile**: a structured record of the user's investment objectives. If the system has a goal intake (e.g. Quinn's `/goal-intake`), load the latest confirmed profile. Otherwise infer from context or ask the user. The goal anchor is the fixed reference every downstream assessment recalibrates against.

| Axis | Values | Why it matters |
|---|---|---|
| Primary objective | income / growth / balanced / preservation | Sets the top-line compass — every downstream posture decision recalibrates against this axis |
| Risk tolerance | conservative / moderate / aggressive | How far from neutral the posture can deviate |
| Investor type | day trader / swing trader / income investor / growth holder | Determines recommendation granularity — traders need entry/exit levels and stops; income investors need yield safety checks; growth holders need macro-driven allocation shifts |
| Time horizon | <1 / 1-5 / 5-15 / 15+ years | Short horizons can't wait out recession; long ones average through |
| Income cadence | weekly / monthly / quarterly / annual / none | recommendations prioritize dividend safety and yield vs total-return reinvestment |
| Concentration | concentrated / balanced / broad | Concentrated tolerates sector risk; broad needs diversification |

**Completion criterion:** Every axis in the goal profile table populated and noted.

## Phase 2 — Read the regime

Recalibrate current market conditions across the structural axes using the thresholds in [`METRICS.md`](METRICS.md). For each axis produce a verdict, then synthesize a single **market pulse**.

### 2A — Valuation: how expensive are stocks vs fundamentals?

Check: **Shiller CAPE**, **Buffett Indicator**, **Tobin's Q**, **S&P 500 ÷ M2**.

Denominator caveat (Machine Age): these ratios divide by human-economy aggregates (GDP, M2). As agents create a growing share of economic value, GDP understates the real economy and equity/GDP ratios read progressively fake-expensive. Treat EXTREME/BUBBLE verdicts from 2A as stale-denominator readings; cross-check against substrate metrics (2M OCPI/OTPI, energy, memory) before acting on a valuation call. A wrong denominator can hide a real bubble or fake one — 2000's fiber buildout was real, the valuations still collapsed.

Verdict: CHEAP / FAIR / RICH / EXTREME / BUBBLE

### 2B — Complacency & credit: is everyone pricing in zero risk?

Check: **VIX**, **high-yield credit spread**.
Verdict: COMPLACENT / NEUTRAL / CONCERN / FEAR / PANIC

### 2C — Macro: is a recession brewing underneath?

Check: **Yield curve (10y − 2y)**.
Verdict: EXPANSION / WARNING / RECESSION / CRISIS

### 2D — Microstructure and liquidity: can the portfolio trade through stress?

Check observable measures: spread, depth when available, volume participation, intraday gaps/reversals, realized-vs-implied volatility, and rolling liquidity stress. `tools/market_pulse.py` supplies a limited SMH >3%-range proxy; label it as a proxy, not AI attribution.

Do not infer an “AI volume share” or causal agent regime without a dated, reproducible source and methodology. Automated volume is not equivalent to AI-driven volume, and tail events do not identify their cause.

Verdict: LIQUID / NORMAL / FRAGILE / DISLOCATED, with data gaps explicit.

### 2E — Event/prediction: what are live probability markets pricing?

Run `tools/market_pulse.py` (stdlib python, no deps) — one shot pulls Polymarket recession + rate-hike probabilities alongside VIX, HY spread, and the 10y−2y curve, each mapped to the [`METRICS.md`](METRICS.md) verdict. Pass extra args for more markets (`market_pulse.py "fed september"`), `--json` for machine output.

Measures: Polymarket-implied probability of recession within 12m, rate-hike probability, sector-outcome markets.
Verdict: [RECESSION p≥0.30 / NEUTRAL p0.10–0.29 / BULLISH p<0.10]

Log every cited probability in [`FORECASTS.md`](FORECASTS.md) with source, volume, and resolution date.

A RICH + COMPLACENT + RECESSION p≥0.30 is LATE CYCLE with extra conviction; a FAIR + ANXIOUS + BULLISH p<0.10 warns the market is pricing tail risk lower than your structural read — flag the tension.

### 2F — Correlation: is diversification real?

Check: **average pairwise equity correlation**, **equity–bond correlation** — `tools/market_pulse.py` computes both (60d SPY/QQQ/SMH pairwise + SPY–IEF). Thresholds in [`METRICS.md`](METRICS.md).
Verdicts: DIVERSIFIED / NORMAL / ELEVATED / CRISIS-CORR and BALLAST-OK / WEAK-BALLAST / CO-CRASH.

### Synthesis

Weight axes 2A–2E into the core pulse (EXPANSION / LATE CYCLE / CONTRACTION / CRISIS). Apply modifiers from 2D and 2F:

- FRAGILE/DISLOCATED → reduce trade size, raise liquidity reserves, model slippage/impact, and prefer bounded-loss structures
- CRISIS-CORR or CO-CRASH → raise non-equity hedge floors; name-count diversification is invalid
- CO-CRASH + LATE CYCLE → duration is not the sole hedge; prefer cash/T-bills/collars

**Structural/thematic axes (2H–2M)** apply as defense-floor / risk-budget / offense-ceiling modifiers via POSTURE.md "Axis → Posture Wiring". FISCAL DOMINANCE + DEBASEMENT set a hard real-asset floor; SECULAR BEAR caps total equity; REAL-GROWTH permits the AI/energy tilt. **Two-Truths rule:** fiscal/currency fragility (defense) and the AI infrastructure/energy supercycle (offense) are simultaneously true in 2026 — neither vetoes the other; they bind different sleeves. See POSTURE.md "The Two-Truths Regime" for falsification conditions.

When AI/ML risk assessment is requested or data supports it, load [`AI_RISK.md`](AI_RISK.md). Keep facts, model estimates, and scenarios separate; model disagreement lowers confidence and position size.

### 2G — Statistical regime confirmation (optional)

`tools/market_pulse.py` runs a thin 2-state Gaussian HMM. Treat it as one ensemble member, not an override. Prefer multiple windows/models or change-point confirmation; report regime probabilities, disagreement, sample size, and out-of-sample calibration. Follow [`AI_RISK.md`](AI_RISK.md) when adding ML.

### 2H — Fiscal & sovereign debt: can the government service its debt?

Check: **debt service as % of federal revenue**, **debt-to-GDP**, **credit-rating trend**, **maturity wall** (thresholds in METRICS.md).

Verdict: HEALTHY / WATCH / STRESSED / FISCAL DOMINANCE

### 2I — Currency & debasement: is the money itself losing value?

Check: **DXY**, **real rates**, **gold & bitcoin as debasement meters**.

Verdict: DOLLAR STRONG / NEUTRAL / DEBASEMENT

### 2J — Money creation: is money being created or drained?

Check: **M2 growth YoY**, **QE/QT regime**, **bank reserves**. (Distinct from 2D market-structure liquidity — this is the *monetary quantity*.)

Verdict: DRAIN / NEUTRAL / PRINTING

### 2K — Digital-asset regime signal: what is bitcoin pricing?

Check: **bitcoin vs 200-week MA**, **reserve-asset adoption**.

Verdict: SECULAR BULL / INFLECTION / SECULAR BEAR

### 2L — Secular trend: are we in a secular bull or bear?

Check: **price vs 200-day MA (equities) and 200-week MA (bitcoin)**. Complements the 200-week-MA *breadth* gauge in SIGNALS.md.

Verdict: SECULAR BULL / LATE-CYCLE BULL / SECULAR BEAR

### 2M — Circular AI financing: is the AI capex cycle fragile or real?

Check: **vendor financing / depreciation insurance**, **cross-investment loops**, **token profitability** (Dell's 1Q→57Q revision and Goldman's higher projection — dated vendor/desk forecasts, not fact), **compute clearing prices (Ornn Compute Price Index)** — free no-key API: `https://api.ornnai.com/api/daily-index/all` (all GPUs) and per-GPU history `/api/gpu/H100%20SXM/index-history` (USD/GPU-hr, hourly-refreshed, executed-transaction benchmark per IOSCO-style methodology; full writeup in ~/Obsidian-vault-PC/Research/machine-age-ocpi-research.md). Readings: frontier GPUs (H100/H200/B200) flat-to-rising over 3mo = demand absorbing supply (REAL-GROWTH evidence); sustained multi-month decline across frontier GPUs = marginal buyer weakening (FRAGILE signal); old-gen collapse (A100, RTX 5090) = compute depreciation speed, i.e. asset-life risk for AI-infrastructure holders; Ornn Token Price Index (`/api/otpi`, realized $/M-token by lab) = application-layer intelligence price — falling token prices with firm compute prices = value migrating to the physical layer (Machine Age thesis).

Verdict: FRAGILE / NEUTRAL / REAL-GROWTH

**Residual-print watch:** lender-grade residuals enter this read only on executed-sale prints (e.g. CCIR-class volumes), never on DCF values, supplier quotes, or rental-curve transforms. Track the print-to-facility ratio (documented used-GPU sales vs outstanding GPU-backed issuance); a liquid print market with observable LTV/borrowing-base language in new issues upgrades financing FRAGILE toward NEUTRAL. Dated compute-derivative milestones (Kalshi ladders, CME H100/B200 review and first-trade dates, CFTC comment windows) log as FORECASTS.md event watches; treat synthetic/term-built curves as upper bounds (non-storable underlying).

**Completion criterion:** Verdicts for 2A–2M each supported by at least one metric reading; synthesized pulse with explicit weighting rationale; modifiers (microstructure, correlation, and structural/thematic 2H–2M) stated; 2G present or explicitly skipped with gap noted.

### Tool fallback

Probed 2026-07-29 — preference order: `tools/market_pulse.py` first (covers 2A, 2B, 2C, 2D proxy, 2E, 2F, 2G; endpoints documented in `tools/feeds.py`) → web reads for the rest: stockanalysis.com (52w ranges, holdings), tradingeconomics.com (index levels). Cross-check for 2A/2B/2C: `https://levels.io/bubble-detector.json` — one-shot JSON with all seven inputs (CAPE, Buffett, Tobin's Q, S&P÷M2, VIX, HY spread, 10y−2y), updated daily; probed 2026-09-07, covers Tobin's Q (previously manual); METRICS.md thresholds stay authoritative. Phase 3.5 → `tools/optimize.py`; Phase 4 forward risk → `tools/risk.py`. Dead in this environment: Yahoo chart API (429), stooq (JS gate), MarketWatch (401), `polymarket-cli`/openbb (not installed), pip (absent → `skfolio`/`Riskfolio-Lib`/`PyPortfolioOpt` unavailable). Still manual: AI volume share, flash-crash count. A missing tool downgrades that step; the brief still ships.

## Phase 3 — Calibrate posture

Map the market pulse against the goal anchor using **[the posture matrix](POSTURE.md)**. The matrix is the cross-product: same pulse × different goals → different postures.

When 2D is FRAGILE or DISLOCATED, apply the **[Microstructure and Liquidity Addendum](POSTURE.md#microstructure-and-liquidity-addendum)**. Match option tenor and structure to the mandate, implied-volatility surface, transaction costs, tax context, and stress loss; do not claim short-duration options structurally outperform without strategy-specific evidence.

When 2F is CRISIS-CORR or CO-CRASH, apply the correlation rules in POSTURE.md: raise non-equity hedge floors and forbid "diversified by ticker count" language.

For each area the portfolio touches, produce:

1. **Current posture** — what the portfolio looks like now
2. **Target posture** — per the matrix, given the pulse and goals
3. **Actions** — specific trades or shifts to close the gap
4. **Risk gate** — the observable condition that, if met, breaks the thesis and triggers a posture revert

When the posture implies individual stock picks, apply the technical gates in [`SCREENING.md`](SCREENING.md). When it implies income-fund picks (monthly/weekly payers, including systematic / AI-marketed option funds), apply the seasoning gate there — unseasoned funds enter capped and in thirds regardless of recent outperformance.

**Completion criterion:** At least one concrete recommendation per portfolio area (equities, fixed income, alternatives, cash, sector tilts, income instruments as applicable), each with target posture, specific actions, and a risk gate.

## Phase 3.5 — Optimize weights

Translate the target posture from Phase 3 into mathematically grounded allocation weights. Heuristic templates give ranges; optimization gives exact weights **inside** those ranges. Full model menu, covariance defaults, Entropy Pooling/BL view encoding, and stress checks: [`OPTIMIZATION.md`](OPTIMIZATION.md).

1. Build the candidate universe (equities, ETFs, bonds per the target posture tilt + SCREENING survivors)
2. Select tool and model per OPTIMIZATION.md — prefer maintained libraries available in the environment; match model to goal × pulse (HRP when valuations are EXTREME; DR-CVaR/CDaR under fragile tails; NCO when universe >12 and correlations unstable)
3. Set covariance prior (default **Ledoit-Wolf shrinkage**) and expected-return prior (James-Stein / BL equilibrium — not raw historical means)
4. Encode Phase 2 pulse as a small BL or Entropy Pooling view set (OPTIMIZATION.md table); scale view confidence by axis agreement. A learned signal enters views only after the [`AI_RISK.md`](AI_RISK.md) promotion gate; scale it by out-of-sample IC/RankIC and uncertainty. Scale income-fund view confidence by seasoning: unseasoned names get weak views even when their 6-month numbers lead.
5. Constrain to posture asset-class bands, sector/name ceilings, liquidity/capacity, and turnover budget if prior weights exist
6. Solve; run optimizer-level stress checks (in-band, concentration, CVaR sanity, correlation-break)
7. Optional: discrete allocation to share counts when deployable cash and prices are known
8. Optional large gap (>15% equity shift): note turnover/cost path (cvxportfolio-class multi-period) without blocking the brief

If no optimizer library is available, run `tools/optimize.py` (stdlib, return-free models: HRP default, min-var, risk parity, inverse-vol; per-name caps, effective-N, CVaR, +0.3 correlation-shock stability check). Only if that fails, fall back to equal-weight or inverse-volatility within target bands and state the gap.

**Completion criterion:** Every recommended asset has an explicit weight, optimized or fallback, summing to 100% inside posture bands; model + risk measure + covariance method named; stress checks passed or fallback path stated.

## Phase 4 — Risk check

Before outputting, validate recommendations against system risk constraints and forward risk analytics. If system values aren't available, use defaults:

- [ ] Position size within goal-appropriate limits
- [ ] Sector concentration under ceiling (≤30% per sector default)
- [ ] Single-name ceiling respected (concentrated vs broad from goal profile)
- [ ] Leverage under cap (≤1.25× default)
- [ ] Polymarket-implied recession probability matches posture level (LATE CYCLE → recession p context; BULLISH tilt → p<0.10)
- [ ] Correlation modifier honored (CRISIS-CORR/CO-CRASH → non-equity hedges present)
- [ ] Drawdown / CVaR within loss tolerance from goal profile
- [ ] Forecast rows logged and income tripwires checked ([`FORECASTS.md`](FORECASTS.md), [`INCOME.md`](INCOME.md))

### Forward risk analytics

Load [`AI_RISK.md`](AI_RISK.md). When return history for the recommended mix (or proxy ETFs) is available — via risk tooling, `tools/risk.py`, or manual calculation — report:

| Metric | Role |
|---|---|
| Historical max drawdown | Sanity vs goal loss tolerance |
| CVaR (expected shortfall) | Tail loss beyond VaR |
| Tail ratio / Calmar | Asymmetry and drawdown-adjusted return |
| Monte Carlo bust probability | P(DD ≤ −loss_tolerance); default 1000 paths; block-bootstrap or regime-aware simulation preferred |
| Monte Carlo goal probability | Only if the profile states a return target + horizon |

Gate: bust probability above comfort (default >25% moderate, >10% conservative/preservation) → downgrade posture one rung or cut equity band and re-run 3.5. If MC tooling is unavailable, use historical max DD + CVaR and state the gap.

If a Markov stationary mix is available from 2G, scale tactical risk: high long-run Bear share → smaller active tilts (stationary distribution as a size modifier).

If any recommendation violates a limit, downgrade the posture to the next safe rung. State the violation and the downgrade explicitly.

### Regime validation

If a prior posture brief exists, check whether the previous regime read was confirmed or contradicted by subsequent market action:

- **Confirmed** — metrics moved in the predicted direction (e.g. prior LATE CYCLE → yield curve un-inverted or spreads widened)
- **Contradicted** — metrics moved against (e.g. prior LATE CYCLE → VIX dropped and spreads tightened)
- **Mixed** — some axes confirmed, others didn't → note which and adjust confidence in the current read

A contradicted prior read lowers confidence in regime calls depending on the same axes. State the adjustment explicitly.

**Completion criterion:** Every recommendation is checked against limits and forward analytics (or a gap is noted). Facts, estimates, and scenarios are labeled; leakage, costs, liquidity, calibration, uncertainty, and drift are tested where applicable. Violations are blocked or downgraded. Prior regime validation and confidence adjustment are stated.

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
| Microstructure | FRAGILE |
| Prediction | RECESSION p=0.34 |
| Correlation | ELEVATED / WEAK-BALLAST |
| **Overall** | **LATE CYCLE** (+ liquidity & correlation modifiers) |

### Posture
| Area | Current | Target | Action | Risk gate |
|---|---|---|---|---|
| Equity allocation | 80% | 65% | Trim 15% → cash/short bonds | Redeploy if CAPE < 25 |
| Sector tilt | Tech-heavy | Add defensive | Buy XLP, XLU | Exit if VIX > 30 |
| Duration | 5yr | 2yr | Shorten bond portfolio | — |

### Weights (Phase 3.5)
| Asset | Weight | Notes |
|---|---|---|
| … | … | model: HRP+CVaR · cov: Ledoit-Wolf |

### Forward risk
| Metric | Value | Gate |
|---|---|---|
| Max DD (hist proxy) | … | vs loss tolerance |
| CVaR | … | |
| MC bust p | … | downgrade if above comfort |

### Stock picks (screener pass)
| Ticker | 52W low | ADR | EMA8/21 | Gate status |
|---|---|---|---|---|
| ABC | +75% | 5.2% | Above both | PASS |
| DEF | +40% | 3.1% | Above EMA8 only | FAIL (low 52W, low ADR) |
```

**Completion criterion:** Every portfolio area from Phase 3 has a corresponding row in the posture table. Weights sum to 100% with model named when 3.5 ran. Forward risk row present or gap noted. Every stock-level example shows which gates it passes or fails.

## Branch: Quick pulse

When only market conditions are requested (no portfolio recommendations), run Phase 2 only (2A–2F; 2G if cheap to run). Output a compact table of axes, modifiers, and overall pulse. Skip Phases 1, 3, 3.5, and 4.

## Branch: Dip/profit signal

When the user asks whether to buy the dip or take profits on an ETF or sector, run `tools/dip_signal.py <ETFS>` and report per [`SIGNALS.md`](SIGNALS.md): score (1–20), band, action, breadth (% of the bucket below its 200-week MA, by weight and by count), and tension flags. When a posture brief exists, fold the score into Phase 3 actions: ≥17 accelerates trims and reserve-building; ≤9 authorizes deploying the reserve tranches the brief staged. Scores are strategic — they size the cash-reserve cycle; tranche timing still comes from the brief.