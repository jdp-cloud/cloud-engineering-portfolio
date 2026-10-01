"""
provider_registry.py

Provider discovery and execution for Agent 10.
"""

from __future__ import annotations

import logging

from collections.abc import Iterable, Mapping
from typing import Any

from providers import (
    AbuseIpDbProvider,
    BaseThreatIntelProvider,
    CisaKevProvider,
    Indicator,
    MitreAttackProvider,
    ProviderResult,
)


LOGGER = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Holds all configured provider implementations.

    Agent 10 asks the registry for relevant providers rather than importing
    or invoking each provider directly.
    """

    def __init__(
        self,
        providers: Iterable[BaseThreatIntelProvider],
    ) -> None:
        self._providers = {
            provider.name: provider
            for provider in providers
        }

    def compatible_providers(
        self,
        indicator: Indicator,
    ) -> list[BaseThreatIntelProvider]:
        return [
            provider
            for provider in self._providers.values()
            if provider.supports(indicator)
        ]

    def enrich(
        self,
        indicator: Indicator,
        *,
        context: Mapping[str, Any] | None = None,
        enabled_providers: set[str] | None = None,
    ) -> list[ProviderResult]:
        results: list[ProviderResult] = []

        for provider in self.compatible_providers(indicator):
            if (
                enabled_providers is not None
                and provider.name not in enabled_providers
            ):
                continue

            LOGGER.info(
                "Running provider=%s indicator=%s",
                provider.name,
                indicator.indicator_id,
            )

            result = provider.enrich(
                indicator,
                context=context,
            )

            results.append(result)

        return results


def build_default_registry() -> ProviderRegistry:
    """
    Construct the providers enabled for the first Agent 10 implementation.

    Provider constructors read credentials and configurable endpoints from
    environment variables.
    """

    return ProviderRegistry(
        providers=[
            CisaKevProvider(),
            AbuseIpDbProvider(),
            MitreAttackProvider(),
        ]
    )
