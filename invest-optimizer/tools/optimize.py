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
correlation-break re-solve drift (+0.3 uniform corr shock).
"""
import json, math, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import feeds
from quant import (corr_matrix, cov_matrix, effective_n, hrp, inverse_vol, log_returns,
                   min_variance, percentile, portfolio_var, risk_parity, shock_corr)

MODELS = {"hrp": hrp, "minvar": min_variance, "riskpar": risk_parity, "invvol": inverse_vol}


def cap_weights(w, cap):
    """Iteratively clip at cap and redistribute to uncapped names."""
    w = w[:]
    for _ in range(len(w) + 2):
        over = [i for i in range(len(w)) if w[i] > cap]
        if not over:
            break
        excess = sum(w[i] - cap for i in over)
        for i in over:
            w[i] = cap
        under = [i for i in range(len(w)) if w[i] < cap]
        if not under:
            break
        room = sum(cap - w[i] for i in under)
        for i in under:
            w[i] += excess * (cap - w[i]) / room
    s = sum(w)
    return [x / s for x in w]


def aligned_returns(tickers):
    hist = {t: dict(feeds.closes(t)) for t in tickers}
    dates = sorted(set.intersection(*[set(h) for h in hist.values()]))[-126:]
    rets = [log_returns([hist[t][d] for d in dates]) for t in tickers]
    return rets, dates


def solve_for(tickers, model, cap):
    rets, dates = aligned_returns(tickers)
    cov = cov_matrix(rets)
    w = cap_weights(MODELS[model](cov), cap)
    port = [sum(w[i] * rets[i][t] for i in range(len(tickers))) for t in range(len(rets[0]))]
    srt = sorted(port)
    k = max(1, len(port) // 20)
    cvar95 = sum(srt[:k]) / k  # mean of worst 5% days
    # correlation-break stress: +0.3 uniform shock, re-solve, max weight drift
    w_shock = cap_weights(MODELS[model](shock_corr(cov)), cap)
    drift = max(abs(w[i] - w_shock[i]) for i in range(len(tickers)))
    return {"weights": dict(zip(tickers, w)), "asof": dates[-1], "obs": len(rets[0]),
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
    print(f"  stress: +0.3 corr shock -> max weight drift {r['corr_shock_drift']:.1%}  [{flag}]")


if __name__ == "__main__":
    main()
