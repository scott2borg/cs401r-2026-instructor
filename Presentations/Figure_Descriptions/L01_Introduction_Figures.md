# L01: Introduction — Figures

## Slide 1 — Title

**Figure:** *Enterprise AI system topology.* A dense network graph on a dark navy background showing 60+ interconnected nodes. Three prominent gold/amber hub nodes are labeled "Churn Model," "Offer Generator," and "Customer Agent." Smaller blue nodes represent data flows, microservices, feature stores, monitoring, and infrastructure. Lines between nodes vary in thickness (data volume) and color (data type). The image communicates complexity, scale, and the "living system" nature of production AI — not a model, not a demo, a running system.

---

## Slide 2 — The State of Enterprise AI

**Figure:** *Split bar chart.* Left bar: "AI Projects Started" (100%). Right bars, decreasing in height: "Reach Pilot" (60%), "Reach Staging" (35%), "Reach Production" (15%), "Still Running at 12 Months" (8%). Bars colored from light blue to deep navy. A red dashed line at 15% labeled "The Production Wall." Clean, white background, large readable labels.

---

## Slide 3 — What This Course Is — and Isn't

**Figure:** *Two-column visual contrast.* The left column, labeled "Demo / Prototype," shows a simple notebook → model path. The right column, labeled "Production System," shows a full system diagram: data ingestion → feature engineering → training pipeline → evaluation gates → deployment → monitoring → governance → feedback loop. The right column is 4× more complex. No numbers, just structural complexity visible at a glance.

---

## Slide 4 — Why AI Engineering Is Different from Software Engineering

**Figure:** *2×2 quadrant diagram.* Each quadrant has a distinct background (navy, teal, amber, slate), a large icon in the corner (dice for probabilistic, database for data, clock with a down-arrow for drift, flask for experimentation), and a 2-3-word label in large type. Sub-text in smaller type below each label. Clean grid lines, no gradients.

---

## Slide 5 — The Build → Operate Arc

**Figure:** *Horizontal arc timeline.* A sweeping arc from left (Week 1) to right (Week 15). The left ~65% of the arc is labeled "BUILD" in blue; the right ~35% is labeled "OPERATE" in teal. Seven gold diamond markers along the arc indicate lab assignments. The names of the assignments in order (starting from week 1) are: Platform Foundation, Data & Feature Engineering, Model Development, XOps & CI/CD Pipeline + Testing, Deployment & Scaling + Security, Monitoring & Reliability, Metrics + Economics & Business Value. A vertical dashed line at Week 10 labeled "Bridge: Build → Operate." Below the arc: a thin row of week numbers. Above the arc: lecture topics in small type at each position. The overall visual feels like a project roadmap.

---

## Slide 6 — NorthStar Retail: The Case That Runs the Semester

**Figure:** *Three-tier architecture diagram.* Top tier: "AWS Data Platform" — S3 buckets (raw/processed/features/artifacts), Glue ETL, SageMaker Feature Store. Middle tier: three side-by-side boxes for each AI system with their key components. Bottom tier: "Business Impact" — churn rate ↓, offer conversion ↑, support cost ↓. Arrows flow from top to middle (data feeds models) and from middle to bottom (models drive outcomes). Color-coded: blue for infrastructure, teal for models, gold for business metrics.

---

## Slide 7 — What You'll Build: Seven Labs, One Platform

**Figure:** *Layer cake / stacked architecture diagram.* Seven horizontal layers stacked from bottom (Lab 1 - Infrastructure) to top (Lab 7 - Business Value). Each layer is a distinct color band. Small icons inside each layer (Terraform logo, S3 logo, XGBoost icon, etc.). The left side shows the lab number; the right side shows a brief description. Top of stack: "Complete NorthStar AI Platform." The visual makes clear that each lab builds on all previous labs.

---

## Slide 8 — How This Course Works

**Figure:** *Simple pie chart* showing grade component weights. Sections: Labs (49%, navy), Team Project (30%, teal), AWS Academy (10%, amber), Quizzes (11%, gray). Clean, large text labels. No 3D effects.

---

## Slide 9 — Lab 1 Assigned: Platform Foundation

**Figure:** *Terraform architecture diagram.* Shows the four Terraform modules (vpc/, iam/, sagemaker/, storage/) in boxes connected to the AWS services they provision. Light gray background with AWS service icons (S3 bucket, SageMaker domain, IAM role shield, VPC network). Module names in bold; AWS resources in standard type below each module name. Arrows show dependency order (vpc → iam → storage → sagemaker).

---

## Slide 10 — The NorthStar Starter Kit

**Figure:** *File tree diagram* styled like a terminal `tree` command output on a dark background. Folders are highlighted in blue, key deliverable files in gold/amber. The `docs/` folder and `infrastructure/` folder are visually emphasized with a subtle glow border. Clean monospace font.

---

## Slide 11 — The Architecture Decision Record (ADR)

**Figure:** *ADR template visual.* Shows a filled-out ADR for the VPC decision as an example. Formatted as a clean document with colored section headers (Context in blue, Options in gray, Decision in navy, Consequences in teal). The document shows realistic content, not lorem ipsum. Demonstrates the professional quality standard expected.

---

## Slide 12 — Who Succeeds in This Course

**Figure:** *Side-by-side timeline visualization.* Two timelines (16 weeks) shown horizontally. Top timeline ("Successful student"): evenly distributed work marks across all weeks, green color. Bottom timeline ("Struggling student"): work spikes at weeks 2, 4, 6... (lab due dates), in red. The visual makes clear the pace problem before students experience it.

---

## Slide 13 — Reading the Book: How to Use EAIE

**Figure:** *Chapter structure visualization.* A vertical flowchart showing the anatomy of a chapter: "Motivation" box → "Challenge" box → "Key Framework" box (highlighted in gold, labeled "This is the core") → "Case Study" box → "Apply It" box. Arrows connect each section. The "Key Framework" section has a bracket pointing to: "This is what the lecture digs into." Clean, minimal, helps students know where to focus their reading attention.

---

## Slide 14 — The Semester Ahead: A Preview

**Figure:** *Visual semester calendar.* A 15-column grid (one column per week). Each column has the week number at the top, lecture topics in small text in the middle, and color-coded bars at the bottom: blue for Build arc, teal for Operate arc, gold for Team Project. Lab assignments and due dates are shown as diamond markers above the grid. A vertical red line labeled "Bridge" at Week 10. The overall visual looks like a Gantt chart but more polished — a project roadmap.

---

## Slide 15 — NorthStar Tech Stack Preview

**Figure:** *AWS architecture reference diagram.* Full AWS architecture showing all services used in the course, organized in three tiers: Data Tier (S3, Glue, Feature Store), Model Tier (SageMaker, Bedrock), and Operational Tier (CloudWatch, CodePipeline, IAM). AWS official service icons. Color-coded by course arc: blue = Build, teal = Operate. Light gray background with subtle grid. Professional engineering diagram quality.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Simple 5-point numbered list visual.* Each takeaway on its own row with a large numbered circle (navy background, white number) on the left and the takeaway text to the right. Below the list: a "Next Up" banner in teal showing the upcoming lecture topic and reading. Clean, high-contrast, readable from the back of the room.
