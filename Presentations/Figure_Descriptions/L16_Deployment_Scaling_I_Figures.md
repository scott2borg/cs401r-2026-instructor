# L16: Deployment & Scaling I — Inference Architecture — Figures

## Slide 1 — Title

**Figure:** *Inference serving architecture overview.* Client request → API Gateway → SageMaker Endpoint (load balancer) → Instance pool (3 instances shown). One instance box expanded to show internals: Model Server, Memory-loaded model, CPU core allocation. Request/response times annotated: network: 8ms, container processing: 20ms, total: 28ms. The diagram establishes the anatomy of the serving architecture for the lecture.

---

## Slide 2 — The Inference Architecture Decision Tree

**Figure:** *Decision tree flowchart.* Binary decision tree with three levels: Real-time/Batch (Level 1), Traffic variability (Level 2, real-time branch), Number of models (Level 3). Each leaf node: endpoint type with NorthStar example. Four outcome leaves: Standard endpoint, Auto-scaling endpoint, Batch Transform, Serverless Inference. The decision tree is clean, readable, and actionable.

---

## Slide 3 — Serverless Inference: The Low-Traffic Option

**Figure:** *Serverless vs. instance-based cost comparison.* Dual-axis chart. X-axis: requests per minute (0 to 500). Y-axis: hourly cost. Serverless line: starts at $0 (when idle), rises linearly with request rate, flattens at $0.15/hr at 500 req/min. Instance-based (1× ml.m5.large) line: flat at $0.115/hr regardless of load. Intersection point: ~200 req/min. "Serverless better" region (left of intersection), "Instance-based better" region (right). The crossover communicates: choose based on load profile.

---

## Slide 4 — Async Inference: The Middle Ground

**Figure:** *Async inference flow diagram.* Client → POST to endpoint (returns immediately with job handle) → SageMaker queue. Background: SageMaker pulls from queue → processes → writes to S3. SNS notification fires → client reads result from S3. Timeline: client wait time = near-zero (just the POST). Processing time: 1-5 min (async). Contrasts with synchronous: client blocks for entire processing duration.

---

## Slide 5 — Multi-Model Endpoints: Serving at Scale

**Figure:** *Multi-model endpoint architecture diagram.* Single SageMaker endpoint with two instances. Model cache in each instance: up to 4 models loaded in memory simultaneously. S3 model library: 5 model artifacts (churn-NE, churn-SE, churn-MW, churn-SW, churn-PAC). Request comes in with target_model header → endpoint routes to correct model → if model not in cache (cache miss) → load from S3 (cold load: ~2-5 seconds). The diagram shows: MME = shared infrastructure with dynamic model routing.

---

## Slide 6 — Inference Optimization: Reducing Latency and Cost

**Figure:** *Latency optimization waterfall.* Four bars: Baseline (28ms), ONNX (21ms, -25%), c5 instance (18ms, -36%), Feature caching (12ms, -57%). Each step labeled with the optimization applied and % improvement. Horizontal SLA line at 200ms — all optimizations well within SLA. Secondary chart: cost/1M requests showing parallel reduction. The visual story: each optimization layers on the previous, compounding improvements.

---

## Slide 7 — SageMaker Inference Recommender

**Figure:** *Inference Recommender scatter plot.* X-axis: cost/hour. Y-axis: P99 latency (ms). Each instance type plotted as a labeled dot. Horizontal line: P99 SLA (200ms). Vertical line: cost budget ($0.20/hr). "Ideal zone" highlighted (bottom-left quadrant). ml.c5.large in ideal zone, labeled "Recommended." ml.t2.medium above SLA line (fail). ml.c5.2xlarge right of cost budget line. The scatter plot is exactly the output format of Inference Recommender.

---

## Slide 8 — Load Testing AI Endpoints

**Figure:** *Load test results chart.* X-axis: requests per minute (0 to 120). Y-axis (left): P99 latency (ms); Y-axis (right): error rate (%). Two series: Latency (rises from 85ms at 10 req/min to 210ms at 90 req/min, SLA violation zone marked). Error rate (near 0% up to 80 req/min, spikes at 90+ req/min). Auto-scaling trigger point marked at 70 req/min — latency stays below SLA because scaling engages before saturation. The chart validates: auto-scaling keeps the endpoint within SLA under expected peak load.

---

## Slide 9 — SageMaker Model Monitor: Production Quality Gates

**Figure:** *Model Monitor pipeline diagram.* SageMaker Endpoint (with data capture at 20%) → captured data to S3. Daily: Monitor Processing Job reads captured data + training baseline → computes PSI for each feature → compares to constraints → if violation: CloudWatch alert fires. Alert connects to SNS notification and retraining trigger (optional). Clean operational flow showing the automated surveillance loop.

---

## Slide 10 — Drift Detection: Reading the Monitor Output

**Figure:** *Drift report dashboard.* Model Monitor output shown as a feature table with: feature name, baseline mean/std, current mean/std, PSI value, status (green/red). monetary_30d row highlighted in red (violation). Below: time series chart of monetary_30d mean over 90 days, showing the seasonal Q4 spike. Annotation: "Expected Q4 seasonal spike — adjust threshold." The visual communicates: drift must be interpreted in context, not acted on mechanically.

---

## Slide 11 — Scaling Bedrock: Throughput and Cost Management

**Figure:** *Bedrock cost tracking dashboard.* Daily cost chart (last 30 days): Offer Generation ($2.90/day average), Agent Sessions ($7.60/day average), Total ($10.50/day average). Budget alert line: $60/day. All days well below alert. Week of Oct 13 highlighted: cost spike to $18.50/day — investigation: NorthStar ran agent load tests that week. The chart communicates: proactive budget monitoring catches cost anomalies before they become surprises.

---

## Slide 12 — The Inference Cost Model: Optimizing at Scale

**Figure:** *Cost scaling chart.* Three bars (Current, 10× scale, 10× scale optimized). Each bar stacked by cost component (Churn endpoint, Batch, RAG, Agent). Colors: Churn (teal), Batch (small, barely visible), RAG (orange), Agent (red). At a 10× scale, RAG and Agent together account for 95% of the cost. Optimization bar shows RAG and Agent shrinking significantly. The visual communicates: optimize where the money is.

---

## Slide 13 — Deployment Anti-Patterns: The Production Hall of Shame

**Figure:** *Five-anti-pattern Hall of Shame board.* Five cards, each: anti-pattern name, icon (red X), one-sentence story, and "Fix" in green. "Friday Big Bang" card has a cartoon calendar with Friday crossed out. Clean, memorable format. The "Hall of Shame" framing communicates: these are real failure modes, not theoretical risks.

---

## Slide 14 — Lab 4 Final Preparation: Common Issues

**Figure:** *Lab 4 final checklist.* Six checkbox items (from above) with status indicators: 3 checked (assuming typical student progress), 3 unchecked. Tips for each unchecked item. "Time estimate to complete: 4-6 hours from a working SageMaker Pipeline." Encouragement tone: "You've got this."

---

## Slide 15 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Lab 4 countdown (4 days, red urgency). Cost scaling chart thumbnail. Inference architecture decision tree thumbnail.
