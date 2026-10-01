"""
mitre_attack.py

MITRE ATT&CK enrichment provider.

Unlike an IP reputation provider, MITRE ATT&CK does not determine whether an
IP address is malicious.

This provider enriches ATT&CK technique IDs that Agent 10 or an earlier
correlation agent has already inferred from observed behavior.

Example:

    Repeated authentication failures
        -> deterministic mapping
        -> T1110
        -> MITRE provider supplies name, description, tactics, and metadata
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


# The URL is configurable because ATT&CK distribution locations and versions
# may change. Production deployments should pin and validate a known version.
DEFAULT_MITRE_STIX_URL = (
    "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/"
    "master/enterprise-attack/enterprise-attack.json"
)


class MitreAttackProvider(BaseThreatIntelProvider):
    """
    Resolve MITRE ATT&CK technique identifiers.

    This provider may be invoked for any indicator, but only when the
    investigation context includes candidate ATT&CK technique IDs.
    """

    name = "mitre_attack"

    supported_indicator_types = frozenset(
        {
            "IPV4",
            "IPV6",
            "DOMAIN",
            "URL",
            "SHA256",
            "SHA1",
            "MD5",
            "CVE",
            "USER_AGENT",
        }
    )

    default_ttl_seconds = 2_592_000  # 30 days
    error_ttl_seconds = 3_600

    def __init__(
        self,
        *,
        stix_url: str | None = None,
        bundle_memory_ttl_seconds: int = 21_600,
        http_client: JsonHttpClient | None = None,
    ) -> None:
        self.stix_url = (
            stix_url
            or os.getenv("MITRE_STIX_URL")
            or DEFAULT_MITRE_STIX_URL
        )

        self.bundle_memory_ttl_seconds = bundle_memory_ttl_seconds
        self.http_client = http_client or JsonHttpClient(
            timeout_seconds=20,
            max_attempts=3,
        )

        self._technique_index: dict[str, dict[str, Any]] = {}
        self._bundle_loaded_at: int = 0
        self._bundle_lock = threading.Lock()

    def lookup(
        self,
        indicator: Indicator,
        context: Mapping[str, Any],
    ) -> ProviderResult:
        requested_ids = normalize_technique_ids(
            context.get("candidate_technique_ids", [])
        )

        if not requested_ids:
            return ProviderResult.not_found(
                provider=self.name,
                indicator=indicator,
                ttl_seconds=self.default_ttl_seconds,
                data={
                    "techniques": [],
                    "reason": (
                        "No candidate ATT&CK technique IDs were supplied by "
                        "the deterministic correlation process."
                    ),
                },
            )

        technique_index = self._get_technique_index()

        matched: list[dict[str, Any]] = []
        unmatched: list[str] = []

        for technique_id in requested_ids:
            technique = technique_index.get(technique_id)

            if technique is None:
                unmatched.append(technique_id)
                continue

            matched.append(technique)

        data = {
            "techniques": matched,
            "matched_technique_ids": [
                technique["technique_id"] for technique in matched
            ],
            "unmatched_technique_ids": unmatched,
        }

        if not matched:
            return ProviderResult.not_found(
                provider=self.name,
                indicator=indicator,
                ttl_seconds=self.default_ttl_seconds,
                data=data,
            )

        return ProviderResult.success(
            provider=self.name,
            indicator=indicator,
            ttl_seconds=self.default_ttl_seconds,
            data=data,
        )

    def _get_technique_index(self) -> dict[str, dict[str, Any]]:
        now = int(time.time())

        if (
            self._technique_index
            and now - self._bundle_loaded_at
            < self.bundle_memory_ttl_seconds
        ):
            return self._technique_index

        with self._bundle_lock:
            now = int(time.time())

            if (
                self._technique_index
                and now - self._bundle_loaded_at
                < self.bundle_memory_ttl_seconds
            ):
                return self._technique_index

            bundle = self.http_client.get_json(self.stix_url)
            objects = bundle.get("objects")

            if not isinstance(objects, list):
                raise ProviderResponseError(
                    "MITRE STIX bundle did not contain an objects list."
                )

            index: dict[str, dict[str, Any]] = {}

            for stix_object in objects:
                technique = self._normalize_attack_pattern(stix_object)

                if technique is None:
                    continue

                index[technique["technique_id"]] = technique

            self._technique_index = index
            self._bundle_loaded_at = now

            return self._technique_index

    @staticmethod
    def _normalize_attack_pattern(
        stix_object: Any,
    ) -> dict[str, Any] | None:
        if not isinstance(stix_object, dict):
            return None

        if stix_object.get("type") != "attack-pattern":
            return None

        if stix_object.get("revoked") is True:
            return None

        if stix_object.get("x_mitre_deprecated") is True:
            return None

        technique_id = extract_attack_id(
            stix_object.get("external_references", [])
        )

        if technique_id is None:
            return None

        kill_chain_phases = stix_object.get("kill_chain_phases", [])

        tactics = []

        if isinstance(kill_chain_phases, list):
            for phase in kill_chain_phases:
                if not isinstance(phase, dict):
                    continue

                phase_name = phase.get("phase_name")

                if isinstance(phase_name, str):
                    tactics.append(phase_name)

        return {
            "technique_id": technique_id,
            "name": stix_object.get("name"),
            "description": stix_object.get("description"),
            "tactics": sorted(set(tactics)),
            "platforms": stix_object.get("x_mitre_platforms", []),
            "is_subtechnique": stix_object.get(
                "x_mitre_is_subtechnique",
                False,
            ),
            "created": stix_object.get("created"),
            "modified": stix_object.get("modified"),
        }


def extract_attack_id(external_references: Any) -> str | None:
    if not isinstance(external_references, list):
        return None

    for reference in external_references:
        if not isinstance(reference, dict):
            continue

        if reference.get("source_name") != "mitre-attack":
            continue

        external_id = reference.get("external_id")

        if isinstance(external_id, str) and external_id.startswith("T"):
            return external_id.upper()

    return None


def normalize_technique_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized = []

    for item in value:
        if not isinstance(item, str):
            continue

        technique_id = item.strip().upper()

        if technique_id.startswith("T"):
            normalized.append(technique_id)

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(normalized))
