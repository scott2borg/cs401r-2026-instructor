# L02: AI Systems Development Lifecycle (AISDLC) — Figures

## Slide 1 — Title

**Figure:** *8-stage pipeline visualization.* Eight colored rectangular boxes arranged left to right on a dark navy background, connected by forward-pointing arrows. Boxes labeled: 1-Define Problem, 2-Discover Data, 3-Prepare Data, 4-Design Solution, 5-Develop, 6-Evaluate, 7-Deploy, 8-Monitor. Each box is a slightly different shade from deep blue (left) to teal (right). Below the linear pipeline, a curved return arrow loops from stage 8 back to stage 1, labeled "Operational feedback." Additional smaller return arrows visible at key points (5→4, 6→2, 8→4). The image communicates: structured, iterative, not waterfall.

---

## Slide 2 — Opening Provocation

**Figure:** *Minimalist dark slide.* The quote in large, elegant type (Calibri Light, white) centered on a deep slate (#2A323E) background. Opening quotation mark in very large (100pt) gray. Attribution line in gold/amber at the bottom. No other elements. The visual restraint makes the words land harder.

---

## Slide 3 — The Story of a Failed AI Project

**Figure:** *Narrative timeline.* A horizontal timeline with 6 stages. Steps 1-3 show a green upward arrow (indicating things are going well). Steps 4-6 show a red downward arrow (failure cascade). The transition point (Step 3, "Deploy") is marked with a vertical red line labeled "The Production Cliff." Each stage has a small icon (team → presentation → rocket → warning → no-monitoring icon → forensics). The visual reads like a case study story. Final box at right: gray, labeled "Lessons Learned (Too Late)."

---

## Slide 4 — The Counter-Story: What Good Looks Like

**Figure:** *Same timeline layout as Slide 3 but entirely green.* Each stage has a checkmark and green upward arrow. Milestones labeled: "Problem Definition Gate ✓", "Baseline Gate ✓", "Model Evaluation Gate ✓", "Production Readiness Gate ✓", "Deployment Gate ✓", "Operational Health ✓". The visual contrast with the previous slide is immediate and deliberate.

---

## Slide 5 — The Four Properties That Make AI Development Different

**Figure:** *2×2 color-blocked quadrant diagram.* Each quadrant has a large background color (navy, dark teal, amber, slate), a single large icon (dice, database, trend-down arrow, flask), and a 2-line label + 1-line sub-text. The quadrant lines are crisp white. Each property number is in large white type in the corner. No gradients, no drop shadows. Clean and high-contrast.

---

## Slide 6 — The AISDLC: 8 Stages Overview

**Figure:** *8-box horizontal pipeline diagram.* Each box is clearly numbered and labeled, with the core question in smaller text below the stage name. Color progression from deep navy (left) to bright teal (right). Forward arrows between stages. Gate symbols (diamond shapes) between each pair of stages — small diamond with a checkmark. A large curved return arrow loops below the entire pipeline from stage 8 back to stage 1. The diagram fits on one slide and reads clearly at presentation size.

---

## Slide 7 — Stage 1: Define Problem

**Figure:** *AI Project Charter template mockup.* A clean document layout showing a realistic (but brief) filled-in example for the NorthStar churn prediction system. Sections: Problem Statement ("Identify customers at risk of churning within 30 days..."), Success Criteria ("AUC ≥ 0.75, precision ≥ 0.68 at threshold 0.4"), Constraints ("$15K/month inference budget, GDPR compliance, no PII in feature names"), Gate Owner ("CDO, Maria Chen"). Document is formatted like a professional one-pager. Header: "NorthStar Retail — AI Project Charter."

---

## Slide 8 — Stages 2 & 3: Discover + Prepare Data

**Figure:** *Two-panel data flow diagram.* Left panel: "Discover" — shows raw data sources (S3 bucket icons: customers.csv, transactions.parquet, clickstream.parquet) flowing into a "Data Readiness Assessment" document. Quality score bars below each source (green = good, amber = marginal, red = problematic). Right panel: "Prepare" — shows the same data flowing through transformation steps (Glue icon) into prepared outputs (Feature Store icon). A "Data Contract" document sits between the two panels, connecting them.

---

## Slide 9 — Stages 4 & 5: Design + Develop

**Figure:** *Development spectrum visualization.* A horizontal arrow from "Simple" (left) to "Complex" (right). Along the arrow, five labeled points: "Prompt Engineering" → "RAG" → "Fine-Tuning" → "Custom Training" → "Agentic System." Each point has: a complexity bar (height), a time estimate (weeks), and a cost indicator ($). A vertical dashed line labeled "Start here" sits at "Prompt Engineering" with an arrow pointing right, labeled "Move right only when justified." Color gradient from green (left) to red (right).

---

## Slide 10 — Stages 6 & 7: Evaluate + Deploy

**Figure:** *Deployment strategy comparison table.* Four rows (Canary, Blue/Green, Shadow, Feature Flags), four columns (How it works, Risk level, Rollback speed, When to use). Color-coded cells: green = low risk, amber = medium risk, red = high risk. A small diagram for each strategy shows traffic flow with percentages. Clean table with header row in navy. This becomes a reference diagram students can return to.

---

## Slide 11 — Stage 8: Monitor (The Stage That Never Ends)

**Figure:** *Monitoring dashboard mockup.* Shows a CloudWatch-style dashboard with four panels: (1) Model AUC over time — line chart with green zone and amber/red alert zones; (2) Data drift score — time series with a threshold line; (3) Request latency P95 — time series; (4) Monthly inference cost — bar chart. One alert is visible in panel 2 (amber spike). Labels are realistic NorthStar values. The dashboard looks like something you'd actually build in Lab 6.

---

## Slide 12 — Stage Gates: The Discipline That Makes It Work

**Figure:** *Gate anatomy diagram.* A horizontal flow showing: "Previous Stage Output" box → large diamond shape (the gate) → three exit arrows (Proceed, Remediate, Halt/Reframe). Inside the diamond: the five gate components listed. The diamond is outlined in gold, with the stage name at the top. Below the gate: a red box labeled "Gate Theater" crossed out, with the caption "Occurs when: criteria are vague / owner lacks authority / pressure overrides judgment." Clean, high-contrast.

---

## Slide 13 — Return Loops: Controlled Iteration, Not Waterfall

**Figure:** *Return loop diagram.* The 8-stage pipeline shown again, this time with prominent curved arrows below the pipeline showing the named return loops. Each arrow is labeled with the trigger condition in small text. A legend at bottom-right distinguishes "Forward flow" (blue arrows above) from "Return loops" (orange/amber arrows below). The visual makes clear this is a structured, deliberate iteration model, not chaotic back-and-forth.

---

## Slide 14 — Calibrating the AISDLC to Risk Level

**Figure:** *Three-tier risk pyramid.* A vertical pyramid divided into three color-coded sections: GREEN (low risk, large base) labeled "Move fast, document lightly"; AMBER (medium risk, middle section) labeled "Full process, full artifacts"; RED (high risk, narrow top) labeled "Maximum rigor, external review." Icons beside each tier illustrate the example use case. A blast-radius graphic sits beside each tier (small explosion at bottom, large at top). Proportions make clear that most enterprise AI projects live in the amber zone.

---

## Slide 15 — The AISDLC at a Glance (Full Reference Table)

**Figure:** *The full table IS the figure.* Style it as a clean, high-contrast reference table with: Stage column in navy, Core Question column in dark gray, Key Artifact column in teal, Gate Decision column in amber/gold. Alternate row shading in very light blue/white. Large enough to read from the back of the room. This table will appear again throughout the course as a reference.

---

## Slide 16 — NorthStar: AISDLC in Practice

**Figure:** *AISDLC pipeline with lab labels.* Same 8-stage pipeline as on Slide 6, with lab assignment badges overlaid on the relevant stages. Stages 1-2 are labeled "NorthStar pre-work" and shown in gray (already done). Stages 3-8 are color-coded by lab: Lab 2 (stage 3), Lab 1/ADR (stage 4), Lab 3 (stages 5-6), Labs 4-5 (stage 7), Lab 6 (stage 8). Makes the entire semester's lab arc legible in one image.

---

## Slide 17 — Key Takeaways + What's Next

**Figure:** *Summary visual.* Five numbered circles (navy) with the key takeaway text beside each. Below: a "Next Up" banner (teal) showing the upcoming lecture topic and reading. The five takeaways are formatted for maximum readability — short, declarative sentences in large type.
