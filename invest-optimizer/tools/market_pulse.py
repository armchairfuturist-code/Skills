#!/usr/bin/env python3
"""market_pulse.py — full Phase 2 data pull for the invest-optimizer skill.

One run covers every regime axis, each mapped to METRICS.md verdicts:
  2A valuation      Shiller CAPE (multpl), trailing PE (multpl), Buffett (FRED), SP500/M2 (FRED)
  2B complacency    VIX close (CBOE), HY spread (FRED BAMLH0A0HYM2)
  2C macro          10y-2y (FRED T10Y2Y) + treasury.gov curve levels
  2D microstructure tail-day proxy: SMH intraday range >3% days/week (stockanalysis OHLC)
  2E prediction     Polymarket gamma-api: recession + fed hike (+ extra search terms as args)
  2F correlation    60d pairwise SPY/QQQ/SMH + SPY-IEF equity-bond (stockanalysis)
  2G HMM regime     2-state Gaussian HMM on SPY daily returns (thin: ~125 obs — tension flag only)
  2H fiscal         debt-to-GDP (FRED GFDEGDQ188S), interest/revenue (FRED), credit-rating + maturity wall (manual)
  2I currency       DXY proxy (FRED DTWEXAFEGS), 10y TIPS real yield (FRED DFII10), gold GLD YoY
  2J money          M2 YoY (FRED M2SL), Fed balance sheet 3m (FRED WALCL)
  2K digital-asset  BTC vs 200-week MA (Kraken weekly OHLC)
  2L secular        SPY 200-day + 200-week MA (stockanalysis)
  2M ai-financing   circular AI financing (manual — web/primary sources)

Every axis fails soft (verdict GAP); a missing reading downgrades that axis,
the brief still ships. Verdict thresholds mirror METRICS.md — edit both or neither.

Usage: market_pulse.py [--json] ["extra polymarket search" ...]
"""
import json, sys
from datetime import date

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import feeds
from quant import corr_matrix, cov_matrix, log_returns, mean
from hmm import regime_report

DEFAULT_POLY_SLUGS = [("recession", "us-recession-by-end-of-2026"),
                      ("fed_hike", "fed-rate-hike-in-2026")]


# --- verdicts (mirror METRICS.md) ---------------------------------------------
def cape_v(v): return ("CHEAP" if v < 10 else "FAIR" if v < 17 else "RICH" if v < 25
                       else "EXTREME" if v < 35 else "BUBBLE")
def buffett_v(v): return ("CHEAP" if v < 80 else "FAIR" if v < 120 else "RICH" if v < 150
                          else "PLAYING WITH FIRE" if v < 200 else "EXTREME")
def vix_v(v): return ("COMPLACENT" if v < 12 else "NEUTRAL" if v < 18 else
                      "CONCERN" if v < 25 else "FEAR" if v < 35 else "PANIC")
def hy_v(v): return ("TIGHT (froth)" if v < 3 else "NORMAL" if v < 5 else
                     "WIDENING (stress)" if v < 8 else "DISTRESS")
def curve_v(v): return "EXPANSION" if v > 0.5 else ("WARNING" if v >= 0 else "RECESSION (inverted)")
def tail_v(w): return ("NORMAL" if w < 1 else "ELEVATED" if w < 3 else
                       "HIGH — tail-range proxy" if w < 8 else "EXTREME — range stress")
def pair_v(r): return ("DIVERSIFIED" if r < 0.3 else "NORMAL" if r < 0.5 else
                       "ELEVATED" if r < 0.7 else "CRISIS-CORR")
def ballast_v(r): return "BALLAST-OK" if r < -0.2 else ("WEAK-BALLAST" if r < 0.2 else "CO-CRASH")
def recession_v(p): return ("RECESSION (p>=0.30)" if p >= 0.30 else
                            "NEUTRAL (0.10-0.29)" if p >= 0.10 else "BULLISH (p<0.10)")

def debt_gdp_v(v): return ("HEALTHY" if v < 60 else "ELEVATED" if v < 100 else
                           "CRISIS-PRONE" if v < 130 else "EXTREME")
def debt_service_v(v): return ("HEALTHY" if v < 10 else "WATCH" if v < 15 else
                               "STRESSED" if v < 25 else "FISCAL DOMINANCE")
