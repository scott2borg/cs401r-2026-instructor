# L10: XOps I — DataOps & MLOps — Figures

## Slide 1 — Title

**Figure:** *XOps stack diagram.* Vertical stack of four layers: DataOps (foundation, wide), MLOps (second layer), LLMOps (third layer), AgentOps (top, narrow). Each layer has: a name, a 2-word subtitle, and icons representing key tools/services. Color gradient from deep blue (bottom) to bright teal (top). The stack communicates: XOps is layered, each layer builds on the one below, and DataOps is the non-negotiable foundation.

---

## Slide 2 — What Is XOps and Why It Matters

**Figure:** *XOps maturity gap visualization.* Horizontal bar chart with three pairs: "Have data pipelines" vs. "Have DataOps practices" (gap: 55%), "Have ML models in production" vs. "Have automated ML lifecycle" (gap: 40%), "Have LLM deployments" vs. "Have LLMOps in place" (gap: 65%). Bars color-coded: deployed (blue), with XOps (teal). The gaps are visually prominent and striking.

---

## Slide 3 — DataOps: Principles and Architecture

**Figure:** *DataOps maturity scorecard.* Six principal rows with traffic-light status (green/amber/red) and NorthStar assessment. Two columns: "After Lab 2" and "Production standard." Makes clear where NorthStar labs bring students to vs. full production maturity. Motivates Labs 4 and 6 as the gaps to close.

---

## Slide 4 — DataOps in Practice: Pipeline Orchestration

**Figure:** *Glue Workflow DAG diagram.* Directed acyclic graph showing the 6-step NorthStar pipeline with dependencies. Steps 1-2 at the top (parallel); Steps 3-4 below (parallel, each depending on both Step 1 and Step 2); Step 5 below (depends on both 3 and 4); Step 6 at the bottom (depends on Step 5). Each node: step number, job name, estimated runtime. Edges: dependency arrows. Color: completed steps in green, running steps in gold, pending steps in gray. This is the Glue Workflow visualization.

---

## Slide 5 — MLOps: The Model Lifecycle Automation Stack

**Figure:** *MLOps maturity staircase.* Four steps (Level 1-4), each labeled, with representative architecture diagram at each level. Level 1: simple notebook. Level 2: pipeline diagram with human deployment step. Level 3: full CI/CD pipeline without human steps. Level 4: feedback loop with online learning. NorthStar course target circled at Level 2→3 transition. "Industry standard" marker at Level 3.

---

## Slide 6 — SageMaker Pipelines: MLOps Automation Engine

**Figure:** *SageMaker Pipeline DAG.* Visual representation of the pipeline above. Five step boxes connected by arrows. Condition step (Step 4) has a diamond shape showing the if/else branch. The "else" branch goes to a "Fail + Alert" box in red. The "if" branch goes to the "Register Model" box in green. Each step box shows the step name, step type, and runtime estimate. This pipeline is the Lab 4 deliverable.

---

## Slide 7 — MLOps Monitoring: The Feedback Loop

**Figure:** *Feedback loop diagram.* Circular flow connecting: Production Endpoint → Model Monitor → Drift Detection → Alert → Retraining Decision → SageMaker Pipeline → New Model → Evaluation Gate → Endpoint (if passes). At the Alert node: two exit paths (auto-retrain vs. human review). At the Evaluation Gate: two paths (deploy if passes, investigate if fails). Arrows form a closed loop, communicating: this is an ongoing operational system, not a one-time deployment.

---

## Slide 8 — Experiment Tracking at Scale: MLflow Governance

**Figure:** *MLflow governance hierarchy diagram.* Three-level pyramid: Exploration (wide base, many runs, free-form), Tuning (middle, systematic, tagged), Production Candidate (narrow top, single run, registered). Each level has: access control (who can run), tagging requirements, and artifact requirements. A "Production Path" arrow shows which runs are eligible for Model Registry registration.

---

## Slide 9 — The NorthStar XOps Assessment

**Figure:** *XOps assessment radar chart.* Radar/spider chart with 10 dimensions (one per capability in the table). Each dimension scored 0-4: 0=none, 1=manual, 2=partial, 3=automated, 4=optimized. After Labs 1-3: irregular polygon showing high scores on data capabilities (3-4), low on CI/CD and monitoring (0-1). After Labs 1-7: nearly full polygon, approaching Level 3 on all dimensions. Both states shown on the same chart: "before" in light blue, "after" in navy.

---

## Slide 10 — DataOps Anti-Patterns: What to Avoid

**Figure:** *Anti-pattern checklist.* Five rows, same format as previous anti-pattern slides. Red X icon for each anti-pattern; green checkmark for the fix. "Notebook Pipeline" row has a specific note: "How to detect: your pipeline runs from a .ipynb file." Practical and direct.

---

## Slide 11 — MLOps Anti-Patterns

**Figure:** *Five-row MLOps anti-patterns table.* Same format. "Model in a Notebook" row has a production incident counter: "Causes ~35% of ML production incidents per industry survey."

---

## Slide 12 — Cost of Technical Debt in AI Operations

**Figure:** *ROI waterfall chart.* Starting from "$0" at left, three positive bars: Manual Deployment Savings ($144K), Incident Cost Reduction ($80K), Retraining Automation ($40K). Final bar: Total XOps ROI ($264K). Each bar labeled with the calculation basis. Clean, credible, business-oriented.

---

## Slide 13 — Lab 4 Preview: What CI/CD for AI Looks Like

**Figure:** *Lab 4 CI/CD architecture overview.* Full CI/CD pipeline diagram: GitHub (code commit) → CodePipeline (orchestrator) → CodeBuild (test runner) → SageMaker Pipeline trigger → Training/Evaluation → ConditionStep (gate) → Model Registry → Canary Endpoint (Lab 5). Arrows show automation flow with no human intervention required in the happy path. "Manual approval" optional gate shown as a toggle (off by default, on for high-risk deployments).

---

## Slide 14 — The XOps Maturity Journey

**Figure:** *XOps maturity progression bar.* Horizontal bar divided into 7 colored segments (one per lab). Under each segment: lab number and key capability added. Above the bar: maturity level markers (Level 0 at left, Level 3 at right). A "current position" marker moves from left to right across labs. The overall visual communicates: each lab is a concrete step toward operational maturity.

---

## Slide 15 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary.* Standard format. Lab 3 countdown in amber (11 days). XOps radar chart thumbnail showing current vs. target state.
