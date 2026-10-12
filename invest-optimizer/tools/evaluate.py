#!/usr/bin/env python3
"""evaluate.py — dated roll-forward check of a weighting policy (stdlib only).

Fits weights on a trailing window, holds them with drift, and rebalances on a
fixed schedule. The conventions are the deliverable, because the headline number
is meaningless without them:

  - a policy sees returns strictly before the rebalance date, so nothing leaks
  - holdings drift with returns between rebalances
  - each rebalance pays cost_bps per unit of notional traded
  - wealth compounds from simple returns

A window of trailing history warms the first fit, so the reported path starts
where the policy is actually live rather than reporting equal-weight drift as
policy output.

Two reference runs sit beside the policy on the same dates and the same cost
assumption: equal weight rebalanced on the same schedule, and equal weight held
from the first date (buy and hold).

Usage:
  evaluate.py JEPI QQQI SPYI SMH [--model hrp] [--cap 0.30] [--window 126]
              [--step 21] [--cost-bps 10] [--json]
"""
import json, math, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import feeds
import optimize
from quant import cov_matrix, is_psd, max_drawdown, mean, stdev

MODELS = optimize.MODELS


def roll(rets, weights_fn, step, cost_bps, warmup=0):
    """Roll a policy forward over per-ticker simple-return lists.

    weights_fn receives returns from before the rebalance date only. A policy
    that cannot fit raises InfeasibleError; the current holdings are held and
    the event is counted rather than hidden.

    warmup is the count of leading periods that pass before the first
    rebalance. The curve starts there, so the reported path is entirely
    policy-live rather than reporting equal-weight drift as policy output.
    """
    n, T = len(rets), len(rets[0])
    w, value, curve = [1.0 / n] * n, 1.0, [1.0]
    traded_total, held = 0.0, 0
    for t in range(warmup, T):
        if (t - warmup) % step == 0:
            try:
                target = weights_fn([r[:t] for r in rets])
            except optimize.InfeasibleError:
                held += 1
                target = None
            if target is not None:
                traded = sum(abs(target[i] - w[i]) for i in range(n))
                traded_total += traded
                value *= 1.0 - traded * cost_bps / 10000.0
                w = list(target)
        gross = [1.0 + r[t] for r in rets]
        port = sum(w[i] * gross[i] for i in range(n))
        value *= port
        curve.append(value)
        w = [w[i] * gross[i] / port for i in range(n)]
    return curve, traded_total, held


def summarize(curve, traded_total, held):
    daily = [curve[i] / curve[i - 1] - 1.0 for i in range(1, len(curve))]
    years = len(daily) / 252.0
    growth = curve[-1] / curve[0]
    vol = stdev(daily) * math.sqrt(252)
    return {"days": len(daily), "growth": round(growth, 4),
            "cagr": round(growth ** (1 / years) - 1, 4) if years > 0 and growth > 0 else 0.0,
            "ann_vol": round(vol, 4),
            "max_drawdown": round(max_drawdown(curve), 4),
            "sharpe": round(mean(daily) * 252 / vol, 2) if vol > 0 else 0.0,
            "turnover": round(traded_total, 3), "held_rebalances": held}


def fixed_policy(model, cap, window):
    """Fit the model on the trailing window and enforce the name cap."""
    def policy(history):
        if not history or len(history[0]) < 2:
            raise optimize.InfeasibleError("not enough history to fit")
        cov = cov_matrix([h[-window:] for h in history])
        if not is_psd(cov):
            raise optimize.InfeasibleError("covariance is not positive semi-definite")
        return optimize.cap_weights(model(cov), cap)
    return policy


def equal_weight_policy(n):
    return lambda history: [1.0 / n] * n


def main():
    args = sys.argv[1:]
    as_json = "--json" in args

    def opt(name, default):
        return float(args[args.index(name) + 1]) if name in args else default

    model = args[args.index("--model") + 1] if "--model" in args else "hrp"
    cap, window = opt("--cap", 0.30), int(opt("--window", 126))
    step, cost_bps = int(opt("--step", 21)), opt("--cost-bps", 10)
    tickers = [a.upper() for a in args if not a.startswith("--") and a not in MODELS
               and a.replace(".", "").isdigit() is False]
    if model not in MODELS or len(tickers) < 2:
        print(__doc__)
        sys.exit(1)

    try:
        hist = {t: dict(feeds.closes(t)) for t in tickers}
    except Exception as e:
        print(f"ERROR fetching history: {e}")
        sys.exit(1)
    dates = sorted(set.intersection(*[set(h) for h in hist.values()]))
    if len(dates) < window + step + 1:
        print(f"ERROR: only {len(dates)} common dates; a {window}d fit with a {step}d step "
              f"needs {window + step + 1}. Lower --window or --step, or fetch longer history.")
        sys.exit(2)
    px = {t: [hist[t][d] for d in dates] for t in tickers}
    rets = [[px[t][i] / px[t][i - 1] - 1.0 for i in range(1, len(dates))] for t in tickers]

    runs = {}
    for name, fn, cadence in [
            ("policy", fixed_policy(MODELS[model], cap, window), step),
            ("equal_weight", equal_weight_policy(len(tickers)), step),
            ("buy_and_hold", equal_weight_policy(len(tickers)), len(rets[0]))]:
        curve, traded, held = roll(rets, fn, cadence, cost_bps, warmup=window)
        runs[name] = summarize(curve, traded, held)
    out = {"tickers": tickers, "model": model, "cap": cap, "window": window,
           "step": step, "cost_bps": cost_bps, "dates": [dates[0], dates[-1]],
           "evaluated": [dates[window], dates[-1]], "runs": runs}

    if as_json:
        print(json.dumps(out, indent=1))
        return
    print(f"ROLL-FORWARD — {dates[window]} to {dates[-1]} ({runs['policy']['days']}d live, "
          f"{window}d warmup from {dates[0]})  "
          f"model={model} step={step}d cost={cost_bps:g}bp cap={cap:.0%}")
    print(f"  {'run':<14}{'growth':>8}{'cagr':>8}{'vol':>8}{'maxDD':>8}{'sharpe':>8}{'turnover':>10}")
    for name, r in runs.items():
        print(f"  {name:<14}{r['growth']:>8.2f}{r['cagr']:>8.1%}{r['ann_vol']:>8.1%}"
              f"{r['max_drawdown']:>8.1%}{r['sharpe']:>8.2f}{r['turnover']:>10.1f}")
    held = runs["policy"]["held_rebalances"]
    if held:
        print(f"  policy held existing weights through {held} unfit rebalance(s)")
    print("  One path, not evidence of edge. Compare only against these same dates and costs.")


if __name__ == "__main__":
    main()
