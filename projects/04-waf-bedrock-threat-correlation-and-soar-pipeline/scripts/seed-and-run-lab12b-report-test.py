#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REGION = "us-east-1"
LAB_DIR = Path("phase-1/lab-12b")
TFDIR = LAB_DIR / "terraform"
CORRELATION_EVENT = LAB_DIR / "test-events/lab12-correlation.json"
EXECUTIVE_EVENT = LAB_DIR / "test-events/lab12b-executive-report.json"
TMP = Path("/tmp")
CORRELATION_RESPONSE = TMP / "lab12b-populated-correlation-response.json"
EXECUTIVE_RESPONSE = TMP / "lab12b-populated-executive-response.json"
REPORT_JSON = TMP / "lab12b-populated-executive-report.json"
REPORT_PDF = TMP / "lab12b-populated-executive-report.pdf"


class CommandError(RuntimeError):
    pass


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        summary = " ".join(command[:4])
        raise CommandError(
            f"Command failed ({result.returncode}): {summary}\n{stderr}"
        )
    return result


def terraform_output(name: str) -> str:
    return run(
        ["terraform", f"-chdir={TFDIR}", "output", "-raw", name]
    ).stdout.strip()


def aws_json(arguments: list[str]) -> dict[str, Any]:
    result = run(
        ["aws", *arguments, "--region", REGION, "--output", "json"]
    )
    return json.loads(result.stdout) if result.stdout.strip() else {}


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dynamodb_item(record: dict[str, Any]) -> dict[str, dict[str, str]]:
    item: dict[str, dict[str, str]] = {}
    for key, value in record.items():
        if isinstance(value, bool):
            item[key] = {"BOOL": value}
        elif isinstance(value, int):
            item[key] = {"N": str(value)}
        else:
            item[key] = {"S": str(value)}
    return item


def put_item(table_name: str, record: dict[str, Any]) -> None:
    request_path = TMP / f"{record['event_id']}.json"
    request_path.write_text(
        json.dumps(dynamodb_item(record)),
        encoding="utf-8",
    )
    try:
        run(
            [
                "aws",
                "dynamodb",
                "put-item",
                "--region",
                REGION,
                "--table-name",
                table_name,
                "--item",
                f"file://{request_path}",
            ]
        )
    finally:
        request_path.unlink(missing_ok=True)


def invoke_lambda(
    function_name: str,
    payload_path: Path,
    response_path: Path,
) -> dict[str, Any]:
    response_path.unlink(missing_ok=True)
    result = run(
        [
            "aws",
            "lambda",
            "invoke",
            "--region",
            REGION,
            "--function-name",
            function_name,
            "--cli-binary-format",
            "raw-in-base64-out",
            "--payload",
            f"fileb://{payload_path}",
            str(response_path),
        ]
    )
    metadata = json.loads(result.stdout)
    if metadata.get("FunctionError"):
        raise CommandError(
            f"Lambda returned FunctionError: {metadata['FunctionError']}"
        )

    outer = json.loads(response_path.read_text(encoding="utf-8"))
    body = json.loads(outer.get("body", "{}"))
    if outer.get("statusCode") != 200:
        raise CommandError(
            f"Lambda payload returned status {outer.get('statusCode')}: "
            f"{body.get('message', 'unknown error')}"
        )
    return body


def get_incident(table_name: str, incident_id: str) -> dict[str, Any] | None:
    key_path = TMP / "lab12b-incident-key.json"
    key_path.write_text(
        json.dumps({"incident_id": {"S": incident_id}}),
        encoding="utf-8",
    )
    try:
        response = aws_json(
            [
                "dynamodb",
                "get-item",
                "--table-name",
                table_name,
                "--key",
                f"file://{key_path}",
                "--consistent-read",
            ]
        )
    finally:
        key_path.unlink(missing_ok=True)
    return response.get("Item")


def head_object(bucket: str, key: str) -> dict[str, Any]:
    return aws_json(
        ["s3api", "head-object", "--bucket", bucket, "--key", key]
    )


def download_object(bucket: str, key: str, destination: Path) -> None:
    destination.unlink(missing_ok=True)
    run(
        [
            "aws",
            "s3api",
            "get-object",
            "--region",
            REGION,
            "--bucket",
            bucket,
            "--key",
            key,
            str(destination),
        ]
    )


