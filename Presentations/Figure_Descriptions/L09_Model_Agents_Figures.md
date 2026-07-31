# L09: Model Development III — Agents — Figures

## Slide 1 — Title

**Figure:** *ReAct agent loop diagram.* A circular flow showing: Thought → Action → Observation → Thought (repeat). In the center: "Foundation Model" brain icon. Radiating outward from Action: tool boxes (Order Lookup, Policy Search, Escalation Handler, Feature Store). The loop arrows are distinct from the tool arrows. Dark navy background. Gold accent on the "Foundation Model" center node. The diagram captures the iterative, tool-using nature of agents at a glance.

---

## Slide 2 — What Is an Agent?

**Figure:** *Power-complexity spectrum.* Horizontal axis: Complexity to build and operate. Vertical axis: Task complexity the approach can handle. Four data points: Prompt (low-low), RAG (medium-medium), Function Call (low-medium), Agent (high-high). A diagonal "sweet spot" band from lower-left to upper-right. Agent sits above the band — more powerful than most tasks require. Caption: "Use the simplest approach that solves the problem."

---

## Slide 3 — The ReAct Pattern: Reasoning + Acting

**Figure:** *ReAct trace visualization.* A vertical timeline showing alternating Thought (gray bubbles) and Action+Observation pairs (blue boxes with tool name and output). Three full iterations visible. The user message at top, the final response at bottom. Each Action box shows the tool name, input, and output (truncated). Makes the iterative "think → act → observe → think" pattern concrete and readable.

---

## Slide 4 — Tool Use: Giving the Agent Reach

**Figure:** *Tool registry card layout.* Four cards (one per tool), each showing: the tool name in a bold header, a description in the body, parameters listed below, and a "when to call" guidance note at the bottom. Color-coded by risk level: order_lookup (green, low risk), policy_search (green), return_initiate (amber, requires confirmation), escalate_to_human (blue, always valid). The card format mirrors the format the foundation model receives for its tool documentation.

---

## Slide 5 — Agent Memory: Types and Architectures

**Figure:** *Memory architecture diagram.* Agent brain in center. Four memory stores around it, with arrows showing: which memory is loaded at session start (long-term), updated during session (short-term), read from context (in-context), and retrieved on demand (semantic). DynamoDB icons for short- and long-term; OpenSearch icon for semantic. Transaction labels on each arrow: "loaded once at start," "updated after each action," "retrieved by query."

---

## Slide 6 — Agent Orchestration on AWS Bedrock

**Figure:** *Bedrock Agents architecture.* User → Agent Endpoint → (Orchestrator: Claude model) → Action Group Executor → Lambda functions (for each tool) → External services (Order Management, CRM, DynamoDB). Knowledge Base connection from Orchestrator to OpenSearch. Trace output path shown going to CloudWatch. All within AWS ecosystem. Clean, official AWS architecture diagram style.

---

## Slide 7 — Failure Modes Unique to Agentic Systems

**Figure:** *Failure mode severity matrix.* Six rows, four columns: Failure Mode, Severity (color-coded badge: red/amber/green), Likelihood in Production, Mitigation. Arranged from highest to lowest severity. Prompt Injection at top in red. Each mitigation is a specific, implementable action — not a vague "add guardrails." The matrix is a practical checklist for agent production readiness.

---

## Slide 8 — Agent Testing: Why It's Harder Than Model Testing

**Figure:** *Agent testing pyramid.* Three tiers (same pyramid concept as L05 data pipeline testing, now for agents). Bottom: Tool Unit Tests (fast, many, cheap). Middle: Agent Integration Tests (scripted flows, mocked tools, deterministic). Top: End-to-End Evaluation (realistic scenarios, red team, adversarial). At each tier: test count estimate, runtime, when to run. Right side: key test types per tier.

---

## Slide 9 — Morgan Stanley AI at Scale: Case Study

**Figure:** *Morgan Stanley architecture diagram.* Advisor interface on left → Azure OpenAI (GPT-4) → Custom RAG pipeline → 100K document index. Human oversight gate shown as a review step between AI output and advisor presentation. Citation trail shown connecting every AI output to source document pages. Right side: outcome metrics (60-90 min/day saved, 2.5% hallucination rate, 100K docs). Official-looking but clearly illustrative.

---

## Slide 10 — When NOT to Use an Agent

**Figure:** *Decision tree flowchart.* Binary decision tree: "Multi-step task?" → No: "Single LLM call or RAG." → Yes: "Requires tool use or side effects?" → No: "Prompt chain / pipeline." → Yes: "Path unpredictable in advance?" → No: "Deterministic pipeline with LLM steps." → Yes: "Use an agent." NorthStar's three systems shown at appropriate leaf nodes. Clear, easy-to-follow decision path.

---

## Slide 11 — Agent Cost and Latency: The Operational Reality

**Figure:** *Cost comparison visualization.* Three columns (one per NorthStar AI system). Each column shows: cost per interaction (bubble size), P95 latency (y-axis position), and daily volume (x-axis position). Churn model: tiny bubble, low position (fast/cheap). Offer generation: medium bubble, medium position. Customer service agent: large bubble, high position (slow/expensive). Log scale on y-axis. Makes the order-of-magnitude cost differences visible at a glance.

---

## Slide 12 — Lab 3 Assigned: Model Development

**Figure:** *Lab 3 architecture diagram.* Shows the full scope: required component (churn model training flow from Feature Store through MLflow to Model Registry) in solid blue, plus two optional components in dashed teal (RAG pipeline) and dashed gold (Agent). Makes clear which is required and what the optional additions are.

---

## Slide 13 — Evaluating Agents: The Scorecard

**Figure:** *Agent scorecard.* Five-section evaluation scorecard matching the dimensions above. Each section has: metric name, target value, and a "current performance" bar (partially filled, showing realistic values close to but not always meeting targets). The scorecard format mirrors a real production operations report — this is what you'd review weekly for a production agent.

---

## Slide 14 — Agents in the Enterprise: Governance Challenges

**Figure:** *Authority matrix visual.* Three-zone horizontal band: green (Autonomous), amber (Confirm First), red (Escalate to Human). Agent actions placed in the appropriate zone. Arrows show the confirmation flow (agent proposes → customer confirms → action executes) and escalation flow (agent detects trigger → flags → human agent queue). The visual makes the authority limits immediately clear.

---

## Slide 15 — NorthStar Customer Service Agent: Complete Design

**Figure:** *NorthStar Customer Service Agent full architecture diagram.* Customer chat interface → Bedrock Agent endpoint → orchestration loop (Claude 3.5 Sonnet) → 4 action groups (each connecting to their backend services) + Bedrock Knowledge Base. DynamoDB memory stores on the side. Bedrock Guardrails shown as a shield icon on both input and output paths. CloudWatch Traces capturing the full ReAct loop. Professional AWS architecture diagram quality.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Summary table + three-system card view.* The model development summary table above, plus three small "system cards" showing each NorthStar AI system with its approach badge and lab assignment. Below: "Next Up" banner for XOps.
