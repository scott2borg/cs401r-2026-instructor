---
tags:
  - cs401r
  - sample-solution
  - lab6
  - monitoring
  - slos
  - cloudwatch
  - drift-detection
  - runbooks
lab_number: 6
status: complete
created: 2026-07-06
---

# Lab 6 — Monitoring & Reliability (Solution Notes)

## Key Decisions Made and Why

### Decision 1: Five-layer monitoring framework, not ad hoc metrics

The five-layer framework (Infrastructure → Pipeline → Model → Application → Business) is a structured way to ensure that monitoring covers every failure mode. Without a framework, students typically instrument only the layers they know how to monitor:
- Pure infrastructure teams monitor CPU and memory
- ML teams monitor AUC and drift
- Neither monitors the pipeline or business layers

The framework forces a question at each layer: "What breaks here that doesn't show up in the layer above?" The answer is always something:
- Infrastructure layer fails → pipeline layer fails too, but via a different alert path
- Pipeline layer fails → model layer shows stale features, but no error
- Model layer drifts → application layer outputs don't fail, they just become wrong
- Application layer produces wrong scores → business layer alert volume changes, but no system error

Each layer needs its own monitoring because failures don't always cascade visibly upward.

### Decision 2: PSI for data drift, not just KS test

Students often implement only the KS test for drift detection. KS test measures distribution shape difference — it is sensitive to any difference in the distribution. PSI (Population Stability Index) measures practical significance — the magnitude of shift that matters for model stability.

PSI thresholds have industry-accepted interpretations:
- PSI < 0.10: stable
- PSI 0.10–0.20: moderate shift — watch
- PSI > 0.20: significant shift — act

The KS test produces a p-value that depends on sample size — with 250K customers, even a trivial shift in `purchase_frequency_90d` will produce a significant KS p-value. PSI is sample-size-independent and more actionable for the retail context.

Both tests appear in the runbook, but PSI is the CloudWatch alarm trigger.

### Decision 3: Anomaly detection band for business metric alarm, not static threshold

The `NorthStar-P3-ChurnVolumeAnomaly` alarm uses CloudWatch Anomaly Detection (`ANOMALY_DETECTION_BAND`) instead of a static threshold (e.g., "alert if < 2,500 alerts"). The reason: NorthStar's customer churn rate is seasonal. A static threshold of 3,500 would alarm during every holiday promotion when churn rates naturally drop (fewer people leave during a sale).

The 2σ anomaly detection band adapts to seasonal patterns — it learns that Q4 churn rates are lower and Q1 is higher, and sets the expected range accordingly. This reduces false positives while preserving sensitivity to genuine anomalies.

### Decision 4: P2 severity for data drift, not P1

Assigning P2 (Slack + JIRA, 1-hour SLA) vs. P1 (page on-call, 15-minute SLA) to data drift requires justification. Data drift does not immediately break the system — the model continues producing predictions, they are just increasingly unreliable. P1 would be appropriate only if:
- Drift is severe enough that predictions are likely wrong (PSI > 0.30 on multiple features)
- The drift is combined with a pipeline failure (see the composite alarm)

The composite alarm (`NorthStar-P1-PipelineAndDriftDegradation`) escalates to P1 when both Glue failure AND drift are present simultaneously — this pattern indicates a data incident, not just seasonal variation.

### Decision 5: SLO error budget, not just SLO targets

The SLO table includes error budgets per month and per quarter, with specific deployment freeze triggers. This is the operational consequence of the SLO — not just a number, but a decision rule.

Example: Availability SLO = 99.5%. Error budget = 0.15 failed runs per month (30 runs × 0.005). The freeze trigger is "2 consecutive failed transforms in 7 days." Without the freeze trigger, a team could exhaust their annual error budget in January and spend the rest of the year trying to catch up.

---

## How Each Rubric Item Is Satisfied

### Five-Layer Monitoring Architecture
- `monitoring/dashboards/northstar-dashboard.json` contains all 5 layers with labeled section headers
- Each layer has a text widget explaining what it monitors and why
- Metrics chosen are appropriate to each layer (not just infrastructure metrics in all widgets)

### CloudWatch Dashboard JSON
- Valid JSON — widgets array with correct CloudWatch Dashboard schema
- All required widget properties: type, x, y, width, height, properties.title, properties.metrics
- Alarm ARNs embedded in metric widgets for visual alarm state in dashboard
- Annotations on all threshold-sensitive widgets (PSI alert line, duration SLO line, etc.)

### Custom Business Metrics Publisher
- `monitoring/custom_metrics.py` publishes 6 metrics (not just the 4 minimum)
- Includes `ImplausibleSpikeDetected` as a sixth metric — the deployment safety check as a monitoring signal
- Input validation: empty DataFrame check, column check, out-of-range score detection with warning
- Dry-run mode for CI testing
- Standalone script with argparse (callable from `canary_deploy.py` or independently)

### Six CloudWatch Alarms with Severity Tiers
- `monitoring/alerts/alerts.tf` contains 8 alarms + 1 composite alarm
- Severity tiers (P0–P3) clearly labeled in alarm_description field
- Each alarm has alarm_actions AND ok_actions (recovery notifications, not just fire notifications)
- Composite alarm demonstrates advanced pattern: multi-alarm correlation

