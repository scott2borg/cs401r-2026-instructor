# L03: AI Platform & Cloud Architecture I — Figures

## Slide 1 — Title

**Figure:** *Multi-tier AWS architecture diagram.* Clean, professional-quality AWS architecture diagram showing three horizontal tiers: (1) Data Tier — S3 buckets, Glue ETL, Feature Store; (2) Compute/Model Tier — SageMaker training, endpoints, Bedrock; (3) Operational Tier — CloudWatch, CodePipeline, IAM. Arrow flows show data moving up through tiers. AWS official service icons. Light gray background. The diagram is the NorthStar platform they'll build this semester — a preview of Lab 1 and beyond.

---

## Slide 2 — What Is an AI Platform (and Why Does It Exist)?

**Figure:** *Cost comparison chart.* X-axis: Number of AI systems deployed. Y-axis: Total cost. Two lines: "Point Solutions" (linear, steep upward slope) and "Platform Approach" (high initial investment, then flattening curve). Lines cross at ~3 systems. Shaded area between the lines labeled "Platform ROI" — widens with each additional system. Data points marked at 1, 3, 5, 10 systems with illustrative cost values. Clean, white background, two-color.

---

## Slide 3 — Platform Maturity Model

**Figure:** *Staircase maturity model.* Five steps from lower-left to upper-right, each step wider and taller. Step color progresses from gray (Level 0) to bright blue (Level 4). Each step labeled with level number, name, and 2-3 word description. A gold arrow sits at the Level 2→3 transition, labeled "Course target." A "You are here" marker at Level 1 (where most student projects start). The visual makes the progression clear and the goal specific.

---

## Slide 4 — Three Reference Architectures for Enterprise AI

**Figure:** *Three architecture comparison diagram.* Three side-by-side panels, each showing a simplified architecture diagram for one model. Hub-and-Spoke: central hexagon connected to 5 outer nodes. Federated: 4 separate clusters with thin connections between them. Full-Stack: single layered diagram with self-service portals at top. Color-coded: Hub-and-Spoke in navy, Federated in teal, Full-Stack in gold. Below each diagram: a 3-word descriptor, a "Best for:" label, and a "Risk:" label.

---

## Slide 5 — Core Platform Component 1: Data Foundation

**Figure:** *Four-zone data architecture diagram.* Four S3 bucket icons arranged vertically (raw → processed → features → artifacts), connected by downward arrows. Between each pair of buckets: the transformation step that connects them (Glue ETL: raw→processed; Feature Engineering Pipeline: processed→features; Training Pipeline: features→artifacts). Color coding: raw=gray, processed=blue, features=teal, artifacts=gold. Lifecycle policy icons beside each bucket. The diagram is the exact structure students build in Lab 1 (S3) and Lab 2 (pipelines).

---

## Slide 6 — Core Platform Component 2: Compute Infrastructure

**Figure:** *Compute topology diagram.* Three horizontal rows: "Training" (SageMaker Training Job boxes, spot instance icon, cost tag), "Inference" (endpoint boxes: Real-Time, Batch Transform, Bedrock), "Development" (Studio icon, Processing Job icon). Arrows show flow from development → training → inference. NorthStar use case labels beside relevant compute components. Instance type labels where relevant. Color: training in blue, inference in teal, development in gray.

---

## Slide 7 — Core Platform Component 3: Model Registry

**Figure:** *Model Registry workflow.* A vertical flow: (1) Training Job completes → (2) Model Package created in Registry (status: Pending) → (3) Evaluation metrics auto-attached → (4) Human approval step (status: Approved) → (5) CI/CD pipeline triggers deployment → (6) Status: Deployed. Beside each step: the required artifact or action. A "Rejected" path shows a model being returned to the Development stage. Clean, readable. Connects directly to Lab 4 (CI/CD) content.

---

## Slide 8 — Core Platform Component 4: Feature Store

**Figure:** *Training/Serving Architecture with Feature Store.* Two paths shown from the same Feature Store: (1) Training path → batch read from offline store → training job → model artifact; (2) Inference path → online read from online store → endpoint → prediction. Both paths connect to the SAME feature computation pipeline feeding the SAME Feature Store. A "Training/Serving Skew" warning icon sits between the two paths, marked with a red X and labeled "This is what we're eliminating." Clear, explanatory, technically accurate.

