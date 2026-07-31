# L22: Reliability Engineering for AI Systems — Figures

## Slide 1 — Title

**Figure:** *Reliability spectrum visual.* Horizontal axis: System availability (0% to 100%). Three zones marked: "Always down" (left, red), "Fails sometimes" (center, amber), "Highly available" (right, green). Above the axis: the famous nine nines: 90% = 36.5 days/year downtime, 99% = 3.65 days, 99.9% = 8.7 hours, 99.99% = 52.6 minutes, 99.999% = 5.3 minutes. NorthStar target: 99.9% marked on the axis. The visual establishes that reliability is quantified, not qualitative — and that the difference between "99%" and "99.9%" is significant.

---

## Slide 2 — SRE Principles Applied to AI Systems

**Figure:** *SRE principles diagram.* Four quadrant layout: Embrace Risk (top-left), SLOs (top-right), Eliminate Toil (bottom-left), Monitoring (bottom-right). Each quadrant: principle name, 1-sentence definition, NorthStar application example. AI-specific additions shown as a fifth element overlaying the four quadrants. The layout communicates: SRE is a complete framework, not just monitoring.

---

## Slide 3 — Designing for Failure: The Failure Mode Analysis

**Figure:** *Failure mode risk matrix.* 5×5 risk matrix: x-axis: Impact (Low to High), y-axis: Probability (Low to High). Each failure mode from the tables plotted as a labeled dot. High-priority failures (high probability + high impact) in the top-right quadrant, highlighted in red. "Mitigation priority" zone circled. The matrix communicates: focus reliability investment on the high-probability, high-impact quadrant.

---

## Slide 4 — Graceful Degradation: Failing with Style

**Figure:** *Degradation hierarchy diagram.* Vertical stack for Churn system: Primary (full AI) at top (bright teal), cascading down through Fallback 1 (lighter), Fallback 2 (lighter still), Fallback 3 (pale), Terminal (near-white). Each level: description, quality score (100%, 85%, 70%, 55%, 30%), and trigger condition. Arrow down the right side: "Degradation path — entered automatically when upstream level fails." The cascade communicates: graceful degradation is a pre-designed, pre-tested path, not an ad hoc response.

---

## Slide 5 — Error Budgets in Practice: The Reliability Investment Decision

**Figure:** *Error budget consumption gauge dashboard.* Four gauges (one per system). Each gauge: monthly budget, consumed (shown as filled sector), remaining (unfilled sector). Traffic-light zones: green (> 50% remaining), amber (20-50%), red (< 20%). All four gauges in green with labels showing % consumed. Small annotation: "Nov 3 incident: 6 min" with arrow pointing to the churn endpoint gauge's filled sector. The gauges make budget consumption visceral and trackable.

---

## Slide 6 — Chaos Engineering for AI: Breaking Things on Purpose

**Figure:** *Chaos experiment log.* Three experiments as cards. Each card includes: hypothesis, method, expected result, actual result, pass/fail status, and action taken. Experiment 1: FAIL (bug found). Experiments 2-3: PASS. "Bug found" card highlighted in amber — this is the value of chaos engineering: finding the bug in a controlled experiment, not during a real incident.

---

## Slide 7 — The Fallback Cache Pattern: Building the Safety Net

**Figure:** *Fallback cache hit rate dashboard.* Stacked bar chart (last 30 days). Daily bars showing: % Real-time (primary, teal, ~95%), % Cache (fallback 1, lighter teal, ~3%), % Segment (fallback 2, amber, ~1%), % Default (fallback 3, red, <1%). One day with elevated cache usage (Nov 3 incident — 6-min endpoint outage causing ~8% cache fallback that day). The chart shows: fallbacks are rarely needed but always available.

---

## Slide 8 — Multi-Component Reliability: Cascading Failure Prevention

**Figure:** *Circuit breaker state diagram.* Three states: CLOSED (normal), OPEN (failing fast), HALF-OPEN (testing). Transitions: CLOSED → OPEN (after 5 failures), OPEN → HALF-OPEN (after 30 seconds), HALF-OPEN → CLOSED (success) or HALF-OPEN → OPEN (failure). Request flow in each state: CLOSED → try Feature Store. OPEN → immediately return fallback (no Feature Store call). HALF-OPEN → try one test request. The state machine diagram shows how the circuit breaker works.

---

## Slide 9 — SLA Design for the Business: What to Promise

**Figure:** *SLA design process flowchart.* Five steps (Business Requirement → Technical SLA → Verify → Measure → Consequences) as a horizontal flow with arrows. For NorthStar churn: each step filled in with the specific values from the content above. The flowchart communicates: SLAs are derived from business requirements through a deliberate process.

---

## Slide 10 — Reliability Patterns in the Lab Sequence

**Figure:** *Lab sequence reliability maturity chart.* After each lab: reliability capability added and MTTR impact. Starting point (before Lab 1): undefined reliability; 4-8 hour MTTR. After Lab 5: 15-minute MTTR. After Lab 6: proactive monitoring; problem detected before users experience it. Staircase chart showing MTTR declining across labs. The chart makes the reliability impact of each lab concrete.

---

## Slide 11 — The Reliability Stack for NorthStar: Full Picture

**Figure:** *Reliability stack diagram.* Four horizontal layers (Prevention, Detection, Recovery, Prevention of Recurrence). Each layer: 3-4 control items with the lab that implemented them labeled. Detection layer: detection latency annotations (P99 alarm: < 5 min; Model Monitor: < 24 hours; RAGAS: < 7 days; agent traces: < 1 hour). Recovery layer: recovery time annotations (rollback: 2 min; cache: 1 sec). The stack communicates: reliability is depth of control, not a single mechanism.

---

## Slide 12 — Lab 6 Final Preparation: 5 Days Out

**Figure:** *Lab 6 critical path Gantt chart.* 5-day timeline (Tue-Sat). Critical path in red: Data capture → Baseline → Monitoring schedule → Alarm → Lambda. Parallel track in blue: Dashboard (can be done independently). Part 4 (compliance report) at end, labeled "simplify if needed." Weekend contingency: "Sunday morning buffer if needed." The Gantt communicates: what must be sequential vs. what can be done in parallel.

---

## Slide 13 — AI Reliability in Context: Real Cases

**Figure:** *Four case study cards.* Each card: company type (anonymized), failure description (2 sentences), impact (monetary or customer), and lesson learned (1 sentence). Cards formatted like incident report summaries. The "alert fatigue" card has a specific impact: "6-week undetected drift." The "missing fallback" card has a specific impact: "45 min, $2.3M in lost bookings." Real consequences make the reliability principles stick.

---

## Slide 14 — Reliability Engineering Career Perspective

**Figure:** *Career path diagram.* Three roles (ML Engineer, ML Reliability Engineer, ML Lead) with salary ranges and demand growth rates (2026). ML Reliability Engineer: highest growth in demand (45% YoY). Skill overlap diagram showing: all three roles need this lecture's content; the Reliability Engineer role goes deeper; the ML Lead role adds business/leadership. The diagram communicates: reliability skills differentiate you in the market.

---

## Slide 15 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Lab 6 countdown (5 days, red). Lab 7 preview: "Assigned Thursday — the final lab, focuses on economic analysis and business value." Reliability stack diagram thumbnail.
