---
name: calibrate-longevity
description: Turn bloodwork, DNA, and health-tracker data into a ranked longevity optimization plan — supplements, peptides, and research compounds. Use when the user shares lab results, wants a longevity/biohacking protocol, or mentions peptides/NAD+/rapamycin.
---

# calibrate-longevity

Turn bloodwork, DNA, and tracker data into a ranked longevity plan. The entire workflow is **gap**-driven: profile signals to find each gap, calibrate whether it's actionable, rank it, close it.

> **Caveat**: This skill discusses experimental compounds (peptides, research chemicals, off-label cognition drugs) that may not have FDA/EMA approval, lack long-term human safety data, and are often sourced from unregulated markets. The user must do their own due diligence on legality, sourcing, dosing, and medical supervision. This skill is a decision-support tool, not a prescription.

## Input

Ask for:

1. **Bloodwork** — recent labs with reference ranges (CBC, CMP, lipids, hormones, inflammation, thyroid, iron, vitamin D, B12, HbA1c, fasting insulin).
2. **DNA / genomics** — raw data or interpreted report.
3. **Health tracker export** — HRV, RHR, sleep stages, steps, activity, VO2 max.
4. **Goals & notes** — what to optimize (longevity, energy, cognition, body composition) and symptoms.
5. **Risk tolerance** — none / established supplements only / open to peptides / open to research chems. Gates the plan's tier ceiling.

Missing data is fine — calibrate with what you have, flag gaps.

## Evidence tiers

| Tier | Label | Examples |
|---|---|---|
| T1 | Established | Magnesium, creatine, zone 2, TRE |
| T2 | Emerging | NAD+ precursors, low-dose rapamycin, apigenin, glycine |
| T3 | Experimental | BPC-157, TB-500, semax, dihexa, noopept, SS-31 |

