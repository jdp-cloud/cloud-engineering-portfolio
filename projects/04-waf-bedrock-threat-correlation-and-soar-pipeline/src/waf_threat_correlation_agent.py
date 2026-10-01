import hashlib
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import BotoCoreError, ClientError


# ============================================================
# AWS clients
# ============================================================

bedrock_client = boto3.client("bedrock-runtime")
dynamodb = boto3.resource("dynamodb")
eventbridge_client = boto3.client("events")


# ============================================================
# Environment variables
# ============================================================

WAF_EVENTS_TABLE = os.environ["WAF_EVENTS_TABLE"]
CORRELATION_FINDINGS_TABLE = os.environ[
    "CORRELATION_FINDINGS_TABLE"
]

BEDROCK_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-haiku-4-5-20251001-v1:0",
)

CORRELATION_WINDOW_MINUTES = int(
    os.environ.get("CORRELATION_WINDOW_MINUTES", "60")
)

MINIMUM_EVENT_COUNT = int(
    os.environ.get("MINIMUM_EVENT_COUNT", "3")
)

MAX_EVENTS = int(
    os.environ.get("MAX_EVENTS", "500")
)

ADMIN_URI_KEYWORDS = [
    keyword.strip().lower()
    for keyword in os.environ.get(
        "ADMIN_URI_KEYWORDS",
        "admin,login,signin,auth,token,cognito",
    ).split(",")
    if keyword.strip()
]

waf_events_table = dynamodb.Table(WAF_EVENTS_TABLE)
findings_table = dynamodb.Table(CORRELATION_FINDINGS_TABLE)


# ============================================================
# DynamoDB helpers
# ============================================================

def decimal_to_native(value: Any) -> Any:
    """Convert DynamoDB Decimal values into Python numbers."""

    if isinstance(value, list):
        return [decimal_to_native(item) for item in value]

    if isinstance(value, dict):
        return {
            key: decimal_to_native(item)
            for key, item in value.items()
        }

    if isinstance(value, Decimal):
        if value % 1 == 0:
            return int(value)

        return float(value)

    return value


def get_recent_events(
    window_minutes: int,
) -> tuple[list[dict[str, Any]], datetime, datetime]:
    """
    Read WAF records inside the correlation window.

    This first lab version uses Scan with a filter. A later version can
    replace this with Query against a time-oriented secondary index.
    """

    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(
        minutes=window_minutes
    )

    minimum_epoch = int(window_start.timestamp())

    print(
        f"Reading WAF events from {window_start.isoformat()} "
        f"through {window_end.isoformat()}."
    )

    scan_kwargs: dict[str, Any] = {
        "FilterExpression": Attr("event_epoch").gte(
            minimum_epoch
        ),
        "Limit": min(MAX_EVENTS, 100),
    }

    items: list[dict[str, Any]] = []

    while True:
        response = waf_events_table.scan(**scan_kwargs)

        items.extend(response.get("Items", []))

        if len(items) >= MAX_EVENTS:
            items = items[:MAX_EVENTS]
            break

        last_evaluated_key = response.get(
            "LastEvaluatedKey"
        )

        if not last_evaluated_key:
            break

        scan_kwargs["ExclusiveStartKey"] = (
            last_evaluated_key
        )

    events = [
        decimal_to_native(item)
        for item in items
    ]

    events.sort(
        key=lambda item: item.get("event_epoch", 0)
    )

    print(
        f"Retrieved {len(events)} event(s) "
        "inside the correlation window."
    )

    return events, window_start, window_end


# ============================================================
# Deterministic correlation
# ============================================================

def contains_sensitive_uri(uri: str) -> bool:
    """Return True if a URI appears identity- or admin-related."""

    normalized_uri = uri.lower()

    return any(
        keyword in normalized_uri
        for keyword in ADMIN_URI_KEYWORDS
    )


