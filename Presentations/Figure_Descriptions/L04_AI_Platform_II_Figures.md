# L04: AI Platform & Cloud Architecture II — Figures

## Slide 1 — Title

**Figure:** *Complete NorthStar AWS architecture diagram, full color.* Professional-quality AWS architecture diagram identical to the "Lab 1 through Lab 7" vision diagram from L03. This time presented as the "what we're building together" visual — all seven lab layers visible, with Lab 1 components highlighted/circled in gold. The rest of the platform in lighter opacity, indicating "coming soon."

---

## Slide 2 — SageMaker Domain: The Hub of the NorthStar Platform

**Figure:** *SageMaker Domain component diagram.* Central box labeled "SageMaker Domain" with sub-components shown as nested boxes: VPC (contains Private Subnet), EFS (shared storage), User Profiles (two: MLEngineer, DataEngineer), and Default S3. Arrows indicate that Studio App reads from EFS and Training Jobs write to S3 artifacts. IAM role shields beside each user profile. Terraform `resource` block shown in small text below the diagram. Clean AWS service icon style.

---

## Slide 3 — VPC Design for AI Workloads

**Figure:** *VPC architecture diagram.* Standard AWS VPC diagram showing the VPC boundary (blue rectangle), two private subnets inside (gray boxes with availability zone labels), VPC endpoints (green circles on the VPC boundary), and traffic flow arrows. No public subnet, no internet gateway. Customer data flow: S3 → VPC Endpoint → Private Subnet → SageMaker Training Job → back through VPC Endpoint → S3. The "No public internet" path is shown with a red X.

---

## Slide 4 — IAM Design: Least Privilege for AI Workloads

**Figure:** *Permission matrix table.* Rows: three IAM roles. Columns: key AWS services (SageMaker, S3-raw, S3-processed, S3-features, S3-artifacts, Glue, Bedrock, Model Registry, CloudWatch). Cell values: Full Access (dark green), Read Only (light green), Write Only (blue), No Access (gray). The matrix makes permission boundaries immediately visible. Common mistake (God Role) shown in a fourth row at bottom in red: "AdministratorAccess — all cells dark green — NEVER do this."

---

## Slide 5 — S3 Bucket Architecture: Design Decisions

**Figure:** *S3 architecture with data lineage arrows.* Four S3 bucket icons in a vertical flow, connected by transformation pipeline boxes between them: "Ingestion Scripts" between raw and processed; "Glue ETL + Feature Engineering" between processed and features; "Training Pipeline" between features and artifacts. Lifecycle policy icons with time labels beside each bucket. Permission lock icons showing who can write. Color coding matches the data zone colors from L03.

---

## Slide 6 — SageMaker Ecosystem: What You'll Actually Use

**Figure:** *SageMaker ecosystem map.* SageMaker logo in center. Radiating outward: service circles (Studio, Training Jobs, Processing Jobs, Pipelines, Model Registry, Feature Store, Real-Time Endpoints, Batch Transform). Lines connecting services show data flows (e.g., Training Job reads from Feature Store, writes artifact to Model Registry). Course lab labels overlaid on relevant services (Lab 2 on Feature Store, Lab 3 on Training Jobs, Lab 4 on Pipelines + Registry, Lab 5 on Endpoints). Highlight circle around the 5-6 most-used services in the first three labs.

---

## Slide 7 — NorthStar Platform Walkthrough: Lab 1 Components

**Figure:** *Split-screen layout.* Left: clean Terraform HCL code with syntax highlighting (similar to above). Right: the NorthStar architecture diagram with each module mapped to the component it creates. Arrows connect code blocks to diagram elements. The split-screen connects the abstract (code) to the concrete (infrastructure). Color-coded by module (VPC=blue, Storage=teal, IAM=amber, SageMaker=navy).

---

## Slide 8 — Architecture Decision Record: How to Write One

**Figure:** *ADR document visual.* The example ADR rendered as a clean document with section headers in distinct colors. Context section: dark gray background. Options: two-column comparison with green/red indicators. Decision: gold highlight. Consequences: teal section. Footer shows: "Status: Accepted | Author: [Name] | Date: Sep 19, 2026." Professional formatting that looks like a real engineering document, not a homework assignment.

---

## Slide 9 — Platform Cost Estimate: How to Build One

**Figure:** *Cost breakdown table.* Clean table with three columns: Service, Estimated Monthly Cost, Notes. Rows for each service listed above. Bottom row: Total with a range ($38-53). Beside the table: a small pie chart showing cost distribution by service (VPC Endpoints are the biggest cost driver, surprising students). Below: "Budget alert recommendation: set alerts at $50 and $100."

---

## Slide 10 — Modularity: Building for the Future Labs

**Figure:** *Module dependency tree with future lab callouts.* A tree diagram showing Lab 1 modules at the root (VPC, IAM, Storage, SageMaker). From each module, dashed arrows point to future labs that depend on it. Lab 2 arrow from Storage (adds Glue resources). Lab 3 arrow from IAM (adds Bedrock permissions). Lab 4 arrow from SageMaker (adds Pipelines). The diagram makes the architectural dependency clear and motivates good modular design now. Color: Lab 1 modules in solid blue; future labs in dashed teal.

---

## Slide 11 — Vendor Strategy: AWS Lock-In and the Mitigation

**Figure:** *Lock-in spectrum diagram.* A horizontal spectrum from "Vendor-Neutral" (left) to "Deep Lock-In" (right). AWS services plotted along the spectrum: S3 (slight lock-in, alternatives exist), SageMaker Training (moderate, containerized), MLflow (neutral), SageMaker Feature Store (high), Bedrock (very high), CodePipeline (high). Each service is shown as a labeled dot. Below: "NorthStar mitigation strategies" arrows pointing from high-lock-in services to their mitigations (containerization, standard model formats, etc.).

---

## Slide 12 — Security Checklist for Lab 1

**Figure:** *Checklist visual.* The table rendered as a clean checklist with checkbox icons. "Auto-fail" item at the bottom in a red box with a warning icon. Two column layout for space efficiency. Each requirement has a brief description. Can be used as a pre-submission self-check.

---

## Slide 13 — Lab 1 Grading Rubric Overview

**Figure:** *Rubric visualization.* The table above with a visual weight bar beside each task showing proportional weight. ADR (25 pts) has the longest bar. A pie chart sidebar shows the distribution visually. Key success criteria for the top 3 tasks shown in bold. Clear, readable at a glance.

---

## Slide 14 — What Good Platform Architecture Feels Like

**Figure:** *Six-pillar hexagon diagram.* Each pillar of the Well-Architected Framework as one segment of a hexagon, with a distinct color and icon. The hexagon rotates so "Security" is at the top (emphasizing its foundational importance). Each segment shows: pillar name + NorthStar-specific implementation example in small text. The overall visual communicates: "well-architected is multidimensional, not a single checkbox."

---

## Slide 15 — NorthStar Architecture Decisions: The Complete ADR Set

**Figure:** *Decision table with rationale column.* Clean table as above. Color coding: decisions that are "buy/configure" choices in light green; "build" decisions in light blue. The rationale column uses concise engineering language — short phrases, not sentences. A bottom row: "Revisit at: Lab 5" indicating which decisions might need to be reconsidered later.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway list + Lab 1 countdown.* Standard numbered takeaway format. Below: a prominent "Lab 1 Due: Saturday" callout in amber/orange with 4-day countdown. Lab 2 preview in teal: "Assigned Thursday."
