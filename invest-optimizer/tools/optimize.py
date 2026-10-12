#!/usr/bin/env python3
"""optimize.py — Phase 3.5 weights for the invest-optimizer skill (stdlib only).

Return-free models only — under EXTREME/BUBBLE valuation reads, expected-return
forecasts are the least trustworthy input (OPTIMIZATION.md). All models long-only,
sum to 100%, with stress checks per OPTIMIZATION.md.

Models:
  hrp      Hierarchical Risk Parity (default; robust when correlations unstable)
  minvar   long-only minimum variance (KKT solve + clipping)
  riskpar  equal risk contribution
  invvol   inverse-volatility (heuristic fallback)

Usage:
  optimize.py JEPI QQQI SPYI SMH JEPQ IWMI [--model hrp] [--cap 0.30] [--json]

Checks reported: in-sum, name cap, effective N, daily CVaR(95) of the mix,
correlation-break re-solve drift (correlations shrunk toward equicorrelation).
"""
import json, math, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import feeds
from quant import (corr_matrix, cov_matrix, effective_n, hrp, inverse_vol, is_psd, log_returns,
                   min_variance, percentile, portfolio_simple_returns, portfolio_var,
                   risk_parity, shock_corr)

MODELS = {"hrp": hrp, "minvar": min_variance, "riskpar": risk_parity, "invvol": inverse_vol}


class InfeasibleError(ValueError):
    """The request cannot be satisfied as stated, so no weights may be emitted."""


def cap_weights(w, cap):
    """Clip at cap and redistribute to uncapped names.

    Raises InfeasibleError when n * cap < 1, because clipping cannot satisfy
    such a cap and the closing renormalization would silently breach it.
    """
    n = len(w)
    if n == 0:
        raise InfeasibleError("empty universe")
    if cap * n < 1.0 - 1e-12:
        raise InfeasibleError(f"cap {cap:.0%} infeasible for {n} names "
                              f"(needs at least {1 / n:.1%})")
    s0 = sum(w)
    w = [x / s0 for x in w] if s0 > 0 else [1.0 / n] * n
    for _ in range(n + 2):
        over = [i for i in range(n) if w[i] > cap + 1e-12]
        if not over:
            break
        excess = sum(w[i] - cap for i in over)
        for i in over:
            w[i] = cap
        under = [i for i in range(n) if w[i] < cap - 1e-12]
        if not under:
            break
        room = sum(cap - w[i] for i in under)
        if room <= 0:
            break
        for i in under:
            w[i] += excess * (cap - w[i]) / room
    w = [x / sum(w) for x in w]
    worst = max(w)
    if worst > cap + 1e-9:
        raise InfeasibleError(f"cap {cap:.0%} breached after clipping (max {worst:.2%})")
    return w


def aligned_returns(tickers):
    hist = {t: dict(feeds.closes(t)) for t in tickers}
    dates = sorted(set.intersection(*[set(h) for h in hist.values()]))[-126:]
    rets = [log_returns([hist[t][d] for d in dates]) for t in tickers]
    return rets, dates


def solve_for(tickers, model, cap):
    rets, dates = aligned_returns(tickers)
    cov = cov_matrix(rets)
    if not is_psd(cov):
        raise InfeasibleError("sample covariance is not positive semi-definite")
    w = cap_weights(MODELS[model](cov), cap)
    simple = portfolio_simple_returns(w, rets)
    srt = sorted(simple)
    k = max(1, len(simple) // 20)
    cvar95 = sum(srt[:k]) / k  # mean of worst 5% days
    # correlation-break stress: shrink toward equicorrelation, re-solve, weight drift
    cov_shock = shock_corr(cov)
    if not is_psd(cov_shock):
        raise InfeasibleError("stress covariance is not positive semi-definite")
    w_shock = cap_weights(MODELS[model](cov_shock), cap)
    drift = max(abs(w[i] - w_shock[i]) for i in range(len(tickers)))
    return {"weights": dict(zip(tickers, w)), "asof": dates[-1], "obs": len(simple),
            "ann_vol": math.sqrt(portfolio_var(w, cov) * 252),
            "daily_cvar95": cvar95,
            "effective_n": effective_n(w), "corr_shock_drift": drift,
            "shock_weights": dict(zip(tickers, w_shock))}


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    model = args[args.index("--model") + 1] if "--model" in args else "hrp"
    cap = float(args[args.index("--cap") + 1]) if "--cap" in args else 0.30
    tickers = [a.upper() for a in args if not a.startswith("--") and a not in MODELS
               and a.replace(".", "").isdigit() is False]
    if model not in MODELS or len(tickers) < 2:
        print(__doc__)
        sys.exit(1)
    try:
        r = solve_for(tickers, model, cap)
    except InfeasibleError as e:
        print(f"ERROR: {e}")
        print(f"NO ALLOCATION EMITTED — raise --cap to {1 / len(tickers):.1%} or more, "
              f"widen the universe, or drop the cap.")
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e} — fall back to equal-weight inside bands (OPTIMIZATION.md heuristic).")
        sys.exit(1)
    r["model"] = model
    r["cap"] = cap
    if as_json:
        print(json.dumps(r, indent=1))
        return
    print(f"OPTIMIZE — model={model} cov=sample/{r['obs']}d asof={r['asof']} cap={cap:.0%}")
    for t, w in sorted(r["weights"].items(), key=lambda kv: -kv[1]):
        print(f"  {t:<8} {w:7.2%}" + ("  <- at cap" if abs(w - cap) < 1e-6 else ""))
    print(f"  sum 100.00%  effective N {r['effective_n']:.1f}  ann vol {r['ann_vol']:.1%}  "
          f"daily CVaR95 {r['daily_cvar95']:.2%}")
    flag = "OK" if r["corr_shock_drift"] < 0.10 else "UNSTABLE — prefer hrp/invvol"
    print(f"  stress: corr-break re-solve -> max weight drift {r['corr_shock_drift']:.1%}  [{flag}]")


if __name__ == "__main__":
    main()
