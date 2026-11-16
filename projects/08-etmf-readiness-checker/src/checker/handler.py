"""Lambda entry point for an uploaded index or the Monday schedule.

boto3 is imported inside the handler so local tests do not need it. The check
itself lives in the other modules and does not call AWS.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import unquote_plus

from checker.findings import evaluate, load_index_text, load_sites_text
from checker.report import summary_payload, write_reports
from checker.rules import load_rules_text
from checker.scoring import score_study


def lambda_handler(event, context):
    import boto3

    event = event or {}
    bucket = os.environ["BUCKET_NAME"]
    s3 = boto3.client("s3")
    key = index_key(event, s3, bucket)
    if key is None:
        return {"status": "error", "message": "No eTMF index CSV found under incoming/."}

    rules = load_rules_text(_get_text(s3, bucket, os.environ.get("RULES_KEY", "config/expected_artifacts.yaml")))
    sites = load_sites_text(
        _get_text(s3, bucket, os.environ.get("MILESTONES_KEY", "config/site_milestones.csv"))
    )
    rows = load_index_text(_get_text(s3, bucket, key))
    as_of = resolve_as_of(event)
    score = score_study(evaluate(rules, sites, rows, as_of), rules.critical_score_cap)
    summary = summary_payload(rules, score, as_of)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prefix = f"reports/{stamp}"
    # write_reports needs a directory. Build the three bodies in memory via a
    # temporary folder only when a local path is set; in Lambda use /tmp.
    local_dir = Path("/tmp") / stamp
    paths = write_reports(rules, score, as_of, local_dir)
    for name, path in paths.items():
        content_type = {
            "findings": "text/csv",
            "summary": "application/json",
            "html": "text/html; charset=utf-8",
        }[name]
        suffix = {"findings": "findings.csv", "summary": "summary.json", "html": "readiness_report.html"}[name]
        s3.put_object(
            Bucket=bucket,
            Key=f"{prefix}/{suffix}",
            Body=path.read_bytes(),
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )

    print(json.dumps({"index_key": key, "report_prefix": prefix, "finding_counts": summary["finding_counts"]}))
    return {
        "status": "ok",
        "index_key": key,
        "as_of": as_of.isoformat(),
        "report_prefix": prefix,
        "study_readiness": summary["study_readiness"],
        "finding_counts": summary["finding_counts"],
    }


def resolve_as_of(event: dict) -> date:
    """The weekly run uses today's UTC date so expiry flags move as time passes.

    A caller can pass as_of to replay the sample study. The local CLI does that
    with the date stored in the rule file.
    """
    raw = event.get("as_of") if event else None
    if raw:
        return date.fromisoformat(str(raw))
    return datetime.now(timezone.utc).date()


def index_key(event: dict, s3, bucket: str) -> str | None:
    records = event.get("Records") or []
    if records and records[0].get("eventSource") == "aws:s3":
        key = unquote_plus(records[0]["s3"]["object"]["key"])
        if key.startswith("incoming/") and key.endswith(".csv") and "/pdf/" not in key:
            return key
        return None
    return latest_index_key(s3, bucket)


def latest_index_key(s3, bucket: str) -> str | None:
    paginator = s3.get_paginator("list_objects_v2")
    latest = None
    for page in paginator.paginate(Bucket=bucket, Prefix="incoming/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".csv") or "/pdf/" in key:
                continue
            if latest is None or obj["LastModified"] > latest[0]:
                latest = (obj["LastModified"], key)
    if latest is None:
        return None
    return latest[1]


def _get_text(s3, bucket: str, key: str) -> str:
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")
