#!/usr/bin/env python3
"""feeds.py — verified data sources for invest-optimizer tools (stdlib only).

Probed live 2026-07-29 (pi sandbox):
  WORKS : Polymarket gamma-api (no auth), CBOE VIX_History.csv,
          FRED fredgraph.csv (no API key), treasury.gov curve CSV,
          multpl.com HTML scrape, stockanalysis.com /api/symbol/{e|s}/<t>/history,
          levels.io/bubble-detector.json (probed 2026-09-07: one-shot JSON with all
          seven 2A/2B/2C inputs incl. Tobin's Q; cross-check, METRICS.md authoritative)
  DEAD  : Yahoo chart API (429), stooq (JS gate), MarketWatch (401),
          pip (absent -> no third-party libs anywhere in this toolchain).

Probed live 2026-09-23 (pi sandbox):
  WORKS : SEC EDGAR full-text search (efts.sec.gov/LATEST/search-index, no key),
          data.sec.gov submissions + XBRL companyfacts JSON (declare a real UA),
          api.ornnai.com compute indices (/api/daily-index/all, /api/gpu/.., /api/otpi).
  DEAD  : 13F/insider aggregator sites are caches over EDGAR and none of them answer
          a plain GET here — whalewisdom.com and dataroma.com return a JS shell, 13f.info
          404s on guessed paths, openinsider.com times out, finviz 403s, macrotrends 403s.
          Read the filing (functions below) instead of the dashboard.
          Kalshi trade-api answers 200 without a key but strips every price field
          (yes_bid/yes_ask/volume null on 429 markets probed) — not a usable
          probability fallback; Polymarket stays the only keyless venue for 2E.

Every fetcher raises on failure; callers decide whether the axis GAPs.
"""
import csv, io, json, os, re, urllib.parse, urllib.request
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


# --- structural/thematic feeds (2H-2N) -----------------------------------------
def _ma_n(daily, n):
    """Price vs n-day MA from daily [(date, close)]; None if too short."""
    if len(daily) < n:
        return None
    closes = [c for _, c in daily[-n:]]
    ma = sum(closes) / n
    price = closes[-1]
    return {"price": price, "ma": ma, "dist": price / ma - 1.0, "asof": daily[-1][0]}


def ma200(ticker):
    return _ma_n(history_long(ticker), 200)


def btc_200w():
    """BTC 200-week MA from Kraken public weekly OHLC (free, no key)."""
    url = "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=10080"
    data = json.loads(fetch(url))
    result = data.get("result", {})
    key = next(iter(result), None)
    candles = result.get(key, []) if key else []
    closes = [(datetime.fromtimestamp(int(c[0]), timezone.utc).strftime("%Y-%m-%d"),
               float(c[4])) for c in candles]
    closes.sort()
    if len(closes) < 200:
        return None
    ma = sum(c for _, c in closes[-200:]) / 200
    price = closes[-1][1]
    return {"price": price, "ma": ma, "dist": price / ma - 1.0, "asof": closes[-1][0]}


def _change_since(series, days):
    """% change vs ~N days ago from a chronological (date, value) series."""
    last_d, last_v = series[-1]
    target = (date.fromisoformat(last_d) - timedelta(days=days)).isoformat()
    prev = None
    for d, v in series:
        if d <= target:
            prev = (d, v)
    if prev is None:
        return None
    return {"asof": last_d, "value": (last_v / prev[1] - 1.0) * 100, "prev_asof": prev[0]}


def dxy():
    """Fed nominal advanced-economies dollar index (free DXY-like proxy)."""
    return fred_series("DTWEXAFEGS")[-1]


def real_rate_10y():
    return fred_series("DFII10")[-1]


def m2_yoy():
    return _change_since(fred_series("M2SL"), 365)


def fed_balance_sheet_3m():
    return _change_since(fred_series("WALCL"), 91)


def debt_to_gdp():
    return fred_series("GFDEGDQ188S")[-1]


def interest_to_revenue():
    """Federal interest payments / receipts (%) — the fiscal-dominance metric."""
    i = fred_series("A091RC1Q027SBEA")[-1]
    r = fred_series("W006RC1Q027SBEA")[-1]
    return {"asof": i[0], "value": i[1] / r[1] * 100}


def gold_yoy():
    daily = history_long("GLD")
    last_d, last_v = daily[-1]
    target = (date.fromisoformat(last_d) - timedelta(days=364)).isoformat()
    prev = None
    for d, v in daily:
        if d <= target:
            prev = (d, v)
    if prev is None:
        return None
    return {"asof": last_d, "value": (last_v / prev[1] - 1.0) * 100, "prev_asof": prev[0]}


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


