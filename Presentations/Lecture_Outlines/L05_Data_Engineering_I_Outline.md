---
lecture: L05
title: Data & Feature Engineering I
date: Thursday, September 17, 2026
week: 3
arc: Build
reading_due: "Data & Feature Engineering — Motivation through Feature Engineering"
lab_assigned: "Lab 2 — Data & Feature Engineering (Due: Sat Oct 3)"
lab_due: "Lab 1 due Sat Sep 19 (2 days)"
slides_target: 16
---

# L05: Data & Feature Engineering I
**Thursday, September 17, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

Why data engineering for AI is fundamentally different from that for analytics. Three ingestion patterns, operational data quality, feature engineering principles, and the Zillow Offers cautionary tale. Lab 2 assigned today.

**Reading Due:** *Data & Feature Engineering* — "Motivation" through "Feature Engineering"  
**Lab 2 Assigned:** Due Saturday, October 3, midnight  
**Lab 1 Due:** Saturday, September 19 (2 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right data pipeline visualization

**Content:**
- Data & Feature Engineering I
- CS 401R · Lecture 05 · Thursday, September 17, 2026
- Ingestion patterns · Data quality · Feature engineering · The Zillow lesson

**Figure:** *Data flow diagram from source to Feature Store.* Raw data sources (CSV files, database icon, clickstream events) on the left, flowing through transformation stages (Glue ETL box, validation checkpoint, feature computation box) into the SageMaker Feature Store on the right. Color gradient from gray (raw) to blue (processed) to gold (features). Each pipeline stage has an annotation: "Schema validated here," "Nulls handled here," "Feature versioned here." Arrows indicate both batch and streaming paths.

**Notes:** Assign Lab 2 at the end of class today. Open with: "Lab 1 is due Saturday. I trust it's under control. Today we start Lab 2's intellectual foundation: data pipelines. Everything we build on top of NorthStar's platform — the churn model, the RAG system, the agent — is only as good as the data that feeds it."

---

## Slide 2 — Why Data Engineering for AI Is Different
**Layout:** Contrast table: Analytics vs. AI data requirements

**Content:**
**Analytics Data Engineering:**
- Goal: accurate aggregations for dashboards and reports
- Quality bar: "close enough" — a slight data quality issue affects a chart's accuracy but doesn't break anything
- Freshness: hourly or daily is usually fine
- Schema changes: tolerable; the BI tool adapts

**AI Data Engineering:**
- Goal: features that preserve signal across training, evaluation, AND production inference
- Quality bar: exact — a label-encoding difference between training and production breaks the model silently
- Freshness: depends on use case; churn model may need nightly; fraud detection may need sub-second
- Schema changes: dangerous — the model was trained on the old schema; retraining required

**The critical difference is that AI data pipelines produce inputs for models, not reports. Models cannot "handle" bad data gracefully — they silently make worse predictions.**

**Figure:** *Side-by-side pipeline comparison.* Left: Analytics pipeline (data → Glue → Redshift → dashboard). One path, simple, all in blue. Right: AI pipeline (data → ingestion validation → Glue → data quality check → feature engineering → Feature Store → training → evaluation → inference). Multiple checkpoints, two paths (training and serving), data quality gates at each step. The complexity difference is visually obvious. Labels on the right diagram highlight: "Training/serving consistency enforced here," "Quality gate here," "Schema versioned here."

**Notes:** "When a report shows a slightly wrong number, someone notices and the analyst fixes the query. When a model receives data that violates an implicit assumption made during training, it silently makes worse predictions — and nobody notices until the churn rate goes up or the business analyst flags something weeks later." This slide establishes the motivation for the rigor we apply to data engineering in this course.

---

## Slide 3 — The Three Ingestion Patterns
**Layout:** Three-column comparison with timing, use cases, and trade-offs

**Content:**
**Pattern 1: Batch Ingestion**
- Timing: scheduled (hourly, daily, weekly)
- Tools: AWS Glue, AWS DMS, S3 batch
- NorthStar use: customer records, transaction history (nightly), product catalog (weekly)
- Trade-off: simple, cheap, high latency; model decisions are based on data up to [batch cadence] old

**Pattern 2: Micro-Batch (Near-Real-Time)**
- Timing: every few minutes (5-15 min windows)
- Tools: Kinesis Data Firehose → S3 → Glue Streaming, or AWS EMR
- NorthStar use: clickstream data aggregated every 10 minutes for session features
- Trade-off: moderate complexity and cost; acceptable latency for many use cases

**Pattern 3: Streaming (Real-Time)**
- Timing: sub-second, event-driven
- Tools: Kinesis Data Streams, Lambda, SageMaker Feature Store streaming ingest
- NorthStar use: agent interaction events (customer sends message → agent state updated immediately)
- Trade-off: highest complexity and cost; required for any real-time inference use case

**Figure:** *Three-lane pipeline timeline.* Horizontal timeline with three swim lanes (Batch, Micro-Batch, Streaming). Each lane shows data events (vertical marks) and processing triggers (horizontal bars). Latency labels on right side: Batch (minutes to hours), Micro-Batch (5-15 min), Streaming (milliseconds). NorthStar data source icons placed in the lane appropriate for each source. Color: Batch in navy, Micro-Batch in teal, Streaming in amber/gold.

**Notes:** "NorthStar uses all three patterns. The churn prediction model needs transaction history — batch is fine, latency of up to 24 hours is acceptable. The clickstream features for the RAG system benefit from micro-batch. The agent needs real-time event state — streaming is required." The cost implication: each step to the right (batch → micro-batch → streaming) roughly doubles complexity and cost. "Use the slowest pattern that meets the business requirement."

---

## Slide 4 — NorthStar Data Sources: What We're Working With
**Layout:** Data source inventory table with schema overview

**Content:**
**NorthStar Simulated Data Sources (Lab 2 starter kit):**

| Source | Format | Size | Update Frequency | Sensitivity |
|--------|--------|------|-----------------|------------|
| `customers.csv` | CSV | 250K rows | Weekly | PII (name, email, address) |
| `transactions.parquet` | Parquet | 4.5M rows (18 months) | Daily | Financial (purchase amounts) |
| `clickstream.parquet` | Parquet | 12M events (90 days) | Streaming (10-min micro-batch) | Behavioral |
| `store_events.csv` | CSV | 15K rows (12 months) | Weekly | Internal |
| `product_catalog.json` | JSON | 12K SKUs | Weekly | Internal |
| `policy_docs/` | Text/PDF | 48 documents | Ad hoc | Internal |

**PII handling requirement:** Customer names, emails, and physical addresses must be masked or excluded from any feature that goes into model training. Use customer_id as the join key.

**Figure:** *Data source inventory visual.* Six data source icons (file-type styled) arranged in two rows. Each icon labeled with source name, format badge, row count, and sensitivity level (red = PII, amber = Financial, green = Internal). Arrows from each source point to the appropriate ingestion pattern lane (batch/micro-batch/streaming). A "PII Alert" badge on customers.csv with a note: "Mask PII before feature engineering."

**Notes:** "These are the six data sources you'll work with in Lab 2. The starter kit on Canvas provides the full synthetic datasets. You should spend 30-60 minutes this week just exploring the data — schema, distributions, null rates, outliers. Stage 2 (Discover Data) work, done informally, before you start building the pipeline."

---

## Slide 5 — Data Quality as an Engineering Discipline
**Layout:** Quality dimensions with detection and remediation approaches

**Content:**
**Seven Data Quality Dimensions (for AI pipelines):**

1. **Completeness:** Are all expected records present? Are null values acceptable or problematic?
2. **Accuracy:** Do values reflect reality? (Hard to verify without ground truth, but outliers reveal errors)
3. **Consistency:** Same customer_id format across sources? Same date format? Same product_id namespace?
4. **Timeliness:** Is the data fresh enough for the model's decision horizon? (Churn model needs 30-day lookback)
5. **Validity:** Do values fall within expected ranges? (Age 250 is not valid; transaction amount -$5,000 needs explanation)
6. **Uniqueness:** No duplicate records in training data — duplicates inflate apparent model confidence
7. **Schema conformance:** Do all records match the expected schema? Schema drift is a silent model killer.

**Operational quality gate:** Every Glue ETL job must emit quality metrics to CloudWatch. Anomalies trigger alerts before data reaches the Feature Store.

**Figure:** *Quality scorecard template.* A table showing the seven quality dimensions as rows. Columns: Dimension, Metric Used, Threshold, Check Frequency, Action if Failed. Filled in with NorthStar-specific examples: Completeness (null rate < 1% on customer_id), Timeliness (data age < 26 hours for daily batch), Schema Conformance (zero schema violations allowed). Green checkmarks and red warning icons in an "example audit result" column. This template becomes part of the Lab 2 deliverable.

**Notes:** "Data quality is not a data science concern — it is an engineering responsibility. If the pipeline produces bad features, the model trains on bad features, and nobody knows until the model fails in production." Practical advice: "In Lab 2, build your quality checks into the Glue job itself — not as a separate validation step. Every transformation should emit a metric. Every anomaly should trigger an alert. This is not extra credit — it's part of the pipeline design."

---

## Slide 6 — The Zillow Cautionary Tale
**Layout:** Case study narrative with timeline and financial impact

**Content:**
**Zillow Offers: A $569 Million Data Engineering Failure**

**What Zillow was trying to do:** Use ML to predict home values and buy/sell homes at scale (iBuying). The "Zestimate" model was central to every offer price.

**What went wrong (data engineering dimension):**
- The Zestimate model was trained on historical market data from normal market conditions
- During COVID-19, the housing market behaved unlike anything in the training data
- The model was extrapolating far outside its training distribution — without any guardrail detecting this
- Data drift detection: absent. Quality monitoring: insufficient. Distribution shift alerts: none.
- Result: Zillow was buying homes at prices far above market value — the model couldn't see that the market had changed

**The financial outcome:** Zillow shut down iBuying in November 2021, wrote down $569M, and laid off 25% of its workforce.

**The lesson:** Data drift is not a theoretical concern. It is a business risk. Your monitoring infrastructure must include distribution shift detection — or you're flying blind.

**Figure:** *Zillow case study timeline.* Horizontal timeline from 2018 (iBuying launch) to 2021 (shutdown). Key events marked: 2018 launch, 2020 COVID impact on market (red marker: "Distribution shift begins"), 2021 Q3 inventory buildup visible, 2021 Q4 shutdown ($569M write-down). Below the timeline: a line chart showing Zestimate prediction error over time — flat 2018-2020, spiking dramatically 2020-2021. A shaded region labeled "Model operating outside training distribution." The visual tells the whole story at a glance.

**Notes:** "This is not an exotic failure mode. This is what happens when you deploy a model without adequate data drift monitoring and the world changes. NorthStar's churn model faces the same risk — customer behavior during a recession, a competitor entering the market, or a major product change could shift the distribution that the model was trained on. Your Lab 6 drift detection is not an afterthought. It is the Zillow lesson applied."

---

## Slide 7 — Data Contracts: Governing What Flows Between Systems
**Layout:** Data contract template with example

**Content:**
**What is a Data Contract?**
- A formal, versioned agreement between a data producer and a data consumer specifying: schema, semantics, quality constraints, and SLAs
- The data engineering equivalent of an API contract
- Without data contracts, pipeline breakages are discovered at the point of failure, not at the source

**NorthStar Data Contract example (transactions → feature engineering):**
```yaml
name: northstar-transactions-v2
producer: data-engineering-team
consumer: ml-engineering-team
schema:
  customer_id: {type: string, nullable: false, format: "NS-[0-9]{8}"}
  transaction_date: {type: date, nullable: false, format: "YYYY-MM-DD"}
  amount_usd: {type: float, nullable: false, min: 0.01, max: 50000}
  store_id: {type: string, nullable: false}
  product_category: {type: string, enum: [Electronics, Apparel, Home, Sports, Beauty]}
quality_constraints:
  null_rate_max: 0.001   # max 0.1% nulls on any field
  duplicate_rate_max: 0.0  # zero duplicates tolerated
sla:
  freshness: "< 26 hours"  # data must arrive within 26 hours of transaction date
versioning: semantic  # v2.1.0 minor changes OK; v3.0 requires consumer migration
```

**Lab 2 deliverable:** A data contract document for the transactions → feature engineering pipeline.

**Figure:** *Data contract document visual.* The YAML contract above rendered as a clean document with colored section headers (Schema in blue, Quality in amber, SLA in teal). A green "Contract Status" badge: "Active · v2.1.0 · Signed by both teams." A versioning history table shows v1.0 (launch), v1.5 (added the product_category field), and v2.0 (added anes SLA requirement). The document looks like an actual engineering contract, not a homework template.

**Notes:** "A data contract is what you write when you stop treating data quality as someone else's problem. In Lab 2, you'll write a contract for your transactions pipeline. This forces you to think: what does the downstream consumer (the churn model) actually need from this data? What quality guarantees does it require? If those guarantees aren't met, the pipeline should fail loudly — not silently deliver bad data."

---

## Slide 8 — Glue ETL: The NorthStar Transformation Engine
**Layout:** Glue architecture diagram with job types and NorthStar-specific jobs

**Content:**
**AWS Glue in the NorthStar Platform:**

**Glue Data Catalog:** Central metadata repository for all NorthStar data assets. Every table, schema, and partition is registered here. SageMaker Feature Store, Athena, and Redshift all read from this catalog.

**Glue ETL Jobs (Lab 2 requirement: at least 2 jobs):**
- **Job 1: `customer-feature-extraction`** — reads `customers.csv` from raw S3, applies PII masking, computes demographic features (tenure_days, loyalty_tier_numeric), writes to processed S3
- **Job 2: `transaction-aggregation`** — reads `transactions.parquet`, aggregates by customer_id over 30/60/90 day windows (total_spend_30d, transaction_count_60d, avg_basket_90d), writes to Feature Store

**Glue Job best practices:**
- Use Glue 4.0 (Spark 3.3) — current stable version
- Bookmark jobs: track which records have been processed (avoid reprocessing)
- Monitor: emit DPU-hours consumed per job to CloudWatch for cost tracking

**Figure:** *Glue ETL architecture diagram.* Shows the Glue Data Catalog at center, connected to: S3 raw zone (input), S3 processed zone (output), SageMaker Feature Store (output), and Athena (query access). Two ETL job boxes labeled "customer-feature-extraction" and "transaction-aggregation" with arrows showing their inputs and outputs. A "Glue Crawler" icon periodically updating the Data Catalog from new S3 objects. Timestamps showing job schedules (daily for transactions, weekly for customers).

**Notes:** Glue is the transformation workhorse for NorthStar. You'll write two Glue jobs in Lab 2 — one for customer features and one for transaction aggregations. The Glue job skeleton is in the starter kit; you write the transformation logic. Practical tip: Test your Glue jobs on a 1,000-row sample before running them on the full dataset. Debugging a Glue job that consumed 4 DPU-hours on the wrong data is expensive and slow.

---

## Slide 9 — Feature Engineering Principles
**Layout:** Feature types and engineering techniques with NorthStar examples

**Content:**
**Feature Engineering: Transforming Raw Data into Model Inputs**

**Principle 1: Features should encode information the model can't learn itself**
- Don't give the model raw timestamps; give it derived temporal features (day_of_week, days_since_last_purchase, is_holiday_period)
- Don't give it raw dollar amounts; give it relative values (spend_vs_avg, basket_size_percentile)

**Principle 2: Features must be computable at inference time**
- If a feature requires data that won't be available when the model makes a real prediction, it will cause training/serving skew
- NorthStar example: using "days until customer's next purchase" as a feature — unknowable at inference time

**Principle 3: Features should be stable under distribution shift**
- Absolute counts degrade as the customer base grows; ratios and percentiles are more stable
- NorthStar example: `transactions_last_30d` is less stable than `transactions_last_30d / avg_transactions_30d_cohort`

**NorthStar Feature Examples:**
| Feature | Type | Engineering |
|---------|------|-------------|
| `tenure_days` | Raw | Days since first purchase |
| `spend_30d` | Aggregation | Sum of transaction amounts, last 30 days |
| `recency_score` | Derived | Days since last purchase, normalized 0-1 |
| `loyalty_tier` | Encoded | Ordinal encoding: Bronze=1, Silver=2, Gold=3 |
| `avg_basket_trend` | Time-series | Ratio: avg_basket_90d / avg_basket_180d |

**Figure:** *Feature engineering pipeline visualization.* Shows raw fields (transaction_date, amount_usd) being transformed into engineered features through computation blocks (aggregation, normalization, encoding). Input fields on left; transformed feature outputs on right. Color-coded: raw fields in gray, engineered features in gold. Three transformation blocks in the middle: Aggregation, Normalization, Encoding. Each with a small example formula beneath.

**Notes:** "Feature engineering is where domain knowledge becomes model signal. The NorthStar churn model isn't predicting from raw data — it's predicting from engineered signals about customer behavior over time. The quality of those features matters more than the sophistication of the model." Classic lesson: "A simple logistic regression with good features almost always outperforms a complex deep learning model with raw data."

---

## Slide 10 — SageMaker Feature Store: Online and Offline Paths
**Layout:** Feature Store architecture with dual-path diagram

**Content:**
**The Training/Serving Skew Problem (revisited):**
Training: feature computed in batch by Glue, stored in S3, loaded into notebook
Serving: feature computed differently (at inference time) → different result → model sees unfamiliar input

**The Feature Store Solution:**
Write features to the Feature Store ONCE, read them from BOTH training and inference.

**Offline Store (Training Path):**
- S3-backed, Parquet format
- Point-in-time lookup: "what were this customer's features on 2024-01-15?" → supports historical backtesting
- Used by: Training Jobs, batch evaluation

**Online Store (Inference Path):**
- DynamoDB-backed, <10ms latency
- Always returns current (latest) feature values
- Used by: Real-Time Endpoints, the Customer Service Agent

**SageMaker Feature Group (Lab 2 requirement: ≥3 feature groups):**
```python
feature_group = FeatureGroup(
    name="northstar-customer-churn-features",
    record_identifier_feature_name="customer_id",
    event_time_feature_name="event_time",
    feature_definitions=[...],
    sagemaker_session=session
)
```

**Figure:** *Feature Store dual-path diagram.* The feature computation pipeline at the top writes to the "Feature Store" (central box). From the Feature Store, two arrows split: the left arrow goes to "Offline Store (S3)" → Training Job → Model Artifact; the right arrow goes to "Online Store (DynamoDB)" → Inference Endpoint → Prediction. A "Skew Prevention" label on the Feature Store box with a checkmark. Explicit notation: "Same data, same features, both paths."

**Notes:** "The Feature Store is the architectural solution to training/serving skew. Once you write features here, you guarantee that training and serving use exactly the same feature values for the same point in time. Without a Feature Store, this consistency requires manual engineering discipline — and it always breaks eventually." Lab 2 deliverable: at least 3 feature groups, including the churn prediction features that Lab 3 will use.

---

## Slide 11 — Data Lineage: The Audit Trail
**Layout:** Lineage graph for the NorthStar churn model

**Content:**
**What is Data Lineage?**
The complete history of where data came from, how it was transformed, and what consumed it — traceable from the final model prediction back to the raw source record.

**Why lineage matters for AI:**
- Debugging: "The model's churn predictions dropped 8% last week. What changed?"
- Compliance: "Which customers' data was used to train this model?" (GDPR data subject access rights)
- Reproducibility: "I want to retrain the exact same model from 3 months ago. Which data snapshot was used?"
- Incident response: "A bug in the Glue job corrupted one week of transaction data. Which model versions are affected?"

**NorthStar Lineage Example:**
```
transactions.parquet (raw) 
  → customer-feature-extraction (Glue job v2.3, 2026-09-15)
    → northstar-customer-churn-features (Feature Group v1.5)
      → churn-xgboost-v12 (Training Job, 2026-09-18)
        → model-package-churn-v12 (Model Registry, approved 2026-09-19)
          → northstar-churn-endpoint-prod (Endpoint, deployed 2026-09-20)
```

**Lab 2 deliverable:** Data lineage diagram showing this complete chain for the NorthStar churn pipeline.

**Figure:** *Data lineage DAG.* A directed acyclic graph (DAG) showing the lineage from the raw source to the model endpoint. Each node is a distinct shape: cylinders for data stores, rectangles for transformation jobs, hexagons for models. Edge labels show transformation version and date. The "transactions.parquet" source node connects through 4 transformation nodes to the final "churn-endpoint-prod" node. Visual design: nodes in distinct colors by type, edges with timestamp annotations. This is a real Glue Data Catalog-style lineage diagram.

**Notes:** "The lineage diagram for Lab 2 is the answer to every data debugging question you'll ever be asked. When something goes wrong — and it will — you start at the symptom (wrong prediction) and trace back through the lineage to find the root cause." Lineage tools: AWS Glue has basic lineage. For more comprehensive lineage, teams use OpenLineage (open standard) with Marquez. For this course, the lineage diagram in your Lab 2 report is manually constructed from your pipeline design.

---

## Slide 12 — Lab 2 Assigned: Data & Feature Engineering
**Layout:** Lab assignment slide (orange header)

**Content:**
**Lab 2: Data & Feature Engineering**
- **Assigned:** Today, Thursday, September 17
- **Due:** Saturday, October 3, midnight
- **Builds on:** Lab 1 (your S3 structure and IAM roles from Lab 1 are the foundation)

**Key Tasks:**
1. Ingest all 6 NorthStar data sources from Canvas into your S3 `raw/` bucket
2. Write 2 Glue ETL jobs: customer feature extraction + transaction aggregation
3. Create a SageMaker Feature Store with ≥3 Feature Groups (including churn prediction features)
4. Build a data quality check framework — emit metrics to CloudWatch, alert on failures
5. Write a Data Contract for the transactions → feature pipeline
6. Produce a Data Lineage diagram for the full churn model pipeline

**Deliverable:** Working pipeline + data lineage diagram (in `docs/lab2-data-contract.md`)

**Figure:** *Lab 2 architecture diagram.* Shows the complete Lab 2 scope: 6 data sources (top) → Glue ETL jobs → S3 processed zone → SageMaker Feature Store (with 3 Feature Group icons) → Lab 3 preview (churn model training). Quality check node beside each Glue job. Lineage arrows connect all components. This diagram is both the lab overview and a preview of what they're building.

**Notes:** Assign this explicitly. "Lab 2 builds directly on Lab 1. Your S3 bucket structure from Lab 1 is the destination for your Glue ETL jobs. Your IAM DataEngineer role from Lab 1 is what the Glue jobs run as. If Lab 1 isn't clean, start there." The full NorthStar dataset is now available in the Lab 2 Canvas folder. "Spend time this weekend just exploring the data before you start writing pipeline code."

---

## Slide 13 — NorthStar Feature Design: Engineering for Churn Prediction
**Layout:** Feature design table with churn prediction rationale

**Content:**
**Churn Prediction Feature Set (v1 design):**

| Feature | Source | Engineering | Why It Matters |
|---------|--------|-------------|----------------|
| `recency_days` | transactions | Days since last purchase | High recency = high churn risk |
| `frequency_90d` | transactions | Transaction count, last 90 days | Low frequency trend = churn signal |
| `monetary_trend` | transactions | avg_basket_30d / avg_basket_90d | Declining spend = disengagement |
| `tenure_days` | customers | (today - first_purchase_date).days | Long tenure customers churn differently |
| `loyalty_tier` | customers | Ordinal: Bronze=1, Silver=2, Gold=3 | Tier predicts retention program eligibility |
| `support_contacts_30d` | interactions | Count of support contacts, 30 days | High support contact = friction signal |
| `session_frequency_7d` | clickstream | App/web sessions, last 7 days | Declining engagement precedes churn |
| `category_breadth_90d` | transactions | Count of distinct categories purchased | Narrow purchasing = single-product risk |

**RFM Framework:** Recency · Frequency · Monetary — classic churn prediction foundation

**Figure:** *RFM visualization.* Three-axis radar/spider chart showing the RFM dimensions (Recency, Frequency, Monetary) for two customer profiles: "Healthy Customer" (full radar, all three dimensions high) and "At-Risk Customer" (collapsed radar, low recency, declining frequency, declining monetary). Side-by-side comparison. Below: the derived features mapped to each RFM dimension (recency_days → Recency, frequency_90d → Frequency, monetary_trend → Monetary).

**Notes:** "The RFM framework is a proven starting point for churn prediction, used in retail analytics for decades before ML existed. We're modernizing it: instead of three buckets, we're engineering 8+ features that capture the same signals with more precision." In Lab 3, students will train the XGBoost model on these features and validate that the feature importance scores reflect the expected relationships (recency should be among the top 3 features for a well-designed churn model).

---

## Slide 14 — Common Data Engineering Mistakes in AI Projects
**Layout:** Five anti-patterns with root cause and fix

**Content:**
1. **Label leakage:** Including features in training that wouldn't be available at inference time (e.g., "did the customer contact support in the week after they churned?" — unknowable at prediction time). Result: model appears excellent in evaluation, fails completely in production.

2. **Temporal leakage:** Training on data from the future relative to the prediction target (e.g., using transaction data from after the "churn or not" label was determined). Result: inflated evaluation metrics; production performance is far worse.

3. **Inconsistent preprocessing:** Different preprocessing code at training time vs. inference time. Result: training/serving skew (why Feature Store exists).

4. **Ignoring PII in features:** Including customer name, email, or address in a feature (even hashed) without proper privacy engineering. Result: model encodes sensitive data that can be extracted through model inversion attacks.

5. **No data versioning:** Training a model, updating the dataset, then being unable to reproduce the exact model version that was approved for production. Result: compliance failure; debugging nightmare.

**Figure:** *Five danger-sign visual.* Same format as L03's anti-patterns slide. Five rows with warning icons, anti-pattern names in bold, root cause in italic, and "Fix:" in teal. PII anti-pattern has a specific badge: "GDPR violation risk." Label leakage anti-pattern has a "Silent failure" badge in red. Clean, readable checklist format.

**Notes:** "Label leakage is the most dangerous because it's the hardest to detect. The model looks perfect in evaluation and then falls apart in production — and the cause isn't obvious unless you carefully audit your feature definitions against your training/serving split." A real example from industry: a fraud detection model was trained with a feature derived from post-transaction data (whether the transaction was later reversed). The model learned to predict past chargebacks, not future ones. Evaluation AUC: 0.97. Production AUC: 0.61.

---

## Slide 15 — Data Pipeline Observability
**Layout:** CloudWatch metrics dashboard mockup for data pipelines

**Content:**
**What to monitor in a data pipeline:**

**Input Metrics (data arriving):**
- `raw_records_ingested` — count of records arriving per batch
- `raw_file_size_bytes` — file size should be consistent; dramatic changes indicate problems
- `data_freshness_hours` — hours since the last successful batch arrived

**Processing Metrics (transformation quality):**
- `null_rate_{field}` — per-field null rate; alert if > threshold
- `schema_violations` — count of records that fail schema validation; alert if > 0
- `duplicate_count` — count of duplicate records; alert if > 0
- `glue_job_duration_minutes` — job run time; spike indicates data volume growth or code regression

**Output Metrics (Feature Store health):**
- `feature_group_ingest_latency` — time from source to Feature Store; SLA = 26 hours
- `feature_freshness_hours` — how old are the features in the Online Store?
- `feature_ingest_error_rate` — failed Feature Store writes

**Figure:** *CloudWatch dashboard mockup for NorthStar data pipeline.* Four-panel dashboard: (1) records ingested per day bar chart (normal ~4,500/day, anomaly day visible at 1,200/day in amber), (2) null rate time series (flat near 0%, one spike at 0.8% labeled "Schema change detected"), (3) Glue job duration trend (stable 12 minutes, then 45 minutes → "Data volume spike"), (4) Feature freshness status (green circle: "All features fresh," last update 3h ago). Realistic CloudWatch UI aesthetic.

**Notes:** "Your Lab 2 data pipeline must emit at least 5 metrics to CloudWatch with appropriate alert thresholds. This isn't an optional extra — it's part of the grading rubric. Why? A pipeline without observability fails silently. And in a production AI system, a pipeline failure is a model performance failure is a business outcome failure."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Takeaways + Lab 2 preview + next session

**Content:**
**Key Takeaways:**
1. Data engineering for AI is fundamentally different from analytics data engineering — quality gates, feature versioning, and training/serving consistency are engineering requirements, not best practices
2. Three ingestion patterns serve different latency requirements: batch (hours), micro-batch (minutes), streaming (milliseconds) — use the slowest pattern that meets the business need
3. Features should encode domain knowledge the model can't learn itself, must be computable at inference time, and should be stable under distribution shift
4. The SageMaker Feature Store eliminates training/serving skew by providing a single source of truth for both training and inference
5. Data lineage is not documentation — it is the audit trail that enables debugging, compliance, and reproducibility

**Next Session (Tue Sep 22):**
- Topic: Data & Feature Engineering II — Feature stores deep dive, data lineage, governance, privacy, Airbnb Zipline case study
- Reading due: *Data & Feature Engineering* — "Feature Stores" through "Key Takeaways"
- Lab 2 running — start exploring the dataset this weekend

**Figure:** *Five-takeaway summary + Lab 2 countdown.* Standard format. "Lab 2 Due: Oct 3" in amber countdown box. "Next Up: Data Eng II" in teal preview box.

**Notes:** "Your Lab 1 is due Saturday. Two days from now. If you're not there yet, come to office hours tomorrow. Seriously." Then: "Lab 2 has been assigned. Spend 30-60 minutes this weekend just opening the data files and understanding what you're working with. The best pipeline engineers start by understanding the data before they write a single line of transformation code."
