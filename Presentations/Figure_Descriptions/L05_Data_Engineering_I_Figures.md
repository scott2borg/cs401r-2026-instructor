# L05: Data & Feature Engineering I — Figures

## Slide 1 — Title

**Figure:** *Data flow diagram from source to Feature Store.* Raw data sources (CSV files, database icon, clickstream events) on the left, flowing through transformation stages (Glue ETL box, validation checkpoint, feature computation box) into the SageMaker Feature Store on the right. Color gradient from gray (raw) to blue (processed) to gold (features). Each pipeline stage has an annotation: "Schema validated here," "Nulls handled here," "Feature versioned here." Arrows indicate both batch and streaming paths.

---

## Slide 2 — Why Data Engineering for AI Is Different

**Figure:** *Side-by-side pipeline comparison.* Left: Analytics pipeline (data → Glue → Redshift → dashboard). One path, simple, all in blue. Right: AI pipeline (data → ingestion validation → Glue → data quality check → feature engineering → Feature Store → training → evaluation → inference). Multiple checkpoints, two paths (training and serving), data quality gates at each step. The complexity difference is visually obvious. Labels on the right diagram highlight: "Training/serving consistency enforced here," "Quality gate here," "Schema versioned here."

---

## Slide 3 — The Three Ingestion Patterns

**Figure:** *Three-lane pipeline timeline.* Horizontal timeline with three swim lanes (Batch, Micro-Batch, Streaming). Each lane shows data events (vertical marks) and processing triggers (horizontal bars). Latency labels on right side: Batch (minutes to hours), Micro-Batch (5-15 min), Streaming (milliseconds). NorthStar data source icons placed in the lane appropriate for each source. Color: Batch in navy, Micro-Batch in teal, Streaming in amber/gold.

---

## Slide 4 — NorthStar Data Sources: What We're Working With

**Figure:** *Data source inventory visual.* Six data source icons (file-type styled) arranged in two rows. Each icon labeled with source name, format badge, row count, and sensitivity level (red = PII, amber = Financial, green = Internal). Arrows from each source point to the appropriate ingestion pattern lane (batch/micro-batch/streaming). A "PII Alert" badge on customers.csv with a note: "Mask PII before feature engineering."

---

## Slide 5 — Data Quality as an Engineering Discipline

**Figure:** *Quality scorecard template.* A table showing the seven quality dimensions as rows. Columns: Dimension, Metric Used, Threshold, Check Frequency, Action if Failed. Filled in with NorthStar-specific examples: Completeness (null rate < 1% on customer_id), Timeliness (data age < 26 hours for daily batch), Schema Conformance (zero schema violations allowed). Green checkmarks and red warning icons in an "example audit result" column. This template becomes part of the Lab 2 deliverable.

---

## Slide 6 — The Zillow Cautionary Tale

**Figure:** *Zillow case study timeline.* Horizontal timeline from 2018 (iBuying launch) to 2021 (shutdown). Key events marked: 2018 launch, 2020 COVID impact on market (red marker: "Distribution shift begins"), 2021 Q3 inventory buildup visible, 2021 Q4 shutdown ($569M write-down). Below the timeline: a line chart showing Zestimate prediction error over time — flat 2018-2020, spiking dramatically 2020-2021. A shaded region labeled "Model operating outside training distribution." The visual tells the whole story at a glance.

---

## Slide 7 — Data Contracts: Governing What Flows Between Systems

**Figure:** *Data contract document visual.* The YAML contract above rendered as a clean document with colored section headers (Schema in blue, Quality in amber, SLA in teal). A green "Contract Status" badge: "Active · v2.1.0 · Signed by both teams." A versioning history table shows v1.0 (launch), v1.5 (added the product_category field), and v2.0 (added anes SLA requirement). The document looks like an actual engineering contract, not a homework template.

---

## Slide 8 — Glue ETL: The NorthStar Transformation Engine

