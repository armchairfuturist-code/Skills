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
from datetime import date, datetime, timedelta, timezone

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


# --- long history (for 200-week MAs) -------------------------------------------
def _sa_chart_history(sym):
    """stockanalysis chart endpoint: epoch-ms closes back to inception."""
    for kind in ("e", "s"):
        try:
            data = json.loads(fetch(f"https://stockanalysis.com/api/symbol/{kind}/{sym}/history?type=chart"))
            pts = data.get("data") or []
            if pts:
                return [(datetime.fromtimestamp(p[0] / 1000, timezone.utc).strftime("%Y-%m-%d"),
                         float(p[1])) for p in pts]
        except Exception:
            continue
    return None


def _nasdaq_history(ticker):
    """NASDAQ historical API fallback (~5y window — enough for 200 weeks)."""
    end = date.today()
    start = end - timedelta(days=365 * 5)
    for asset in ("etf", "stocks"):
        try:
            url = (f"https://api.nasdaq.com/api/quote/{ticker.upper()}/historical"
                   f"?assetclass={asset}&fromdate={start}&todate={end}&limit=9999")
            rows = json.loads(fetch(url))["data"]["tradesTable"]["rows"]
            if rows:
                out = [(datetime.strptime(r["date"], "%m/%d/%Y").strftime("%Y-%m-%d"),
                        float(r["close"].replace(",", "").replace("$", ""))) for r in rows]
                return sorted(out)
        except Exception:
            continue
    return None


def history_long(ticker):
    """Full daily close history, chronological [(YYYY-MM-DD, close)]."""
    return _sa_chart_history(ticker.lower()) or _nasdaq_history(ticker) \
        or (_ for _ in ()).throw(ValueError(f"no long history for {ticker}"))


def weekly_closes(daily):
    """Daily [(date, close)] -> weekly last closes (ISO week buckets)."""
    weeks = {}
    for d, c in daily:
        y, w, _ = date.fromisoformat(d).isocalendar()
        weeks[(y, w)] = (d, c)  # later dates overwrite -> last close of week
    return [weeks[k] for k in sorted(weeks)]


def ma200w(ticker, weeks=200):
    """Price vs N-week moving average. Returns (price, ma, pct_distance) or None
    when history < weeks (young listing — caller must exclude, not fake it)."""
    wc = weekly_closes(history_long(ticker))
    if len(wc) < weeks:
        return None
    ma = sum(c for _, c in wc[-weeks:]) / weeks
    price = wc[-1][1]
    return {"price": price, "ma": ma, "dist": price / ma - 1.0, "asof": wc[-1][0]}


# --- ETF holdings (SSR page scrape) ----------------------------------------------
def holdings(etf, top=25):
    """Top holdings [(symbol, weight_pct)] from the stockanalysis holdings page.
    Page order is weight-sorted; nav slugs are filtered by alignment with weights."""
    html = fetch(f"https://stockanalysis.com/etf/{etf.lower()}/holdings/")
    import re
    syms = re.findall(r'/stocks/([a-z.]+)/"', html)
    seen, order = set(), []
    for s in syms:
        if s not in seen:
            seen.add(s)
            order.append(s)
    wts = [float(w) for w in re.findall(r'>(\d+\.\d+)%<', html)]
    if not wts:
        raise ValueError(f"no holdings parsed for {etf}")
    wts = wts[1:]  # first value is the "Top 10 = X% of assets" aggregate
    syms = order[-len(wts):]  # nav junk sorts first; holdings are the tail
    return [(s.upper(), w) for s, w in zip(syms, wts)][:top]
