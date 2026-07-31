# L23: AI Economics — Cost, ROI & FinOps — Figures

## Slide 1 — Title

**Figure:** *AI ROI equation visual.* Large centered equation: ROI = (Value Created − Cost) / Cost × 100%. Below: two scales (like a balance). Left scale: "Cost" — stacked elements (Compute, Storage, Data Engineering, Model Development, Inference, Operations). Right scale: "Value" — stacked elements (Churn Reduction, Offer Revenue Lift, Agent Cost Savings, Operational Efficiency). The balance tips toward Value, communicating: well-designed enterprise AI creates more value than it costs. The margin is the ROI.

---

## Slide 2 — The Full AI Cost Taxonomy

**Figure:** *Cost breakdown donut chart.* Donut chart with four segments: Development (one-time, amortized): 24%; Infrastructure: 13%; Operations: 55%; Maintenance: 8%. The dominance of operational costs (55%) is striking and important. A second mini-chart: infrastructure breakdown (Bedrock inference accounts for 66% of the infrastructure). The charts communicate: AI costs are primarily people costs (operations), not compute costs.

---

## Slide 3 — Infrastructure Cost Modeling: AWS Pricing Deep Dive

**Figure:** *AWS cost breakdown table.* Itemized bill format: each service with unit cost, usage, and monthly total. Bold line: "Total Infrastructure: $484/month." Comparison: "With all optimizations (prompt caching, spot for batch): $318/month." Savings: $166/month ($1,992/year). The table format mirrors what students will see in the AWS Cost Explorer.

---

## Slide 4 — FinOps for AI: Managing Cloud AI Costs

**Figure:** *FinOps dashboard for NorthStar.* Three-panel dashboard. Panel 1: cost by service (Bedrock vs. SageMaker vs. other) as a trend line over 6 months. Panel 2: cost per unit by system (cost/prediction, cost/session, cost/offer) with historical trend. Panel 3: monthly budget utilization by budget (Bedrock: 82% of $600; SageMaker: 65% of $200; other: 40% of $100). Panel 2 is the key FinOps metric — cost per unit must be stable or declining as you optimize.

---

## Slide 5 — The ROI Framework: From Cost to Value

**Figure:** *ROI waterfall chart.* Starting from $0, three value bars (Churn: +$3,971, Offers: +$450,000, Agent: +$185,370), then one cost bar (-$2,859). Final position: +$636,482 net monthly value. Total ROI percentage labeled on the chart. The chart makes the dominance of offer generation value immediately visible. "The offer system generates 70% of total platform value."

---

## Slide 6 — The Hidden Costs of AI: Technical Debt

**Figure:** *Technical debt vs. engineering rigor cost curve.* Same structure as L12 Slide 15 (testing the debt cost curve), but for the full engineering-rigor investment. X-axis: time (months 0-24). Two lines: "With rigor (this course's approach)" — upfront investment ($33K at month 0), then low maintenance costs. "Without rigor" — low upfront, but incident costs accelerating, crossing the "with rigor" line at month 4. By month 24: "without rigor" is $228K more expensive. The curve makes the ROI of engineering rigor concrete.

---

## Slide 7 — Cost Optimization: Where to Focus

**Figure:** *Cost optimization impact vs. effort matrix.* X-axis: Implementation effort (hours). Y-axis: Annual savings ($). Four labeled dots: Prompt Caching ($600/year, 4 hours), Savings Plans ($312/year, 0.25 hours), Response Length ($1,350/year, 8 hours), Spot Training ($70/year, 4 hours). "High ROI zone" quadrant (low effort, high savings). Savings Plans in the ideal zone: highest ROI, minimal effort. The matrix guides which optimization to do first.

---

## Slide 8 — The AI Investment Decision Framework

**Figure:** *ROI vs. strategic alignment 2×2 matrix.* X-axis: ROI (Low to High). Y-axis: Strategic alignment (Low to High). Four quadrants: High ROI + High Strategic Alignment (Build immediately, NorthStar's three systems), High ROI + Low Strategic Alignment (Build if capacity allows), Low ROI + High Strategic Alignment (Fund with reduced scope), Low ROI + Low Strategic Alignment (Don't build). NorthStar's three current systems plotted in the upper-right quadrant. Store layout AI in lower-left. Fraud detection in upper-right. The matrix guides AI portfolio investment.

