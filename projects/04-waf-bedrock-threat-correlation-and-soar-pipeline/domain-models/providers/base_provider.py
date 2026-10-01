"""
base_provider.py

Shared provider interfaces for Agent 10 — Threat Intelligence Agent.

Every threat-intelligence provider behaves differently:

- AbuseIPDB evaluates IP addresses.
- CISA KEV evaluates CVE identifiers.
- MITRE ATT&CK describes adversary behavior.
- VirusTotal may evaluate IPs, domains, URLs, and file hashes.

Without a shared interface, the main agent would need custom logic for
every provider.

This module gives every provider the same contract:

    provider.lookup(indicator, context)

and requires every provider to return a ProviderResult.
"""

from __future__ import annotations

import json
import logging
import random
import time
import urllib.error
import urllib.parse
import urllib.request

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ProviderError(Exception):
    """Base exception for threat-intelligence provider failures."""


class ProviderConfigurationError(ProviderError):
    """Raised when a provider is missing required configuration."""


class ProviderAuthenticationError(ProviderError):
    """Raised when a provider rejects credentials."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider's API rate limit is reached."""


class ProviderResponseError(ProviderError):
    """Raised when a provider returns an invalid or unexpected response."""


class UnsupportedIndicatorError(ProviderError):
    """Raised when a provider cannot process the supplied indicator type."""


# ---------------------------------------------------------------------------
# Normalized indicator model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Indicator:
    """
    A normalized threat indicator.

    The indicator_id becomes the DynamoDB partition key.

    Examples:

        IPv4:198.51.100.25
        DOMAIN:example.test
        SHA256:abc123...
        CVE:CVE-2021-44228
    """

    indicator_id: str
    value: str
    indicator_type: str

    @classmethod
    def create(cls, value: str, indicator_type: str) -> "Indicator":
        normalized_type = indicator_type.strip().upper()
        normalized_value = value.strip()

        if not normalized_value:
            raise ValueError("Indicator value cannot be empty.")

        return cls(
            indicator_id=f"{normalized_type}:{normalized_value}",
            value=normalized_value,
            indicator_type=normalized_type,
        )


# ---------------------------------------------------------------------------
# Normalized provider result
# ---------------------------------------------------------------------------

