---
lecture: L06
title: Data & Feature Engineering II
date: Tuesday, September 22, 2026
week: 4
arc: Build
reading_due: "Data & Feature Engineering — Feature Stores through Key Takeaways"
lab_due: "Lab 2 due Sat Oct 3"
slides_target: 15
---

# L06: Data & Feature Engineering II
**Tuesday, September 22, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Feature stores deep dive, training/serving skew root causes, data lineage, governance, privacy engineering for AI, and the Airbnb Zipline case study. Lab 2 check-in.

**Reading Due:** *Data & Feature Engineering* — "Feature Stores" through "Key Takeaways"

---

## Slide 1 — Title
**Layout:** Left dark panel + right Feature Store architecture diagram

**Content:**
- Data & Feature Engineering II
- CS 401R · Lecture 06 · Tuesday, September 22, 2026
- Feature Stores · Data Governance · Privacy Engineering · Airbnb Case Study

**Figure:** *SageMaker Feature Store architecture.* Dual-path diagram showing Feature Computation Pipeline at top feeding the Feature Store. Left path: Offline Store (S3) → Training Job. Right path: Online Store (DynamoDB) → Real-Time Endpoint. Both paths read from the same stored features, eliminating skew. Labels: "Point-in-time lookup for training," "Sub-10ms read for inference." Clean, symmetrical layout on white background.

**Notes:** "Lab 2 check-in: raise your hand if you have data flowing through at least one Glue job into S3 processed." Get a status read. Address blockers quickly at the end of class or office hours. Today deepens the theoretical foundation for what they're building.

---

## Slide 2 — Training/Serving Skew: The Root Causes
**Layout:** Causal diagram showing four paths to skew

**Content:**
**What is training/serving skew?** The model receives different input distributions at serving time than it was trained on — causing silent performance degradation.

**Root Cause 1: Different computation code**
- Training: feature computed in a Pandas notebook (custom logic)
- Serving: feature computed by a different function in the inference handler
- Even a subtle difference (float rounding, null handling) causes skew

**Root Cause 2: Different data freshness**
- Training: features computed from the full historical dataset
- Serving: features computed from a real-time snapshot that may be stale or missing records

**Root Cause 3: Different preprocessing steps**
- Training: outliers clipped at 99th percentile of training data
- Serving: same clipping threshold applied to production data where the 99th percentile has shifted

**Root Cause 4: Temporal leakage**
- Training features inadvertently use information from after the label was assigned

**Prevention:** The Feature Store — single computation, written once, read by both training and serving.

**Figure:** *Skew causation diagram.* Four-branch tree with "Training/Serving Skew" at the root. Four branches: Code Divergence, Data Freshness, Preprocessing Inconsistency, Temporal Leakage. Each branch shows a small "before (correct)" and "after (skewed)" state diagram. A green "Feature Store" box beside the root with a line labeled "Eliminates Causes 1-3." A separate red "Code Review" box for Cause 4 (temporal leakage requires human review, not just tooling).

**Notes:** "Root Cause 4 — temporal leakage — is the insidious one. The Feature Store doesn't protect you from it. Temporal leakage happens in your feature design, not your pipeline architecture. This is why your feature definitions need a careful review against the question: 'Is this information available at the moment the model would make this prediction in production?'"

---

## Slide 3 — SageMaker Feature Store: Technical Deep Dive
**Layout:** Feature Group structure + API examples

**Content:**
**Feature Group Anatomy:**
```python
FeatureGroup(
    name="northstar-churn-features-v1",
    record_identifier_feature_name="customer_id",   # unique key
    event_time_feature_name="event_time",            # required for point-in-time
    feature_definitions=[
        FeatureDefinition("customer_id", FeatureTypeEnum.STRING),
        FeatureDefinition("recency_days", FeatureTypeEnum.INTEGRAL),
        FeatureDefinition("spend_30d", FeatureTypeEnum.FRACTIONAL),
        FeatureDefinition("frequency_90d", FeatureTypeEnum.INTEGRAL),
        FeatureDefinition("loyalty_tier", FeatureTypeEnum.INTEGRAL),
        FeatureDefinition("event_time", FeatureTypeEnum.STRING),
    ]
)
```

**Ingest (batch via Glue):**
```python
feature_group.ingest(data_frame=features_df, max_workers=3)
```

**Read from Offline Store (training):**
```python
# Point-in-time correct: features as of 2026-09-01
query = feature_group.athena_query()
query.run(query_string=f"SELECT * FROM {table} WHERE event_time < '2026-09-01'")
```