---

## Slide 9 — Core Platform Component 5: Experiment Tracking

**Figure:** *MLflow experiment tracking UI mockup.* A clean table showing 6 experiment runs for "churn-prediction-v2." Columns: Run ID, Date, AUC, Precision@0.4, F1, n_estimators, max_depth, Data Version, Status. Rows are sorted by AUC descending. Best run highlighted in gold. Click-through to artifact shows: model.pkl, evaluation_report.json, feature_importance.png. This is exactly what students will produce in Lab 3.

---

## Slide 10 — Core Platform Component 6: CI/CD Pipeline

**Figure:** *CI/CD pipeline diagram.* Horizontal pipeline with 6 stages represented as connected boxes: (1) Code Commit → (2) Data Validation → (3) Training Pipeline → (4) Model Evaluation Gate → (5) Staging Deployment → (6) Production Promotion. Colored indicators at each stage (green = pass, red = fail, amber = gate decision). Below the pipeline: AWS service icons mapped to each stage. The gate at stage 4 shows: "AUC ≥ 0.72? → Yes: promote. No: alert." This maps directly to Lab 4.

---

## Slide 11 — The Build vs. Buy Decision Framework

**Figure:** *2×2 decision matrix.* X-axis: "Differentiation Potential" (low→high). Y-axis: "Complexity" (low→high). Four-quadrant labels: Buy/Subscribe (top-left), Configure (bottom-left), Build Carefully (bottom-right), Build as an Investment (top-right). NorthStar component examples placed in each quadrant (S3/SageMaker in Buy, IAM in Configure, XGBoost model in Build Carefully). A diagonal arrow from top-left to bottom-right labeled "In-house build increases as strategic value increases." Clean 2×2 format.

---

## Slide 12 — NorthStar Platform Architecture: Full View

**Figure:** *Full NorthStar AWS architecture diagram.* Comprehensive, multi-tier AWS diagram showing all components from Lab 1 through Lab 7. Organized into horizontal layers (Foundation → Data → Models → CI/CD → Operations → Business Value). AWS service icons throughout. Color-coded by lab number (each lab adds a different color layer). Arrows show data flows and dependencies. This diagram should feel slightly overwhelming — but also exciting. It is what the semester builds toward.

---

## Slide 13 — Infrastructure as Code: Why Everything Is Terraform

**Figure:** *Side-by-side comparison.* Left panel: Console screenshot (clicking AWS UI buttons, manual steps numbered 1-8). Right panel: Terraform code snippet for the same resource (SageMaker domain), showing provider, resource type, and configuration in clean HCL syntax. Below both panels: two metrics: "Time to reproduce in new account" (Console: "Unknown / Days"; Terraform: "12 minutes") and "Recoverable from disaster?" (Console: "Maybe"; Terraform: "Yes, always"). The contrast is stark and immediate.

---

## Slide 14 — Platform Cost Governance

**Figure:** *AWS Cost Explorer mockup.* Shows a realistic cost breakdown chart for a NorthStar-like environment. Bar chart by service: SageMaker (largest), S3 (medium), Glue (small), CloudWatch (small), Other (small). Monthly total: ~$32. Below: a budget alert timeline showing: $0 → Month 1 $32 → Month 2 $38 → Budget alert triggered at $50 → Month 3 costs controlled at $41. Green and amber color coding. Shows cost governance working as intended.

---

## Slide 15 — Common Platform Architecture Mistakes

**Figure:** *Five warning-sign visual.* Five rows, each with a red warning triangle icon on the left, an anti-pattern name in bold, a 1-sentence description, and a small "Fix:" label containing the remediation. Alternating row shading in very light pink/white. The visual design clearly communicates "these are mistakes" without clutter.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-point takeaway summary.* Same format as L01/L02 takeaways: numbered circles in navy on the left, takeaway text in large, readable type on the right. "Next Up" banner in teal below. Lab 1 deadline counter prominently displayed (e.g., "⏱ Lab 1 due in 9 days").
