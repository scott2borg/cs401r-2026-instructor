# L14: Continuous Delivery I — Deployment Patterns — Figures

## Slide 1 — Title

**Figure:** *Canary deployment diagram.* Traffic flowing in from the left, hitting a traffic splitter, with 95% routing to "Production v2.3" (large box, solid) and 5% routing to "Canary v3.0" (smaller box, dashed border). Both pointing to the same downstream (Response to User). Metrics panel on the right, showing Canary latency (green), Canary error rate (green), and Canary prediction quality (green). "Canary healthy → expand to 20%" action at bottom. The diagram communicates that canary deployment is a controlled, measurable risk exposure.

---

## Slide 2 — The Deployment Problem: Why It's Different for AI

**Figure:** *AI deployment risk matrix.* 2×2 matrix: x-axis: "Model Change?" (No/Yes), y-axis: "Feature/Prompt/Index Change?" (No/Yes). Four quadrants: No/No (Low: code update only), Yes/No (Medium: model retraining), No/Yes (Medium: data/prompt changes), Yes/Yes (High: compound changes). Examples in each quadrant from NorthStar. "Never do High risk all at once" label on the Yes/Yes quadrant.

---

## Slide 3 — Deployment Patterns Taxonomy

**Figure:** *Six-pattern risk/complexity scatter plot.* X-axis: Deployment Complexity (Low to High). Y-axis: User Risk Exposure (Low to High). Six labeled dots: Big Bang (high risk, low complexity), Blue/Green (medium risk, medium complexity), Canary (low-medium risk, medium complexity), Shadow (lowest risk, medium complexity), Feature Flag (low risk, high complexity), A/B (medium risk, high complexity). "Recommended zone" circle around Canary and Shadow. The scatter plot communicates: the optimal patterns are not the simplest ones.

---

## Slide 4 — Canary Deployment Deep Dive

**Figure:** *Canary progression timeline.* Four-panel horizontal timeline: Day 0 (90/10), Day 1 (70/30), Day 2 (50/50), Day 3 (100%). Each panel shows: traffic split pie chart, monitoring metrics (all green), decision (advance/hold/rollback). Rollback arrow shown going from Day 1 back to Day 0 with annotation "Auto-rollback if error rate spikes." The timeline communicates: canary is a measured, multi-day process.

---

## Slide 5 — Blue/Green Deployment for AI

**Figure:** *Blue/green architecture diagram.* Traffic Router in the center with two arrows: one pointing left to "Blue" endpoint box (green/active border, "LIVE" badge), one pointing right to "Green" endpoint box (dashed border, "READY" badge). Switch arrow below the router: "Traffic switch (atomic, < 1s)." Rollback arrow: reverse direction, "Instant rollback." Cost annotation: "Cost: 2× endpoint hours during transition." Comparison to canary: "canary = days; blue/green = seconds."

---

## Slide 6 — Feature Flag Deployment for AI

**Figure:** *Feature flag rollout diagram.* Customer request arrives with customer_id. Feature Flag Service evaluates: "Is this customer in the rollout group?" Premium: YES → v2 offer system. High-Value + lucky 25%: YES → v2. Others: NO → v1. Both paths serve a response. Rollout percentage dial on the right: starts at 0%, then moves to Premium (100%) → HV (25%) → HV (100%) → All (100%). The dial communicates: gradual, controllable rollout.

---

## Slide 7 — Deployment Health Gates: Automated Promotion and Rollback

**Figure:** *Canary health gate flowchart.* Scheduled Lambda (every 15 min) → check metrics → three branches: Hard failure (red, immediate rollback + alert), Soft warning (amber, pause + alert), Healthy (green, advance to next percentage). The health gate check shows: metrics comparison with thresholds, decision, and action. This is the automation that makes canary practical.

---

## Slide 8 — Deployment for LLM Systems: Prompt Deployment