def dxy_v(yoy): return ("DOLLAR STRONG" if yoy > 2 else "DEBASEMENT" if yoy < -2 else "NEUTRAL")
def real_rate_v(v): return ("TIGHT (high)" if v > 1.5 else "NEUTRAL" if v > 0 else "DEBASEMENT REGIME (negative)")
def m2_v(yoy): return ("PRINTING" if yoy > 5 else "NEUTRAL" if yoy >= 0 else "QT (contracting)")
def qeqt_v(chg): return ("PRINTING (QE)" if chg > 1 else "NEUTRAL" if chg > -1 else "DRAIN (QT)")
def btc_200w_v(dist): return ("SECULAR BULL" if dist > 0.05 else
                              "INFLECTION (testing 200w)" if dist >= -0.05 else "SECULAR BEAR")
def secular_v(d200, d200w):
    if d200 is None or d200w is None:
        return "GAP (insufficient history)"
    a = d200["dist"] > 0
    b = d200w["dist"] > 0
    if a and b: return "SECULAR BULL"
    if a and not b: return "LATE-CYCLE BULL"
    return "SECULAR BEAR"




# --- axis builders -------------------------------------------------------------
def axis_valuation():
    rows = []
    try:
        v = feeds.multpl("shiller-pe")
        rows.append({"metric": "Shiller CAPE", "value": v, "verdict": cape_v(v)})
    except Exception as e:
        rows.append({"metric": "Shiller CAPE", "verdict": f"GAP ({e})"})
    try:
        v = feeds.multpl("s-p-500-pe-ratio")
        rows.append({"metric": "S&P trailing PE", "value": v, "verdict": cape_v(v)})
    except Exception as e:
        rows.append({"metric": "S&P trailing PE", "verdict": f"GAP ({e})"})
    try:
        b = feeds.buffett_indicator()
        rows.append({"metric": "Buffett (equities/GDP)", "value": round(b["value"], 1),
                     "asof": b["asof"], "verdict": buffett_v(b["value"])})
    except Exception as e:
        rows.append({"metric": "Buffett", "verdict": f"GAP ({e})"})
    try:
        m = feeds.sp500_div_m2()
        rows.append({"metric": "SP500 / M2 (no fixed thresholds)", "value": round(m["value"], 4),
                     "asof": m["asof"], "verdict": "compare vs own history"})
    except Exception as e:
        rows.append({"metric": "SP500/M2", "verdict": f"GAP ({e})"})
    return rows


def axis_complacency():
    rows = []
    try:
        v = feeds.cboe_vix()
        rows.append({"metric": "VIX close", "value": v["close"], "asof": v["date"],
                     "verdict": vix_v(v["close"])})
    except Exception as e:
        rows.append({"metric": "VIX", "verdict": f"GAP ({e})"})
    try:
        d, v = feeds.fred_series("BAMLH0A0HYM2")[-1]
        rows.append({"metric": "HY spread", "value": v, "asof": d, "verdict": hy_v(v)})
    except Exception as e:
        rows.append({"metric": "HY spread", "verdict": f"GAP ({e})"})
    return rows


def axis_macro():
    rows = []
    try:
        d, v = feeds.fred_series("T10Y2Y")[-1]
        rows.append({"metric": "10y-2y", "value": v, "asof": d, "verdict": curve_v(v)})
    except Exception as e:
        rows.append({"metric": "10y-2y", "verdict": f"GAP ({e})"})
    try:
        c = feeds.treasury_curve()
        rows.append({"metric": f"curve {c['date']}",
                     "value": f"3M {c['3M']} / 2Y {c['2Y']} / 10Y {c['10Y']} / 30Y {c['30Y']}",
                     "verdict": "levels"})
    except Exception:
        pass
    return rows


def axis_microstructure():
    """2D proxy: SMH intraday range >3% days per week, last 30 trading days."""
    try:
        h = feeds.history("SMH")[-30:]
        tails = sum(1 for r in h if (r["h"] - r["l"]) / r["c"] > 0.03)
        per_week = tails / 6.0
        return [{"metric": "SMH >3%-range days/wk (30d proxy)", "value": round(per_week, 1),
                 "asof": h[-1]["t"], "verdict": tail_v(per_week),
                 "note": "SMH high-low range proxy only; not reversal, flash-crash, market-wide, or AI-attribution evidence"}]
    except Exception as e:
        return [{"metric": "2D tail proxy", "verdict": f"GAP ({e})"}]


def axis_prediction(extra_terms):
    rows = []
    for label, slug in DEFAULT_POLY_SLUGS:
        try:
            for m in feeds.poly_event(slug):
                m["kind"] = label
                if label == "recession" and m.get("yes") is not None:
                    m["verdict"] = recession_v(m["yes"])
                rows.append(m)
        except Exception as e:
            rows.append({"question": slug, "kind": label, "verdict": f"GAP ({e})"})
    for t in extra_terms:
        try:
            rows.extend(dict(m, kind="search") for m in feeds.poly_search(t))
        except Exception as e:
            rows.append({"question": t, "kind": "search", "verdict": f"GAP ({e})"})
    return rows


