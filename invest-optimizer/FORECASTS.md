# Forecast Ledger

Scores every probability the skill states, so calibration compounds instead of resetting each brief. Write rows in Phase 2E; resolve and review in Phase 4.

## Row schema

| Date | Axis / market | Stated p | Source + volume | Resolves | Outcome | Brier | Notes |
|---|---|---|---|---|---|---|---|
| 2026-09-05 | Recession by end-2026 | 0.065 | Polymarket, vol $1.7M | 2026-12-31 | — | — | BULLISH read |

- **Outcome:** 1 (happened), 0 (did not), void (market voided / horizon lapsed without resolution).
- **Brier:** (p − outcome)² once resolved. Lower is better; 0.25 is the always-say-0.5 baseline.

## Quarterly review

Mean Brier across resolved rows vs 0.25. Persistent means above ~0.20 with p far from outcomes in one direction = systematic over/under-confidence → state narrower/wider future p bands explicitly until the next review reverses it.

## Open rows

| Date | Axis / market | Stated p | Source + volume | Resolves |
|---|---|---|---|---|
| 2026-09-05 | Recession by end-2026 | 0.065 | Polymarket, vol $1.7M | 2026-12-31 |
| 2026-09-05 | Fed hike in 2026 | 0.715 | Polymarket, vol $8.7M | 2026-12-31 |
| 2026-09-05 | No dissent at Sept decision | 0.105 | Polymarket, vol $9k | Sept 2026 meeting |

## Event watches (no cited market probability — track, do not score)

| Date logged | Event | Resolves | Outcome |
|---|---|---|---|
| 2026-09-06 | CME H100/B200 futures review ends (default approval unless CFTC acts) | 2026-09-25 | — |
| 2026-09-06 | First regulated compute futures begin trading | 2026-10-05 | — |
| 2026-09-06 | CFTC compute-derivatives comment period closes | 2026-10-20 | — |

## Completion criterion

Every probability cited in a brief has a row with source, volume, and resolution date; every resolved row carries an outcome and Brier score; the quarterly review is current or explicitly overdue.
