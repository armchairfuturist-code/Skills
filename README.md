# Skills

Two custom AI agent skills that turn raw personal data into a ranked action plan. One handles your healthspan. One handles your portfolio. Both follow the same philosophy: profile the data, find the gaps, rank by impact, then act.

## What these skills are

These are prompt packs for an AI coding agent (Claude Code, Cline, MiMoCode, and others). Drop the folder into your agent's skills directory and call it by name. The agent then runs a structured workflow instead of free-form guessing.

- `/calibrate-longevity` turns bloodwork, DNA, and tracker data into a ranked longevity plan.
- `/invest-optimizer` combines market-regime analysis, goal-aware posture, robust allocation, liquidity and tail-risk controls, and leakage-safe AI/ML signal validation.

## calibrate-longevity: your bloodwork, ranked into a plan

### The plain version
You hand the agent your lab results, your DNA file, and your wearable data. It tells you what to fix first, what to take, and when to re-test. No more staring at a lab sheet wondering what matters.

### What to give it
- Bloodwork (recent, any format): any panel at all — a single CBC or a full longevity workup. The skill is panel-agnostic: it maps and contextualizes every marker present, then tells you which high-value longevity markers are *missing* so you know what to test next.
- DNA report (optional): 23andMe or Ancestry raw data
- Health tracker export (optional): HRV, resting heart rate, sleep stages, VO2 max
- Goals: what you want (longevity, energy, sharp thinking, body composition)
- Risk tolerance: how far you will go (established supplements only, peptides, research compounds)

Missing data is fine. The skill works with whatever you provide and flags gaps on two axes: out-of-range values (visible gaps) and absent high-value markers (invisible gaps — you can't calibrate what you can't see).

### What it does, step by step
1. Profile your signals. It parses every marker in the panel you gave it, maps each to a canonical name, and checks whether the test was done right (fasted? right time of day?). It writes a card with your value, optimal range, trend, and confidence — and scans for the longevity markers you *weren't* tested for.
2. Map to body systems. Metabolic, hormonal, cardiovascular, inflammatory, mitochondrial, nutritional, sleep, cognitive. Your numbers land in the system they belong to.
3. Find the gaps. A gap is a marker that is actionable and outside its optimal range. It ranks each gap P0 (fix now), P1 (borderline), P2 (nice to have).
4. Build the plan in three layers:
   - Drains first. Stop the things hurting you (late eating, alcohol, bad sleep, blue light). Removing a drain beats adding any single supplement.
   - Foundational supports. Established, safe interventions matched to each gap.
   - Enhancement. Emerging or experimental compounds, only if your risk tolerance allows.

### Evidence tiers (how sure the science is)
- T1 Established: magnesium, creatine, zone 2 cardio, time-restricted eating.
- T2 Emerging: NAD+ precursors, low-dose rapamycin, glycine, apigenin.
- T3 Experimental: peptides like BPC-157, TB-500, semax, noopept. These need your explicit consent and come with a full warning about sourcing, dosing, and stop signals.

### What you get
A calibration report. The top three calibrations to start this month. Specific dosages, timing, and a re-check date. DNA notes baked in (for example, an MTHFR variant means methylfolate beats folic acid).

### The caveat
This skill discusses experimental compounds that may lack FDA or EMA approval and long-term safety data. It is a decision-support tool, not a prescription. Do your own due diligence on legality, sourcing, dosing, and medical supervision.

## invest-optimizer: posture your portfolio to the moment

### The plain version
The market has a regime and you have a goal. This skill measures valuation, credit, macro conditions, liquidity, prediction-market probabilities, correlation, and statistical regime evidence; converts that evidence into a goal-aware posture; optimizes weights inside strict bands; then stress-tests the result. AI/ML signals remain research-only until they pass point-in-time, walk-forward, cost, capacity, calibration, and drift gates.

### What to give it
Your goal profile:
- Primary objective: income, growth, balanced, or preservation
- Risk tolerance: conservative, moderate, aggressive
- Investor type: day trader, swing trader, income investor, long-term holder
- Time horizon: under 1 year up to 15+ years
- Income cadence: how often you need cash from the portfolio
- Concentration: concentrated, balanced, or broad

If you have not set these, the agent asks or infers them. It will not proceed without a goal anchor. A growth investor and a preservation investor read the same market and should do opposite things.

