"""
abuseipdb.py

AbuseIPDB threat-intelligence provider.

Supported indicators:

- IPv4
- IPv6

The API key is read from configuration and is never returned in provider
results or written to logs.
"""

from __future__ import annotations

import ipaddress
import os

from typing import Any, Mapping

from .base_provider import (
    BaseThreatIntelProvider,
    Indicator,
    JsonHttpClient,
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderResult,
)


DEFAULT_ABUSEIPDB_URL = "https://api.abuseipdb.com/api/v2/check"


class AbuseIpDbProvider(BaseThreatIntelProvider):
    """Retrieve IP reputation information from AbuseIPDB."""

    name = "abuseipdb"
    supported_indicator_types = frozenset({"IPV4", "IPV6"})

    default_ttl_seconds = 86_400
    error_ttl_seconds = 900

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint: str | None = None,
        max_age_days: int = 90,
        http_client: JsonHttpClient | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("ABUSEIPDB_API_KEY")
        self.endpoint = (
            endpoint
            or os.getenv("ABUSEIPDB_ENDPOINT")
            or DEFAULT_ABUSEIPDB_URL
        )
        self.max_age_days = max_age_days
        self.http_client = http_client or JsonHttpClient()

    def lookup(
        self,
        indicator: Indicator,
        context: Mapping[str, Any],
    ) -> ProviderResult:
        if not self.api_key:
            raise ProviderConfigurationError(
                "ABUSEIPDB_API_KEY is not configured."
            )

        self._validate_ip_address(indicator)

        payload = self.http_client.get_json(
            self.endpoint,
            headers={
                "Key": self.api_key,
                "Accept": "application/json",
            },
            query_parameters={
                "ipAddress": indicator.value,
                "maxAgeInDays": self.max_age_days,
                "verbose": "",
            },
        )

        provider_data = payload.get("data")

        if not isinstance(provider_data, dict):
            raise ProviderResponseError(
                "AbuseIPDB response did not contain a data object."
            )

        abuse_score = integer_or_none(
            provider_data.get("abuseConfidenceScore")
        )
        total_reports = integer_or_none(provider_data.get("totalReports"))
        distinct_users = integer_or_none(
            provider_data.get("numDistinctUsers")
        )

        normalized_data: dict[str, Any] = {
            "ip_address": provider_data.get(
                "ipAddress",
                indicator.value,
            ),
            "is_public": provider_data.get("isPublic"),
            "ip_version": provider_data.get("ipVersion"),
            "is_whitelisted": provider_data.get("isWhitelisted"),
            "abuse_confidence_score": abuse_score,
            "country_code": provider_data.get("countryCode"),
            "usage_type": provider_data.get("usageType"),
            "isp": provider_data.get("isp"),
            "domain": provider_data.get("domain"),
            "hostnames": provider_data.get("hostnames", []),
            "is_tor": provider_data.get("isTor"),
            "total_reports": total_reports,
            "distinct_reporting_users": distinct_users,
            "last_reported_at": provider_data.get("lastReportedAt"),
            "risk": classify_abuseipdb_risk(
                abuse_score=abuse_score,
                is_whitelisted=provider_data.get("isWhitelisted"),
            ),
        }

        return ProviderResult.success(
            provider=self.name,
            indicator=indicator,
            ttl_seconds=self.default_ttl_seconds,
            data=normalized_data,
        )

    @staticmethod
    def _validate_ip_address(indicator: Indicator) -> None:
        try:
            parsed = ipaddress.ip_address(indicator.value)
        except ValueError as exc:
            raise ProviderResponseError(
                f"Invalid IP address: {indicator.value}"
            ) from exc

        expected_version = 4 if indicator.indicator_type == "IPV4" else 6

        if parsed.version != expected_version:
            raise ProviderResponseError(
                f"Indicator type {indicator.indicator_type} does not match "
                f"IP version {parsed.version}."
            )


def classify_abuseipdb_risk(
    *,
    abuse_score: int | None,
    is_whitelisted: bool | None,
) -> str:
    """
    Convert the provider score into the platform's normalized risk language.

    These are Gen2X policy thresholds, not AbuseIPDB-defined labels.
    """

    if is_whitelisted is True:
        return "LOW"

    if abuse_score is None:
        return "UNKNOWN"

    if abuse_score >= 75:
        return "HIGH"

    if abuse_score >= 25:
        return "MEDIUM"

    return "LOW"


def integer_or_none(value: Any) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None
