# Skills

Two custom AI agent skills that turn raw personal data into a ranked action plan. One handles your healthspan. One handles your portfolio. Both follow the same philosophy: profile the data, find the gaps, rank by impact, then act.

## What these skills are

These are prompt packs for an AI coding agent (Claude Code, Cline, MiMoCode, and others). Drop the folder into your agent's skills directory and call it by name. The agent then runs a structured workflow instead of free-form guessing.

- `/calibrate-longevity` turns bloodwork, DNA, and tracker data into a ranked longevity plan.
- `/invest-optimizer` postures your portfolio to the current market regime through the lens of your goals.

## calibrate-longevity: your bloodwork, ranked into a plan

### The plain version
You hand the agent your lab results, your DNA file, and your wearable data. It tells you what to fix first, what to take, and when to re-test. No more staring at a lab sheet wondering what matters.

### What to give it
- Bloodwork (recent, any format): the standard panel plus hormones, inflammation, thyroid, iron, vitamin D, B12, HbA1c, fasting insulin
- DNA report (optional): 23andMe or Ancestry raw data
- Health tracker export (optional): HRV, resting heart rate, sleep stages, VO2 max
- Goals: what you want (longevity, energy, sharp thinking, body composition)
- Risk tolerance: how far you will go (established supplements only, peptides, research compounds)

Missing data is fine. The skill works with what you have and flags the gaps.

### What it does, step by step
1. Profile your signals. It reads each marker. It checks whether the test was done right (fasted? right time of day?). It writes a card with your value, optimal range, trend, and confidence.
2. Map to body systems. Metabolic, hormonal, cardiovascular, inflammatory, mitochondrial, nutritional, sleep, cognitive. Your numbers land in the system they belong to.
3. Find the gaps. A gap is a marker that is actionable and outside its optimal range. It ranks each gap P0 (fix now), P1 (borderline), P2 (nice to have).
4. Build the plan in three layers:
   - Drains first. Stop the things hurting you (late eating, alcohol, bad sleep, blue light). Removing a drain beats adding any single supplement.
   - Foundational supports. Established, safe interventions matched to each gap.
   - Enhancement. Emerging or experimental compounds, only if your risk tolerance allows.

### Evidence tiers (how sure the science is)
- T1 Established: magnesium, creatine, zone 2 cardio, time-restricted eating.
- T2 Emerging: NAD+ precursors, low-dose rapamycin, glycine, apigenin.
- T3 Experimental: peptides like BPC-157, TB-500, semax, noopept. These need your explicit consent and come with a full warning about sourcing, dosing, and stop signals.

### What you get
A calibration report. The top three calibrations to start this month. Specific dosages, timing, and a re-check date. DNA notes baked in (for example, an MTHFR variant means methylfolate beats folic acid).

### The caveat
This skill discusses experimental compounds that may lack FDA or EMA approval and long-term safety data. It is a decision-support tool, not a prescription. Do your own due diligence on legality, sourcing, dosing, and medical supervision.

## invest-optimizer: posture your portfolio to the moment

### The plain version
The market has a mood (the regime) and you have a goal (the anchor). This skill reads the market's mood from hard data, then tells you how to tilt your portfolio so the two line up. Same market, different goals, different answer.

### What to give it
Your goal profile:
- Primary objective: income, growth, balanced, or preservation
- Risk tolerance: conservative, moderate, aggressive
- Investor type: day trader, swing trader, income investor, long-term holder
- Time horizon: under 1 year up to 15+ years
- Income cadence: how often you need cash from the portfolio
- Concentration: concentrated, balanced, or broad

If you have not set these, the agent asks or infers them. It will not proceed without a goal anchor. A growth investor and a preservation investor read the same market and should do opposite things.

### What it does, step by step
1. Anchor to goals. Load your profile. This is the fixed reference every later call measures against.
2. Read the regime. It checks five axes:
   - Valuation: are stocks expensive? (Shiller CAPE, Buffett Indicator, Tobin's Q, S&P 500 vs M2)
   - Complacency: is everyone pricing in zero risk? (VIX, credit spreads)
   - Macro: is a recession brewing? (yield curve)
   - Microstructure: are AI trading bots running the tape? (agent volume share, flash crash count)
   - Prediction markets: what are betting markets implying about recession and rate moves? (Polymarket)
   Each axis gets a verdict. Together they form one market pulse: EXPANSION, LATE CYCLE, CONTRACTION, or CRISIS.
3. Calibrate posture. The pulse meets your goals in a matrix. Late cycle plus a growth goal means trim and raise cash. Late cycle plus a preservation goal means cut equity to the floor. Same pulse, different posture.
4. Risk check. Every recommendation is tested against position-size and concentration limits. Anything that breaks a limit is downgraded, with the reason stated.

### What you get
A posture brief. Your profile and why it matters. The market pulse table. A posture table with current allocation, target allocation, the action to take, and the trigger that reverses it. If the posture implies stock picks, a screener shows which candidates pass three technical gates (near 52-week low, average daily range, trend above moving averages). The screener is a research list, not a buy list.

### The quick version
Ask only about market conditions and the skill skips your portfolio. You get a compact pulse table: valuation, complacency, macro, overall.

## How to install and run

Both skills install the same way. Copy the skill folder into your agent's skills directory (for example `.claude/skills/` for Claude Code, `.agents/skills/` for MiMoCode). Then start a session and type the slash command:

- `/calibrate-longevity`
- `/invest-optimizer`

Paste your data. The agent runs the workflow and hands back the report.

## The shared idea

Both skills refuse to guess. They demand real data, rank by impact, and separate what is established from what is experimental. Give them signal, not vibes.
