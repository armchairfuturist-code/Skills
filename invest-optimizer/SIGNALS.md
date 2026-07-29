# Dip/Profit Signal Reference

A sector heat gauge for ETFs: **should this bucket be harvested or accumulated?**
Computed by [`tools/dip_signal.py`](tools/dip_signal.py). Strategic (slow) signal — it sizes the cash reserve cycle, it does not time entries. Tactical entries still come from the posture brief's tranche plan.

## The one question it answers

What share of this ETF's bucket is trading **below its 200-week moving average**? When most of the bucket is below the long trend, the sector is being given away — that is when reserves deploy. When almost nothing is below trend, the sector is owned by everyone — that is when profits become reserves.

## Scale (1–20)

| Score | Band | Action |
|---|---|---|
| 17–20 | OVERBOUGHT | **TAKE PROFITS** — free up cash for the coming dip. Trim oversized winners, let distributions sweep to T-bills. |
| 13–16 | EXTENDED | Stop adding. Trim into strength only if position exceeds target band. |
| 10–12 | NEUTRAL | Hold. Reinvest distributions per the posture brief. |
| 6–9 | DIP | Staged buys — deploy reserves in thirds (now / −8% / capitulation). |
| 1–5 | DEEP DIP | Deploy cash aggressively. The bucket is well below its weekly averages — this is what the reserves were for. |

**The cash-recycling loop:** scores ≥17 *build* the reserve; scores ≤9 *spend* it. The signal's job is to make "take profits" and "buy the dip" two ends of one mechanical cycle, not two separate decisions.

## Formula (mirrors dip_signal.py — edit both or neither)

1. **Breadth** = % of top-20 holdings (by ETF weight) below their 200-week MA → spans 2–19. 0% below = hottest, 100% below = deepest dip.
2. **±1** if the ETF itself is above/below its own 200WMA.
3. **+1** if within 5% of its 52-week high; **−1** at −15…−25% off the high; **−2** beyond −25%.
4. Clamp 1–20. Report by-weight %, by-count %, and the raw inputs alongside the score.

## Reading it honestly

- **Bubble regimes pin the top.** With valuations EXTREME/BUBBLE, most risk-on sectors will sit 17–20 for long stretches. That is the signal working, not broken: it is telling you the 4-year trend is stretched. Compare *across* sectors (an 18 vs a 15 is information) and wait for the cycle turn.
- **A 20–25% correction is not a dip on this lens.** After a parabolic run, a sector can fall a quarter and still be far above its 200WMA. The gauge says "not the dip you're looking for" — believe it. Deep dips are generational (2008/2020/2022-style), and this scale is built to catch exactly those.
- **Weight% vs count% divergence >20pts** means mega-caps disagree with the average stock — the index level is lying about breadth. Flag the tension; trust count% for the average-stock read.
- **Young listings** (<200 weeks of history) are excluded from breadth, never faked. Funds younger than ~4 years (many option-income ETFs) score on their *constituents'* trends — right answer for a basket, but say so in the brief.
- **Active/rotating funds** (e.g. JEPI) read the *current* basket, not a stable index — the score describes today's holdings, which is what you actually own.
- **Not a margin signal.** DEEP DIP means deploy *reserves* (cash/T-bills raised at 17–20), never leverage. Phase 4 leverage caps still bind.
- **AGENT-DOMINATED modifier:** in parabolic-and-drop tape, dip legs overshoot — prefer the staged deployment (thirds) even at scores ≤5, and let VIX >30 or a capitulation day trigger the final tranche.

## Data provenance

Holdings: stockanalysis holdings page (top 20 by weight). 200WMA: full daily history resampled to weekly closes (stockanalysis chart endpoint, NASDAQ fallback). Same-day disk cache in `/tmp/dip_signal_cache/`. Every constituent failure is excluded and counted, never guessed.