### What it does, step by step
1. Anchor to goals. Load your profile. This is the fixed reference every later call measures against.
2. Read the regime. It checks seven axes:
- Valuation: are stocks expensive? (Shiller CAPE, Buffett Indicator, S&P 500 vs M2)
- Complacency: is everyone pricing in zero risk? (VIX, credit spreads)
- Macro: is a recession brewing? (yield curve)
- Microstructure and liquidity: can the portfolio trade through stress? (spreads, depth/volume participation when available, gaps, volatility, and a clearly labeled ETF range proxy)
- Prediction markets: what are betting markets implying about recession and rate moves? (Polymarket)
- Correlation: is diversification real? (equity pairwise, equity–bond)
- Regime models: does statistical evidence agree? (HMM as one thin ensemble member, with probabilities, disagreement, and calibration—not an override)
Each axis gets a verdict. Together they form one market pulse: EXPANSION, LATE CYCLE, CONTRACTION, or CRISIS. A bundled tool (`tools/market_pulse.py`) pulls every axis live — no API keys, nothing to install.
3. Calibrate posture. The pulse meets your goals in a matrix. Late cycle plus a growth goal means trim and raise cash. Late cycle plus a preservation goal means cut equity to the floor. Same pulse, different posture.
4. Optimize weights. A bundled stdlib optimizer (`tools/optimize.py`) runs return-free models—HRP by default, plus min-variance, risk parity, and inverse-volatility—with per-name caps, effective-N, CVaR, and correlation-shock stability. When available, maintained libraries add shrinkage covariance, Black–Litterman or Entropy-Pooling views, drawdown-aware optimization, and multi-period turnover/cost planning. Equal weight is the final fallback, not the default.
5. Validate learned signals. A Qlib-style, tool-independent research contract requires point-in-time universes, immutable chronological splits, fold-local preprocessing, simple baselines, purged/embargoed walk-forward tests, IC/RankIC and decay diagnostics, capacity and execution costs, reproducible experiment records, and champion/challenger rollback rules. Forecast, portfolio policy, and execution remain separate. A model may affect views only after passing the promotion gate.
6. Risk check. Every recommendation is tested against position-size, sector, leverage, liquidity, capacity, and correlation limits plus max drawdown, CVaR, tail ratio, Calmar, and Monte Carlo bust probability. Block or regime-aware bootstrap is preferred over IID simulation. Facts, model estimates, and scenarios are labeled separately; uncertainty, disagreement, calibration, costs, drift, and fallback behavior are explicit. Failed gates downgrade the posture.

### Bundled tools — zero dependencies, no API keys
Everything in `invest-optimizer/tools/` is plain Python 3 standard library. Nothing to pip install, no keys to configure. Every data source fails soft: a missing reading downgrades that axis, and the brief still ships.
- `market_pulse.py` — the full regime read in one run: Shiller CAPE, Buffett Indicator, S&P/M2, VIX, high-yield spread, the yield curve, a limited SMH high-low-range proxy, Polymarket recession/rate-hike odds, 60-day equity and equity–bond correlations, and a thin 2-state HMM check. The proxy is not treated as a reversal, flash-crash, market-wide, or AI-attribution measure.
- `optimize.py` — portfolio weights from daily prices: HRP (default), min-variance, risk parity, or inverse-volatility, with caps and a correlation-shock stress test.
- `risk.py` — forward risk for a proposed mix: max drawdown, CVaR, tail ratio, Calmar, and Monte Carlo bust probability.
- `dip_signal.py` — a 1–20 sector heat gauge: what share of an ETF's bucket trades below its 200-week moving average. 17–20 says take profits and build cash; 6–9 says deploy it in stages; 1–5 says the bucket is well below its weekly averages — buy aggressively. Scale and formula: `SIGNALS.md`.
- `extensions/invest-tools.ts` — optional for pi users: exposes all three as native agent tools. Copy it to `~/.pi/agent/extensions/`.

### What you get
A posture brief with the profile, evidence-dated market pulse, confidence and model disagreement, current-to-target allocation actions, reversal gates, exact weights, liquidity/capacity assumptions, and forward-risk results. Learned signals include their experiment provenance and promotion status. If stock selection is appropriate, candidates pass explicit technical gates; they remain a research list, not a buy list.

### AI/quant guardrails
The skill borrows useful research patterns from Qlib and tools catalogued by Awesome Quant without assuming any repository creates alpha. It favors deterministic baselines, point-in-time data, reproducible experiments, realistic execution, maintained libraries, and the smallest stack that closes a named gap. Deep learning, graph models, transformers, RL, LLM sentiment, synthetic scenarios, and model-zoo results never receive automatic allocation authority.

### The quick version
Ask only about market conditions and the skill skips your portfolio. You get a compact pulse table: valuation, complacency, macro, overall. ### The dip/profit signal
Ask "should I buy this dip or take profits?" about any ETF and you get a score from 1 to 20. It counts how many of the fund's top holdings trade below their 200-week moving average. High scores mean the bucket is stretched — harvest it and build cash. Low scores mean the bucket is on sale — spend the cash the high scores told you to save. One mechanical loop: profits become reserves, reserves become dips.

## How to install and run

Both skills install the same way. Copy the skill folder into your agent's skills directory (for example `.claude/skills/` for Claude Code, `.agents/skills/` for MiMoCode). Then start a session and type the slash command:

- `/calibrate-longevity`
- `/invest-optimizer`

Paste your data. The agent runs the workflow and hands back the report. invest-optimizer's tools need only Python 3 (standard library — no pip step). If your agent is pi, copy `invest-optimizer/extensions/invest-tools.ts` into `~/.pi/agent/extensions/` to call the tools natively.

## The shared idea

Both skills demand traceable data, label uncertainty, rank by impact, and separate measurement from judgment. Sophisticated models earn authority only by beating simple baselines under realistic validation.