T3 compounds: require consent (risk tolerance ≥ "open to peptides"). Full spec — warning, dose escalation, stop signals, sourcing — lives in the [experimental compounds register](#5-present-the-calibration-report).

## Steps

### 1. Profile the signal set

Extract relevant metrics from each source. Bloodwork gets priority weight; DNA provides predisposition context; tracker validates real-world.

**Before grading, run the confounder checklist** (full reference: `lab-ground-rules.md`):
- Properly fasted (10+ h) for glucose, insulin, lipids, iron, homocysteine?
- Draw time matching marker diurnal peak (cortisol/T/TSH by 10 AM)?
- Sex hormones at correct cycle phase (follicular vs luteal ranges differ 2–5×)?
- Enough time since last intervention for recheck?
- Tracker-tension: does HRV/sleep contradict the lab picture?

Write each finding as a signal card: `[marker] = [value] | optimal: [range] | trend: [stable/improving/worsening] | confidence: [high/medium/low]`

**Completion**: every data source processed, every relevant marker written as a signal card.

### 2. Map signals to systems

Group signal cards by biological system. DNA SNPs that directly modulate a system live inline with that system's card.

| System | Key markers |
|---|---|
| **Metabolic** | glucose, HbA1c, fasting insulin, HOMA-IR, lipids |
| **Inflammatory / immune** | hs-CRP, homocysteine, ferritin, WBC diff |
| **Hormonal** | free T, SHBG, cortisol, DHEA-S, TSH, fT4, fT3 |
| **Cardiovascular** | BP, HRV, RHR, apoB, Lp(a), TG |
| **Mitochondrial / oxidative** | CoQ10, oxidative markers, VO2 max |
| **Nutritional** | vitamin D, B12, iron/ferritin, Mg, Zn, Se |
| **Sleep / recovery** | sleep stages, latency, HRV trend, RHR during sleep |
| **Cognitive / neurological** | BDNF, cortisol awakening response, subjective cognition, EEG |

**Completion**: every signal card assigned to at least one system.

### 3. Calibrate — rank intervention opportunities

For each system, decide: is there a calibratable **gap**? A gap is calibratable when:
- The marker is actionable (not fixed genetic expression)
- Outside optimal range
- The user has data to track effect

Score each gap as **P0 / P1 / P2**:
- **P0** — clearly outside optimal range and actionable now
- **P1** — borderline/trending wrong, or actionable but needs a P0 fixed first
- **P2** — within range but improvable; nice-to-have

For each gap, propose interventions tagged by evidence tier.

**Completion**: every system assessed, all gaps scored P0–P2, each with at least one proposed intervention.

### 4. Build the optimization plan

Three mandatory sections, in order. Every section includes the system/gap table. **For every intervention you propose, across all sections:**
- Cross-reference with DNA: SNP affecting metabolism → flag it (e.g. "MTHFR C677T — methylfolate > folic acid")
- Cross-reference with tracker: if HRV or sleep contradicts bloodwork, note the tension pattern from `lab-ground-rules.md` and lower confidence on the lab-only interpretation

---

#### Section A: Drains & Removals (do FIRST)

List what the user should stop or reduce before adding anything. For each drain: what to stop, why it matters (mechanism), and what observable feedback signs it's working (HRV/sleep/tracker).

- **Sleep hygiene**: late eating (stop 3 h before bed), alcohol, inconsistent schedule
- **Circadian disruptors**: blue light after 10 PM, screen before sunlight, eating outside daylight window
- **Chronic stress**: overtraining, insufficient rest days, cognitive load without decompression
- **Dietary drains**: excess alcohol, late-night eating, refined seed oils, excessive PUFA oxidation
- **Supplement timing errors**: Ca with Fe, Zn without Cu, fat-solubles on empty stomach

> Drains first: removing correctly is higher ROI than adding any single supplement, and makes subsequent additions more effective.

**Completion**: every relevant drain identified with mechanism and feedback signal.

---

#### Section B: Foundational supports (T1)

T1 interventions addressing calibratable gaps. Table per gap:

| System | Gap | Mechanism | Intervention | Tier | Dosage / Protocol | Timing | Re-check | Interaction notes |

Timing guidance per `interactions.md`:
- Food vs empty stomach
- Pairs to separate (Ca ↔ Fe: 4 h; Zn ↔ Cu: always pair; Mg ↔ Ca: different meals)
- Morning vs evening circadian guidance
- Fat-required absorption (A, D, E, K, CoQ10, curcumin)

Assess existing stack for conflicts:
- Zn:Cu ratio (flag if Zn >30 mg/day without Cu)
- Ca + Fe taken together (separate 4+ h)
- Multiple GABAergics → sedation risk (Mg, glycine, theanine, melatonin, ashwagandha, GABA)
- D + K2 + Mg triad completeness
- NAC + glycine taken together (necessary for GSH)

**Completion**: every P0–P1 gap has at least one T1 intervention proposed with timing guidance and interaction check.

---

#### Section C: Enhancement & experimental (T2–T3)

Only when risk tolerance permits. Covers:
- **Emerging supplements** (T2): NAD+ precursors, low-dose rapamycin, glycine, apigenin
- **Peptides** (T3): protocol from `peptides.md` with cycle, dose, route, sourcing
- **Cognition compounds** (T3): protocol from `cognition-compounds.md`

**Completion**: every P0–P1 gap at the permitted tier has an intervention; T3 entries reference the experimental register below.

### 5. Present the calibration report

- **Top 3 calibrations to start this month** — highest-ROI gaps regardless of tier
- **Full plan by system** — intervention tables from step 4
- **Markers to re-draw** — which labs to repeat and when
- **Tracker watchpoints** — which metrics to monitor as feedback
- **Experimental compounds register** — all T3 suggestions, each with:
  - Rationale & mechanism
  - Full protocol (dose, cycle, route from `peptides.md` or `cognition-compounds.md`)
  - Sourcing checklist: third-party CoA verified, purity ≥98%, endotoxin-tested
  - Dose-escalation plan: start at 25–50% of target dose for 3–5 days
  - Stop signals: adverse effects warranting discontinuation
  - Interaction flags with other plan interventions
  - **Warning**: "Limited human data. Unknown long-term profile. Source from tested batches only."

**Completion**: the plan covers all calibratable gaps at the user's risk tolerance, with specific dosages, protocols, evidence tiers, and re-check cadences. T3 suggestions are isolated in the experimental register with the full warning.

## Reference pointers

- [`peptides.md`](peptides.md) — peptide protocols: dosing, cycle, administration route, interaction risks.
- [`cognition-compounds.md`](cognition-compounds.md) — nootropics and research chems: mechanisms, half-lives, side effects, tolerance management.
- [`biomarkers.md`](biomarkers.md) — optimal ranges, SNP interactions, recheck intervals for each marker.
- [`interactions.md`](interactions.md) — supplement synergy, antagonism, absorption conflicts, circadian timing.
- [`lab-ground-rules.md`](lab-ground-rules.md) — pre-analytical confounders, diurnal variation, cycle-phase dependencies, recheck intervals, tracker-lab tension.