# --- compute clearing prices (Ornn; free, no key) ---------------------------------
def ornn_compute(gpu="H100 SXM"):
    """Ornn compute index for one GPU class: {asof, value, chg_window}.
    Probed 2026-09-23: /api/gpu/<GPU>/index-history and /api/daily-index/all answer 200
    JSON with no key; the public window is 3 months (access: public-3mo), which is
    exactly the 2M reading. Index points, not a spot quote — read the trend."""
    d = json.loads(fetch("https://api.ornnai.com/api/gpu/"
                         f"{urllib.parse.quote(gpu)}/index-history"))
    rows = d.get("data") or []
    if len(rows) < 2:
        raise ValueError(f"ornn:{gpu} history empty")
    first, last = float(rows[0]["index_value"]), float(rows[-1]["index_value"])
    return {"asof": str(rows[-1].get("timestamp", ""))[:10], "value": last,
            "chg_window": (last / first - 1.0) * 100, "window": d.get("access", "")}


# --- primary-source filings (SEC EDGAR) ------------------------------------------
# EDGAR sits upstream of every 13F/insider dashboard: dataroma, whalewisdom, 13f.info,
# capitoltrades and openinsider are caches over these endpoints. SEC will not serve
# document files (/Archives/) to a User-Agent without a contact address, and asks for
# one it can reach — set EDGAR_USER_AGENT="You Name you@example.com" to be a good citizen.
SEC_UA = os.environ.get("EDGAR_USER_AGENT",
                        "invest-optimizer/1.0 (skill research; contact: user@example.com)")


def sec_get(url, as_json=True):
    req = urllib.request.Request(url, headers={"User-Agent": SEC_UA,
                                               "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        text = r.read().decode("utf-8", "replace")
    return json.loads(text) if as_json else text


def edgar_search(phrase, forms="10-Q,10-K,8-K", startdt="", enddt="", n=8):
    """Full-text search over filings: [(company, form, filed)] + total hit count.
    Counts *disclosures* of a phrase, not exposure — report it that way."""
    url = (f"https://efts.sec.gov/LATEST/search-index?q={urllib.parse.quote(chr(34) + phrase + chr(34))}"
           f"&forms={urllib.parse.quote(forms)}")
    if startdt:
        url += f"&startdt={startdt}&enddt={enddt}"
    # No window: hits come back relevance-sorted (they skew old) — read `total`, not `hits`.
    hits = sec_get(url).get("hits", {})
    out = []
    for h in hits.get("hits", [])[:n]:
        s = h.get("_source", {})
        names = s.get("display_names") or ["?"]
        out.append((names[0].split("(CIK")[0].strip(), s.get("form"), s.get("file_date")))
    return {"phrase": phrase, "total": hits.get("total", {}).get("value"), "hits": out}


def edgar_filings(cik, form="13F-HR", n=6):
    """Recent filings of `form` (amendments included): [(filingDate, accession, primaryDoc)]."""
    r = sec_get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")["filings"]["recent"]
    out = []
    for f, dt, acc, doc in zip(r["form"], r["filingDate"], r["accessionNumber"],
                               r.get("primaryDocument") or []):
        if f == form or f == form + "/A":
            out.append((dt, acc, doc))
        if len(out) >= n:
            break
    return out


def edgar_13f(cik, top=20):
    """Latest 13F-HR, read from the filing: {asof, total_usd, n_positions, holdings}.
    13F is ~45-day lagged, long-only, no shorts/derivatives — see METRICS.md 2N."""
    import html
    rec = edgar_filings(cik, "13F-HR", n=1)
    if not rec:
        raise ValueError(f"no 13F-HR on file for CIK {cik}")
    asof, acc, _doc = rec[0]
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}"
    names = [i["name"] for i in sec_get(f"{base}/index.json")["directory"]["item"]
             if i["name"].endswith(".xml") and "primary_doc" not in i["name"]]
    rows = []
    for name in names:
        for blk in re.findall(r"<infoTable>.*?</infoTable>",
                              sec_get(f"{base}/{name}", as_json=False), re.S):
            issuer = re.search(r"<nameOfIssuer>(.*?)</nameOfIssuer>", blk, re.S)
            val = re.search(r"<value>(\d+)</value>", blk)
            if issuer and val:
                rows.append((html.unescape(issuer.group(1)).strip(), int(val.group(1))))
        if rows:
            break
    if not rows:
        raise ValueError(f"no infoTable rows in {acc} (tried {names})")
    rows.sort(key=lambda t: -t[1])
    return {"asof": asof, "total_usd": sum(v for _, v in rows),
            "n_positions": len(rows), "holdings": rows[:top]}