@dataclass
class ProviderResult:
    """
    Standard response returned by every threat-intelligence provider.

    Provider-specific fields belong inside `data`.

    The surrounding structure remains consistent regardless of provider.
    """

    provider: str
    indicator_id: str
    indicator: str
    indicator_type: str
    status: str

    retrieved_at: str
    expires_at: int

    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def success(
        cls,
        *,
        provider: str,
        indicator: Indicator,
        ttl_seconds: int,
        data: Mapping[str, Any],
    ) -> "ProviderResult":
        now = int(time.time())

        return cls(
            provider=provider,
            indicator_id=indicator.indicator_id,
            indicator=indicator.value,
            indicator_type=indicator.indicator_type,
            status="SUCCESS",
            retrieved_at=utc_now_iso(),
            expires_at=now + ttl_seconds,
            data=dict(data),
            error=None,
        )

    @classmethod
    def not_found(
        cls,
        *,
        provider: str,
        indicator: Indicator,
        ttl_seconds: int,
        data: Mapping[str, Any] | None = None,
    ) -> "ProviderResult":
        """
        NOT_FOUND is not necessarily an error.

        For example, a CVE not appearing in CISA KEV simply means that the
        current catalog did not identify it as a known-exploited vulnerability.
        """

        now = int(time.time())

        return cls(
            provider=provider,
            indicator_id=indicator.indicator_id,
            indicator=indicator.value,
            indicator_type=indicator.indicator_type,
            status="NOT_FOUND",
            retrieved_at=utc_now_iso(),
            expires_at=now + ttl_seconds,
            data=dict(data or {}),
            error=None,
        )

    @classmethod
    def failure(
        cls,
        *,
        provider: str,
        indicator: Indicator,
        ttl_seconds: int,
        error: str,
    ) -> "ProviderResult":
        """
        Failed lookups receive a shorter TTL.

        This prevents Agent 10 from repeatedly calling a failing provider for
        every security event while also ensuring the failure is retried soon.
        """

        now = int(time.time())

        return cls(
            provider=provider,
            indicator_id=indicator.indicator_id,
            indicator=indicator.value,
            indicator_type=indicator.indicator_type,
            status="ERROR",
            retrieved_at=utc_now_iso(),
            expires_at=now + ttl_seconds,
            data={},
            error=error,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the result into a DynamoDB-friendly dictionary."""

        return asdict(self)

    def to_source_record(self) -> dict[str, Any]:
        """
        Return only the portion stored under:

            item["sources"][provider_name]
        """

        return {
            "status": self.status,
            "retrieved_at": self.retrieved_at,
            "expires_at": self.expires_at,
            "data": self.data,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# Base provider interface
# ---------------------------------------------------------------------------

class BaseThreatIntelProvider(ABC):
    """
    Abstract base class implemented by all intelligence providers.
    """

    name: str = "base"
    supported_indicator_types: frozenset[str] = frozenset()

    # Successful results usually remain useful longer than provider failures.
    default_ttl_seconds: int = 86_400
    error_ttl_seconds: int = 900

    def supports(self, indicator: Indicator) -> bool:
        """Return True when this provider supports the indicator type."""

        return indicator.indicator_type in self.supported_indicator_types

    def enrich(
        self,
        indicator: Indicator,
        context: Mapping[str, Any] | None = None,
    ) -> ProviderResult:
        """
        Public provider entry point.

        This wrapper performs shared validation and failure normalization.
        Subclasses implement only `lookup()`.
        """

        if not self.supports(indicator):
            raise UnsupportedIndicatorError(
                f"{self.name} does not support "
                f"{indicator.indicator_type} indicators."
            )

        try:
            return self.lookup(indicator, context or {})

        except UnsupportedIndicatorError:
            raise

        except ProviderError as exc:
            LOGGER.warning(
                "Provider %s failed for %s: %s",
                self.name,
                indicator.indicator_id,
                exc,
            )

            return ProviderResult.failure(
                provider=self.name,
                indicator=indicator,
                ttl_seconds=self.error_ttl_seconds,
                error=str(exc),
            )

        except Exception as exc:
            # We normalize unexpected exceptions rather than allowing one
            # provider to terminate the complete Agent 10 investigation.
            LOGGER.exception(
                "Unexpected provider failure: provider=%s indicator=%s",
                self.name,
                indicator.indicator_id,
            )

            return ProviderResult.failure(
                provider=self.name,
                indicator=indicator,
                ttl_seconds=self.error_ttl_seconds,
                error=f"Unexpected provider failure: {type(exc).__name__}",
            )

    @abstractmethod
    def lookup(
        self,
        indicator: Indicator,
        context: Mapping[str, Any],
    ) -> ProviderResult:
        """Perform the provider-specific intelligence lookup."""

        raise NotImplementedError


# ---------------------------------------------------------------------------
# Shared HTTP client
# ---------------------------------------------------------------------------

class JsonHttpClient:
    """
    Small JSON HTTP client based entirely on Python's standard library.

    This avoids requiring `requests` in the initial Lambda package.

    Features:

    - Timeouts
    - Retries
    - Exponential backoff
    - Rate-limit recognition
    - JSON validation
    - User-Agent identification
    """

    def __init__(
        self,
        *,
        timeout_seconds: int = 10,
        max_attempts: int = 3,
        user_agent: str = "Gen2X-Agent10/1.0",
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.user_agent = user_agent

    def get_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        query_parameters: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        final_url = self._build_url(url, query_parameters)

        request_headers = {
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }

        if headers:
            request_headers.update(headers)

        request = urllib.request.Request(
            final_url,
            headers=request_headers,
            method="GET",
        )

        for attempt in range(1, self.max_attempts + 1):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout_seconds,
                ) as response:
                    raw_body = response.read().decode("utf-8")

                try:
                    parsed = json.loads(raw_body)
                except json.JSONDecodeError as exc:
                    raise ProviderResponseError(
                        "Provider returned invalid JSON."
                    ) from exc

                if not isinstance(parsed, dict):
                    raise ProviderResponseError(
                        "Provider JSON response was not an object."
                    )

                return parsed

            except urllib.error.HTTPError as exc:
                if exc.code in {401, 403}:
                    raise ProviderAuthenticationError(
                        f"Provider authentication failed with HTTP {exc.code}."
                    ) from exc

                if exc.code == 429:
                    if attempt == self.max_attempts:
                        raise ProviderRateLimitError(
                            "Provider API rate limit reached."
                        ) from exc

                    self._sleep_before_retry(attempt)
                    continue

                if 500 <= exc.code <= 599 and attempt < self.max_attempts:
                    self._sleep_before_retry(attempt)
                    continue

                raise ProviderResponseError(
                    f"Provider returned HTTP {exc.code}."
                ) from exc

            except urllib.error.URLError as exc:
                if attempt == self.max_attempts:
                    raise ProviderResponseError(
                        f"Could not reach provider: {exc.reason}"
                    ) from exc

                self._sleep_before_retry(attempt)

            except TimeoutError as exc:
                if attempt == self.max_attempts:
                    raise ProviderResponseError(
                        "Provider request timed out."
                    ) from exc

                self._sleep_before_retry(attempt)

        raise ProviderResponseError("Provider request failed.")

    @staticmethod
    def _build_url(
        url: str,
        query_parameters: Mapping[str, Any] | None,
    ) -> str:
        if not query_parameters:
            return url

        encoded = urllib.parse.urlencode(query_parameters)
        separator = "&" if "?" in url else "?"

        return f"{url}{separator}{encoded}"

    @staticmethod
    def _sleep_before_retry(attempt: int) -> None:
        # Exponential backoff with a small random jitter prevents many Lambda
        # invocations from retrying simultaneously.
        delay = (2 ** (attempt - 1)) + random.uniform(0.0, 0.5)
        time.sleep(delay)


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
