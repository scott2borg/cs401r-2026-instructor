---
lecture: L23
title: AI Economics — Cost, ROI & FinOps
date: Thursday, November 19, 2026
week: 12
arc: Operate
reading_due: "AI Economics — Cost Model through ROI Frameworks"
lab_assigned: "Lab 7 — Economics & Business Value (due Sat Dec 5)"
lab_due: "Lab 6 due Sat Nov 22 (3 days)"
slides_target: 16
---

# L23: AI Economics — Cost, ROI & FinOps
**Thursday, November 19, 2026 | CS 401R: Engineering Production AI Systems | Fall 2026**

> Every AI system is a capital allocation decision. Someone is spending money to build and run it. Someone is supposed to benefit. The gap between those two statements is the business case — and building it with rigor is one of the most valuable skills an AI engineer can have.

**Reading Due:** *AI Economics* — "Cost Model" through "ROI Frameworks"
**Lab 7 Assigned Today:** Economics & Business Value — due Sat Dec 5
**Lab 6 Due:** Sat Nov 22 (3 days)

---

## Slide 1 — Title
**Layout:** Left dark panel + right ROI equation visual

**Content:**
- AI Economics: Cost, ROI & FinOps for Enterprise AI
- CS 401R · Lecture 23 · Thursday, November 19, 2026
- ⚠️ Lab 7 Assigned Today — The Final Lab

**Figure:** *AI ROI equation visual.* Large centered equation: ROI = (Value Created − Cost) / Cost × 100%. Below: two scales (like a balance). Left scale: "Cost" — stacked elements (Compute, Storage, Data Engineering, Model Development, Inference, Operations). Right scale: "Value" — stacked elements (Churn Reduction, Offer Revenue Lift, Agent Cost Savings, Operational Efficiency). The balance tips toward Value, communicating: well-designed enterprise AI creates more value than it costs. The margin is the ROI.

**Notes:** "AI Economics is the lens that connects everything we've built to the business that paid for it. We've spent 12 weeks building a platform. Today we ask: was it worth it? And, more importantly, how do you know? The ability to answer that question with rigor and data is what makes AI leaders, not just AI engineers. Lab 7 is your economic analysis of the NorthStar platform."

---

## Slide 2 — The Full AI Cost Taxonomy
**Layout:** Complete AI cost breakdown with NorthStar estimates

**Content:**
**The Seven Cost Categories of Enterprise AI:**

**Category 1 — Development costs (one-time):**
- Problem scoping and requirements: 40 hours × $150/hr = $6,000
- Data engineering (Lab 2 equivalent): 80 hours = $12,000
- Model development (Lab 3): 60 hours = $9,000
- Platform setup (Lab 1 equivalent): 40 hours = $6,000
- Total development: ~$33,000 for NorthStar (simplified course estimate)

**Category 2 — Infrastructure costs (ongoing):**
- SageMaker endpoints (churn, real-time): ~$100/month
- Batch Transform (monthly scoring): ~$2.25/month
- Bedrock inference (offers + agent): ~$320/month
- Feature Store + Glue ETL: ~$30/month
- Model Monitor + CloudWatch: ~$15/month
- CodePipeline + CodeBuild: ~$17/month
- Total infrastructure: ~$484/month

**Category 3 — Operational costs (ongoing):**
- Model monitoring and review: 4 hours/week × $150/hr = $600/month
- Incident response: 2 incidents/month × 4 hours = $1,200/month
- Weekly operations review: 2 hours × $150/hr = $300/month
- Total operational: ~$2,100/month

**Category 4 — Maintenance and retraining:**
- Quarterly retraining runs: 4 × $2.24 compute + 10 hours engineering = $1,500/year = $125/month
- Drift-triggered retraining: 2-4/year × 8 hours each = $1,800/year = $150/month
- Total maintenance: ~$275/month

**Total NorthStar AI Platform Cost: ~$2,859/month | ~$34,308/year**
(Plus ~$33,000 one-time development amortized over 3 years = $11,000/year)
**Annualized total (3-year amortization): ~$45,308/year**

**Figure:** *Cost breakdown donut chart.* Donut chart with four segments: Development (one-time, amortized): 24%; Infrastructure: 13%; Operations: 55%; Maintenance: 8%. The dominance of operational costs (55%) is striking and important. A second mini-chart: infrastructure breakdown (Bedrock inference accounts for 66% of the infrastructure). The charts communicate: AI costs are primarily people costs (operations), not compute costs.

**Notes:** "The 55% operational cost share is the number that surprises most students. Teams focus on compute costs because those are the AWS bills. But the real cost driver is engineering time: monitoring, incident response, retraining, model review. This is why the automation investments in Labs 4-6 are economically justified — they reduce the share of operational costs. Automate the operational work, and you change this pie chart dramatically."

---

