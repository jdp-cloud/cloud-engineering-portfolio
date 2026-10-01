"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    provider.py

Part I:
    Provider Domain Models

===============================================================================

Business Objective
-------------------------------------------------------------------------------

Providers connect Gen2X to external security platforms.

Every provider exposes different APIs, authentication methods, and
capabilities. Rather than allowing those implementation details to leak
throughout the platform, Gen2X represents every provider using a common
domain model.

Fusion does not need to understand individual APIs.

Fusion understands Providers.

-------------------------------------------------------------------------------

Architecture

ProviderIdentity
        │
        ▼
ProviderCapabilities
        │
        ▼
ProviderHealth
        │
        ▼
ProviderStatistics
        │
        ▼
ProviderConfiguration

These objects describe a provider.

They do not execute provider logic.

===============================================================================
"""

from __future__ import annotations

from pydantic import Field, field_validator
from datetime import datetime
from typing import Any

from models.base_model import Gen2XModel
from models.enums import (
    IndicatorType,
    PlatformType,
    ProviderStatus,
    ProviderTrustLevel,
    ProviderType,
    ThreatCondition,
)
from models.time_utils import utc_now


# =============================================================================
# Provider Identity
# =============================================================================


class ProviderIdentity(Gen2XModel):
    """
    Represents the identity of a security provider.

    Identity answers one question:

        "Who is this provider?"

    It intentionally contains descriptive information only.
    """

    name: str

    display_name: str

    version: str = "1.0.0"

    platform: PlatformType = PlatformType.UNKNOWN

    provider_type: ProviderType = ProviderType.UNKNOWN

    description: str = ""

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator("name", "display_name")
    @classmethod
    def validate_names(cls, value: str) -> str:
        """
        Normalize and validate provider names.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Provider names cannot be empty."
            )

        return value


# =============================================================================
# Provider Capabilities
# =============================================================================


class ProviderCapabilities(Gen2XModel):
    """
    Describes what a provider is capable of detecting.

    Capabilities define the provider's scope rather than
    its implementation.
    """

    supported_indicators: set[IndicatorType] = Field(
        default_factory=set
    )

    supported_conditions: set[ThreatCondition] = Field(
        default_factory=set
    )

    supports_batch: bool = False

    supports_streaming: bool = False

    supports_realtime: bool = False

    supports_historical_queries: bool = False

    max_batch_size: int | None = None


# =============================================================================
# Provider Health
# =============================================================================


class ProviderHealth(Gen2XModel):
    """
    Represents the operational health of a provider.

    Health describes whether Gen2X can currently rely on
    the provider.

    Health does not describe threat activity.
    """

    status: ProviderStatus = ProviderStatus.UNKNOWN

    trust_level: ProviderTrustLevel = (
        ProviderTrustLevel.UNKNOWN
    )

    last_success: datetime | None = None

    last_failure: datetime | None = None

    last_error: str | None = None


# =============================================================================
# Provider Statistics
# =============================================================================


class ProviderStatistics(Gen2XModel):
    """
    Operational statistics collected for one provider.

    These values help administrators understand provider
    behavior over time.
    """

    total_requests: int = 0

    successful_requests: int = 0

    failed_requests: int = 0

    total_findings: int = 0

    average_latency_ms: float = 0.0


# =============================================================================
# Provider Configuration
# =============================================================================


class ProviderConfiguration(Gen2XModel):
    """
    Configuration shared by provider implementations.

    These settings influence provider behavior without
    exposing provider-specific implementation details.
    """

    enabled: bool = True

    timeout_seconds: int = Field(default=30, gt=0)

    retry_limit: int = Field(default=3, ge=0)

    region: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Before engineers
#
# understand
#
# what a provider
#
# can do...
#
# they should understand
#
# what the provider
#
# is.
#
# Identity.
#
# Capabilities.
#
# Health.
#
# Statistics.
#
# Configuration.
#
# Large systems
#
# become understandable
#
# when complicated ideas
#
# are divided
#
# into smaller,
#
# well-defined pieces.
#
# Fusion doesn't need
#
# to know
#
# how every provider works.
#
# It only needs
#
# a common language
#
# for describing them.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================

# =============================================================================
# Provider
# =============================================================================


