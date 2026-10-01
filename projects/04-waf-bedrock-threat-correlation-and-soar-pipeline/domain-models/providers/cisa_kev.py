"""
cisa_kev.py

CISA Known Exploited Vulnerabilities provider.

This provider supports CVE indicators.

It downloads the CISA KEV JSON catalog, creates a dictionary indexed by CVE
identifier, and checks whether the supplied CVE appears in the catalog.

Important distinction:

    Not present in KEV != vulnerability is safe.

It only means the vulnerability was not present in the catalog version that
this provider retrieved.
"""

from __future__ import annotations

import os
import threading
import time

from typing import Any, Mapping

from .base_provider import (
    BaseThreatIntelProvider,
    Indicator,
    JsonHttpClient,
    ProviderResponseError,
    ProviderResult,
)


DEFAULT_CISA_KEV_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/"
    "known_exploited_vulnerabilities.json"
)


class CisaKevProvider(BaseThreatIntelProvider):
    """Look up CVE identifiers in the CISA KEV catalog."""

    name = "cisa_kev"
    supported_indicator_types = frozenset({"CVE"})

    # KEV data can be refreshed daily for this instructional platform.
    default_ttl_seconds = 86_400
    error_ttl_seconds = 900

    def __init__(
        self,
        *,
        catalog_url: str | None = None,
        catalog_memory_ttl_seconds: int = 3_600,
        http_client: JsonHttpClient | None = None,
    ) -> None:
        self.catalog_url = (
            catalog_url
            or os.getenv("CISA_KEV_URL")
            or DEFAULT_CISA_KEV_URL
        )

        self.catalog_memory_ttl_seconds = catalog_memory_ttl_seconds
        self.http_client = http_client or JsonHttpClient()

        self._catalog_index: dict[str, dict[str, Any]] = {}
        self._catalog_metadata: dict[str, Any] = {}
        self._catalog_loaded_at: int = 0
        self._catalog_lock = threading.Lock()

    def lookup(
        self,
        indicator: Indicator,
        context: Mapping[str, Any],
    ) -> ProviderResult:
        cve_id = indicator.value.strip().upper()

        catalog_index, metadata = self._get_catalog()
        vulnerability = catalog_index.get(cve_id)

        if vulnerability is None:
            return ProviderResult.not_found(
                provider=self.name,
                indicator=indicator,
                ttl_seconds=self.default_ttl_seconds,
                data={
                    "known_exploited": False,
                    "catalog_version": metadata.get("catalogVersion"),
                    "catalog_released": metadata.get("dateReleased"),
                    "interpretation": (
                        "The CVE was not present in the retrieved CISA KEV "
                        "catalog. This does not establish that exploitation "
                        "has never occurred."
                    ),
                },
            )

        normalized_data = {
            "known_exploited": True,
            "cve_id": vulnerability.get("cveID"),
            "vendor_project": vulnerability.get("vendorProject"),
            "product": vulnerability.get("product"),
            "vulnerability_name": vulnerability.get("vulnerabilityName"),
            "date_added": vulnerability.get("dateAdded"),
            "short_description": vulnerability.get("shortDescription"),
            "required_action": vulnerability.get("requiredAction"),
            "due_date": vulnerability.get("dueDate"),
            "known_ransomware_campaign_use": (
                vulnerability.get("knownRansomwareCampaignUse")
            ),
            "notes": vulnerability.get("notes"),
            "cwes": vulnerability.get("cwes", []),
            "catalog_version": metadata.get("catalogVersion"),
            "catalog_released": metadata.get("dateReleased"),
        }

        return ProviderResult.success(
            provider=self.name,
            indicator=indicator,
            ttl_seconds=self.default_ttl_seconds,
            data=normalized_data,
        )

    def _get_catalog(
        self,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        now = int(time.time())

        if (
            self._catalog_index
            and now - self._catalog_loaded_at
            < self.catalog_memory_ttl_seconds
        ):
            return self._catalog_index, self._catalog_metadata

        # Lambda may process concurrent work inside the same execution
        # environment. The lock prevents duplicate catalog downloads.
        with self._catalog_lock:
            now = int(time.time())

            if (
                self._catalog_index
                and now - self._catalog_loaded_at
                < self.catalog_memory_ttl_seconds
            ):
                return self._catalog_index, self._catalog_metadata

            payload = self.http_client.get_json(self.catalog_url)

            vulnerabilities = payload.get("vulnerabilities")

            if not isinstance(vulnerabilities, list):
                raise ProviderResponseError(
                    "CISA KEV response did not contain a vulnerabilities list."
                )

            index: dict[str, dict[str, Any]] = {}

            for vulnerability in vulnerabilities:
                if not isinstance(vulnerability, dict):
                    continue

                cve_id = vulnerability.get("cveID")

                if isinstance(cve_id, str) and cve_id:
                    index[cve_id.upper()] = vulnerability

            self._catalog_index = index
            self._catalog_metadata = {
                "catalogVersion": payload.get("catalogVersion"),
                "dateReleased": payload.get("dateReleased"),
                "count": payload.get("count"),
            }
            self._catalog_loaded_at = now

            return self._catalog_index, self._catalog_metadata