## Slide 3 — Infrastructure Cost Modeling: AWS Pricing Deep Dive
**Layout:** Detailed AWS cost model for NorthStar

**Content:**
**AWS Pricing for NorthStar AI Platform:**

**SageMaker Costs:**
```
Real-time Endpoint (churn prediction):
  Instance: ml.c5.large = $0.110/hr
  Hours/month: 720 (24×30)
  Monthly: $79.20

  Auto-scaling: adds 0-3 instances during peak
  Estimated peak: 2× instance × 2 hours/day × 30 days = $6.60
  Monthly endpoint cost: ~$86

Batch Transform (monthly scoring):
  Instances: 2× ml.m5.xlarge = $0.23/hr each = $0.46/hr
  Duration: 45 minutes = 0.75 hours
  Monthly: $0.46 × 0.75 = $0.35 per run × 1 run/month = $0.35

SageMaker Pipelines + Processing (CI/CD runs):
  ~8 pipeline runs/month
  Per run: ~$2.80 (Processing + Training + Evaluation)
  Monthly: ~$22.40

Model Monitor (daily monitoring job):
  ml.m5.xlarge × 20 min/day × 30 days = 10 hours/month
  $0.23/hr × 10 hr = $2.30/month
```

**Bedrock Costs:**
```
Offer Generation (Claude 3.5 Sonnet):
  5,000 offers/day × 30 days = 150,000 offers/month
  Input tokens: 1,500 per offer × $3/1M = $0.0045/offer
  Output tokens: 300 per offer × $15/1M = $0.0045/offer
  Per offer: $0.009 | Monthly: 150,000 × $0.009 = $1,350
  With prompt caching (-80% input): ~$750/month

Customer Service Agent (Claude 3.5 Sonnet):
  847 sessions/day × 30 days = 25,410 sessions/month
  Avg: 3,000 input tokens + 800 output tokens per session
  Cost: ($3/1M × 3,000 + $15/1M × 800) = $0.009 + $0.012 = $0.021/session
  Monthly: 25,410 × $0.021 = $533.61
```

**Figure:** *AWS cost breakdown table.* Itemized bill format: each service with unit cost, usage, and monthly total. Bold line: "Total Infrastructure: $484/month." Comparison: "With all optimizations (prompt caching, spot for batch): $318/month." Savings: $166/month ($1,992/year). The table format mirrors what students will see in the AWS Cost Explorer.

**Notes:** "Bedrock Prompt Caching for the offer generation system saves approximately $600/year at NorthStar's current volume. At 10× scale (50,000 offers/day), the savings are $6,000/year. Prompt caching is the highest-value single optimization for token-heavy LLM systems. The engineering effort to implement it is 2-4 hours; the payback period is measured in days."

---

## Slide 4 — FinOps for AI: Managing Cloud AI Costs
**Layout:** FinOps practices specific to AI workloads

**Content:**
**FinOps for AI: The Discipline of Cloud Cost Management**

FinOps (Financial Operations) for cloud AI goes beyond watching the AWS bill. It's the practice of connecting every dollar of AI spend to business value created.

**The FinOps Toolkit for AI Teams:**

**1. Cost allocation tags:**
```terraform
# Every NorthStar resource tagged for cost allocation
resource "aws_sagemaker_endpoint" "churn" {
  tags = {
    Project     = "NorthStar"
    System      = "churn-prediction"
    Environment = "production"
    CostCenter  = "retention-marketing"
    Team        = "ml-platform"
  }
}
```

With cost allocation tags, the retention marketing team sees exactly how much the churn model costs to operate. They own the cost; they see the ROI.

**2. AWS Budgets with alerts:**
```python
# Budget: $600/month for Bedrock (inference)
budgets_client.create_budget(
    AccountId=AWS_ACCOUNT_ID,
    Budget={
        'BudgetName': 'northstar-bedrock-monthly',
        'BudgetLimit': {'Amount': '600', 'Unit': 'USD'},
        'BudgetType': 'COST',
        'TimeUnit': 'MONTHLY',
        'CostFilters': {'Service': ['Amazon Bedrock']}
    },
    NotificationsWithSubscribers=[{
        'Notification': {
            'NotificationType': 'ACTUAL',
            'ComparisonOperator': 'GREATER_THAN',
            'Threshold': 80  # Alert at 80% of budget
        },
        'Subscribers': [{'SubscriptionType': 'EMAIL', 'Address': 'ml-lead@northstar.internal'}]
    }]
)
```

**3. Cost-per-value tracking (the FinOps goal):**
Track: cost per offer generated, cost per churn prediction, cost per agent session resolved.
Connect to: revenue per offer accepted, revenue retained per churn prediction, cost saved per agent resolution.
Result: cost/value ratio per AI system — the key FinOps metric.

**4. Unit economics review (monthly):**
- Review cost/prediction, cost/session, and cost/offer monthly
- Alert if unit economics trends worsen (cost increasing faster than value)