**Read from Online Store (inference):**
```python
runtime.get_record(FeatureGroupName="northstar-churn-features-v1",
                   RecordIdentifierValueAsString="NS-00000042")
```

**Figure:** *Code walkthrough visual.* Split layout: left column shows the Python API calls with syntax highlighting; right column shows what each call does in the Feature Store architecture (ingest writes to both stores; offline read = Athena query on S3; online read = DynamoDB get-item). Arrows connect code blocks to architecture components. Makes the API concrete and immediately actionable for Lab 2.

**Notes:** "These are the exact API calls you'll use in Lab 2. The starter kit includes a Feature Group creation template; you define the feature schema and the ingest function. Walk through the event_time requirement carefully — every Feature Store record needs a timestamp, which is what enables point-in-time lookups for reproducible training."

---

## Slide 4 — Data Governance Framework for AI
**Layout:** Governance pyramid with four layers

**Content:**
**Data Governance for AI — four layers:**

**Layer 1: Access Control** (who can read/write which data)
- IAM roles scoped to specific S3 prefixes and Feature Groups
- No individual access keys; all access through role assumption
- NorthStar: three roles, each scoped to their functional domain

**Layer 2: Data Classification** (sensitivity level drives handling rules)
- PII (customers.csv): masked before Feature Store ingest; never used as direct feature
- Financial (transactions): aggregated only; raw amounts excluded from features
- Internal (store_events, product_catalog): standard access controls

**Layer 3: Audit Trail** (record of who accessed what, when)
- S3 access logging enabled → CloudTrail → CloudWatch Logs
- SageMaker Model Registry: approval chain recorded with timestamp and approver identity
- Glue Data Catalog: change history tracked

**Layer 4: Data Quality SLAs** (contractual guarantees on pipeline outputs)
- Data contracts (Lab 2 deliverable) define quality obligations
- Violations trigger automated alerts and pipeline pauses

**Figure:** *Governance pyramid.* Four horizontal layers in a pyramid, from bottom to top: Access Control (widest, foundation), Data Classification, Audit Trail, Data Quality SLAs (narrowest, top). Each layer has an icon (lock, label, clock, checkmark). Right side: NorthStar implementation examples for each layer. Color: deeper blue as you move up the pyramid.

**Notes:** "Data governance is the set of rules that let an organization trust its data — including the data that feeds its AI systems. Without governance, you cannot answer the regulatory questions that matter: 'Who trained on this customer's data?' 'Who approved this model?' 'When was this feature last validated?' These questions arise in enterprise contexts, regulatory audits, and, increasingly, court cases involving AI systems.

---

## Slide 5 — Privacy Engineering for AI
**Layout:** Privacy threat → engineering control mapping

**Content:**
**Privacy Threats Specific to AI Systems:**

**1. PII in Features:** Including names, emails, or exact addresses in features exposes them to model inversion attacks.
**Control:** Pseudonymization — use customer_id as the join key; never use PII as a feature.

**2. Membership Inference:** An attacker can determine whether a specific individual was in the training dataset by probing the model.
**Control:** Differential privacy training (DP-SGD) for high-risk models; record-level data access logging.

**3. Model Inversion:** With sufficient queries, an attacker can reconstruct training data from model outputs.
**Control:** Rate limiting on inference endpoints; output perturbation for sensitive attribute predictions.

**4. Regulatory Compliance (GDPR Article 17 — Right to Erasure):**
- If a customer requests deletion, can you remove them from training data and retrain?
- **Control:** Data lineage tracking (which training runs used this customer) + model retraining infrastructure.

**NorthStar PII handling:**
- `customers.csv` → mask name, email, phone, address before any downstream processing
- Feature Store contains only: customer_id (hashed), derived numeric features
- Training data: no PII; only customer_id as identifier

**Figure:** *Privacy controls architecture diagram.* Data flow from customers.csv through three stages: (1) PII Masking (name → null, email → null, customer_id → hashed_id), (2) Feature Engineering (only hashed_id + numeric features), (3) Model Training (no PII in training matrix). Red X marks at each stage where PII would have flowed before controls. "GDPR Compliant" badge at the end of the flow.

**Notes:** "GDPR and CCPA are not hypothetical. NorthStar's customers include EU residents. Any EU customer has the right to request deletion of their data — including removal from model training. Without data lineage and model retraining infrastructure, you cannot comply. This is a real operational requirement, not an academic exercise." We cover the full regulatory framework in L18-L19 (Security/Privacy). Today: understand that privacy constraints shape data engineering choices.