class Provider(Gen2XModel):
    """
    Represents one security provider within the Gen2X platform.

    Provider combines the descriptive models defined in Part I into one
    reusable domain object.

    Providers collect observations.

    Fusion reasons about those observations.

    Providers should remain lightweight domain models.

    Business workflows belong to agents and services.
    """

    identity: ProviderIdentity

    capabilities: ProviderCapabilities

    configuration: ProviderConfiguration

    health: ProviderHealth = Field(
        default_factory=ProviderHealth
    )

    statistics: ProviderStatistics = Field(
        default_factory=ProviderStatistics
    )

    # =========================================================================
    # Validation
    # =========================================================================
    #
    # Validation lives where the fields live:
    #
    #     ProviderIdentity validates its names.
    #
    #     ProviderConfiguration constrains timeout_seconds (gt=0)
    #     and retry_limit (ge=0) directly on the field declarations.
    #
    # Composing validated components requires no additional rules here.
    #
    # =========================================================================

    # =========================================================================
    # Convenience Properties
    # =========================================================================

    @property
    def is_enabled(self) -> bool:
        """
        Return True if the provider is enabled.
        """

        return self.configuration.enabled

    @property
    def is_available(self) -> bool:
        """
        Return True if the provider is operational.
        """

        return (
            self.configuration.enabled
            and
            self.health.status == ProviderStatus.SUCCESS
        )

    @property
    def success_rate(self) -> float:
        """
        Return the provider success rate.

        Values range from 0.0 to 1.0.
        """

        total = self.statistics.total_requests

        if total == 0:
            return 0.0

        return (
            self.statistics.successful_requests
            / total
        )

    @property
    def supported_indicator_count(self) -> int:
        """
        Return the number of supported indicator types.
        """

        return len(
            self.capabilities.supported_indicators
        )

    @property
    def supported_condition_count(self) -> int:
        """
        Return the number of supported threat conditions.
        """

        return len(
            self.capabilities.supported_conditions
        )

    # =========================================================================
    # Capability Helpers
    # =========================================================================

    def supports_indicator(
        self,
        indicator: IndicatorType,
    ) -> bool:
        """
        Return True if the provider supports the indicator.
        """

        return (
            indicator
            in self.capabilities.supported_indicators
        )

    def supports_condition(
        self,
        condition: ThreatCondition,
    ) -> bool:
        """
        Return True if the provider supports the threat condition.
        """

        return (
            condition
            in self.capabilities.supported_conditions
        )

    # =========================================================================
    # Operational Helpers
    # =========================================================================

    def increment_success(self) -> None:
        """
        Record a successful provider execution.
        """

        self.statistics.total_requests += 1
        self.statistics.successful_requests += 1

        self.health.status = ProviderStatus.SUCCESS
        self.health.last_success = utc_now()
        self.health.last_error = None

    def increment_failure(
        self,
        message: str,
    ) -> None:
        """
        Record a failed provider execution.
        """

        self.statistics.total_requests += 1
        self.statistics.failed_requests += 1

        self.health.status = ProviderStatus.ERROR
        self.health.last_failure = utc_now()
        self.health.last_error = message

    def record_latency(
        self,
        latency_ms: float,
    ) -> None:
        """
        Update the running average latency.

        Simple rolling average suitable for educational
        purposes.
        """

        total = self.statistics.total_requests

        if total == 0:
            self.statistics.average_latency_ms = latency_ms
            return

        current = self.statistics.average_latency_ms

        self.statistics.average_latency_ms = (
            (current * (total - 1)) + latency_ms
        ) / total

    def reset_statistics(self) -> None:
        """
        Reset operational statistics.

        Provider identity and configuration remain unchanged.
        """

        self.statistics = ProviderStatistics()

    # =========================================================================
    # Lifecycle Helpers
    # =========================================================================

    def mark_available(self) -> None:
        """
        Mark the provider as operational.
        """

        self.health.status = ProviderStatus.SUCCESS

    def mark_unavailable(
        self,
        message: str,
    ) -> None:
        """
        Mark the provider as unavailable.
        """

        self.health.status = ProviderStatus.ERROR
        self.health.last_error = message
        self.health.last_failure = utc_now()

    def clear_error(self) -> None:
        """
        Clear the recorded provider error.
        """

        self.health.last_error = None

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise human-readable description.
        """

        state = (
            "Enabled"
            if self.is_enabled
            else "Disabled"
        )

        health = self.health.status.value

        return (
            f"{self.identity.display_name} "
            f"({self.identity.platform.value}, "
            f"{state}, "
            f"{health})"
        )

    # =========================================================================
    # Serialization
    # =========================================================================
    #
    # to_dict(), to_json(), and from_dict() are inherited from Gen2XModel.
    #
    # The inherited implementations understand nested models,
    # enumerations, and datetimes in both directions:
    #
    #     provider == Provider.from_dict(provider.to_dict())
    #
    # =========================================================================


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Every provider
#
# sees
#
# a different part
#
# of reality.
#
# One watches
#
# repositories.
#
# Another watches
#
# cloud accounts.
#
# Another watches
#
# network traffic.
#
# None of them
#
# knows
#
# the entire story.
#
# That's why
#
# Fusion exists.
#
# Great engineers
#
# don't expect
#
# one tool
#
# to answer
#
# every question.
#
# They combine
#
# many perspectives
#
# into one
#
# understandable picture.
#
# Architecture
#
# isn't about
#
# making
#
# one component
#
# smarter.
#
# It's about
#
# helping
#
# many components
#
# work together.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================