**Figure:** *FinOps dashboard for NorthStar.* Three-panel dashboard. Panel 1: cost by service (Bedrock vs. SageMaker vs. other) as a trend line over 6 months. Panel 2: cost per unit by system (cost/prediction, cost/session, cost/offer) with historical trend. Panel 3: monthly budget utilization by budget (Bedrock: 82% of $600; SageMaker: 65% of $200; other: 40% of $100). Panel 2 is the key FinOps metric — cost per unit must be stable or declining as you optimize.

**Notes:** "Cost allocation tags are the first FinOps practice to implement, and they have a powerful organizational side effect: when the retention marketing team sees 'churn prediction: $86/month' on their cost report, they become stakeholders in the AI system's efficiency. Before cost tags, AI costs were an invisible IT expense. After cost tags are in place, business teams own their AI costs and have an incentive to monitor them. This changes the conversation from 'IT spends money on AI' to 'marketing's AI investment returns 77× ROI.'"

---

## Slide 5 — The ROI Framework: From Cost to Value
**Layout:** Complete ROI calculation methodology

**Content:**
**Building the AI ROI Case:**

ROI for enterprise AI requires measuring both cost (which you control) and value (which you must measure carefully).

**The ROI Framework:**

**Step 1: Define the unit of value**
What does this AI system produce that has business value?
- Churn Model: identifies at-risk customers for retention outreach
- Offer Generation: produces personalized offers that increase acceptance rate
- Agent: resolves customer service issues without a human agent

**Step 2: Measure the value per unit**
- Churn model: a retained customer is worth (average customer lifetime value × probability of long-term retention) - (intervention cost)
- Offer generation: incremental revenue from personalized offer vs. generic offer
- Agent: cost savings from AI resolution vs. human agent cost

**Step 3: Count the units produced per month**
- Churn: 166 customers retained/month (derived in L20 metric chain)
- Offers: 150,000 generated; 30,000 accepted (20%); average $15 incremental revenue per accepted offer
- Agent: 847 sessions/day × 0.917 resolution rate = 777 sessions resolved/day without human agent

**Step 4: Value = units × value per unit**
- Churn: 166 customers × $287 avg annual value ÷ 12 months = $3,971/month
- Offers: 30,000 accepted × $15 incremental revenue = $450,000/month
- Agent: 777 sessions × ($8 human cost - $0.021 AI cost) = $6,179/day = $185,370/month

**Total monthly value: $639,341**
**Total monthly cost: $2,859**
**Monthly ROI: ($639,341 - $2,859) / $2,859 = 22,273% return**

**Figure:** *ROI waterfall chart.* Starting from $0, three value bars (Churn: +$3,971, Offers: +$450,000, Agent: +$185,370), then one cost bar (-$2,859). Final position: +$636,482 net monthly value. Total ROI percentage labeled on the chart. The chart makes the dominance of offer generation value immediately visible. "The offer system generates 70% of total platform value."

**Notes:** "The offer generation value of $450,000/month seems large — and it is. It's the economic argument that justifies the entire NorthStar AI platform. But challenge this number: is the $15 incremental revenue actually *incremental*, or would some customers have bought anyway? This is why the A/B test matters: the 20% acceptance rate, minus the baseline 12% generic acceptance rate, means only 8% of offer recipients are *incremental* buyers. Adjust: 150,000 × 8% × $15 = $180,000/month. The offer system is still the biggest value driver — just at half the naive estimate."

---

## Slide 6 — The Hidden Costs of AI: Technical Debt
**Layout:** AI technical debt taxonomy and quantification

**Content:**
**The Hidden Costs: What Doesn't Show Up on the AWS Bill**

**Technical debt categories in AI systems:**

**1. Model debt:** Shortcuts taken in model development that accumulate over time
- Skipping segment evaluation → missing performance gaps; discovered during incident
- Skipping calibration → business decisions based on uncalibrated probabilities
- No MLflow tracking → can't reproduce previous experiments; restarting from scratch costs $40K+ in engineering time
- Estimated NorthStar model debt (if Labs were skipped): $60K in future correction costs

**2. Data debt:** Problems in the data foundation
- No feature contracts → upstream schema changes break downstream models silently
- No lineage tracking → data incident takes days to trace to source
- No data quality gates → corrupted data reaches training
- Estimated NorthStar data debt (if Lab 2 best practices skipped): $45K in future data incident costs

**3. Operational debt:** Absence of operational controls
- No CI/CD → manual deployments; each deployment costs 4 engineering hours
- No monitoring → drift detected months after onset; $25K/incident recovery cost
- No canary → a bad deployment takes down 100% of traffic; $50K average incident
- Estimated NorthStar operational debt (if Labs 4-6 skipped): $120K/year in incident costs