def main() -> int:
    for required in (TFDIR, CORRELATION_EVENT, EXECUTIVE_EVENT):
        if not required.exists():
            raise SystemExit(f"Missing required path: {required}")

    waf_table = terraform_output("waf_events_table_name")
    incidents_table = terraform_output("security_incidents_table_name")
    correlation_function = terraform_output("correlation_lambda_name")
    executive_function = terraform_output(
        "executive_dashboard_lambda_name"
    )

    run_id = uuid.uuid4().hex[:10]
    now = datetime.now(timezone.utc)

    previous_times = [
        now - timedelta(hours=30),
        now - timedelta(hours=29, minutes=55),
    ]
    current_times = [
        now - timedelta(minutes=4),
        now - timedelta(minutes=3),
        now - timedelta(minutes=2),
        now - timedelta(minutes=1),
    ]

    previous_records = [
        {
            "event_id": f"lab12b-{run_id}-previous-01",
            "timestamp": iso_z(previous_times[0]),
            "event_epoch": int(previous_times[0].timestamp()),
            "source_ip": "203.0.113.45",
            "uri": "/products",
            "action": "BLOCK",
            "rule": "AWSManagedRulesCommonRuleSet",
            "country": "US",
        },
        {
            "event_id": f"lab12b-{run_id}-previous-02",
            "timestamp": iso_z(previous_times[1]),
            "event_epoch": int(previous_times[1].timestamp()),
            "source_ip": "203.0.113.45",
            "uri": "/search",
            "action": "BLOCK",
            "rule": "AWSManagedRulesCommonRuleSet",
            "country": "US",
        },
    ]

    current_specs = [
        ("/admin/login", "AWSManagedRulesCommonRuleSet"),
        ("/account/reset", "AWSManagedRulesKnownBadInputsRuleSet"),
        ("/api/users", "AWSManagedRulesCommonRuleSet"),
        ("/auth/token", "AWSManagedRulesKnownBadInputsRuleSet"),
    ]

    current_records = []
    for index, (uri, rule) in enumerate(current_specs, start=1):
        timestamp = current_times[index - 1]
        current_records.append(
            {
                "event_id": f"lab12b-{run_id}-current-{index:02d}",
                "timestamp": iso_z(timestamp),
                "event_epoch": int(timestamp.timestamp()),
                "source_ip": "198.51.100.88",
                "uri": uri,
                "action": "BLOCK",
                "rule": rule,
                "country": "US",
            }
        )

    print("LAB 12B CONTROLLED SYNTHETIC DATA TEST")
    print("======================================")
    print(f"Synthetic run ID:             {run_id}")
    print("Documentation source IP:      198.51.100.88")
    print("Prior-period WAF records:     2")
    print("Current-period WAF records:   4")
    print("Expected severity:            HIGH")
    print("Containment authorized:       false")
    print()

    for record in previous_records + current_records:
        put_item(waf_table, record)
    print("PASS: Six synthetic WAF records were written.")

    correlation = invoke_lambda(
        correlation_function,
        CORRELATION_EVENT,
        CORRELATION_RESPONSE,
    )
    if not correlation.get("finding_created"):
        raise CommandError(
            "Correlation completed without creating a finding."
        )

    finding_id = correlation["finding_id"]
    incident_id = f"INC-{finding_id}"

    print(
        "PASS: Correlation finding created with "
        f"severity {correlation.get('severity')} and "
        f"risk score {correlation.get('risk_score')}."
    )

    incident = None
    for _ in range(30):
        incident = get_incident(incidents_table, incident_id)
        if incident:
            break
        time.sleep(2)

    if not incident:
        raise CommandError(
            "SOAR incident was not found within 60 seconds."
        )

    print("PASS: EventBridge triggered SOAR incident creation.")

    executive = invoke_lambda(
        executive_function,
        EXECUTIVE_EVENT,
        EXECUTIVE_RESPONSE,
    )

    artifacts = executive["artifacts"]
    bucket = artifacts["bucket"]
    pdf = artifacts["pdf"]
    json_artifact = artifacts["json"]

    pdf_head = head_object(bucket, pdf["key"])
    json_head = head_object(bucket, json_artifact["key"])

    download_object(bucket, pdf["key"], REPORT_PDF)
    download_object(bucket, json_artifact["key"], REPORT_JSON)

    report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    current = report["current_period"]
    previous = report["previous_period"]

    assert executive["containment_performed"] is False
    assert executive["human_review_required"] is True
    assert pdf_head["ContentType"] == "application/pdf"
    assert json_head["ContentType"] == "application/json"
    assert pdf_head["ServerSideEncryption"] == "AES256"
    assert json_head["ServerSideEncryption"] == "AES256"
    assert pdf_head["Metadata"]["report-id"] == report["report_id"]
    assert json_head["Metadata"]["report-id"] == report["report_id"]
    assert current["waf"]["total_events"] >= 4
    assert previous["waf"]["total_events"] >= 2
    assert current["findings"]["high"] >= 1
    assert current["incidents"]["total_incidents"] >= 1

    print()
    print("LAB 12B POPULATED REPORT VERIFICATION")
    print("=====================================")
    print(f"Report ID:                    {report['report_id']}")
    print(
        f"Overall security posture:     "
        f"{report['overall_security_posture']}"
    )
    print(
        f"Current WAF events:           "
        f"{current['waf']['total_events']}"
    )
    print(
        f"Previous WAF events:          "
        f"{previous['waf']['total_events']}"
    )
    print(
        f"Current blocked requests:     "
        f"{current['waf']['blocked_requests']}"
    )
    print(
        f"Current high findings:        "
        f"{current['findings']['high']}"
    )
    print(
        f"Current total incidents:      "
        f"{current['incidents']['total_incidents']}"
    )
    print(
        f"Awaiting human review:        "
        f"{current['incidents']['awaiting_human_review']}"
    )
    print(
        f"Bedrock narrative used:       "
        f"{executive['bedrock_used']}"
    )
    print(
        f"Containment performed:        "
        f"{executive['containment_performed']}"
    )
    print(
        f"Human review required:        "
        f"{executive['human_review_required']}"
    )
    print(f"PDF content type:             {pdf_head['ContentType']}")
    print(
        f"PDF encryption:               "
        f"{pdf_head['ServerSideEncryption']}"
    )
    print(f"JSON content type:            {json_head['ContentType']}")
    print(
        f"JSON encryption:              "
        f"{json_head['ServerSideEncryption']}"
    )
    print("Synchronized report IDs:      true")
    print()
    print(
        "PASS: Populated executive report generated "
        "from the WAF-to-correlation-to-SOAR pipeline."
    )
    print()
    print(f"Local PDF:  {REPORT_PDF}")
    print(f"Local JSON: {REPORT_JSON}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CommandError, KeyError, AssertionError) as error:
        print()
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
