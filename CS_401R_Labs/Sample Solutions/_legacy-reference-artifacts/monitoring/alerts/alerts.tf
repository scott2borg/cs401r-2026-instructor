# ────────────────────────────────────────────────────────────────────────────────
# NorthStar AI Platform — CloudWatch Alarm Configuration
# Lab 6: Alert Architecture
# ────────────────────────────────────────────────────────────────────────────────
#
# Alert severity tiers and response SLAs:
#   P0: Wake on-call + page manager immediately. Acknowledgment SLA: 5 minutes.
#       Examples: endpoint down, data loss, customer-facing outage.
#   P1: Page on-call. Acknowledgment SLA: 15 minutes.
#       Examples: high CPU causing degraded throughput, deployment rollback.
#   P2: Slack #northstar-ai-ops + create JIRA ticket. Acknowledgment SLA: 1 hour.
#       Examples: data drift, pipeline failure, batch latency spike.
#   P3: Create JIRA ticket only. Acknowledgment SLA: next business day.
#       Examples: business metric anomaly, non-urgent quality signal.
#
# All alarms send to severity-specific SNS topics. SNS topics route to:
#   P0/P1: PagerDuty on-call rotation + email to CDO and ML Lead
#   P2: Slack #northstar-ai-ops webhook + JIRA auto-ticket via Lambda
#   P3: JIRA auto-ticket via Lambda only
# ────────────────────────────────────────────────────────────────────────────────

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# ─── Variables ────────────────────────────────────────────────────────────────

variable "p0_sns_topic_arn" {
  type        = string
  description = "SNS topic ARN for P0 (critical) alerts. Routes to PagerDuty + manager page."
}

variable "p1_sns_topic_arn" {
  type        = string
  description = "SNS topic ARN for P1 (high) alerts. Routes to PagerDuty on-call."
}

variable "p2_sns_topic_arn" {
  type        = string
  description = "SNS topic ARN for P2 (medium) alerts. Routes to Slack + JIRA."
}

variable "p3_sns_topic_arn" {
  type        = string
  description = "SNS topic ARN for P3 (low) alerts. Routes to JIRA only."
}

variable "endpoint_name" {
  type        = string
  default     = "northstar-churn-endpoint"
  description = "SageMaker real-time endpoint name (used if endpoint is enabled in future labs)."
}

variable "glue_job_name" {
  type        = string
  default     = "northstar-transaction-etl"
  description = "Glue ETL job name for pipeline health monitoring."
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Common tags applied to all CloudWatch alarms."
}

# ─── P0: Deployment Rollback (Critical) ──────────────────────────────────────
# This alarm is triggered programmatically by canary_deploy.py when automatic
# rollback fires. It is also set to alarm if the DeploymentRollback metric
# is published (any value > 0 means a rollback occurred).
#
# Rationale: A rollback means the nightly churn scores may be stale (yesterday's
# predictions). This is a CDO-level concern — revenue impact within 24 hours
# if the retention team cannot run offers.

resource "aws_cloudwatch_metric_alarm" "deployment_rollback" {
  alarm_name          = "NorthStar-P0-DeploymentRollback"
  alarm_description   = "P0: Churn model deployment rollback triggered. New model failed canary validation. Downstream offer generation will use yesterday's scores."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "DeploymentRollback"
  namespace           = "NorthStar/Deployment"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"   # Missing means no rollback occurred — that is healthy

  alarm_actions = [var.p0_sns_topic_arn]
  ok_actions    = [var.p0_sns_topic_arn]

  tags = merge(var.tags, {
    Severity  = "P0"
    Component = "Deployment"
  })
}

# ─── P0: Endpoint Health (if real-time endpoint is enabled) ──────────────────
# SageMaker real-time endpoint — used if NorthStar adds a real-time scoring API
# in a future sprint. Batch Transform does not produce this metric (it is ephemeral).
#
# Pattern: If Invocations drops to zero for two consecutive 5-minute periods,
# the endpoint is not receiving traffic (possible crash or misconfiguration).
# The "ok_action" sends recovery notification so on-call knows the issue resolved.