**The total technical debt cost:** ~$225K in expected annual incident and recovery costs if NorthStar were built without the engineering practices in this course.
**The total lab investment:** ~$33K in development time.
**Technical debt reduction ROI:** ~7× return on investment in engineering rigor.

**Figure:** *Technical debt vs. engineering rigor cost curve.* Same structure as L12 Slide 15 (testing the debt cost curve), but for the full engineering-rigor investment. X-axis: time (months 0-24). Two lines: "With rigor (this course's approach)" — upfront investment ($33K at month 0), then low maintenance costs. "Without rigor" — low upfront, but incident costs accelerating, crossing the "with rigor" line at month 4. By month 24: "without rigor" is $228K more expensive. The curve makes the ROI of engineering rigor concrete.

**Notes:** "The technical debt calculation is the argument you make to a time-pressured manager who says 'just ship the model, skip the testing and monitoring.' The answer: 'Skipping the engineering practices saves $33K upfront but costs $228K over 24 months in incident recovery. The net cost of shipping fast is $195K. I'd like to propose we spend the $33K instead.' Present it as a business decision, not an engineering preference."

---

## Slide 7 — Cost Optimization: Where to Focus
**Layout:** Cost optimization strategies with NorthStar impact estimates

**Content:**
**NorthStar Cost Optimization Roadmap:**

**High-ROI optimizations (implement first):**

**1. Bedrock Prompt Caching** — Impact: -$600/year at current scale
- Implementation: Add `cache_control` headers to system prompt
- Effort: 2-4 hours
- Payback period: < 1 month

**2. SageMaker Savings Plans** — Impact: -20-30% on compute
- Commit to 1 or 3 years of SageMaker usage → get a 20-30% discount
- For NorthStar: $86/month endpoint → $60-69/month with Savings Plan
- Savings: $17-26/month; $204-312/year
- Effort: 15 minutes to purchase in AWS Console

**3. Spot Instances for Training** — Impact: -60-80% on training compute
- Training jobs are interruption-tolerant (SageMaker handles spot interruptions automatically)
- Training spot price (ml.m5.xlarge): ~$0.065/hr vs. on-demand $0.23/hr
- Savings on 4 quarterly retrains: $0.17/hr × 2 hr × 4 = $1.36/year (small at this scale)
- At 10× scale (weekly retraining): $1.36/week × 52 = $70/year savings

**4. Response Length Optimization** — Impact: -15% on Bedrock costs
- Current: max_tokens=512 for offers; average output: 380 tokens (75% utilization)
- Optimize: max_tokens=400; should reduce average output to 330 tokens (-13%)
- Savings: 150,000 offers × 50 tokens × $15/1M = $112.50/month

**5. Multi-model Endpoint for Regional Models** — Impact: -20% if scaling regionally
- Applicable when NorthStar deploys regional churn models
- Current scale: not applicable; future scale: significant

**Figure:** *Cost optimization impact vs. effort matrix.* X-axis: Implementation effort (hours). Y-axis: Annual savings ($). Four labeled dots: Prompt Caching ($600/year, 4 hours), Savings Plans ($312/year, 0.25 hours), Response Length ($1,350/year, 8 hours), Spot Training ($70/year, 4 hours). "High ROI zone" quadrant (low effort, high savings). Savings Plans in the ideal zone: highest ROI, minimal effort. The matrix guides which optimization to do first.

**Notes:** "SageMaker Savings Plans is the 'free money' optimization — 15 minutes of work in the AWS Console saves 20-30% on all SageMaker compute costs for the next 1-3 years. At NorthStar scale, the savings are modest ($312/year). At 10× scale, the savings are $3,120/year. At enterprise scale (1000× SageMaker usage), the savings are 6-figure annually. This is the optimization that enterprise FinOps teams spend significant time on."

---

## Slide 8 — The AI Investment Decision Framework
**Layout:** Framework for AI investment decisions

**Content:**
**When to Invest More in AI (and When to Stop)**

Not every AI investment is worth making. Use this framework to evaluate AI investments:

**The AI Investment Decision Matrix:**

| Business Problem | AI Approach | Estimated Value | Estimated Cost | ROI | Decision |
|----------------|-------------|-----------------|---------------|-----|---------|
| Churn prediction | XGBoost model | $47K/year | $5K/year | 840% | ✅ Built |
| Offer personalization | RAG (Bedrock) | $2.16M/year | $9K/year | 23,900% | ✅ Built |
| Customer service automation | Bedrock Agent | $2.2M/year | $6.4K/year | 34,275% | ✅ Built |
| Inventory forecasting (potential) | Time-series ML | $500K/year | $80K/year | 525% | 🔄 Evaluate |
| Fraud detection (potential) | XGBoost | $1.2M/year | $30K/year | 3,900% | ✅ High priority |
| Store layout optimization (potential) | Simulation AI | $200K/year | $500K/year | -60% | ❌ Don't build |