---

## Slide 9 — Total Cost of Ownership: The 3-Year View

**Figure:** *3-year TCO vs. value chart.* Stacked bar chart (3 years). TCO bars (cost): Year 1 ($67K), Year 2 ($37K), Year 3 ($38K). Value bars (benefit): dwarfs the cost bars visually — Year 1 ($3.8M), Year 2 ($7.7M), Year 3 ($9M). The cost bars are barely visible compared to the value bars. Net value annotation: $20.5M cumulative. The visual communicates: for well-designed enterprise AI, value creation is orders of magnitude larger than cost.

---

## Slide 10 — Lab 7 Overview: The Economics Lab

**Figure:** *Lab 7 deliverables diagram.* Five deliverable boxes arranged as a flow: Cost Analysis → Value Analysis → Optimization Recommendations → FinOps Implementation → Executive Briefing. Final deliverable (Executive Briefing) presented as a document cover: "NorthStar AI Platform: Investment Analysis for CFO Review." The flow communicates: Lab 7 builds from analysis (Parts 1-2) to recommendations (Part 3) to implementation (Part 4) to communication (Part 5).

---

## Slide 11 — FinOps in Practice: AWS Cost Explorer

**Figure:** *AWS Cost Explorer dashboard screenshot-style mockup.* Bar chart by service (SageMaker: $108; CloudWatch: $3; Bedrock: $1,278; S3: $4; Glue: $8). Color-coded by system tag. "Bedrock dominates (91% of variable costs)" annotation. Trend line showing 3 months of costs: October ($1,350), November ($1,402), December (projected at $1,480 — holiday traffic increase). The mockup looks exactly like AWS Cost Explorer output, preparing students for the actual tool.

---

## Slide 12 — The Business Case Structure

**Figure:** *Business case document layout.* Single page with five sections. Each section: title, 2-3 sentences, one supporting number or chart (thumbnail). Clean, professional, minimal design. At the bottom: "ROI: 224×" in large, bold type — the number that makes the case. The one-page format communicates: executives don't read appendices; the summary must contain everything that matters.

---

## Slide 13 — Sensitivity Analysis: Stress-Testing the Business Case

**Figure:** *Tornado chart (sensitivity analysis).* Horizontal bar chart showing impact of each assumption on total monthly value. Bars extend left (pessimistic) and right (optimistic) from a center line (base case value: $369K/month). Longest bar: offer incremental acceptance rate (dominant uncertainty). Shortest bar: agent resolution rate (low uncertainty). The tornado shape communicates: focus your estimation effort on the variables with the longest bars — those are the assumptions that matter most.

---

## Slide 14 — AI Portfolio Management: Beyond a Single System

**Figure:** *AI Portfolio bubble chart.* X-axis: Monthly Cost. Y-axis: Monthly Value. Bubble size: strategic importance. Three existing systems in upper-left quadrant (high value, low cost). Fraud detection in mid-right (medium value, medium cost). Inventory forecasting in lower-right (lower value, higher cost). Store layout AI below the break-even line. Break-even line (diagonal: value = cost) divides the chart. Portfolio manager labels: "Scale Up" (existing systems), "Evaluate" (fraud), "Pilot" (inventory), "Pass" (store layout).

---

## Slide 15 — What You'll Compute in Lab 7

**Figure:** *Unit economics table.* Three-column table: Churn, Offers, Agent. Rows: Monthly volume, Monthly cost, Cost per unit, Value per unit, Value/Cost ratio. Clean presentation of the unit economics. "Value/Cost ratio" row shows: Churn 22×, Offers 240×, Agent 348×. The table is the core of Lab 7's economic analysis.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Lab 6 countdown (3 days, red). Lab 7 countdown (16 days, amber). ROI waterfall chart thumbnail. TCO vs. value chart thumbnail (value bar dwarfs cost bar).
