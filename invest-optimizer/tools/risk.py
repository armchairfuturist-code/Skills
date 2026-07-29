#!/usr/bin/env python3
"""risk.py — Phase 4 forward risk analytics for a proposed mix (stdlib only).

Reports per OPTIMIZATION.md / SKILL.md Phase 4:
  historical max drawdown, daily CVaR(95), tail ratio, Calmar,
  Monte Carlo bust probability P(maxDD <= -loss_tol within horizon, bootstrap),
  optional goal probability P(final equity >= target).

Usage:
  risk.py JEPI:0.22 QQQI:0.20 SPYI:0.20 SMH:0.14 JEPQ:0.12 IWMI:0.12 \
          [--loss-tol 0.25] [--horizon 63] [--paths 1000] [--goal 1.10] [--json]

Gates (SKILL.md Phase 4): bust >25% (moderate) / >10% (conservative) ->
downgrade posture one rung. ~125 trading days of history is thin; MC is
bootstrap, not forecast. State the gap in the brief.
"""
import json, math, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import feeds
from quant import log_returns, max_drawdown, mc_bust, mean, percentile, stdev


def main():
    args = sys.argv[1:]
    as_json = "--json" in args

    def opt(name, default):
        return float(args[args.index(name) + 1]) if name in args else default

    loss_tol, horizon = opt("--loss-tol", 0.25), int(opt("--horizon", 63))
    paths, goal = int(opt("--paths", 1000)), opt("--goal", 0.0)
    positions = []
    for a in args:
        if ":" in a and not a.startswith("--"):
            t, w = a.rsplit(":", 1)
            positions.append((t.upper(), float(w)))
    if not positions:
        print(__doc__)
        sys.exit(1)
    tickers = [t for t, _ in positions]
    w = [x for _, x in positions]
    s = sum(w)
    if abs(s - 1.0) > 0.01:
        print(f"WARN: weights sum {s:.3f} — renormalized to 1.0", file=sys.stderr)
        w = [x / s for x in w]

    try:
        hist = {t: dict(feeds.closes(t)) for t in tickers}
    except Exception as e:
        print(f"ERROR fetching history: {e}")
        sys.exit(1)
    dates = sorted(set.intersection(*[set(h) for h in hist.values()]))[-126:]
    rets = {t: log_returns([hist[t][d] for d in dates]) for t in tickers}
    port = [sum(w[i] * rets[t][tt] for i, t in enumerate(tickers)) for tt in range(len(dates) - 1)]
    simple = [math.exp(r) - 1 for r in port]

    equity, acc = [1.0], 1.0
    for r in simple:
        acc *= (1 + r)
        equity.append(acc)
    mdd = max_drawdown(equity)
    srt = sorted(simple)
    k = max(1, len(srt) // 20)
    cvar95 = sum(srt[:k]) / k
    var95 = percentile(simple, 0.05)
    p5, p95 = percentile(simple, 0.05), percentile(simple, 0.95)
    tail_ratio = abs(p95 / p5) if p5 != 0 else float("inf")
    ann_ret = mean(simple) * 252
    ann_vol = stdev(simple) * math.sqrt(252)
    calmar = ann_ret / abs(mdd) if mdd != 0 else float("inf")
    bust = mc_bust(port, loss_tol, horizon, paths)
    gate = "PASS" if bust <= 0.25 else "FAIL — downgrade posture one rung (moderate gate 25%)"

    out = {"tickers": dict(zip(tickers, [round(x, 4) for x in w])), "asof": dates[-1],
           "obs": len(simple), "ann_return": round(ann_ret, 4), "ann_vol": round(ann_vol, 4),
           "max_drawdown": round(mdd, 4), "daily_var95": round(var95, 4),
           "daily_cvar95": round(cvar95, 4), "tail_ratio": round(tail_ratio, 2),
           "calmar": round(calmar, 2), "mc": {"paths": paths, "horizon_days": horizon,
           "loss_tol": loss_tol, "bust_p": round(bust, 3), "gate": gate}}
    if goal > 0:
        import random
        rng = random.Random(42)
        hit = sum(1 for _ in range(paths)
                  if math.exp(sum(rng.choice(port) for _ in range(horizon))) >= goal)
        out["mc"]["goal"] = goal
        out["mc"]["goal_p"] = round(hit / paths, 3)

    if as_json:
        print(json.dumps(out, indent=1))
        return
    print(f"FORWARD RISK — asof {out['asof']} obs={out['obs']}d (thin: bootstrap, not forecast)")
    print(f"  mix: " + "  ".join(f"{t} {x:.0%}" for t, x in zip(tickers, w)))
    print(f"  ann return {ann_ret:.1%}   ann vol {ann_vol:.1%}   hist maxDD {mdd:.1%}")
    print(f"  daily VaR95 {var95:.2%}  CVaR95 {cvar95:.2%}  tail ratio {tail_ratio:.2f}  Calmar {calmar:.2f}")
    print(f"  MC({paths} paths, {horizon}d): P(DD<=-{loss_tol:.0%}) = {bust:.1%}  [{gate}]")
    if goal > 0:
        print(f"  P(reach {goal:.0%} in {horizon}d) = {out['mc']['goal_p']:.1%}")


if __name__ == "__main__":
    main()