**The decision criteria:**
- ROI < 100%: Stop. Don't build.
- ROI 100-500%: Evaluate carefully. Consider timeline, risk, and alternatives.
- ROI > 500%: Build. Prioritize based on ROI and strategic alignment.
- ROI > 5000%: This is either wrong (revisit assumptions) or a genuinely transformative opportunity.

**Figure:** *ROI vs. strategic alignment 2×2 matrix.* X-axis: ROI (Low to High). Y-axis: Strategic alignment (Low to High). Four quadrants: High ROI + High Strategic Alignment (Build immediately, NorthStar's three systems), High ROI + Low Strategic Alignment (Build if capacity allows), Low ROI + High Strategic Alignment (Fund with reduced scope), Low ROI + Low Strategic Alignment (Don't build). NorthStar's three current systems plotted in the upper-right quadrant. Store layout AI in lower-left. Fraud detection in upper-right. The matrix guides AI portfolio investment.

**Notes:** "The store layout optimization example (negative ROI) is worth discussing. The technology exists to use AI for store layout optimization. The cost is high because it requires spatial data integration, store simulation, and the operational changes are expensive to implement. The $200K value estimate is plausible but the $500K cost makes it a negative-ROI project at current scale. At 400 stores with 10× traffic, the value scales linearly but the cost doesn't — it might become positive ROI. The framework tells you: not now, maybe later."

---

## Slide 9 — Total Cost of Ownership: The 3-Year View
**Layout:** 3-year TCO model for NorthStar AI platform

**Content:**
**NorthStar AI Platform: 3-Year Total Cost of Ownership**

**Year 1 (Build + Early Operations):**
- Development: $33,000 (one-time)
- Infrastructure: $484/month × 12 = $5,808
- Operations: $2,100/month × 12 = $25,200 (high: new system, more incidents)
- Maintenance: $275/month × 12 = $3,300
- Total Year 1: $67,308

**Year 2 (Maturation):**
- Development: $10,000 (improvements, new features)
- Infrastructure: $484/month × 12 = $5,808 (stable)
- Operations: $1,500/month × 12 = $18,000 (lower: team expertise, runbooks, automation)
- Maintenance: $275/month × 12 = $3,300
- Total Year 2: $37,108

**Year 3 (Optimized Operations):**
- Development: $15,000 (new AI capabilities — e.g., fraud detection)
- Infrastructure: $420/month × 12 = $5,040 (optimizations implemented)
- Operations: $1,200/month × 12 = $14,400 (further automation, team efficiency)
- Maintenance: $275/month × 12 = $3,300
- Total Year 3: $37,740

**3-Year TCO: $142,156**

**3-Year Value Created:**
- Year 1: $639,341/month × 6 months (ramp-up) = $3,836,046
- Year 2: $639,341/month × 12 = $7,672,092
- Year 3: $750,000/month × 12 (growth) = $9,000,000
- **3-Year Total Value: $20,508,138**

**3-Year ROI: ($20.5M - $142K) / $142K = 14,334%**

**Figure:** *3-year TCO vs. value chart.* Stacked bar chart (3 years). TCO bars (cost): Year 1 ($67K), Year 2 ($37K), Year 3 ($38K). Value bars (benefit): dwarfs the cost bars visually — Year 1 ($3.8M), Year 2 ($7.7M), Year 3 ($9M). The cost bars are barely visible compared to the value bars. Net value annotation: $20.5M cumulative. The visual communicates: for well-designed enterprise AI, value creation is orders of magnitude larger than cost.

**Notes:** "The 14,334% 3-year ROI is a real number for enterprise AI when the use cases are well-chosen. The offer personalization system alone — if the incremental revenue estimate is accurate — generates returns that most companies would consider exceptional. This is why AI investment in enterprise is accelerating: the ROI for well-scoped, well-implemented AI is genuinely extraordinary. The risk is poor scoping, poor implementation, or both — which is why the engineering rigor in this course matters."

---

## Slide 10 — Lab 7 Overview: The Economics Lab
**Layout:** Lab 7 complete requirements and structure

**Content:**
**Lab 7: AI Economics & Business Value Analysis**
*(Assigned Today | Due Sat Dec 5 | 16 days)*

**What Lab 7 builds on:**
Lab 7 doesn't build new AWS infrastructure — it analyzes the NorthStar platform you've already built and generates the economic case for it.

**Part 1: Cost Analysis (required)**
- Pull actual AWS Cost Explorer data for your NorthStar account (or use provided estimates)
- Complete the cost taxonomy: infrastructure + estimated operational costs
- Produce a monthly cost breakdown by service and by system (using cost allocation tags from Lab 1)
- Calculate: cost per prediction, cost per offer generated, cost per agent session

**Part 2: Value Analysis (required)**
- Build the metric chain: technical metric → operational metric → business metric for each system
- Estimate value per unit using the methodology from L24 (next session)
- Calculate monthly value created by each system
- Produce a combined ROI calculation