def axis_correlation():
    """2F: 60d pairwise equity corr (SPY/QQQ/SMH) + SPY-IEF equity-bond corr."""
    try:
        tickers = ["SPY", "QQQ", "SMH", "IEF"]
        hist = {t: dict(feeds.closes(t)) for t in tickers}
        dates = sorted(set.intersection(*[set(h) for h in hist.values()]))[-61:]
        rets = {t: log_returns([hist[t][d] for d in dates]) for t in tickers}
        corr = corr_matrix(cov_matrix([rets[t] for t in tickers]))
        idx = {t: i for i, t in enumerate(tickers)}
        eq_pairs = [corr[idx["SPY"]][idx["QQQ"]], corr[idx["SPY"]][idx["SMH"]],
                    corr[idx["QQQ"]][idx["SMH"]]]
        eq = mean(eq_pairs)
        bond = corr[idx["SPY"]][idx["IEF"]]
        return [{"metric": "60d pairwise equity (SPY/QQQ/SMH)", "value": round(eq, 2),
                 "asof": dates[-1], "verdict": pair_v(eq)},
                {"metric": "60d SPY-IEF (equity-bond)", "value": round(bond, 2),
                 "asof": dates[-1], "verdict": ballast_v(bond)}]
    except Exception as e:
        return [{"metric": "2F correlation", "verdict": f"GAP ({e})"}]


def axis_hmm():
    try:
        r = regime_report(log_returns([c for _, c in feeds.closes("SPY")]))
        return [{"metric": f"HMM 2-state on SPY ({r['obs']} obs)", "value": r["regime"],
                 "verdict": f"P(turbulent)={r['p_turbulent_now']:.2f} "
                            f"P(stay)={r['p_stay'][0]:.2f}/{r['p_stay'][1]:.2f} "
                            f"stationary bear={r['stationary'][1]:.2f} "
                            f"vol_ann={r['vol_ann'][0]:.0%}/{r['vol_ann'][1]:.0%}",
                 "note": "confirmation layer only — flag tension, never silent override"}]
    except Exception as e:
        return [{"metric": "2G HMM", "verdict": f"GAP ({e})"}]


def axis_fiscal():
    rows = []
    try:
        d, v = feeds.debt_to_gdp()
        rows.append({"metric": "Debt-to-GDP", "value": round(v, 1), "asof": d, "verdict": debt_gdp_v(v)})
    except Exception as e:
        rows.append({"metric": "Debt-to-GDP", "verdict": f"GAP ({e})"})
    try:
        m = feeds.interest_to_revenue()
        rows.append({"metric": "Interest / federal revenue", "value": round(m["value"], 1),
                     "asof": m["asof"], "verdict": debt_service_v(m["value"])})
    except Exception as e:
        rows.append({"metric": "Interest / revenue", "verdict": f"GAP ({e})"})
    rows.append({"metric": "Credit-rating trend", "verdict": "MANUAL - full sweep (S&P 2011, Fitch 2023, Moody's May 2025)"})
    rows.append({"metric": "Maturity wall", "verdict": "MANUAL - near-term refi at 2-3x old coupon = risk"})
    return rows


def axis_currency():
    rows = []
    try:
        d, v = feeds.dxy()
        yoy = feeds._change_since(feeds.fred_series("DTWEXAFEGS"), 365)
        note = "DXY is relative (EUR/JPY/GBP) - gold/BTC are the better absolute meters"
        if yoy:
            note += f"; YoY {yoy['value']:.1f}%"
        rows.append({"metric": "DXY proxy (Fed adv. economies)", "value": round(v, 2), "asof": d,
                     "verdict": dxy_v(yoy["value"]) if yoy else "NEUTRAL", "note": note})
    except Exception as e:
        rows.append({"metric": "DXY", "verdict": f"GAP ({e})"})
    try:
        d, v = feeds.real_rate_10y()
        rows.append({"metric": "10y TIPS real yield", "value": round(v, 2), "asof": d, "verdict": real_rate_v(v),
                     "note": "high real yields can BE the debasement mechanism (fiscal premia), not its absence"})
    except Exception as e:
        rows.append({"metric": "10y real rate", "verdict": f"GAP ({e})"})
    try:
        g = feeds.gold_yoy()
        rows.append({"metric": "Gold (GLD) YoY", "value": round(g["value"], 1), "asof": g["asof"],
                     "verdict": "rising = debasement bid" if g["value"] > 0 else "falling"})
    except Exception as e:
        rows.append({"metric": "Gold (GLD)", "verdict": f"GAP ({e})"})
    return rows


