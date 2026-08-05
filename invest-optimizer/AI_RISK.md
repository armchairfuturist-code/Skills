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

## Qlib-style research contract

Use this contract when a learned signal is proposed; Qlib may implement it, but the contract is tool-independent.

1. **Point-in-time data:** pin universe membership, corporate-action handling, calendar, vendor snapshot, and feature availability time.
2. **Dataset boundary:** fit processors only on the training window; keep train/validation/test segments chronological and immutable.
3. **Baselines first:** compare with a simple linear/GBDT model and a fixed factor set such as Alpha158-class price/volume features before deep, graph, transformer, or RL models.
4. **Forecast diagnostics:** report IC and RankIC, stability by regime, turnover, capacity, and signal-decay curve—not accuracy alone.
5. **Recorder:** persist data/version hashes, universe, features, labels, splits, seed, model/config, predictions, costs, and artifacts for every run.
6. **Signal-policy-execution split:** the model emits forecasts with uncertainty; portfolio policy converts forecasts to constrained targets; an executor models limits, suspensions, spread, impact, and fill timing.
7. **Rolling deployment:** retrain on a declared schedule, compare champion/challenger out of sample, and define rollback triggers.

**Promotion gate:** a learned signal may alter Black–Litterman/Entropy-Pooling views only when net walk-forward results beat the baseline across multiple folds, IC sign is stable, drawdown and turnover fit the goal, and the result survives a cost/capacity stress. Otherwise it remains research-only.

## Hard gates

- Prevent look-ahead, survivorship, and universe-selection bias.
- Split by time; use purging/embargo when labels overlap.
- Fit scalers, features, covariance, and model selection inside each training fold.
- Report gross and net results with realistic fees, borrow, latency, spread, and impact.
- Backtest VaR exceedances and CVaR stability; state sample size and horizon.
- Treat synthetic scenarios as sensitivity tests, never observed probabilities unless calibrated.
- Keep an audit trail of source snapshots, prompts/model versions, parameters, and overrides.

## Tool landscape

Inspect the environment before recommending or installing anything; verify current maintenance, license, data rights, and release date. Treat Awesome Quant as a discovery index, not an endorsement.

- **End-to-end ML research:** Qlib when point-in-time datasets, experiment recording, model comparison, rolling retraining, and signal-to-execution evaluation are needed.
- **Research/features:** OpenBB and vectorbt for focused data/exploration paths.
- **Portfolio/risk:** skfolio, Riskfolio-Lib, PyPortfolioOpt; cvxportfolio for multi-period cost-aware paths.
- **Factor diagnostics:** Alphalens-reloaded or equivalent for IC, quantiles, turnover, and decay.
- **Performance reports:** empyrical-reloaded/pyfolio-reloaded or equivalent; verify definitions against in-skill metrics.
- **Backtest/execution:** LEAN or NautilusTrader when fill, order, venue, and event fidelity matter; lightweight engines are acceptable for daily allocation if assumptions are explicit.
- **Calendars:** exchange-calendars or equivalent; never infer sessions from weekdays.
- **RL experimentation:** FinRL only after leakage-safe supervised and rules-based baselines pass.
- **Monitoring:** Evidently or equivalent drift/calibration tooling.

Select the smallest stack that closes a named gap. Score candidates on active maintenance, test coverage, reproducibility, asset/venue fit, point-in-time data support, cost/execution fidelity, license, and integration burden. Popularity or a recent release is not evidence of edge.

## Completion criterion

The brief distinguishes observed facts, model estimates, and scenarios; reports uncertainty and model disagreement; tests leakage, calibration, costs, liquidity, and drift; and states the deterministic fallback.