**Part 3: Optimization Recommendations (required)**
- Identify the top 3 cost optimization opportunities for NorthStar
- For each: effort estimate, cost savings, implementation plan
- Recommendation ranked by ROI

**Part 4: FinOps Implementation (required)**
- Add cost allocation tags to all remaining untagged resources (Terraform)
- Set up AWS Budget with alerts (3 budgets: per-system monthly spend)
- Create a simple cost dashboard in CloudWatch (daily spend by service)

**Part 5: Executive Briefing (required)**
- 1-page business case for NorthStar AI platform
- Audience: NorthStar CFO
- Include: 3-year TCO, 3-year value, ROI, key risks, recommendation

**Figure:** *Lab 7 deliverables diagram.* Five deliverable boxes arranged as a flow: Cost Analysis → Value Analysis → Optimization Recommendations → FinOps Implementation → Executive Briefing. Final deliverable (Executive Briefing) presented as a document cover: "NorthStar AI Platform: Investment Analysis for CFO Review." The flow communicates: Lab 7 builds from analysis (Parts 1-2) to recommendations (Part 3) to implementation (Part 4) to communication (Part 5).

**Notes:** "The Executive Briefing (Part 5) is the most important deliverable in Lab 7 — and possibly in the entire course. It's the document that demonstrates whether you can synthesize technical and business understanding into a single page that a C-suite executive can read and act on. One page. Not 10 pages of methodology. Not raw numbers. One page that says: here's what we built, here's what it costs, here's what it returns, here's the recommendation. Practice this skill — you'll use it your entire career."

---

## Slide 11 — FinOps in Practice: AWS Cost Explorer
**Layout:** AWS Cost Explorer walkthrough for NorthStar cost analysis

**Content:**
**Using AWS Cost Explorer for Lab 7 Part 1:**

**Finding your costs:**
```python
# AWS Cost Explorer API for programmatic cost retrieval
ce = boto3.client('ce', region_name='us-east-1')

response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': '2026-11-01',
        'End': '2026-11-30'
    },
    Granularity='MONTHLY',
    Filter={
        'Tags': {
            'Key': 'Project',
            'Values': ['NorthStar']
        }
    },
    GroupBy=[
        {'Type': 'TAG', 'Key': 'System'},  # Cost per system
        {'Type': 'DIMENSION', 'Key': 'SERVICE'}  # Cost per service
    ],
    Metrics=['BlendedCost']
)

# Output: cost breakdown by system and service
for result in response['ResultsByTime'][0]['Groups']:
    system = result['Keys'][0]
    service = result['Keys'][1]
    cost = float(result['Metrics']['BlendedCost']['Amount'])
    print(f"{system} / {service}: ${cost:.2f}")
```

**Expected output for NorthStar (November):**
```
churn-prediction / Amazon SageMaker: $108.43
churn-prediction / Amazon CloudWatch: $3.21
offer-generation / Amazon Bedrock: $743.18
agent / Amazon Bedrock: $534.67
platform / Amazon S3: $4.32
platform / AWS Glue: $8.10
Total November: $1,401.91
```

**Figure:** *AWS Cost Explorer dashboard screenshot-style mockup.* Bar chart by service (SageMaker: $108; CloudWatch: $3; Bedrock: $1,278; S3: $4; Glue: $8). Color-coded by system tag. "Bedrock dominates (91% of variable costs)" annotation. Trend line showing 3 months of costs: October ($1,350), November ($1,402), December (projected at $1,480 — holiday traffic increase). The mockup looks exactly like AWS Cost Explorer output, preparing students for the actual tool.

**Notes:** "When you run this for your actual NorthStar account, you'll see slightly different numbers depending on your Lab 3 option (whether you built RAG, Agent, or both) and how much you've been testing. Lab 7 Part 1 asks you to use your actual Cost Explorer data. If you've been running everything for Labs 1-6, you should have 2-3 months of cost history to work with."

---

## Slide 12 — The Business Case Structure
**Layout:** Business case document structure for executive audiences

**Content:**
**Writing the AI Business Case (Lab 7 Part 5):**

A business case for AI investment follows a standard structure:

**Section 1 — Executive Summary (3 sentences max):**
"The NorthStar AI Platform (churn prediction, offer personalization, customer service AI) delivers an estimated $639K/month in combined business value at a fully-loaded cost of $2,859/month — a 224× return. Over 3 years, the platform is projected to generate $20.5M in retained revenue and cost savings against a total investment of $142K. We recommend continued investment and expansion to fraud detection and inventory forecasting."

**Section 2 — Investment Required:**
- What was built, at what cost
- 3-year TCO breakdown

**Section 3 — Value Created:**
- Value per system with methodology
- Total value vs. cost comparison

**Section 4 — Risk Assessment:**
- What could go wrong (model degradation, data quality, regulatory change)
- Mitigation controls in place (monitoring, canary, governance)

