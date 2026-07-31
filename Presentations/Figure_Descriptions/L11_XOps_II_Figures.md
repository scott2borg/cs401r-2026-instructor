# L11: XOps II — LLMOps & AgentOps — Figures

## Slide 1 — Title

**Figure:** *LLM production pipeline with monitoring overlay.* Horizontal pipeline: User Query → Prompt Template → Context Injection (RAG) → LLM API Call → Response Filter → User Response. Below the pipeline: four monitoring overlays — latency tracker, cost meter, faithfulness evaluator, guardrail alert. Colors: pipeline steps in teal, monitoring in amber. Communicates: LLM production isn't just calling an API — it's a pipeline with operational requirements at every step.

---

## Slide 2 — Why LLMOps Is Distinct from MLOps

**Figure:** *Two-column comparison visual.* Left (MLOps): traditional model diagram with training → evaluation → deploy arc. Right (LLMOps): prompt template + RAG index + LLM API + guardrail diagram. Connecting arrow between the columns: "Both need: versioning, monitoring, CI/CD, cost governance." The differences are highlighted in the rows of the table above.

---

## Slide 3 — Prompt Engineering as an Engineering Discipline

**Figure:** *Prompt version control diagram.* Git commit history for a prompt template file. Commit messages: "v3.0: Add RULES block", "v3.1: Add INSUFFICIENT_DATA handling", "v3.2: Add citation format requirement." Branch `main` shows the production version; branch experiment/offer-v4-concise shows an A/B test in progress. Below: evaluation metric trend for each version (format compliance improving from 82% to 100% across versions).

---

## Slide 4 — RAG Index Operations: The Living Knowledge Base

**Figure:** *RAG index lifecycle diagram.* S3 knowledge base bucket → Bedrock Knowledge Base sync → Vector index. Weekly cron trigger at top. Below the index: five operational boxes: Full Re-index, Incremental Update, Emergency Update, Health Check, Rollback. Each box: frequency, trigger mechanism, approximate duration, risk level color (green/amber/red). This communicates: the index is not set-and-forget — it's an operational system with its own lifecycle.

---

## Slide 5 — LLMOps Monitoring: What to Measure

**Figure:** *LLMOps CloudWatch dashboard mockup.* Four-panel dashboard. Top-left: latency time series (P50 blue, P90 teal, P99 orange; P99 spike on Oct 3 highlighted with annotation "Bedrock throttling"). Top-right: cost bar chart by day (green bars below budget line; one day exceeds budget in amber). Bottom-left: quality trend (faithfulness and format compliance as dual line chart, both above thresholds). Bottom-right: guardrail trigger rate as area chart (mostly near-zero; spike on Oct 5 highlighted "prompt injection attempt detected"). Professional dashboard layout.

---

## Slide 6 — Guardrails: Safety in Production

**Figure:** *Guardrail flow diagram.* User Request → Input Guardrail → (if pass) → LLM → Output Guardrail → (if pass) → User Response. Two failure paths: "Input blocked" → "BLOCKED_REQUEST" response with reason code. "Output blocked" → "FILTERED_RESPONSE" response with safe fallback. Below the diagram: metrics: 0.1% of requests blocked at input; 0.05% filtered at output; 99.85% pass-through rate.

---

## Slide 7 — AgentOps: The New Frontier

**Figure:** *AgentOps monitoring layer diagram.* ReAct agent trace on left (Thought → Action → Observation → Thought → ...). On the right, four monitoring sidecars: Trace Capture (records every step), Tool Audit Log (append-only), Authority Monitor (checks each tool call against authority matrix), Loop Detector (counts tool calls per invocation). Each sidecar connects to CloudWatch. This visualizes AgentOps as a set of monitoring overlays on the agent execution trace.

---

## Slide 8 — Bedrock Agents: Trace Logging in Practice

**Figure:** *Agent trace in CloudWatch Logs Insights.* Screenshot-style mockup showing CloudWatch Logs Insights query results. Query: `fields @timestamp, trace_type, trace_data.orchestrationTrace.rationale.text | filter trace_type = 'orchestrationTrace' | sort @timestamp asc`. Results: table showing three rows — rationale text for each Thought step in the agent's ReAct trace. Demonstrates that the agent's full reasoning is captured and queryable.

---

## Slide 9 — NorthStar AgentOps: The Customer Service Agent Dashboard

**Figure:** *AgentOps operational dashboard mockup.* Six metric panels in a 2×3 grid. Top row: session duration distribution (histogram), tool calls per session (histogram), cost per session (box plot). Bottom row: 24h sessions timeline (area chart by hour), human escalation rate (gauge: green zone 5-15%), tool failure rate by tool (bar chart highlighting order_lookup_tool in amber). Two alert banners at the top in red and amber. Professional operational look.

---

## Slide 10 — The XOps CI/CD Landscape: All Four Layers

**Figure:** *Four-layer CI/CD comparison table.* Same structure as above, formatted as a visual table with four rows (DataOps, MLOps, LLMOps, AgentOps) and five columns (Trigger, Pipeline, Artifact, Rollback, Approver). Color-coded by XOps layer. The table communicates: each layer has its own CI/CD pattern, but they follow the same principles.

---

## Slide 11 — LLMOps Evaluation: Automated Quality Checks

**Figure:** *RAGAS CI/CD gate diagram.* Prompt template change in Git → trigger pipeline → RAGAS evaluation on test set (50 test cases) → metrics computed → gate check (≥0.95 / ≥0.85 / ≥0.80) → pass → production deploy / fail → alert to ML team. Sample output shown: "faithfulness: 0.97 ✅, answer_relevancy: 0.91 ✅, context_recall: 0.83 ✅ → GATE PASSED."

---

## Slide 12 — The XOps Observability Stack for NorthStar

**Figure:** *NorthStar unified monitoring dashboard architecture.* Five-section layout (matching the content above). Each section: 2-3 representative metric tiles. System-health indicators: traffic-light status for each section (all green for normal state). Total platform cost in bottom-right: "$47.23 today vs. $52.00 budget (90.8%)" in green. This is the "single pane of glass" view for the platform operator.

---

## Slide 13 — When Things Go Wrong: XOps Incident Response

**Figure:** *Incident response timeline diagram.* Three horizontal swim lanes (DataOps, MLOps, LLMOps). Each lane: a timeline from Alert to Resolved, with named steps. Time estimates: DataOps incident: 45 min typical resolution; MLOps incident: 2-4 hours; LLMOps incident: 1-2 hours. MTTR (Mean Time to Recover) shown for each layer as a metric.

---

## Slide 14 — XOps Tooling Landscape

**Figure:** *XOps tool map.* Four columns (DataOps, MLOps, LLMOps, AgentOps), each with tool cards. Cross-cutting tools at the bottom spanning all columns. Color-coded: AWS services in orange/black, open-source tools (MLflow, RAGAS, Git) in teal. This is the NorthStar technology map for XOps.

---

## Slide 15 — XOps Maturity: Where This Course Takes You

**Figure:** *XOps maturity radar chart (dual view).* Same radar chart as L10 Slide 9, now showing all four XOps layers as dimensions. After Lab 3 (light blue): strong data capabilities, weak automation. After Lab 7 (navy): full polygon approaching Level 3 on all dimensions. The visual progress between the two states tells the story of the lab sequence.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *XOps stack recap visual.* Four-layer stack (DataOps, MLOps, LLMOps, AgentOps) with the key operational tool for each layer highlighted. Five takeaways as a numbered list alongside the stack. Lab 3 countdown in amber.