### SLO Table (4 SLOs)
- `docs/lab6-runbook.md` Part 2 covers all 4 required SLOs
- Each SLO has: Target, SLI Definition, Monthly Error Budget, Annual Error Budget, Deployment Freeze Trigger
- Error budget calculation shown explicitly (not just "0.5%")
- Error budget burn rate concept included (not required by rubric but demonstrates mastery)

### Drift Detection Plan
- `docs/lab6-runbook.md` Part 1 covers all 3 drift types (data, concept, model degradation)
- Seasonal context (retail promotions) correctly identified as the primary driver of data drift
- Statistical tests with thresholds per feature (PSI for continuous, KS for distributions, chi-squared for categorical)
- Concept drift proxy monitoring (score distribution shift, early return rate)

### Two Complete Runbooks
- Runbook A (Data Drift): detection, triage steps with actual commands, two containment options, escalation criteria, resolution verification, post-incident actions
- Runbook B (Batch Latency Spike): same structure, includes graceful degradation option (serve yesterday's scores)
- Both runbooks include actual AWS CLI commands, not pseudocode

---

## Common Student Mistakes to Watch For

### Dashboard
- **All widgets are infrastructure metrics.** A five-layer monitoring architecture requires metrics from all five layers. A dashboard with only CPU, memory, and latency is a two-layer dashboard.
- **Invalid CloudWatch Dashboard JSON.** Missing required fields (type, x, y, width, height) will cause the dashboard to fail when imported. The JSON schema is strict.
- **No annotations on threshold widgets.** A PSI widget without a line at PSI = 0.20 is not actionable — engineers can't tell at a glance whether the metric is in the danger zone.
- **Missing alarm ARN linkage.** Without alarmArns in the metric widget properties, the dashboard doesn't show alarm state visually.

### Custom Metrics
- **Publishing metrics without dimensions.** A `DailyChurnAlertsGenerated` metric without a `RunDate` dimension cannot be queried per batch run. All custom metrics need at least one dimension.
- **Publishing metrics inside the Batch Transform loop (per-record) instead of once post-transform.** This creates 250K metric data points instead of 1, blowing the CloudWatch custom metrics cost budget.
- **No input validation.** An empty DataFrame or missing column should raise a clear ValueError, not a cryptic KeyError.

### Alerts
- **Missing ok_actions.** Alarms without ok_actions don't send recovery notifications — the team doesn't know when the incident resolved.
- **All alarms at P1 severity.** Alert fatigue from over-alarming is as dangerous as under-alarming. Data drift is P2, not P1. Business metric anomalies are P3, not P2.
- **Static threshold for seasonal business metrics.** `DailyChurnAlertsGenerated` should use anomaly detection, not a static number. A static threshold of 3,500 alarms during every holiday sale.
- **No treat_missing_data specification.** CloudWatch defaults to "missing" state for gaps. `notBreaching` is appropriate for batch metrics (no data during off-hours is healthy); `breaching` is appropriate for real-time endpoint metrics (no data means the endpoint is down).

### Runbooks
- **No actual commands.** A runbook that says "check the SageMaker console" is not a runbook — it is a suggestion. Runbooks must contain the exact command to run, with the actual metric name, namespace, and resource name.
- **No escalation criteria.** A runbook without "escalate to P1 when X" forces the on-call engineer to make a judgment call at 03:00 UTC. Bad outcomes follow.
- **No resolution verification.** A runbook that says "fix the problem" without defining what "fixed" looks like leads to premature incident closure.
- **Conflating drift types.** Data drift (input distribution changes) and concept drift (feature-to-outcome relationship changes) have different detection methods and different responses. Conflating them produces an incoherent detection plan.

---

## Key AWS Services and Patterns Used

| Service | Pattern | Why This Pattern |
|---------|---------|-----------------|
| CloudWatch Dashboard | Layer-structured widgets with alarm ARN linkage | Provides a single-pane view of system health from infrastructure to business outcomes |
| CloudWatch Custom Metrics (PutMetricData) | NorthStar/Business namespace with RunDate dimension | Enables time-series query per batch run; feeds the business-layer alarm |
| CloudWatch Anomaly Detection | ANOMALY_DETECTION_BAND for seasonal business metrics | Adapts to seasonal patterns; reduces false positives from holiday promotion effects |
| CloudWatch Composite Alarms | AND logic across Glue failure + drift alarms | Pattern-based alerting (two simultaneous signals) more actionable than single-metric alerting |
| SageMaker Model Monitor | Daily constraint violation check against baseline | Automated drift detection without custom code; publishes to CloudWatch |
| CloudWatch `extended_statistic = "p95"` | p95 on batch duration alarm | Catches worst-case behavior; average would be masked by fast runs |
| Terraform `treat_missing_data` | `notBreaching` for batch, `breaching` for real-time | Prevents false alarms during scheduled off-hours; immediate alarm when real-time endpoint goes silent |

---

## Connections to Prior Labs

- Lab 4's CI/CD pipeline (CodePipeline) is the mechanism that triggers model retraining in Runbook A, Option B
- Lab 5's canary_deploy.py calls `custom_metrics.py` after each Batch Transform — the monitoring pipeline starts at deployment
- Lab 6's SLOs inform the deployment freeze triggers in Lab 5's deployment plan — the monitoring and deployment systems are mutually dependent
- Lab 2's Feature Store is the source of the feature drift metrics monitored in Layer 3
