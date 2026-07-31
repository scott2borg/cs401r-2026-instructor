# L06: Data & Feature Engineering II — Figures

## Slide 1 — Title

**Figure:** *SageMaker Feature Store architecture.* Dual-path diagram showing Feature Computation Pipeline at top feeding the Feature Store. Left path: Offline Store (S3) → Training Job. Right path: Online Store (DynamoDB) → Real-Time Endpoint. Both paths read from the same stored features, eliminating skew. Labels: "Point-in-time lookup for training," "Sub-10ms read for inference." Clean, symmetrical layout on white background.

---

## Slide 2 — Training/Serving Skew: The Root Causes

**Figure:** *Skew causation diagram.* Four-branch tree with "Training/Serving Skew" at the root. Four branches: Code Divergence, Data Freshness, Preprocessing Inconsistency, Temporal Leakage. Each branch shows a small "before (correct)" and "after (skewed)" state diagram. A green "Feature Store" box beside the root with a line labeled "Eliminates Causes 1-3." A separate red "Code Review" box for Cause 4 (temporal leakage requires human review, not just tooling).

---

## Slide 3 — SageMaker Feature Store: Technical Deep Dive

**Figure:** *Code walkthrough visual.* Split layout: left column shows the Python API calls with syntax highlighting; right column shows what each call does in the Feature Store architecture (ingest writes to both stores; offline read = Athena query on S3; online read = DynamoDB get-item). Arrows connect code blocks to architecture components. Makes the API concrete and immediately actionable for Lab 2.

---

## Slide 4 — Data Governance Framework for AI

**Figure:** *Governance pyramid.* Four horizontal layers in a pyramid, from bottom to top: Access Control (widest, foundation), Data Classification, Audit Trail, Data Quality SLAs (narrowest, top). Each layer has an icon (lock, label, clock, checkmark). Right side: NorthStar implementation examples for each layer. Color: deeper blue as you move up the pyramid.

---

## Slide 5 — Privacy Engineering for AI

**Figure:** *Privacy controls architecture diagram.* Data flow from customers.csv through three stages: (1) PII Masking (name → null, email → null, customer_id → hashed_id), (2) Feature Engineering (only hashed_id + numeric features), (3) Model Training (no PII in training matrix). Red X marks at each stage where PII would have flowed before controls. "GDPR Compliant" badge at the end of the flow.

---

## Slide 6 — Airbnb Zipline: The Case for Feature Stores

**Figure:** *Before/After timeline comparison.* Two rows. Top row: "Before Zipline" — 6 separate team pipelines (duplicated work, divergent features, skew). Bottom row: "After Zipline" — single Zipline platform with 6 teams reading from it. Metrics beside each row: Time to production (3-4 months → 2-3 weeks), Feature reuse rate (0% → 60%), Debugging time (weeks → hours). The improvement is dramatic and visual.

---

## Slide 7 — Data Lineage: Building the Audit Trail

**Figure:** *Data lineage DAG diagram.* Directed acyclic graph with nodes shaped by type: cylinders (data stores), rectangles (jobs), hexagons (model artifacts), rounded rectangles (endpoints). Edge labels show: job version, run timestamp, data hash/version. The "transactions.parquet" source is highlighted in gold at the top, and the "northstar-churn-prod" endpoint is at the bottom. The path from top to bottom can be traced in under 10 seconds. Visual style mimics Apache Atlas or AWS Glue Data Catalog lineage view.

---

## Slide 8 — Data Contracts in Practice

**Figure:** *Data contract lifecycle diagram.* Four-stage cycle: Define → Enforce → Monitor → Version. Each stage has an icon and description. A "Consumer Signature" box sits between Define and Enforce, indicating the formal agreement between the producer and the consumer. A "Contract Violation" alert path shows what happens when enforcement fails: Glue job stops → alert triggered → investigation. This lifecycle makes contracts feel operational, not just documentary.

---

## Slide 9 — Feature Versioning and Backward Compatibility

**Figure:** *Version timeline diagram.* Horizontal timeline. At bottom: Feature Group versions (v1 launches at Lab 2, v2 launches at Lab 5). Above: Model versions with arrows showing which Feature Group version they were trained on. At top: Endpoint versions showing which model (and therefore which Feature Group) they're connected to. Deprecation events are shown as strikethrough in older versions with dates. The visual shows that v1 must remain available until all v1-trained models are retired.

---

## Slide 10 — Data Pipeline Testing

**Figure:** *Testing pyramid for data pipelines.* Classic pyramid shape, bottom to top: Unit Tests (wide base, many tests, fast), Integration Tests (middle, fewer, minutes), Contract Tests (narrow, one per boundary, always run), Volume Tests (tip, rare, slow). Each layer has a test count estimate, a runtime estimate, and a run time. Color-coded: unit=green, integration=blue, contract=amber, volume=gray.

---

## Slide 11 — Lab 2 Progress Check and Common Issues

**Figure:** *FAQ-style visual.* Five numbered boxes arranged in two columns, plus one at the bottom. Each box: question in bold at top, answer below in smaller text. Color-coded: IAM issues in amber, Feature Store issues in teal, implementation tips in blue. A "Common Debug Commands" sidebar shows the 3 most useful CLI commands for diagnosing these issues.

---

## Slide 12 — Data Engineering at Scale: What Changes

**Figure:** *Comparison table visual.* The table above, styled with clear color coding: NorthStar column in light blue, Enterprise Scale column in navy, Architectural Response column in teal. Key insight callout: "The pattern is the same. The scale changes the parameters, not the architecture." A small NorthStar logo on the left and an "Enterprise" building icon on the right.

---

## Slide 13 — The Data Engineering Maturity Arc

**Figure:** *Three-stage progression diagram.* Three platforms on ascending steps. Stage 1 (left, ground level): "It works." Shows data flowing through the pipeline. Stage 2 (middle, one step up): "We can see it." Adds monitoring dashboards and alert icons. Stage 3 (right, highest): "It heals itself." Adds self-healing loop and automated remediation. Consistent color progression (gray → blue → gold). NorthStar lab labels at each stage.

---

## Slide 14 — NorthStar Feature Store: What It Should Look Like After Lab 2

**Figure:** *Three Feature Group schema cards.* Three side-by-side "schema cards" showing each Feature Group as a structured card with: Group name at the top (in a navy header), a list of features with type icons (string, integer, float) on the left, and a brief description on the right. Below each card: "Used by: [Lab 3 churn model / Lab 5 RAG / Lab 6 monitoring]." Clean card design with consistent layout.

---

## Slide 15 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary + upcoming schedule.* Standard format. Lab 2 progress bar showing "Due in 11 days" in amber.