**Section 5 — Recommendation:**
- Continue? Expand? Reduce? Kill?
- Specific next investment recommended (if any)

**The test for a good business case:**
"Would the CFO fund or continue this based solely on this document?" If yes: the business case is complete.

**Figure:** *Business case document layout.* Single page with five sections. Each section: title, 2-3 sentences, one supporting number or chart (thumbnail). Clean, professional, minimal design. At the bottom: "ROI: 224×" in large, bold type — the number that makes the case. The one-page format communicates: executives don't read appendices; the summary must contain everything that matters.

**Notes:** "The 'would the CFO fund this?' test is not rhetorical. Get a business-minded friend or family member to read your executive briefing and ask them: if you were the CFO of a retailer, would you continue funding this platform based on this document? If they hesitate or ask clarifying questions, the document hasn't done its job. Iterate until the answer is an unambiguous yes — and they understand why."

---

## Slide 13 — Sensitivity Analysis: Stress-Testing the Business Case
**Layout:** Sensitivity analysis for ROI assumptions

**Content:**
**Stress-Testing the Business Case: What If You're Wrong?**

ROI calculations are built on estimates. Good business cases include sensitivity analysis — what happens to the ROI if key assumptions differ from expectations?

**NorthStar Key Assumptions and Sensitivities:**

**Assumption 1: Offer incremental acceptance rate = 8% (above 12% generic baseline)**
- Optimistic: 12% incremental → value increases by 50%
- Pessimistic: 3% incremental → value decreases by 62%
- Break-even: 0.4% incremental → offer system just breaks even

**Assumption 2: Agent resolution rate = 91.7% (777 sessions/day resolved by AI)**
- Optimistic: 95% resolution → +3.6% value
- Pessimistic: 70% resolution → -23% value
- Break-even: 0.3% resolution (virtually impossible to fail this test)

**Assumption 3: Churn model intervention effectiveness = 32%**
- Optimistic: 50% → churn value increases 56%
- Pessimistic: 15% → churn value decreases 53%
- Break-even: 0.3% effectiveness (model barely needs to work)

**The sensitivity table:**

| Scenario | Offer Value | Agent Value | Churn Value | Total Value | ROI |
|---------|------------|------------|------------|-------------|-----|
| Pessimistic | $90K/month | $135K/month | $1.9K/month | $227K/month | 79× |
| Base case | $180K/month | $185K/month | $4K/month | $369K/month | 129× |
| Optimistic | $540K/month | $192K/month | $6K/month | $738K/month | 258× |

**Even in the pessimistic case: ROI is 79× — strongly positive.**

**Figure:** *Tornado chart (sensitivity analysis).* Horizontal bar chart showing impact of each assumption on total monthly value. Bars extend left (pessimistic) and right (optimistic) from a center line (base case value: $369K/month). Longest bar: offer incremental acceptance rate (dominant uncertainty). Shortest bar: agent resolution rate (low uncertainty). The tornado shape communicates: focus your estimation effort on the variables with the longest bars — those are the assumptions that matter most.

**Notes:** "The tornado chart reveals where the business case uncertainty lives. In NorthStar's case, the offer incremental acceptance rate is the dominant uncertainty — it drives most of the ROI variance. This is the assumption you should invest in validating through A/B testing. The agent resolution rate is highly certain (it's directly observable), so it contributes little uncertainty. Invest your validation effort where the tornado bar is longest."

---

## Slide 14 — AI Portfolio Management: Beyond a Single System
**Layout:** Portfolio view of enterprise AI investments

**Content:**
**Managing an AI Portfolio: The Enterprise Perspective**

At enterprise scale, you're not managing one AI system — you're managing a portfolio of AI investments, each with different ROIs, risks, and strategic importance.

**NorthStar AI Portfolio (current + planned):**

| System | Status | Monthly Value | Monthly Cost | ROI | Priority |
|--------|--------|--------------|--------------|-----|----------|
| Churn Prediction | Production | $4K | $86 | 4,553% | Maintain |
| Offer Generation | Production | $180K | $750 | 24,000% | Expand |
| Customer Service Agent | Production | $185K | $534 | 34,643% | Expand |
| Fraud Detection | Proposed | $100K est. | $2,500 est. | 3,900% est. | Build next |
| Inventory Forecasting | Proposed | $40K est. | $8,000 est. | 400% est. | Evaluate |
| Store Layout AI | Proposed | $16K est. | $40K est. | -60% est. | Don't build |

**Portfolio management principles:**
1. **Retire underperformers:** If churn model ROI dropped to < 200%, evaluate retirement
2. **Double down on winners:** Offer generation and agent have extraordinary ROI — invest in scaling them
3. **Stage new investments:** Fraud detection looks promising — build an MVP; validate ROI before full build
4. **Kill losers fast:** Store layout AI has negative ROI at current scale — don't start

