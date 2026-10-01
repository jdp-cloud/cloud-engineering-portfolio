# ==================================================
# LAMBDA HANDLER
# ==================================================

import json
import os
from datetime import datetime, timezone
from typing import Any


ALLOWED_GROUPS = {
    "security-analysts",
    "security-admins",
}

TOKEN_TABLE_NAME = os.environ.get("TOKEN_TABLE_NAME", "")


def _response(
    status_code: int,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Build a consistent API Gateway proxy response."""

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _get_claims(event: dict[str, Any]) -> dict[str, Any]:
    """Extract Cognito claims supplied by the API Gateway authorizer."""

    return (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims", {})
    )


def _get_groups(claims: dict[str, Any]) -> set[str]:
    """Normalize the Cognito groups claim into a set of group names."""

    raw_groups = claims.get("cognito:groups", [])

    if isinstance(raw_groups, list):
        return {
            str(group).strip()
            for group in raw_groups
            if group
        }

    if isinstance(raw_groups, str):
        return {
            group.strip()
            for group in raw_groups.split(",")
            if group.strip()
        }

    return set()


def _get_header(
    event: dict[str, Any],
    header_name: str,
) -> str | None:
    """Return an API Gateway header using case-insensitive matching."""

    headers = event.get("headers") or {}

    for name, value in headers.items():
        if str(name).lower() == header_name.lower():
            return str(value).strip() if value else None

    return None


def _mark_token_used(
    token_id: str,
    username: str,
) -> tuple[bool, str | None]:
    """Verify token ownership and mark the tracking record as used."""

    if not TOKEN_TABLE_NAME:
        return False, "configuration"

    import boto3
    from botocore.exceptions import ClientError

    table = boto3.resource("dynamodb").Table(TOKEN_TABLE_NAME)

    try:
        response = table.get_item(
            Key={"token_id": token_id},
            ConsistentRead=True,
        )
    except ClientError as exc:
        print(
            json.dumps(
                {
                    "level": "ERROR",
                    "event": "TOKEN_LOOKUP_FAILED",
                    "error_code": exc.response.get(
                        "Error",
                        {},
                    ).get("Code", "Unknown"),
                }
            )
        )
        return False, "service"

    item = response.get("Item")

    if not item:
        return False, "ownership"

    if item.get("username") != username:
        return False, "ownership"

    if item.get("used") is True:
        return True, None

    used_at = datetime.now(timezone.utc).isoformat()

    try:
        table.update_item(
            Key={"token_id": token_id},
            UpdateExpression=(
                "SET used = :used, "
                "used_at = if_not_exists(used_at, :used_at)"
            ),
            ConditionExpression=(
                "attribute_exists(token_id) "
                "AND username = :username"
            ),
            ExpressionAttributeValues={
                ":used": True,
                ":used_at": used_at,
                ":username": username,
            },
        )
    except ClientError as exc:
        error_code = exc.response.get(
            "Error",
            {},
        ).get("Code", "Unknown")

        if error_code == "ConditionalCheckFailedException":
            return False, "ownership"

        print(
            json.dumps(
                {
                    "level": "ERROR",
                    "event": "TOKEN_UPDATE_FAILED",
                    "error_code": error_code,
                }
            )
        )
        return False, "service"

    print(
        json.dumps(
            {
                "level": "INFO",
                "event": "TOKEN_MARKED_USED",
                "token_id": token_id,
                "username": username,
                "used_at": used_at,
            }
        )
    )

    return True, None


def lambda_handler(
    event: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    """Authorize the caller and record successful token use."""

    claims = _get_claims(event)
    groups = _get_groups(claims)

    if not groups.intersection(ALLOWED_GROUPS):
        return _response(
            403,
            {
                "error": "Access denied",
                "message": (
                    "User is not authorized to invoke "
                    "this operation."
                ),
            },
        )

    username = (
        claims.get("cognito:username")
        or claims.get("username")
    )

    if not username:
        return _response(
            403,
            {
                "error": "Access denied",
                "message": "Authenticated username is unavailable.",
            },
        )

    token_id = _get_header(event, "x-token-id")

    if not token_id:
        return _response(
            400,
            {
                "error": "Missing token identifier",
                "message": "The x-token-id header is required.",
            },
        )

    token_valid, failure_reason = _mark_token_used(
        token_id,
        str(username),
    )

    if not token_valid:
        if failure_reason == "configuration":
            return _response(
                500,
                {
                    "error": "Service configuration error",
                },
            )

        if failure_reason == "service":
            return _response(
                500,
                {
                    "error": "Token telemetry service error",
                },
            )

        return _response(
            403,
            {
                "error": "Access denied",
                "message": (
                    "Token identifier is not valid "
                    "for the authenticated user."
                ),
            },
        )

    return _response(
        200,
        {
            "message": "Armageddon 2 protected API is running",
            "username": username,
            "groups": sorted(groups),
        },
    )