def to_dynamodb_compatible(value: Any) -> Any:
    """Recursively convert Python values for DynamoDB."""
    if isinstance(value, float):
        return Decimal(str(value))

    if isinstance(value, dict):
        return {
            key: to_dynamodb_compatible(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            to_dynamodb_compatible(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            to_dynamodb_compatible(item)
            for item in value
        ]

    return value


def calculate_risk_score(
    event_count: int,
    unique_uris: int,
    unique_rules: int,
    blocked_count: int,
    sensitive_uri_targeted: bool,
    active_span_minutes: float,
) -> tuple[int, list[str]]:
    """Create a transparent deterministic risk score."""

    score = 0
    reasons: list[str] = []

    if event_count >= 5:
        score += 20
        reasons.append(
            "Source generated at least five WAF events."
        )

    if event_count >= 15:
        score += 10
        reasons.append(
            "Source generated at least fifteen WAF events."
        )

    if unique_uris >= 3:
        score += 20
        reasons.append(
            "Source targeted at least three unique URIs."
        )

    if unique_rules >= 2:
        score += 20
        reasons.append(
            "Source triggered at least two WAF rule types."
        )

    if sensitive_uri_targeted:
        score += 15
        reasons.append(
            "Source targeted an identity, authentication, "
            "or administrative URI."
        )

    if blocked_count == event_count and event_count > 0:
        score += 5
        reasons.append(
            "All observed requests were blocked by WAF."
        )

    if event_count >= 5 and active_span_minutes <= 5:
        score += 10
        reasons.append(
            "At least five events occurred within five minutes."
        )

    return min(score, 100), reasons


def classify_severity(score: int) -> str:
    """Translate risk score into a severity label."""

    if score >= 80:
        return "CRITICAL"

    if score >= 60:
        return "HIGH"

    if score >= 30:
        return "MEDIUM"

    return "LOW"


def build_source_ip_correlations(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Group WAF events by source IP and calculate risk."""

    grouped_events: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for event in events:
        source_ip = event.get("source_ip", "UNKNOWN")
        grouped_events[source_ip].append(event)

    correlations: list[dict[str, Any]] = []

    for source_ip, source_events in grouped_events.items():
        source_events.sort(
            key=lambda item: item.get("event_epoch", 0)
        )

        event_count = len(source_events)

        blocked_count = sum(
            1
            for item in source_events
            if item.get("action") == "BLOCK"
        )

        uris = {
            item.get("uri", "UNKNOWN")
            for item in source_events
        }

        rules = {
            item.get("rule", "UNKNOWN")
            for item in source_events
        }

        countries = {
            item.get("country", "UNKNOWN")
            for item in source_events
        }

        first_epoch = source_events[0].get(
            "event_epoch",
            0,
        )

        last_epoch = source_events[-1].get(
            "event_epoch",
            first_epoch,
        )

        active_span_seconds = max(
            last_epoch - first_epoch,
            0,
        )

        active_span_minutes = round(
            active_span_seconds / 60,
            2,
        )

        sensitive_uri_targeted = any(
            contains_sensitive_uri(uri)
            for uri in uris
        )

        risk_score, score_reasons = calculate_risk_score(
            event_count=event_count,
            unique_uris=len(uris),
            unique_rules=len(rules),
            blocked_count=blocked_count,
            sensitive_uri_targeted=sensitive_uri_targeted,
            active_span_minutes=active_span_minutes,
        )

        correlations.append(
            {
                "source_ip": source_ip,
                "event_count": event_count,
                "blocked_count": blocked_count,
                "allowed_count": (
                    event_count - blocked_count
                ),
                "unique_uris": len(uris),
                "uris": sorted(uris),
                "unique_rules": len(rules),
                "rules": sorted(rules),
                "countries": sorted(countries),
                "first_seen": source_events[0].get(
                    "timestamp"
                ),
                "last_seen": source_events[-1].get(
                    "timestamp"
                ),
                "active_span_minutes": (
                    active_span_minutes
                ),
                "sensitive_uri_targeted": (
                    sensitive_uri_targeted
                ),
                "risk_score": risk_score,
                "severity": classify_severity(
                    risk_score
                ),
                "score_reasons": score_reasons,
            }
        )

    correlations.sort(
        key=lambda item: (
            item["risk_score"],
            item["event_count"],
        ),
        reverse=True,
    )

    return correlations


def build_target_correlations(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize activity by targeted URI."""

    uri_events: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for event in events:
        uri = event.get("uri", "UNKNOWN")
        uri_events[uri].append(event)

    target_correlations: list[dict[str, Any]] = []

    for uri, related_events in uri_events.items():
        source_ips = {
            item.get("source_ip", "UNKNOWN")
            for item in related_events
        }

        rule_counter = Counter(
            item.get("rule", "UNKNOWN")
            for item in related_events
        )

        most_common_rule = (
            rule_counter.most_common(1)[0][0]
            if rule_counter
            else "UNKNOWN"
        )

        target_correlations.append(
            {
                "uri": uri,
                "event_count": len(related_events),
                "unique_source_ips": len(source_ips),
                "most_common_rule": most_common_rule,
                "sensitive_uri": contains_sensitive_uri(
                    uri
                ),
            }
        )

    target_correlations.sort(
        key=lambda item: item["event_count"],
        reverse=True,
    )

    return target_correlations


def build_rule_correlations(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize activity by terminating WAF rule."""

    rule_events: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(list)

    for event in events:
        rule = event.get("rule", "UNKNOWN")
        rule_events[rule].append(event)

    correlations: list[dict[str, Any]] = []

    for rule, related_events in rule_events.items():
        correlations.append(
            {
                "rule": rule,
                "event_count": len(related_events),
                "unique_source_ips": len(
                    {
                        item.get(
                            "source_ip",
                            "UNKNOWN",
                        )
                        for item in related_events
                    }
                ),
                "targeted_uris": sorted(
                    {
                        item.get("uri", "UNKNOWN")
                        for item in related_events
                    }
                ),
            }
        )

    correlations.sort(
        key=lambda item: item["event_count"],
        reverse=True,
    )

    return correlations


def build_evidence_package(
    events: list[dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
) -> dict[str, Any]:
    """Build the compact evidence package sent to Bedrock."""

    source_correlations = (
        build_source_ip_correlations(events)
    )

    target_correlations = (
        build_target_correlations(events)
    )

    rule_correlations = (
        build_rule_correlations(events)
    )

    blocked_count = sum(
        1
        for item in events
        if item.get("action") == "BLOCK"
    )

    unique_source_ips = {
        item.get("source_ip", "UNKNOWN")
        for item in events
    }

    unique_uris = {
        item.get("uri", "UNKNOWN")
        for item in events
    }

    deterministic_findings: list[str] = []

    if source_correlations:
        top_source = source_correlations[0]

        deterministic_findings.append(
            f"Highest-risk source IP "
            f"{top_source['source_ip']} generated "
            f"{top_source['event_count']} event(s), "
            f"targeted {top_source['unique_uris']} URI(s), "
            f"and triggered "
            f"{top_source['unique_rules']} rule type(s)."
        )

    if target_correlations:
        top_target = target_correlations[0]

        deterministic_findings.append(
            f"Most targeted URI was "
            f"{top_target['uri']} with "
            f"{top_target['event_count']} event(s) "
            f"from {top_target['unique_source_ips']} "
            "unique source IP(s)."
        )

    if rule_correlations:
        top_rule = rule_correlations[0]

        deterministic_findings.append(
            f"Most frequently triggered WAF rule was "
            f"{top_rule['rule']} with "
            f"{top_rule['event_count']} event(s)."
        )

    return {
        "analysis_window": {
            "start": window_start.isoformat(),
            "end": window_end.isoformat(),
            "minutes": CORRELATION_WINDOW_MINUTES,
        },
        "summary": {
            "total_events": len(events),
            "blocked_events": blocked_count,
            "allowed_events": (
                len(events) - blocked_count
            ),
            "unique_source_ips": len(
                unique_source_ips
            ),
            "unique_uris": len(unique_uris),
        },
        "top_source_ips": source_correlations[:10],
        "top_targeted_uris": (
            target_correlations[:10]
        ),
        "top_waf_rules": rule_correlations[:10],
        "deterministic_findings": (
            deterministic_findings
        ),
    }


# ============================================================
# Bedrock interpretation
# ============================================================

def call_bedrock(
    evidence_package: dict[str, Any],
) -> str:
    """Ask Bedrock to interpret deterministic findings."""

    prompt = f"""
You are a senior SOC analyst assisting with AWS WAF threat correlation.

The following evidence was calculated deterministically by Python.
Do not alter the supplied counts or risk scores.

Evidence:
{json.dumps(evidence_package, indent=2, default=str)}

Return the response using exactly these headings:

Threat Classification:
Overall Severity:
Confidence:
Correlated Indicators:
Likely Activity:
Business Impact:
Recommended Analyst Actions:
Executive Summary:

Requirements:
- Separate observed facts from possible interpretations.
- Do not claim that exploitation succeeded.
- Do not invent IP reputation, geolocation, identity, or attack data.
- Explain why the events may or may not represent coordinated activity.
- Keep the response suitable for both a SOC analyst and a manager.
""".strip()

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 900,
        "temperature": 0.2,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ],
            }
        ],
    }

    print(
        f"Invoking Bedrock correlation model "
        f"{BEDROCK_MODEL_ID}."
    )

    response = bedrock_client.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(request_body),
    )

    response_body = json.loads(response["body"].read())

    content = response_body.get("content", [])

    if not content:
        raise ValueError(
            "Bedrock returned no correlation content."
        )

    report = content[0].get("text")

    if not report:
        raise ValueError(
            "Bedrock response did not contain report text."
        )

    print("Bedrock correlation invocation successful.")

    return report


# ============================================================
# Finding persistence
# ============================================================

def determine_overall_risk(
    evidence_package: dict[str, Any],
) -> tuple[int, str, str | None]:
    """Determine the highest deterministic risk in the window."""

    source_findings = evidence_package.get(
        "top_source_ips",
        [],
    )

    if not source_findings:
        return 0, "LOW", None

    highest = source_findings[0]

    return (
        highest.get("risk_score", 0),
        highest.get("severity", "LOW"),
        highest.get("source_ip"),
    )


def create_finding_id(
    events: list[dict[str, Any]],
) -> str:
    """
    Create a deterministic ID from the correlated event set.

    Reprocessing the same WAF event set produces the same finding
    ID, preventing exact retries from creating duplicate findings
    and duplicate SOAR incidents. Overlapping windows with changed
    event sets intentionally produce different IDs.
    """

    event_keys: list[str] = []

    for event in events:
        event_id = event.get("event_id")

        if event_id:
            event_keys.append(str(event_id))
            continue

        fallback_key = {
            "timestamp": event.get("timestamp"),
            "source_ip": event.get("source_ip"),
            "uri": event.get("uri"),
            "rule": event.get("rule"),
            "action": event.get("action"),
        }

        event_keys.append(
            json.dumps(
                fallback_key,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
        )

    fingerprint_material = json.dumps(
        {
            "fingerprint_version": 1,
            "event_keys": sorted(event_keys),
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    fingerprint = hashlib.sha256(
        fingerprint_material.encode("utf-8")
    ).hexdigest()

    return f"FINDING-{fingerprint}"


def save_finding(
    events: list[dict[str, Any]],
    evidence_package: dict[str, Any],
    bedrock_report: str,
) -> tuple[str, bool]:
    """
    Store the final correlation finding.

    Returns the finding ID and whether a new item was created.
    """

    finding_id = create_finding_id(events)
    created_at = datetime.now(timezone.utc).isoformat()

    risk_score, severity, primary_source_ip = (
        determine_overall_risk(evidence_package)
    )

    targeted_uris = evidence_package.get(
        "top_targeted_uris",
        [],
    )

    primary_target = (
        targeted_uris[0].get("uri")
        if targeted_uris
        else None
    )

    item = {
        "finding_id": finding_id,
        "created_at": created_at,
        "window_start": evidence_package[
            "analysis_window"
        ]["start"],
        "window_end": evidence_package[
            "analysis_window"
        ]["end"],
        "severity": severity,
        "risk_score": risk_score,
        "event_count": evidence_package["summary"][
            "total_events"
        ],
        "primary_source_ip": (
            primary_source_ip or "NONE"
        ),
        "primary_target": primary_target or "NONE",
        "status": "OPEN",
        "bedrock_report": bedrock_report,
        "evidence": evidence_package,
    }

    try:
        findings_table.put_item(
            Item=to_dynamodb_compatible(item),
            ConditionExpression=(
                "attribute_not_exists(finding_id)"
            ),
        )

    except ClientError as error:
        error_code = error.response.get(
            "Error",
            {},
        ).get("Code")

        if error_code == "ConditionalCheckFailedException":
            print(
                f"Correlation finding {finding_id} already "
                "exists. Skipping duplicate finding."
            )

            return finding_id, False

        raise

    print(
        f"Saved correlation finding {finding_id} "
        f"with severity {severity}."
    )

    return finding_id, True



def publish_finding_event(
    finding_id: str,
    severity: str,
    risk_score: int,
) -> str:
    """Publish finding routing data to the default event bus."""

    detail = {
        "finding_id": finding_id,
        "severity": severity,
        "risk_score": risk_score,
    }

    response = eventbridge_client.put_events(
        Entries=[
            {
                "Source": "seir.waf.correlation",
                "DetailType": "WAF Threat Finding Created",
                "Detail": json.dumps(detail),
                "EventBusName": "default",
            }
        ]
    )

    failed_entry_count = int(
        response.get("FailedEntryCount", 0)
    )
    entries = response.get("Entries", [])

    if failed_entry_count:
        failed_entry = entries[0] if entries else {}

        error_code = failed_entry.get(
            "ErrorCode",
            "UnknownError",
        )
        error_message = failed_entry.get(
            "ErrorMessage",
            "No EventBridge error message returned.",
        )

        raise RuntimeError(
            "EventBridge rejected the threat-finding event: "
            f"{error_code}: {error_message}"
        )

    event_id = (
        entries[0].get("EventId")
        if entries
        else None
    )

    if not event_id:
        raise RuntimeError(
            "EventBridge did not return an EventId."
        )

    print(
        f"Published finding {finding_id} to EventBridge "
        f"as event {event_id}."
    )

    return event_id


# ============================================================
# Lambda handler
# ============================================================

def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Correlate recent WAF telemetry and generate a finding."""

    print("=" * 60)
    print("Starting WAF Threat Correlation Agent")
    print("=" * 60)

    requested_window = event.get(
        "correlation_window_minutes"
    )

    window_minutes = (
        int(requested_window)
        if requested_window is not None
        else CORRELATION_WINDOW_MINUTES
    )

    try:
        events, window_start, window_end = (
            get_recent_events(window_minutes)
        )

        if len(events) < MINIMUM_EVENT_COUNT:
            message = (
                f"Only {len(events)} event(s) found. "
                f"At least {MINIMUM_EVENT_COUNT} are "
                "required for correlation."
            )

            print(message)

            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": message,
                        "events_found": len(events),
                        "finding_created": False,
                    }
                ),
            }

        evidence_package = build_evidence_package(
            events=events,
            window_start=window_start,
            window_end=window_end,
        )

        print("\n===== DETERMINISTIC EVIDENCE =====")
        print(
            json.dumps(
                evidence_package,
                indent=2,
                default=str,
            )
        )
        print("==================================\n")

        bedrock_report = call_bedrock(
            evidence_package
        )

        print("\n===== BEDROCK THREAT REPORT =====")
        print(bedrock_report)
        print("=================================\n")

        finding_id, finding_created = save_finding(
            events=events,
            evidence_package=evidence_package,
            bedrock_report=bedrock_report,
        )

        risk_score, severity, primary_source_ip = (
            determine_overall_risk(evidence_package)
        )

        eventbridge_event_id = None

        if finding_created:
            eventbridge_event_id = publish_finding_event(
                finding_id=finding_id,
                severity=severity,
                risk_score=risk_score,
            )
        else:
            print(
                "Skipping EventBridge publication because "
                "the correlation finding already exists."
            )

        result = {
            "message": (
                "Threat correlation completed."
                if finding_created
                else (
                    "Threat correlation completed; "
                    "duplicate finding skipped."
                )
            ),
            "finding_created": finding_created,
            "finding_id": finding_id,
            "events_correlated": len(events),
            "severity": severity,
            "risk_score": risk_score,
            "eventbridge_event_id": eventbridge_event_id,
            "primary_source_ip": primary_source_ip,
        }

        print("Correlation result:")
        print(json.dumps(result, indent=2))

        return {
            "statusCode": 200,
            "body": json.dumps(result),
        }

    except (ClientError, BotoCoreError) as error:
        print(f"AWS service error: {error}")

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": (
                        "Threat correlation failed "
                        "because an AWS service returned "
                        "an error."
                    ),
                    "error": str(error),
                }
            ),
        }

    except Exception as error:
        print(
            f"Unexpected correlation error: "
            f"{type(error).__name__}: {error}"
        )

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": (
                        "Threat correlation failed."
                    ),
                    "error": str(error),
                }
            ),
        }