**Figure:** *Prompt deployment architecture diagram.* Parameter Store at center with active-version pointer. Offer generation service reads active version → fetches prompt → invokes Bedrock. Rollback: change the active-version pointer (single-parameter update). Prompt canary: 10% of requests use v3.2; 90% use v3.1; RAGAS evaluation running on both groups. The diagram communicates: prompt deployment is simpler than model deployment but still requires gates and rollback mechanisms.

---

## Slide 9 — Deployment for RAG Index Updates

**Figure:** *Blue/green RAG index diagram.* Two Bedrock Knowledge Base boxes: "Active KB (v7)" and "Staging KB (v8, syncing)." Offer generation service → active KB (100% traffic). Sync process: S3 new docs → Staging KB (background, 30-45 min). Smoke test → if pass, swap pointers. After swap: "Active KB (v8)" → Staging KB (old v7, available for rollback). Zero downtime indicated throughout.

---

## Slide 10 — Deployment Strategy for NorthStar: The Full Picture

**Figure:** *Deployment decision tree.* Root question: "Is this a routine update or major change?" → branches. "Routine" → "How reversible?" → "Easy (prompt/index): Pointer swap with canary." "Moderate (model weights): Canary deployment." "Hard (architecture change): Shadow first." "Major change" branch → "Shadow mode → evaluate → Blue/Green → Canary to 100%." Emergency branch: immediate rollback to last known good version. Clean decision tree logic.

---

## Slide 11 — Deployment Readiness Checklist

**Figure:** *Deployment readiness checklist card.* Two-section checklist card: "Model Release" (8 items) and "Prompt/Index Release" (5 items). All items shown unchecked. "DON'T DEPLOY FRIDAY" rule shown in red at the bottom with a calendar showing Friday highlighted. Clean, printable format. The checklist communicates: deployment is a process, not a button push.

---

## Slide 12 — Deployment Incident: What Good Rollback Looks Like

**Figure:** *Incident timeline diagram.* Horizontal timeline from 09:00 to 10:30. Key events marked. Between 09:45-09:48: red zone "Canary error spike detected + rollback." After 09:48: green zone "Production v2.3 100% traffic." Error rate graph overlaid on the timeline: production flat at 0.3%, canary spikes to 3.2%, then canary is removed. The diagram communicates that the automated rollback limited the user impact to a 3-minute window.

---

## Slide 13 — Deployment and AISDLC: Stage 7 in Detail

**Figure:** *AISDLC Stage 7 detail diagram.* Stage 7 box expanded to show internal steps: Deployment Plan → Pre-Deploy Checks → Canary Start (10%) → Health Gate → Traffic Advance → Health Gate → Traffic Advance → Full Rollout → Stage 7 Gate → Stage 8 (Monitor). Return loops shown: from Health Gate "FAIL" back to "Rollback and Investigate." The diagram shows Stage 7 is a process with gates and return loops, not a single action.

---

## Slide 14 — Lab 5 Preview: What You'll Deploy

**Figure:** *Lab 5 architecture preview.* Three-lane diagram: Churn (canary endpoint), RAG (blue/green KB), Agent (alias-based canary). Each lane shows the current version (blue), the new version (green/canary), traffic percentage, and health gate lambda. The full NorthStar deployment architecture in a single diagram. Lab 5 is the lab that connects to this architecture.

---

## Slide 15 — Deployment Metrics: What to Track

**Figure:** *DORA metrics dashboard for NorthStar.* Four metric gauges: Deployment Frequency (current vs. target), Lead Time (days, current vs. target), Change Failure Rate (%, current: 30% / target: 15%), MTTR (hours, current: 3h / target: 15min). Arrow from "current state" to "target state" for each metric. Lab 4 and Lab 5 impact shown: which lab closes which gap.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Lab 4 countdown (9 days) in amber. Lab 5 preview: "Assigned Thursday — start thinking about canary deployment architecture now."