**Figure:** *AI Portfolio bubble chart.* X-axis: Monthly Cost. Y-axis: Monthly Value. Bubble size: strategic importance. Three existing systems in upper-left quadrant (high value, low cost). Fraud detection in mid-right (medium value, medium cost). Inventory forecasting in lower-right (lower value, higher cost). Store layout AI below the break-even line. Break-even line (diagonal: value = cost) divides the chart. Portfolio manager labels: "Scale Up" (existing systems), "Evaluate" (fraud), "Pilot" (inventory), "Pass" (store layout).

**Notes:** "The portfolio view is what a VP or CAIO sees when they look at AI investment. They're not looking at one model — they're allocating capital across a portfolio of AI opportunities. Being able to present the portfolio view — with each system's ROI, cost, and strategic priority — is how ML engineers get invited into strategy conversations instead of just execution conversations."

---

## Slide 15 — What You'll Compute in Lab 7
**Layout:** Lab 7 specific computations walkthrough

**Content:**
**Lab 7 Part 1: Cost Analysis — The Exact Computation**

For each NorthStar AI system, compute:

**Cost per prediction (Churn):**
- Monthly predictions: 500K (batch) + ~15K (real-time estimates)
- Monthly infrastructure cost: $86 (endpoint) + $0.35 (batch) + $5 (Glue ETL share) + $2.30 (Monitor) = $93.65
- Cost per prediction: $93.65 / 515,000 = $0.000182/prediction = $0.018 per 100 predictions

**Cost per offer generated (Offer Generation):**
- Monthly offers: 150,000
- Monthly cost: $750 (Bedrock with caching)
- Cost per offer: $750 / 150,000 = $0.005/offer

**Cost per session resolved (Agent):**
- Monthly sessions: 25,410
- Sessions resolved without human: 23,301 (91.7%)
- Monthly cost: $534
- Cost per resolved session: $534 / 23,301 = $0.0229/resolved session

**Lab 7 Part 2: Value Analysis — The Metric Chain**
- Use the metric chain from L20 Slide 13 (AUC → recall → intervention coverage → effectiveness → revenue retained) for the churn system
- Build equivalent chains for offers (acceptance rate → incremental revenue) and agent (resolution rate → cost savings)
- Document your assumptions explicitly — this is what makes your business case credible

**Figure:** *Unit economics table.* Three-column table: Churn, Offers, Agent. Rows: Monthly volume, Monthly cost, Cost per unit, Value per unit, Value/Cost ratio. Clean presentation of the unit economics. "Value/Cost ratio" row shows: Churn 22×, Offers 240×, Agent 348×. The table is the core of Lab 7's economic analysis.

**Notes:** "The Value/Cost ratio per unit is the most powerful number in the business case. When you tell the CFO 'every dollar spent on offer generation returns $240 in value,' that's a number they can act on — 'double the offer budget.' The per-unit analysis is what makes AI investment decisions precise rather than gut-feel. Build the habit of computing and tracking unit economics for every AI system you build."

---

## Slide 16 — Key Takeaways + What's Next
**Layout:** Takeaways + L24 preview

**Content:**
**Key Takeaways:**
1. Enterprise AI cost has seven categories: development, infrastructure, operations, maintenance, technical debt, compliance, and hidden costs — operational costs (people) typically dominate compute costs
2. FinOps for AI requires cost allocation tags, per-system budgets, and unit economics tracking — connect every dollar of spend to a dollar of value
3. ROI must be computed from first principles: define value per unit → count units → multiply; document assumptions and stress-test with sensitivity analysis
4. The AI portfolio view: manage AI as a capital allocation portfolio with explicit ROI, risk, and strategic priority for each investment
5. Technical debt has calculable cost: skipping engineering rigor costs $225K/year in incidents for NorthStar; the rigor costs $33K — a 7× debt reduction ROI

**Next Session (Tue Nov 24):**
- Topic: Measuring Business Value — connecting AI metrics to business outcomes; the last full lecture before project workshops
- Reading due: *AI Economics* — "Business Value Measurement" through "Key Takeaways"
- **Lab 6 due Saturday** — 3 days
- **Lab 7 running** — 16 days; start Part 1 (Cost Explorer analysis) this weekend

**Figure:** *Five-takeaway summary card.* Lab 6 countdown (3 days, red). Lab 7 countdown (16 days, amber). ROI waterfall chart thumbnail. TCO vs. value chart thumbnail (value bar dwarfs cost bar).

**Notes:** "Lab 6 is due in 3 days. Is everything submitted? Check the checklist: Model Monitor data capture, baseline created, monitoring schedule configured, alarm active, retraining Lambda, compliance report Lambda, unified dashboard. If any of these are missing, that's your weekend. After Saturday: Lab 7 and project work. The final project workshop is in 2 weeks — come with a complete platform, not a work in progress."
