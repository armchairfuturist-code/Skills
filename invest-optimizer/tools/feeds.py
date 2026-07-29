#!/usr/bin/env python3
"""feeds.py — verified data sources for invest-optimizer tools (stdlib only).

Probed live 2026-07-29 (pi sandbox):
  WORKS : Polymarket gamma-api (no auth), CBOE VIX_History.csv,
          FRED fredgraph.csv (no API key), treasury.gov curve CSV,
          multpl.com HTML scrape, stockanalysis.com /api/symbol/{e|s}/<t>/history
  DEAD  : Yahoo chart API (429), stooq (JS gate), MarketWatch (401),
          pip (absent -> no third-party libs anywhere in this toolchain).

Every fetcher raises on failure; callers decide whether the axis GAPs.
"""
import csv, io, json, re, urllib.parse, urllib.request

TIMEOUT = 15
UA = {"User-Agent": "Mozilla/5.0 (invest-optimizer tools)"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", "replace")


# --- macro / rates -----------------------------------------------------------
def fred_series(sid):
    """FRED series as [(date, float)] chronological; skips '.' rows."""
    text = fetch(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")
    rows = [l.split(",") for l in text.strip().splitlines()[1:] if "," in l]
    return [(d, float(v)) for d, v in rows if v not in (".", "")]


def cboe_vix():
    text = fetch("https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv")
    lines = [l for l in text.strip().splitlines() if l and not l.startswith("DATE")]
    d, o, h, l, c = lines[-1].split(",")[:5]
    return {"date": d, "close": float(c)}


def treasury_curve():
    from datetime import date
    yr = date.today().year
    text = fetch("https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
                 f"daily-treasury-rates.csv/{yr}/all?type=daily_treasury_yield_curve"
                 f"&field_tdr_date_value={yr}&page&_format=csv")
    row = next(csv.DictReader(io.StringIO(text)))  # newest first
    return {"date": row["Date"], "3M": float(row["3 Mo"]), "2Y": float(row["2 Yr"]),
            "10Y": float(row["10 Yr"]), "30Y": float(row["30 Yr"])}


# --- valuation ---------------------------------------------------------------
def multpl(page):
    """Scrape 'Current X is N' from a multpl.com page; returns float."""
    html = fetch(f"https://www.multpl.com/{page}")
    m = re.search(r'is ([0-9]+\.[0-9]+), a change', html)
    if not m:
        raise ValueError(f"multpl:{page} pattern not found")
    return float(m.group(1))


def buffett_indicator():
    """Corporate equities (NCBEILQ027S, $M) / GDP ($B) * 100 -> percent."""
    eq = fred_series("NCBEILQ027S")[-1]
    gdp = fred_series("GDP")[-1]
    return {"asof": eq[0], "value": eq[1] / 1e3 / gdp[1] * 100}


def sp500_div_m2():
    spx = fred_series("SP500")[-1]
    m2 = fred_series("WM2NS")[-1]  # weekly M2, $B
    return {"asof": spx[0], "value": spx[1] / m2[1]}


# --- Polymarket ---------------------------------------------------------------
def poly_event(slug):
    data = json.loads(fetch(f"https://gamma-api.polymarket.com/events?slug={slug}"))
    if not data:
        return []
    out = []
    for m in data[0].get("markets", []):
        if m.get("closed"):
            continue
        prices = json.loads(m.get("outcomePrices", "[null,null]"))
        out.append({"question": m.get("question"), "slug": slug,
                    "yes": float(prices[0]) if prices[0] is not None else None,
                    "volume": round(float(m.get("volumeNum") or 0))})
    return out


def poly_search(term, n=3):
    q = urllib.parse.quote(term)
    data = json.loads(fetch("https://gamma-api.polymarket.com/public-search"
                            f"?q={q}&limit_per_type={n}"))
    out = []
    for ev in data.get("events", [])[:n]:
        out.extend(poly_event(ev.get("slug", ""))[:1])
    return out


# --- price history -------------------------------------------------------------
def history(ticker):
    """Daily OHLCV, chronological: [{'t','o','h','l','c','v'}].
    ETF endpoint first, stock fallback. ~125 rows (6 months)."""
    sym = ticker.lower()
    for kind in ("e", "s"):
        try:
            data = json.loads(fetch(f"https://stockanalysis.com/api/symbol/{kind}/{sym}/history"))
            rows = data.get("data", {}).get("data", [])
            if rows:
                return [{"t": r["t"], "o": float(r["o"]), "h": float(r["h"]),
                         "l": float(r["l"]), "c": float(r["c"]), "v": float(r.get("v") or 0)}
                        for r in reversed(rows)]
        except Exception:
            continue
    raise ValueError(f"no history for {ticker}")


def closes(ticker):
    rows = history(ticker)
    return [(r["t"], r["c"]) for r in rows]
