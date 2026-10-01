# ==================================================
# UNUSED TOKEN DETECTOR
# ==================================================

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any


ALERT_AFTER_MINUTES = int(
    os.environ.get("ALERT_AFTER_MINUTES", "10")
)


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp and normalize it to UTC."""

    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def is_unused_and_stale(
    item: dict[str, Any],
    now: datetime,
    threshold_minutes: int,
) -> bool:
    """Return True when a token is unused and older than the threshold."""

    if item.get("used") is not False:
        return False

    issued_at_raw = item.get("issued_at")

    if not isinstance(issued_at_raw, str):
        return False

    issued_at = parse_timestamp(issued_at_raw)
    cutoff = now - timedelta(minutes=threshold_minutes)

    return issued_at < cutoff


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Scan token telemetry and alert on unused stale records."""

    import boto3
    from boto3.dynamodb.conditions import Attr

    table_name = os.environ["TOKEN_TABLE_NAME"]
    table = boto3.resource("dynamodb").Table(table_name)

    now = datetime.now(timezone.utc)
    alerts: list[dict[str, Any]] = []

    scan_arguments: dict[str, Any] = {
        "FilterExpression": Attr("used").eq(False),
        "ProjectionExpression": (
            "token_id, username, issued_at, used"
        ),
    }

    while True:
        response = table.scan(**scan_arguments)

        for item in response.get("Items", []):
            try:
                if not is_unused_and_stale(
                    item,
                    now,
                    ALERT_AFTER_MINUTES,
                ):
                    continue
            except (TypeError, ValueError) as exc:
                print(
                    json.dumps(
                        {
                            "level": "WARNING",
                            "event": "INVALID_TOKEN_TIMESTAMP",
                            "token_id": item.get(
                                "token_id",
                                "unknown",
                            ),
                            "error": str(exc),
                        }
                    )
                )
                continue

            issued_at = parse_timestamp(item["issued_at"])

            age_minutes = int(
                (now - issued_at).total_seconds() // 60
            )

            alert = {
                "level": "ALERT",
                "alert_type": "UNUSED_TOKEN",
                "token_id": item.get("token_id", "unknown"),
                "username": item.get("username", "unknown"),
                "issued_at": item["issued_at"],
                "age_minutes": age_minutes,
                "threshold_minutes": ALERT_AFTER_MINUTES,
            }

            alerts.append(alert)
            print(json.dumps(alert))

        last_key = response.get("LastEvaluatedKey")

        if not last_key:
            break

        scan_arguments["ExclusiveStartKey"] = last_key

    summary = {
        "checked_at": now.isoformat(),
        "threshold_minutes": ALERT_AFTER_MINUTES,
        "alert_count": len(alerts),
        "alerts": alerts,
    }

    print(
        json.dumps(
            {
                "level": "INFO",
                "event": "UNUSED_TOKEN_SCAN_COMPLETE",
                "alert_count": len(alerts),
            }
        )
    )

    return summary