---

## Slide 6 — Airbnb Zipline: The Case for Feature Stores
**Layout:** Case study narrative with architecture comparison

**Content:**
**Before Zipline (Airbnb's feature store, 2017):**
- Each ML team computed its own features independently
- Same feature ("days since host registration") computed 6 different ways across 6 teams
- Training/serving skew: features computed differently in notebooks vs. production
- Feature reuse: 0% — every team rebuilt from scratch
- Debugging time: "weeks of forensic work" when production models underperformed

**After Zipline:**
- Central feature computation platform; features are published, versioned, and shared
- Same feature computation code runs for both training and serving — architecturally guaranteed
- Airbnb ML engineers spend 80% less time on feature engineering (per Airbnb Engineering Blog)
- Feature reuse: 60% of features used by multiple teams
- Time to production for new models: 2-3 weeks vs. 3-4 months

**The Zipline Lessons for NorthStar:**
1. Feature standardization pays dividends immediately across multiple models
2. The online/offline store architecture is the only way to guarantee training/serving consistency
3. Feature reuse is a force multiplier: features built for churn prediction can be reused for offer personalization

**Figure:** *Before/After timeline comparison.* Two rows. Top row: "Before Zipline" — 6 separate team pipelines (duplicated work, divergent features, skew). Bottom row: "After Zipline" — single Zipline platform with 6 teams reading from it. Metrics beside each row: Time to production (3-4 months → 2-3 weeks), Feature reuse rate (0% → 60%), Debugging time (weeks → hours). The improvement is dramatic and visual.

**Notes:** "Airbnb is the canonical case study for why feature stores exist. The 2017 Zipline paper essentially defined the feature store pattern that SageMaker Feature Store, Feast, Tecton, and Hopsworks implement today. The lesson is not 'Airbnb is smart' — it's 'the same pain that forced Airbnb to build Zipline is the same pain you're preventing in NorthStar by using SageMaker Feature Store.'"

---

## Slide 7 — Data Lineage: Building the Audit Trail
**Layout:** DAG visualization with NorthStar example

**Content:**
**Complete NorthStar Lineage Chain (churn model):**
```
Source:
  customers.csv (raw, version: 2026-09-17, hash: a3f2...)
  transactions.parquet (raw, 2026-09-17, hash: b7c1...)

↓ Glue Job: customer-feature-extraction (v2.3, run: 2026-09-18 02:14 UTC)
  → Output: s3://northstar-processed/customers/2026-09-18/*.parquet

↓ Glue Job: transaction-aggregation (v1.8, run: 2026-09-18 02:47 UTC)  
  → Output: northstar-churn-features Feature Group (ingested 02:53 UTC)

↓ SageMaker Training Job: churn-xgb-v12 (instance: ml.m5.xlarge, 2026-09-18 03:15 UTC)
  → Training data: northstar-churn-features, event_time < 2026-09-01
  → Artifact: s3://northstar-artifacts/churn/v12/model.tar.gz

↓ Model Registry: churn-model-v12 (approved: 2026-09-19 14:22 UTC, approver: governance-role)

↓ Endpoint: northstar-churn-prod (deployed: 2026-09-20 09:00 UTC)
```

**Lab 2 deliverable:** Document this lineage chain for your own pipeline.

**Figure:** *Data lineage DAG diagram.* Directed acyclic graph with nodes shaped by type: cylinders (data stores), rectangles (jobs), hexagons (model artifacts), rounded rectangles (endpoints). Edge labels show: job version, run timestamp, data hash/version. The "transactions.parquet" source is highlighted in gold at the top, and the "northstar-churn-prod" endpoint is at the bottom. The path from top to bottom can be traced in under 10 seconds. Visual style mimics Apache Atlas or AWS Glue Data Catalog lineage view.

**Notes:** "If something goes wrong with the churn predictions next month, you open this lineage diagram and walk backward. Predictions degraded? Check the Feature Group. Feature Group quality issue? Check the Glue job version. Glue job output looks right, but model is wrong? Check the training data snapshot. In 5 minutes you know where the problem is." Without lineage, the same investigation takes days or weeks.

---

## Slide 8 — Data Contracts in Practice
**Layout:** Data contract implementation with monitoring

**Content:**
**The Data Contract Implementation Pattern:**

**Step 1: Define the contract (schema + quality + SLA)**
- Document schema for each field: type, nullable, allowed values/ranges
- Define quality constraints: null_rate_max, duplicate_rate_max, value_range
- Define SLA: data freshness, delivery time, success rate

**Step 2: Enforce the contract at the pipeline boundary**
```python
# In Glue job — validate before writing to processed zone
def validate_contract(df, contract):
    for field, constraints in contract['schema'].items():
        null_rate = df[field].isna().mean()
        assert null_rate <= constraints['null_rate_max'], \
            f"NULL rate {null_rate:.3%} exceeds contract {constraints['null_rate_max']:.3%}"
```

**Step 3: Monitor contract compliance over time**
- Emit compliance metrics to CloudWatch
- Alert on contract violations
- Version contracts with the data pipeline — breaking changes require migration

**Step 4: Consumer acknowledgment**
- Downstream teams sign the contract — they know what to expect
- Schema breaking changes require advance notice and consumer migration window

**Figure:** *Data contract lifecycle diagram.* Four-stage cycle: Define → Enforce → Monitor → Version. Each stage has an icon and description. A "Consumer Signature" box sits between Define and Enforce, indicating the formal agreement between the producer and the consumer. A "Contract Violation" alert path shows what happens when enforcement fails: Glue job stops → alert triggered → investigation. This lifecycle makes contracts feel operational, not just documentary.

**Notes:** "Data contracts are the handshake between data producers and consumers. Without them, the ML team discovers that the data team changed a field name during a post-mortem following the model's failure in production. With them, the change requires a migration window, a version bump, and consumer acknowledgment before any data changes."

---

## Slide 9 — Feature Versioning and Backward Compatibility
**Layout:** Feature version management diagram

**Content:**
**Why Feature Versioning Matters:**
- Lab 3 trains a model on Feature Group v1 features
- After Lab 3, you realize recency_days should be computed differently
- If you update the Feature Group in place, Lab 3's trained model now reads incompatible features at inference time

**Feature Group Versioning Strategy:**
- **Minor version** (v1.0 → v1.1): Add new features; never remove or change existing features
- **Major version** (v1 → v2): Create a new Feature Group; migrate models when ready; deprecate v1 on a schedule

**SageMaker Feature Store versioning approach:**
```
northstar-churn-features-v1  # Labs 3-4; deprecated after Lab 5
northstar-churn-features-v2  # Lab 5+; adds session_frequency_7d and support_contacts_30d
```

**Backward compatibility rule:** Any model in production must be able to read from the Feature Group version it was trained on for as long as it remains in production.

**Figure:** *Version timeline diagram.* Horizontal timeline. At bottom: Feature Group versions (v1 launches at Lab 2, v2 launches at Lab 5). Above: Model versions with arrows showing which Feature Group version they were trained on. At top: Endpoint versions showing which model (and therefore which Feature Group) they're connected to. Deprecation events are shown as strikethrough in older versions with dates. The visual shows that v1 must remain available until all v1-trained models are retired.

**Notes:** "This is a real operational concern. In production, you may still have a model trained on a Feature Group from 6 months ago running — because it's the most reliable version and retraining takes time. During that time, you cannot break that Feature Group. Versioning is how you maintain backward compatibility while moving forward."

---

## Slide 10 — Data Pipeline Testing
**Layout:** Testing pyramid for data pipelines

**Content:**
**AI Data Pipeline Testing Hierarchy:**

**Unit Tests** (per transformation function):
- Input: known DataFrame with controlled values
- Expected output: explicitly specified
- Examples: test that `recency_days` returns 0 when transaction_date == today, NaN when no transactions

**Integration Tests** (per pipeline):
- Run the complete Glue job on a 1,000-row sample
- Validate output schema, row count, and quality metrics
- Must complete in < 5 minutes (fast feedback loop)

**Data Contract Tests** (at pipeline boundary):
- Validate that pipeline output conforms to the signed data contract
- Run automatically on every pipeline execution
- Contract violations halt the pipeline

**Volume/Performance Tests** (monthly or pre-release):
- Run the pipeline on the full dataset (4.5M transaction records)
- Validate that it completes within the SLA window

**Figure:** *Testing pyramid for data pipelines.* Classic pyramid shape, bottom to top: Unit Tests (wide base, many tests, fast), Integration Tests (middle, fewer, minutes), Contract Tests (narrow, one per boundary, always run), Volume Tests (tip, rare, slow). Each layer has a test count estimate, a runtime estimate, and a run time. Color-coded: unit=green, integration=blue, contract=amber, volume=gray.

**Notes:** "Data pipeline testing is the most commonly skipped engineering practice in AI projects. Teams test their model code (sometimes) but not their data transformation code (rarely). A bug in a feature computation function that passes all unit tests but fails on the actual production data distribution is exactly the kind of failure that causes production incidents." In Lab 2, students are required to include at least one unit test for each feature computation function and a contract test.

---

## Slide 11 — Lab 2 Progress Check and Common Issues
**Layout:** Status check format with common blockers and solutions

**Content:**
**Where Lab 2 stands (assigned 5 days ago):**
- Lab 2 is due in 11 days (Oct 3)
- At this point, you should have: explored the dataset, designed your feature schema, and started writing Glue job code

**Common Issues Students Hit (and how to fix them):**

1. **Glue job can't read from S3:** Check that the DataEngineer IAM role has `s3:GetObject` on the `raw/` bucket prefix. Also check that the Glue job's IAM role is set correctly.

2. **Feature Store ingest fails with schema mismatch:** Your DataFrame column types must exactly match the FeatureDefinition types. Cast all columns explicitly before ingest.

3. **Athena query on Offline Store returns no results:** Feature Store takes ~15 minutes to appear in the Offline Store after ingest. Run `describe_feature_group()` to check status.

4. **PII masking: how to hash customer_id for privacy?** Use `hashlib.sha256(customer_id.encode()).hexdigest()` — consistent hash, non-reversible without the original.

5. **Data lineage diagram: what tool to use?** The Lab 2 starter kit includes a draw.io template. Lucidchart and Mermaid (for markdown-embedded diagrams) are also acceptable.

**Figure:** *FAQ-style visual.* Five numbered boxes arranged in two columns, plus one at the bottom. Each box: question in bold at top, answer below in smaller text. Color-coded: IAM issues in amber, Feature Store issues in teal, implementation tips in blue. A "Common Debug Commands" sidebar shows the 3 most useful CLI commands for diagnosing these issues.

**Notes:** "These are the five issues I see every semester. If you're stuck on one of them, you're not alone. Come to office hours — I've seen each of these resolved in under 10 minutes with the right guidance." Also: "Start testing your Glue jobs this week. Don't wait until the weekend before the deadline — Glue jobs fail in ways that take time to debug, and AWS support responses can take 24 hours."

---

## Slide 12 — Data Engineering at Scale: What Changes
**Layout:** Scale considerations table with NorthStar vs. enterprise comparison

**Content:**
**What Changes When Data Gets Larger:**

| Dimension | NorthStar (Course) | Enterprise Scale | Architectural Response |
|-----------|-------------------|------------------|----------------------|
| Customers | 250K | 50M-500M | Partitioning, columnar formats (Parquet), parallel Glue DPUs |
| Transaction history | 18 months | 10+ years | Data archiving, tiered storage, time-partitioned Feature Groups |
| Feature groups | 3 groups, 8 features | 200+ groups, 1,000+ features | Feature catalog, feature discovery tooling |
| Pipeline latency | 2 hours acceptable | 5-minute SLA | Streaming ingestion, Kinesis, real-time Feature Store |
| Team size | 1 person | 10-20 data engineers | Data contract enforcement, versioning governance, shared standards |
| Cost | ~$5-10/month | $50K-500K/month | FinOps, cost allocation, tiered storage classes |

**The NorthStar platform is designed to be extendable:** The Terraform modules, IAM design, and S3 structure you're building are the same patterns used at enterprise scale — just parameterized differently.

**Figure:** *Comparison table visual.* The table above, styled with clear color coding: NorthStar column in light blue, Enterprise Scale column in navy, Architectural Response column in teal. Key insight callout: "The pattern is the same. The scale changes the parameters, not the architecture." A small NorthStar logo on the left and an "Enterprise" building icon on the right.

**Notes:** "The architectural patterns you're learning in this course — Feature Stores, data contracts, lineage tracking, version management — are the same patterns AWS, Google, and Netflix use at 100x the scale. The difference is not the pattern; it's the parameterization. When you graduate and join a company with 10 million customers, you know what the right architecture looks like."

---

## Slide 13 — The Data Engineering Maturity Arc
**Layout:** Three-stage arc connecting Lab 2 to real-world data maturity

**Content:**
**Stage 1 — Functional (Lab 2 level):**
Data moves from sources to features. Pipeline runs. Quality is checked. Features are versioned.

**Stage 2 — Observable (Lab 6 level):**
Pipeline health is visible. Failures alert. Drift is detected. Data quality SLAs are monitored.

**Stage 3 — Self-Healing (advanced):**
Pipeline failures trigger automated remediation. Drift triggers automatic retraining. Data contracts enforce schema evolution automatically. Few teams reach this level.

**NorthStar Labs map:**
- Lab 2: functional pipeline → Stage 1
- Lab 6: monitoring added → Stage 2
- Stage 3 is the team project north star for ambitious teams

**Figure:** *Three-stage progression diagram.* Three platforms on ascending steps. Stage 1 (left, ground level): "It works." Shows data flowing through the pipeline. Stage 2 (middle, one step up): "We can see it." Adds monitoring dashboards and alert icons. Stage 3 (right, highest): "It heals itself." Adds self-healing loop and automated remediation. Consistent color progression (gray → blue → gold). NorthStar lab labels at each stage.

**Notes:** "Most enterprise teams are at Stage 1 or transitioning to Stage 2. Stage 3 is the aspiration. Your labs take NorthStar from Stage 1 (Lab 2) to Stage 2 (Lab 6). If your team project attempts Stage 3 behaviors — automated retraining triggers, self-healing data pipelines — that's exceptional work and will be recognized."

---

## Slide 14 — NorthStar Feature Store: What It Should Look Like After Lab 2
**Layout:** Three Feature Group descriptions with schema + rationale

**Content:**
**Required Feature Groups (Lab 2):**

**Feature Group 1: `northstar-customer-demographics-v1`**
- Fields: customer_id, tenure_days, loyalty_tier, age_group, region_code, event_time
- Purpose: stable demographic signals for churn model

**Feature Group 2: `northstar-transaction-features-v1`**
- Fields: customer_id, spend_30d, spend_60d, spend_90d, frequency_30d, frequency_60d, frequency_90d, avg_basket_size, event_time
- Purpose: RFM features for churn prediction

**Feature Group 3: `northstar-engagement-features-v1`**
- Fields: customer_id, sessions_7d, sessions_30d, pages_per_session_avg, support_contacts_30d, event_time
- Purpose: engagement signals from clickstream and support data

**These three groups will feed the XGBoost churn model in Lab 3.** Lab 5 will add a fourth group for the RAG offer system.

**Figure:** *Three Feature Group schema cards.* Three side-by-side "schema cards" showing each Feature Group as a structured card with: Group name at the top (in a navy header), a list of features with type icons (string, integer, float) on the left, and a brief description on the right. Below each card: "Used by: [Lab 3 churn model / Lab 5 RAG / Lab 6 monitoring]." Clean card design with consistent layout.

**Notes:** "These three Feature Groups are the minimum for Lab 2. If you add additional features that you think will improve the churn model, document why in your lab report — extra features without rationale won't earn extra points." The three Feature Groups are designed so that their contents come from the three different data sources (customers.csv, transactions.parquet, clickstream.parquet), ensuring students work with multiple ingestion pipelines.

---

## Slide 15 — Key Takeaways + What's Next
**Layout:** Takeaways + Week 4 schedule

**Content:**
**Key Takeaways:**
1. Training/serving skew has four root causes; the Feature Store eliminates three of them architecturally — temporal leakage still requires human judgment
2. Data governance is four layers: access control → data classification → audit trail → quality SLAs; each layer depends on the one below
3. Privacy engineering is not an add-on — PII handling rules shape feature design from the beginning
4. Data contracts are the API contract for data: sign them, version them, enforce them at pipeline boundaries
5. Feature versioning and backward compatibility are operational requirements, not best practices — a model in production is held to the Feature Group version it was trained on

**Next Session (Thu Sep 24):**
- Topic: Model Development I — the development spectrum, prompt engineering, custom training, fine-tuning, reproducibility
- Reading due: *Model Development* — "Motivation" through "Fine-Tuning Foundation Models"
- Lab 2 progress: Feature Store should have at least one Feature Group ingested by now

**Figure:** *Five-takeaway summary + upcoming schedule.* Standard format. Lab 2 progress bar showing "Due in 11 days" in amber.

**Notes:** "Lab 2 halfway point is next Thursday. If you don't have a Glue job running by then, come to office hours — I won't let you fall behind if you ask for help. The pipeline you build in Lab 2 is what every subsequent lab reads from."