**Figure:** *Glue ETL architecture diagram.* Shows the Glue Data Catalog at center, connected to: S3 raw zone (input), S3 processed zone (output), SageMaker Feature Store (output), and Athena (query access). Two ETL job boxes labeled "customer-feature-extraction" and "transaction-aggregation" with arrows showing their inputs and outputs. A "Glue Crawler" icon periodically updating the Data Catalog from new S3 objects. Timestamps showing job schedules (daily for transactions, weekly for customers).

---

## Slide 9 — Feature Engineering Principles

**Figure:** *Feature engineering pipeline visualization.* Shows raw fields (transaction_date, amount_usd) being transformed into engineered features through computation blocks (aggregation, normalization, encoding). Input fields on left; transformed feature outputs on right. Color-coded: raw fields in gray, engineered features in gold. Three transformation blocks in the middle: Aggregation, Normalization, Encoding. Each with a small example formula beneath.

---

## Slide 10 — SageMaker Feature Store: Online and Offline Paths

**Figure:** *Feature Store dual-path diagram.* The feature computation pipeline at the top writes to the "Feature Store" (central box). From the Feature Store, two arrows split: the left arrow goes to "Offline Store (S3)" → Training Job → Model Artifact; the right arrow goes to "Online Store (DynamoDB)" → Inference Endpoint → Prediction. A "Skew Prevention" label on the Feature Store box with a checkmark. Explicit notation: "Same data, same features, both paths."

---

## Slide 11 — Data Lineage: The Audit Trail

**Figure:** *Data lineage DAG.* A directed acyclic graph (DAG) showing the lineage from the raw source to the model endpoint. Each node is a distinct shape: cylinders for data stores, rectangles for transformation jobs, hexagons for models. Edge labels show transformation version and date. The "transactions.parquet" source node connects through 4 transformation nodes to the final "churn-endpoint-prod" node. Visual design: nodes in distinct colors by type, edges with timestamp annotations. This is a real Glue Data Catalog-style lineage diagram.

---

## Slide 12 — Lab 2 Assigned: Data & Feature Engineering

**Figure:** *Lab 2 architecture diagram.* Shows the complete Lab 2 scope: 6 data sources (top) → Glue ETL jobs → S3 processed zone → SageMaker Feature Store (with 3 Feature Group icons) → Lab 3 preview (churn model training). Quality check node beside each Glue job. Lineage arrows connect all components. This diagram is both the lab overview and a preview of what they're building.

---

## Slide 13 — NorthStar Feature Design: Engineering for Churn Prediction

**Figure:** *RFM visualization.* Three-axis radar/spider chart showing the RFM dimensions (Recency, Frequency, Monetary) for two customer profiles: "Healthy Customer" (full radar, all three dimensions high) and "At-Risk Customer" (collapsed radar, low recency, declining frequency, declining monetary). Side-by-side comparison. Below: the derived features mapped to each RFM dimension (recency_days → Recency, frequency_90d → Frequency, monetary_trend → Monetary).

---

## Slide 14 — Common Data Engineering Mistakes in AI Projects

**Figure:** *Five danger-sign visual.* Same format as L03's anti-patterns slide. Five rows with warning icons, anti-pattern names in bold, root cause in italic, and "Fix:" in teal. PII anti-pattern has a specific badge: "GDPR violation risk." Label leakage anti-pattern has a "Silent failure" badge in red. Clean, readable checklist format.

---

## Slide 15 — Data Pipeline Observability

**Figure:** *CloudWatch dashboard mockup for NorthStar data pipeline.* Four-panel dashboard: (1) records ingested per day bar chart (normal ~4,500/day, anomaly day visible at 1,200/day in amber), (2) null rate time series (flat near 0%, one spike at 0.8% labeled "Schema change detected"), (3) Glue job duration trend (stable 12 minutes, then 45 minutes → "Data volume spike"), (4) Feature freshness status (green circle: "All features fresh," last update 3h ago). Realistic CloudWatch UI aesthetic.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary + Lab 2 countdown.* Standard format. "Lab 2 Due: Oct 3" in amber countdown box. "Next Up: Data Eng II" in teal preview box.