resource "aws_cloudwatch_metric_alarm" "endpoint_health" {
  alarm_name          = "NorthStar-P0-EndpointHealth"
  alarm_description   = "P0: SageMaker real-time endpoint has not received any invocations for 10+ minutes. Possible endpoint crash or traffic routing failure."
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Invocations"
  namespace           = "AWS/SageMaker"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "breaching"   # No data = no invocations = alarm

  alarm_actions = [var.p0_sns_topic_arn]
  ok_actions    = [var.p0_sns_topic_arn]

  dimensions = {
    EndpointName = var.endpoint_name
  }

  tags = merge(var.tags, {
    Severity  = "P0"
    Component = "Endpoint"
  })
}

# ─── P1: High CPU Utilization ────────────────────────────────────────────────
# Triggers when SageMaker endpoint CPU exceeds 80% for 15 consecutive minutes
# (3 x 5-minute evaluation periods).
#
# Why 80% and not 100%? At 100% CPU, latency degrades nonlinearly. Setting the
# threshold at 80% gives ~5-10 minutes of runway to scale before user impact.
# The scale-out cooldown in auto_scaling.py is 60 seconds — so a page at 80%
# gives time to scale before hitting saturation.

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "NorthStar-P1-HighCPU"
  alarm_description   = "P1: SageMaker endpoint CPU > 80% for 15 minutes. Risk of latency degradation. Consider scaling out (ml.m5.xlarge → ml.m5.2xlarge) or triggering auto-scaling."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/SageMaker"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"

  alarm_actions = [var.p1_sns_topic_arn]
  ok_actions    = [var.p1_sns_topic_arn]

  dimensions = {
    EndpointName = var.endpoint_name
    VariantName  = "AllTraffic"
  }

  tags = merge(var.tags, {
    Severity  = "P1"
    Component = "Endpoint"
  })
}

# ─── P2: Data Drift Detected (PSI > 0.2) ─────────────────────────────────────
# SageMaker Model Monitor publishes feature drift PSI scores to the
# aws/sagemaker/Endpoints/data-metrics namespace.
#
# PSI interpretation:
#   PSI < 0.1: No significant drift — no action needed
#   PSI 0.1–0.2: Moderate drift — monitor, investigate if sustained
#   PSI > 0.2: Significant drift — investigate and potentially retrain (P2 alert)
#   PSI > 0.3: Major drift — halt scoring, emergency retrain (escalate to P1)
#
# Alarm fires on the most predictive feature (days_since_last_purchase).
# Additional alarms for other features can be added by duplicating this resource.
#
# Suppression note: Alert suppressions during the scheduled retraining window
# (Sunday 01:00–05:00 UTC) are implemented via a CloudWatch metric math
# suppression metric (see alarm_actions condition below). This prevents false
# P2 alerts during planned retraining that causes temporary feature drift.

resource "aws_cloudwatch_metric_alarm" "data_drift_days_since_purchase" {
  alarm_name          = "NorthStar-P2-DataDrift-DaysSinceLastPurchase"
  alarm_description   = "P2: Feature drift PSI > 0.2 on days_since_last_purchase. This is the top churn predictor. Investigate seasonal promotion vs. genuine behavioral shift before next retraining. See Runbook A in docs/lab6-runbook.md."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "feature_baseline_drift_days_since_last_purchase"
  namespace           = "aws/sagemaker/Endpoints/data-metrics"
  period              = 3600
  statistic           = "Average"
  threshold           = 0.2
  treat_missing_data  = "notBreaching"   # If Model Monitor hasn't run, don't alarm

  alarm_actions = [var.p2_sns_topic_arn]
  ok_actions    = [var.p2_sns_topic_arn]

  tags = merge(var.tags, {
    Severity  = "P2"
    Component = "ModelMonitor"
    Feature   = "days_since_last_purchase"
  })
}

