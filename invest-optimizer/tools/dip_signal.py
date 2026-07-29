#!/usr/bin/env python3
"""dip_signal.py — sector heat gauge: take-profits vs buy-the-dip for ETFs.

Score 1-20 from constituent breadth: the share of an ETF's top holdings trading
below their 200-WEEK moving average (per SIGNALS.md — scale, formula, bands).

  17-20 OVERBOUGHT  -> TAKE PROFITS (free up cash for the coming dip)
  13-16 EXTENDED    -> stop adding; trim into strength
  10-12 NEUTRAL     -> hold
   6-9  DIP         -> staged buys; deploy reserves in thirds
   1-5  DEEP DIP    -> deploy cash aggressively; the bucket is well below
                       its weekly averages — this is what reserves are for

Cash-recycling loop: scores >=17 build the reserve; scores <=9 spend it.

Data: holdings from stockanalysis SSR page; 200w MA from full daily history
(stockanalysis chart endpoint, NASDAQ fallback). Young listings (<200 weeks)
are excluded from breadth, never faked. Same-day disk cache in /tmp.

Usage: dip_signal.py SMH QQQ XLU [--top 20] [--weeks 200] [--verbose] [--json]
"""
import json, os, sys
from datetime import date

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import feeds

CACHE_DIR = "/tmp/dip_signal_cache"

BANDS = [(17, "OVERBOUGHT", "TAKE PROFITS — free up cash for the coming dip"),
         (13, "EXTENDED", "stop adding; trim into strength"),
         (10, "NEUTRAL", "hold — no action"),
         (6, "DIP", "staged buys — deploy reserves in thirds"),
         (1, "DEEP DIP", "deploy cash aggressively — bucket is well below weekly averages")]


def band_for(score):
    for lo, name, action in BANDS:
        if score >= lo:
            return name, action
    return BANDS[-1][1], BANDS[-1][2]


def ma200w_cached(ticker, weeks):
    os.makedirs(CACHE_DIR, exist_ok=True)
    f = os.path.join(CACHE_DIR, f"{ticker.upper()}_{weeks}.json")
    try:
        cached = json.load(open(f))
        if cached.get("run_date") == str(date.today()):
            return cached["result"]
    except Exception:
        pass
    result = None
    try:
        result = feeds.ma200w(ticker, weeks)
    except Exception:
        result = None
    json.dump({"run_date": str(date.today()), "result": result}, open(f, "w"))
    return result


def high52_distance(ticker):
    h = feeds.history(ticker)  # ~6mo daily OHLC — fine for 52w-high check
    if not h:
        return None
    hi = max(r["h"] for r in h)
    return h[-1]["c"] / hi - 1.0


def signal(etf, top, weeks, verbose):
    out = {"etf": etf.upper(), "weeks": weeks}
    try:
        hold = feeds.holdings(etf, top)
    except Exception as e:
        out["error"] = f"holdings: {e}"
        return out
    checked, below, young, failed = [], [], [], []
    for sym, w in hold:
        m = ma200w_cached(sym, weeks)
        if m is None:
            young.append(sym)
            continue
        row = {"symbol": sym, "weight": w, "dist": m["dist"], "below": m["dist"] < 0}
        checked.append(row)
        if row["below"]:
            below.append(row)
    if not checked:
        out["error"] = "no constituents with sufficient history"
        return out
    w_checked = sum(r["weight"] for r in checked)
    w_below = sum(r["weight"] for r in below)
    pct_below_count = len(below) / len(checked)
    pct_below_weight = w_below / w_checked if w_checked else 0.0

    # score (SIGNALS.md): breadth spans 2-19 (0% below -> hot, 100% below -> deep dip);
    # +1/-1 vs own 200WMA; +1 within 5% of 52w high; -1 at -15..-25% off high; -2 beyond -25%.
    score = 2 + round((1 - pct_below_weight) * 17)
    etf_ma = ma200w_cached(etf, weeks)
    d52 = None
    try:
        d52 = high52_distance(etf)
    except Exception:
        pass
    if etf_ma:
        score += 1 if etf_ma["dist"] > 0 else -1
    if d52 is not None:
        if d52 >= -0.05:
            score += 1
        elif d52 <= -0.25:
            score -= 2
        elif d52 <= -0.15:
            score -= 1
    score = max(1, min(20, score))
    band, action = band_for(score)

    out.update({
        "score": score, "band": band, "action": action,
        "pct_below_count": round(pct_below_count, 3),
        "pct_below_weight": round(pct_below_weight, 3),
        "checked": len(checked), "excluded_young": young,
        "etf_vs_200wma": round(etf_ma["dist"], 3) if etf_ma else None,
        "etf_from_52w_high": round(d52, 3) if d52 is not None else None,
        "asof": etf_ma["asof"] if etf_ma else str(date.today()),
    })
    if abs(pct_below_weight - pct_below_count) > 0.20:
        out["tension"] = ("mega-caps vs breadth disagree: weight% and count% diverge "
                          ">20pts — the index level is lying about the average stock")
    if verbose:
        out["detail"] = sorted(checked, key=lambda r: r["dist"])
    return out


def print_row(r, verbose):
    print(f" {r['etf']:<7} {r['score']:>3}/20  {r['band']:<11} "
          f"below200w: {r['pct_below_weight']:.0%} w / {r['pct_below_count']:.0%} c "
          f"({r['checked']} names" + (f", -{len(r['excluded_young'])} young" if r['excluded_young'] else "") + ")")
    if r.get("etf_vs_200wma") is not None:
        print(f"          ETF vs 200WMA {r['etf_vs_200wma']:+.1%}"
              + (f"   from 52w high {r['etf_from_52w_high']:+.1%}" if r.get("etf_from_52w_high") is not None else "")
              + f"   [{r['asof']}]")
    print(f"          -> {r['action']}")
    if r.get("tension"):
        print(f"          ! {r['tension']}")
    if verbose and r.get("detail"):
        for d in r["detail"]:
            mark = "BELOW" if d["below"] else "above"
            print(f"            {d['symbol']:<7} w={d['weight']:>5.2f}%  vs200WMA {d['dist']:+7.1%}  {mark}")


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    verbose = "--verbose" in args

    def opt(name, default):
        return int(args[args.index(name) + 1]) if name in args else default

    top, weeks = opt("--top", 20), opt("--weeks", 200)
    etfs = [a.upper() for a in args if not a.startswith("--") and not a.isdigit()]
    if not etfs:
        print(__doc__)
        sys.exit(1)
    results = [signal(e, top, weeks, verbose) for e in etfs]
    if as_json:
        print(json.dumps(results, indent=1))
        return
    print(f"DIP/PROFIT SIGNAL — {date.today()}  (breadth = % of top holdings below {weeks}w MA; scale in SIGNALS.md)")
    for r in results:
        if "error" in r:
            print(f" {r['etf']:<7} GAP ({r['error']})")
            continue
        print_row(r, verbose)
    print("  1-5 DEEP DIP deploy aggressively · 6-9 DIP staged buys · 10-12 hold · 13-16 trim · 17-20 TAKE PROFITS")


if __name__ == "__main__":
    main()
