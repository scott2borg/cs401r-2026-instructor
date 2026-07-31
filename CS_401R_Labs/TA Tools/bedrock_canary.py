#!/usr/bin/env python3
"""
Bedrock canary probe — CS 401R TA tooling.

Measures how long it actually takes a brand-new AWS account to get usable
Bedrock access. The answer determines whether the Pre-Lab 3 exercise window
(assigned Sep 17, due Sep 30) is long enough. Nobody knows that number yet;
this script is how we find out.

Run it repeatedly. Every run appends a timestamped row to a log, so the moment
access flips from blocked to working is captured precisely rather than
estimated.

USAGE

    # One probe, append to the log, print current status
    python3 bedrock_canary.py

    # Probe every 30 min until everything passes (or 14 days elapse)
    python3 bedrock_canary.py --watch

    # Summarize the log into the table the procedure doc asks for
    python3 bedrock_canary.py --report

    # What has Bedrock actually cost on this account
    python3 bedrock_canary.py --cost

Requires: boto3, and AWS credentials for the CANARY account (not your own).
Verify before you start:  aws sts get-caller-identity
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

try:
    import boto3
    import botocore
except ImportError:
    sys.exit("boto3 required:  pip install boto3")

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
LOG = os.environ.get("CANARY_LOG", "bedrock_canary_log.csv")

# The two models Lab 3 actually needs. Titan for embeddings (Track B corpus),
# Claude Haiku for generation (Track B offers, Track C agent reasoning).
EMBED_MODEL = "amazon.titan-embed-text-v2:0"
GEN_MODEL = "us.anthropic.claude-haiku-4-5-20251001-v1:0"   # inference profile, not bare model id

# Substrings that identify the quotas governing those models. Quota names are
# verbose and change wording occasionally, so match loosely and report what
# was found rather than assuming an exact string.
QUOTA_PATTERNS = {
    "titan_embed_tpm": ("Titan Text Embeddings V2", "tokens per minute"),
    "titan_embed_rpm": ("Titan Text Embeddings V2", "requests per minute"),
    "haiku_tpm": ("Claude Haiku 4.5", "tokens per minute"),
    "haiku_rpm": ("Claude Haiku 4.5", "requests per minute"),
}

FIELDS = [
    "timestamp_utc", "account", "embed_status", "embed_detail",
    "gen_status", "gen_detail",
    "titan_embed_tpm", "titan_embed_rpm", "haiku_tpm", "haiku_rpm",
    "all_pass",
]


def _client(name):
    cfg = botocore.config.Config(retries={"max_attempts": 1})
    return boto3.client(name, region_name=REGION, config=cfg)


def classify(exc):
    """Turn a Bedrock exception into a short, actionable label.

    The two failure modes look nothing like 'access denied', which is why
    students misdiagnose them:
      * FORM_NOT_SUBMITTED - Anthropic use-case form outstanding
      * QUOTA_ZERO         - 'Too many tokens per day' actually means the
                             daily allowance is zero, not exhausted
    """
    name = type(exc).__name__
    msg = str(exc)
    if "use case details have not been submitted" in msg:
        return "FORM_NOT_SUBMITTED", "Anthropic use-case form outstanding"
    if "ThrottlingException" in name or "Too many tokens" in msg:
        return "QUOTA_ZERO", "quota is zero (message says 'too many tokens' - misleading)"
    if "AccessDenied" in name:
        return "ACCESS_DENIED", "model not enabled on Model access page"
    if "ValidationException" in name and "on-demand" in msg:
        return "NEEDS_PROFILE", "use the us.* inference profile id, not the bare model id"
    if "ResourceNotFound" in name:
        return "NOT_FOUND", msg[:90]
    return name, msg[:90]


def probe_embeddings():
    try:
        r = _client("bedrock-runtime").invoke_model(
            modelId=EMBED_MODEL, body=json.dumps({"inputText": "30 day return policy"}))
        dim = len(json.loads(r["body"].read())["embedding"])
        return "PASS", f"dim={dim}"
    except Exception as e:
        return classify(e)


def probe_generation():
    try:
        r = _client("bedrock-runtime").converse(
            modelId=GEN_MODEL,
            messages=[{"role": "user", "content": [{"text": "Reply with OK"}]}],
            inferenceConfig={"maxTokens": 10})
        return "PASS", r["output"]["message"]["content"][0]["text"].strip()[:30]
    except Exception as e:
        return classify(e)


def read_quotas():
    """Return the four governing quota values, or None where not found."""
    out = {k: None for k in QUOTA_PATTERNS}
    try:
        sq = _client("service-quotas")
        quotas = []
        for page in sq.get_paginator("list_service_quotas").paginate(ServiceCode="bedrock"):
            quotas.extend(page["Quotas"])
        for key, (model_part, metric_part) in QUOTA_PATTERNS.items():
            hits = [q for q in quotas
                    if model_part in q["QuotaName"] and metric_part in q["QuotaName"]]
            if hits:
                # If several match (cross-region vs on-demand variants), take the
                # highest - that is the one that will actually let work through.
                out[key] = max(h["Value"] for h in hits)
    except Exception as e:
        print(f"  ! could not read quotas: {type(e).__name__}: {str(e)[:80]}")
    return out


def probe(quiet=False):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        account = _client("sts").get_caller_identity()["Account"]
    except Exception as e:
        sys.exit(f"No usable AWS credentials: {e}")

    e_status, e_detail = probe_embeddings()
    g_status, g_detail = probe_generation()
    q = read_quotas()
    all_pass = e_status == "PASS" and g_status == "PASS"

    row = {
        "timestamp_utc": ts, "account": account,
        "embed_status": e_status, "embed_detail": e_detail,
        "gen_status": g_status, "gen_detail": g_detail,
        **{k: ("" if q[k] is None else q[k]) for k in QUOTA_PATTERNS},
        "all_pass": "YES" if all_pass else "no",
    }

    new_file = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)

    if not quiet:
        print(f"\n  {ts}   account {account}")
        print(f"  embeddings  {e_status:20s} {e_detail}")
        print(f"  generation  {g_status:20s} {g_detail}")
        print("  quotas:")
        for k in QUOTA_PATTERNS:
            v = q[k]
            shown = "not found" if v is None else (f"{v:,.0f}" + ("  <-- BLOCKED" if v == 0 else ""))
            print(f"    {k:18s} {shown}")
        print(f"  ==> {'ALL PASS - access is working' if all_pass else 'still blocked'}")
        print(f"  logged to {LOG}")
    return all_pass


def watch(interval_min, max_days):
    print(f"Probing every {interval_min} min, giving up after {max_days} days.")
    print("Safe to leave running, or ctrl-C and resume later - the log persists.\n")
    deadline = datetime.now(timezone.utc) + timedelta(days=max_days)
    n = 0
    while datetime.now(timezone.utc) < deadline:
        n += 1
        print(f"--- probe {n} ---")
        if probe():
            print("\nAccess is working. Run --report to summarize timings.")
            return 0
        time.sleep(interval_min * 60)
    print("\nTimed out. Access still blocked - this is itself the finding. Run --report.")
    return 1


def report():
    if not os.path.exists(LOG):
        sys.exit(f"No log at {LOG}. Run a probe first.")
    with open(LOG) as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("Log is empty.")

    def parse(r):
        return datetime.fromisoformat(r["timestamp_utc"])

    first, last = parse(rows[0]), parse(rows[-1])
    print(f"\n  Canary account : {rows[-1]['account']}")
    print(f"  Probes         : {len(rows)}")
    print(f"  First probe    : {first.isoformat()}")
    print(f"  Latest probe   : {last.isoformat()}")
    print(f"  Elapsed        : {(last - first).total_seconds() / 3600:.1f} hours\n")

    def first_where(pred):
        for r in rows:
            if pred(r):
                return parse(r)
        return None

    milestones = [
        ("Anthropic form cleared", lambda r: r["gen_status"] != "FORM_NOT_SUBMITTED"),
        ("Embeddings quota > 0", lambda r: (r["titan_embed_tpm"] or "0") not in ("", "0", "0.0")),
        ("Haiku quota > 0", lambda r: (r["haiku_tpm"] or "0") not in ("", "0", "0.0")),
        ("Embeddings invoke PASS", lambda r: r["embed_status"] == "PASS"),
        ("Generation invoke PASS", lambda r: r["gen_status"] == "PASS"),
        ("ALL PASS", lambda r: r["all_pass"] == "YES"),
    ]
    print("  MILESTONE                     REACHED (UTC)          HOURS FROM FIRST PROBE")
    for label, pred in milestones:
        t = first_where(pred)
        if t is None:
            print(f"  {label:28s}  not reached")
        else:
            print(f"  {label:28s}  {t.isoformat():22s} {(t - first).total_seconds()/3600:>8.1f}")

    done = first_where(lambda r: r["all_pass"] == "YES")
    print()
    if done is None:
        print("  VERDICT: access never became usable during the observed window.")
        print("           If this exceeds 13 days, the Sep 30 due date will not work.")
    else:
        hours = (done - first).total_seconds() / 3600
        days = hours / 24
        print(f"  VERDICT: usable access took {hours:.1f} hours ({days:.1f} days).")
        if days <= 7:
            print("           Comfortably inside the Sep 17 -> Sep 30 window. No change needed.")
        elif days <= 11:
            print("           Inside the window but with little margin. Consider assigning earlier.")
        else:
            print("           TOO SLOW for the Sep 17 -> Sep 30 window. Move the assignment earlier")
            print("           or decouple Track B/C from the Lab 3 deadline.")


def cost():
    ce = boto3.client("ce", region_name="us-east-1")
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=30)
    try:
        r = ce.get_cost_and_usage(
            TimePeriod={"Start": str(start), "End": str(end)},
            Granularity="MONTHLY", Metrics=["UnblendedCost"],
            Filter={"Dimensions": {"Key": "SERVICE", "Values": ["Amazon Bedrock"]}})
        for period in r["ResultsByTime"]:
            amt = period["Total"]["UnblendedCost"]["Amount"]
            print(f"  Bedrock spend {period['TimePeriod']['Start']} to "
                  f"{period['TimePeriod']['End']}: ${float(amt):.4f}")
        print("\n  Compare against the ~$2 estimate in the Pre-Lab 3 doc.")
        print("  Cost Explorer lags 24-48h, so run this a day after your Track B test.")
    except Exception as e:
        print(f"  Could not read Cost Explorer: {type(e).__name__}: {str(e)[:100]}")
        print("  Cost Explorer must be enabled once in the console, and takes ~24h to populate.")


def main():
    ap = argparse.ArgumentParser(description="Bedrock access canary for CS 401R")
    ap.add_argument("--watch", action="store_true", help="probe on a loop until access works")
    ap.add_argument("--interval", type=int, default=30, help="minutes between probes (default 30)")
    ap.add_argument("--max-days", type=int, default=14, help="give up after N days (default 14)")
    ap.add_argument("--report", action="store_true", help="summarize the log")
    ap.add_argument("--cost", action="store_true", help="show Bedrock spend")
    args = ap.parse_args()

    if args.report:
        return report()
    if args.cost:
        return cost()
    if args.watch:
        return watch(args.interval, args.max_days)
    probe()


if __name__ == "__main__":
    sys.exit(main() or 0)