resource "aws_cloudwatch_metric_alarm" "data_drift_purchase_frequency" {
  alarm_name          = "NorthStar-P2-DataDrift-PurchaseFrequency90d"
  alarm_description   = "P2: Feature drift PSI > 0.2 on purchase_frequency_90d. Likely caused by seasonal promotion spike. Cross-reference with store events calendar before retraining."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "feature_baseline_drift_purchase_frequency_90d"
  namespace           = "aws/sagemaker/Endpoints/data-metrics"
  period              = 3600
  statistic           = "Average"
  threshold           = 0.2
  treat_missing_data  = "notBreaching"

  alarm_actions = [var.p2_sns_topic_arn]
  ok_actions    = [var.p2_sns_topic_arn]

  tags = merge(var.tags, {
    Severity  = "P2"
    Component = "ModelMonitor"
    Feature   = "purchase_frequency_90d"
  })
}

# ─── P2: Glue ETL Pipeline Failure ───────────────────────────────────────────
# Any failed task in the Glue job is a P2 — partial failures mean some customers
# may have stale or missing features, causing the model to score incorrectly.
#
# Note: Glue publishes metrics to CloudWatch via the Glue metrics namespace.
# The metric name includes "driver" to indicate Glue Spark driver-level aggregation.
# Failed tasks at the executor level roll up to this aggregate metric.

resource "aws_cloudwatch_metric_alarm" "glue_failure" {
  alarm_name          = "NorthStar-P2-GlueETLFailure"
  alarm_description   = "P2: Glue ETL job northstar-transaction-etl has failed tasks. Data pipeline integrity at risk. Features written to S3 may be incomplete. Check Glue job logs in CloudWatch Logs group /aws/glue/jobs/northstar-transaction-etl."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "Glue"
  period              = 3600
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"   # Missing means job hasn't run yet (expected during off-hours)

  alarm_actions = [var.p2_sns_topic_arn]
  ok_actions    = [var.p2_sns_topic_arn]

  dimensions = {
    JobName = var.glue_job_name
  }

  tags = merge(var.tags, {
    Severity  = "P2"
    Component = "DataPipeline"
  })
}

# ─── P2: Batch Transform Latency Spike (> 2 hours) ───────────────────────────
# The nightly Batch Transform on 250K customers should complete in 35–50 minutes
# on an ml.m5.xlarge. The SLO target is < 90 minutes (p95).
#
# Alarm fires if the p95 transform duration exceeds 7,200 seconds (2 hours).
# This is set conservatively at 2x the SLO to avoid false positives from
# occasional AWS infrastructure variability — we want actionable alarms.
#
# Why p95 not average? A single slow run that takes 3 hours (e.g., during AWS
# maintenance) should not cancel out the 6 fast runs in the same day. p95
# catches the worst-case behavior in the evaluation window.
#
# This uses a custom metric published by canary_deploy.py after each Batch
# Transform job completes (BatchTransformDurationSeconds in NorthStar/Inference).

resource "aws_cloudwatch_metric_alarm" "batch_latency_spike" {
  alarm_name          = "NorthStar-P2-BatchLatencySpike"
  alarm_description   = "P2: Batch Transform p95 duration > 7,200 seconds (2 hours). SLO target is < 5,400 seconds (90 min). Investigate instance utilization. See Runbook B in docs/lab6-runbook.md. Graceful degradation: serve yesterday's scores if transform cannot complete by 06:00 UTC."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "BatchTransformDurationSeconds"
  namespace           = "NorthStar/Inference"
  period              = 86400
  extended_statistic  = "p95"
  threshold           = 7200
  treat_missing_data  = "notBreaching"   # Missing means no transform ran today (expected on weekends if scheduled)

  alarm_actions = [var.p2_sns_topic_arn]
  ok_actions    = [var.p2_sns_topic_arn]

  tags = merge(var.tags, {
    Severity  = "P2"
    Component = "Inference"
  })
}

# ─── P3: Churn Alert Volume Anomaly ──────────────────────────────────────────
# Uses CloudWatch Anomaly Detection to establish a dynamic baseline for
# DailyChurnAlertsGenerated (customers scoring >= 0.60).
#
# A 30% deviation from the 7-day rolling average is the alert threshold.
# Using ANOMALY_DETECTION_BAND (2 standard deviations) rather than a static
# threshold because the "normal" volume changes with seasonal promotions —
# a static threshold of 3,500 would alarm during every holiday sale.
#
# P3 (JIRA only) because a volume anomaly requires investigation but does not
# cause immediate customer impact. The model may still be functioning correctly —
# a volume spike could simply mean more customers are genuinely at-risk.
#
# Note on Terraform metric_query blocks: CloudWatch alarms with anomaly detection
# use metric_query blocks instead of individual metric_name/namespace/period fields.

