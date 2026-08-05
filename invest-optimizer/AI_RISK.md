# AI-assisted market-risk protocol

Load this reference during Phase 2 and Phase 4 when return history or current text/event data is available.

## Principle

Use AI to expand and challenge the risk model, not to manufacture precision. Separate **measurement** (prices, spreads, liquidity, exposures) from **judgment** (regime, narrative, scenario). Every model output carries an as-of time, horizon, provenance, uncertainty, and falsification condition.

## Risk stack

| Layer | Useful methods | Required output |
|---|---|---|
| Market state | change-point detection; HMM/Markov-switching; volatility and correlation clustering | regime probabilities and disagreement, not one hard label |
| Tail risk | historical/filtered simulation; EVT; quantile or distributional models; scenario generation | VaR plus CVaR, drawdown, scenario P&L, and calibration/backtest |
| Event risk | NLP/LLM extraction from filings, earnings calls, central-bank releases, news | structured event, affected exposures, source quote, timestamp, confidence |
| Cross-asset contagion | dynamic correlation, factor exposure, graph/network stress | concentration by risk factor and stressed correlation loss |
| Liquidity/execution | spread, depth, volume participation, market impact, gap frequency | liquidation horizon and cost under normal/stress conditions |
| Model risk | ensemble disagreement, conformal intervals where valid, drift/OOD detection | uncertainty band, drift flag, fallback model |

## Workflow

1. Establish deterministic baselines: realized volatility, drawdown, beta/factors, spread/liquidity, historical VaR/CVaR, and correlation stress.
2. Add models only where they improve a named decision. Compare each model with the baseline using purged, embargoed walk-forward evaluation; include costs and slippage.
3. Use an ensemble for regime/tail estimates. Report probability distribution and disagreement. High disagreement reduces position size and view confidence.
4. Convert NLP/LLM findings into structured claims. Require a primary source or mark the claim unverified. LLM sentiment alone never changes weights.
5. Stress scenarios spanning price, volatility, correlation, credit, liquidity, and execution. Include at least one historical and one forward hypothetical scenario.
6. Monitor calibration, feature/data drift, and performance decay. On drift, fall back to the deterministic baseline and shorten review cadence.

## Hard gates

- Prevent look-ahead, survivorship, and universe-selection bias.
- Split by time; use purging/embargo when labels overlap.
- Fit scalers, features, covariance, and model selection inside each training fold.
- Report gross and net results with realistic fees, borrow, latency, spread, and impact.
- Backtest VaR exceedances and CVaR stability; state sample size and horizon.
- Treat synthetic scenarios as sensitivity tests, never observed probabilities unless calibrated.
- Keep an audit trail of source snapshots, prompts/model versions, parameters, and overrides.

## Tool landscape

Inspect the environment before recommending or installing anything; verify current maintenance, license, data rights, and release date.

- **Research/features:** Qlib, OpenBB, vectorbt.
- **Portfolio/risk:** skfolio, Riskfolio-Lib, PyPortfolioOpt.
- **RL experimentation:** FinRL; apply only after leakage-safe baselines and cost-aware walk-forward tests.
- **Backtest/execution:** LEAN, NautilusTrader, Backtrader.
- **Monitoring:** Evidently or equivalent drift/calibration tooling.

A repository's popularity or recent release is not evidence of trading edge. Prefer reproducible data lineage, realistic execution, active maintenance, and tests over agent demos or headline returns.

## Completion criterion

The brief distinguishes observed facts, model estimates, and scenarios; reports uncertainty and model disagreement; tests leakage, calibration, costs, liquidity, and drift; and states the deterministic fallback.