def axis_money():
    rows = []
    try:
        m = feeds.m2_yoy()
        rows.append({"metric": "M2 YoY", "value": round(m["value"], 1), "asof": m["asof"],
                     "verdict": m2_v(m["value"]), "note": f"vs {m['prev_asof']}"})
    except Exception as e:
        rows.append({"metric": "M2 YoY", "verdict": f"GAP ({e})"})
    try:
        b = feeds.fed_balance_sheet_3m()
        rows.append({"metric": "Fed balance sheet 3m", "value": round(b["value"], 1), "asof": b["asof"],
                     "verdict": qeqt_v(b["value"]), "note": "QT=shrinking, QE=expanding"})
    except Exception as e:
        rows.append({"metric": "Fed balance sheet", "verdict": f"GAP ({e})"})
    return rows


def axis_digital():
    try:
        b = feeds.btc_200w()
        if b is None:
            return [{"metric": "BTC vs 200-week MA", "verdict": "GAP (young/no history)"}]
        return [{"metric": "BTC vs 200-week MA",
                 "value": "$" + format(b["price"], ",.0f") + " vs $" + format(b["ma"], ",.0f") + " (" + format(b["dist"]*100, "+.1f") + "%)",
                 "asof": b["asof"], "verdict": btc_200w_v(b["dist"]),
                 "note": "never broken in 15y - highest-leverage risk gate"}]
    except Exception as e:
        return [{"metric": "BTC 200-week MA", "verdict": f"GAP ({e})"}]


def axis_secular():
    rows = []
    try:
        d200 = feeds.ma200("SPY")
        rows.append({"metric": "SPY vs 200-day MA",
                     "value": format(d200["dist"]*100, "+.1f") + "%" if d200 else "n/a",
                     "asof": d200["asof"] if d200 else None,
                     "verdict": ("ABOVE" if d200["dist"] > 0 else "BELOW") if d200 else "GAP"})
    except Exception as e:
        rows.append({"metric": "SPY 200d", "verdict": f"GAP ({e})"})
    try:
        d200w = feeds.ma200w("SPY")
        rows.append({"metric": "SPY vs 200-week MA",
                     "value": format(d200w["dist"]*100, "+.1f") + "%" if d200w else "n/a",
                     "asof": d200w["asof"] if d200w else None,
                     "verdict": ("ABOVE" if d200w["dist"] > 0 else "BELOW") if d200w else "GAP"})
    except Exception as e:
        rows.append({"metric": "SPY 200w", "verdict": f"GAP ({e})"})
    try:
        rows.append({"metric": "Secular trend (200d + 200w)",
                     "verdict": secular_v(feeds.ma200("SPY"), feeds.ma200w("SPY"))})
    except Exception as e:
        rows.append({"metric": "Secular trend", "verdict": f"GAP ({e})"})
    return rows


def axis_ai_financing():
    return [{"metric": "Circular AI financing (2M)", "verdict": "MANUAL - web/primary sources",
             "note": "vendor financing, cross-investment loops, token profitability (Dell 1Q->57Q, Goldman higher) - qualitative, not computed"}]

# --- main -----------------------------------------------------------------------
def main():
    extra = [a for a in sys.argv[1:] if a != "--json"]
    report = {"generated": str(date.today()),
              "2A valuation": axis_valuation(),
              "2B complacency": axis_complacency(),
              "2C macro": axis_macro(),
              "2D microstructure": axis_microstructure(),
              "2E prediction": axis_prediction(extra),
              "2F correlation": axis_correlation(),
              "2G hmm": axis_hmm(),
              "2H fiscal": axis_fiscal(),
              "2I currency": axis_currency(),
              "2J money": axis_money(),
              "2K digital-asset": axis_digital(),
              "2L secular": axis_secular(),
              "2M ai-financing": axis_ai_financing()}

    if "--json" in sys.argv:
        print(json.dumps(report, indent=1))
        return
    print(f"MARKET PULSE — {report['generated']}  (thresholds mirror METRICS.md)")
    for axis, rows in report.items():
        if axis == "generated":
            continue
        print(f" {axis}")
        for r in rows:
            val = f"{r['value']}" if "value" in r else ""
            asof = f"  [{r['asof']}]" if r.get("asof") else ""
            print(f"   {r.get('metric') or r.get('question','')[:48]:<46} {val:<48} {r.get('verdict','')}{asof}")
            if r.get("yes") is not None:
                print(f"      YES {r['yes']*100:.1f}%  vol ${r['volume']:,}")
            if r.get("note"):
                print(f"      ({r['note']})")


if __name__ == "__main__":
    main()