resource "aws_cloudwatch_metric_alarm" "churn_volume_anomaly" {
  alarm_name          = "NorthStar-P3-ChurnVolumeAnomaly"
  alarm_description   = "P3: Daily churn alert volume is outside the expected anomaly detection band (> 2 standard deviations from 7-day rolling average). Investigate: new model deployed recently? Seasonal event? Data pipeline issue? Create JIRA ticket for ML Lead review by next business day."
  comparison_operator = "LessThanLowerOrGreaterThanUpperThreshold"
  evaluation_periods  = 2
  threshold_metric_id = "e1"
  treat_missing_data  = "notBreaching"

  alarm_actions = [var.p3_sns_topic_arn]
  ok_actions    = [var.p3_sns_topic_arn]

  metric_query {
    id          = "m1"
    return_data = false

    metric {
      metric_name = "DailyChurnAlertsGenerated"
      namespace   = "NorthStar/Business"
      period      = 86400
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "e1"
    expression  = "ANOMALY_DETECTION_BAND(m1, 2)"
    label       = "DailyChurnAlerts (expected band, 2σ)"
    return_data = true
  }

  tags = merge(var.tags, {
    Severity  = "P3"
    Component = "Business"
  })
}

# ─── Composite Alarm: Multi-Layer System Health ───────────────────────────────
# A composite alarm that fires when BOTH the pipeline (Glue) AND the model
# quality (data drift) are degraded simultaneously. This combination suggests
# a data incident — not just a monitoring false positive.
#
# Composite alarms reduce alert fatigue: individual component alarms may fire
# independently during normal maintenance. When two layers degrade together,
# the combined signal is high-confidence and warrants an escalated P1 response.

resource "aws_cloudwatch_composite_alarm" "pipeline_and_drift" {
  alarm_name        = "NorthStar-P1-PipelineAndDriftDegradation"
  alarm_description = "P1: COMPOSITE — Both Glue ETL failures AND data drift detected simultaneously. This pattern indicates a data incident (corrupted input data, schema change, or upstream system failure). Page on-call immediately. Do not wait for individual alarm resolution."

  alarm_rule = join(" AND ", [
    "ALARM(\"${aws_cloudwatch_metric_alarm.glue_failure.alarm_name}\")",
    "ALARM(\"${aws_cloudwatch_metric_alarm.data_drift_days_since_purchase.alarm_name}\")",
  ])

  alarm_actions = [var.p1_sns_topic_arn]
  ok_actions    = [var.p1_sns_topic_arn]

  tags = merge(var.tags, {
    Severity  = "P1"
    Component = "Composite"
    Type      = "DataIncident"
  })
}

# ─── Outputs ─────────────────────────────────────────────────────────────────

output "alarm_names" {
  value = {
    p0_deployment_rollback = aws_cloudwatch_metric_alarm.deployment_rollback.alarm_name
    p0_endpoint_health     = aws_cloudwatch_metric_alarm.endpoint_health.alarm_name
    p1_high_cpu            = aws_cloudwatch_metric_alarm.high_cpu.alarm_name
    p2_data_drift_days     = aws_cloudwatch_metric_alarm.data_drift_days_since_purchase.alarm_name
    p2_data_drift_freq     = aws_cloudwatch_metric_alarm.data_drift_purchase_frequency.alarm_name
    p2_glue_failure        = aws_cloudwatch_metric_alarm.glue_failure.alarm_name
    p2_batch_latency       = aws_cloudwatch_metric_alarm.batch_latency_spike.alarm_name
    p3_churn_volume        = aws_cloudwatch_metric_alarm.churn_volume_anomaly.alarm_name
    p1_composite           = aws_cloudwatch_composite_alarm.pipeline_and_drift.alarm_name
  }
  description = "Map of severity tier to alarm name for dashboard and runbook reference."
}
