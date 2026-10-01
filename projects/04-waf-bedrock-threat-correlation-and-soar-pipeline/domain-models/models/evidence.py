"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    evidence.py

Part I:
    Evidence Domain Models

===============================================================================

Business Objective
-------------------------------------------------------------------------------

Security providers observe the world.

Fusion reasons about those observations.

The classes in this module describe one observation without attempting to
interpret it.

By separating observations from analysis, Gen2X keeps evidence portable,
testable, and reusable across providers.

===============================================================================
"""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator
from datetime import datetime
from hashlib import sha256
from typing import Any

from models.base_model import Gen2XModel
from models.enums import (
    IndicatorSource,
    IndicatorType,
    PlatformType,
    ProviderTrustLevel,
    ProviderType,
    ThreatCondition,
    ThreatConfidence,
    ThreatSeverity,
)
from models.time_utils import utc_now


# =============================================================================
# Evidence Identity
# =============================================================================


class EvidenceIdentity(Gen2XModel):
    """
    Identifies one provider observation.

    Identity answers one question:

        "Who observed this, and when?"
    """

    evidence_id: str

    provider_name: str

    provider_type: ProviderType

    provider_platform: PlatformType

    provider_version: str = "1.0.0"

    observed_at: datetime = Field(
        default_factory=utc_now
    )

    collected_at: datetime = Field(
        default_factory=utc_now
    )

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, value: str) -> str:
        """
        Normalize and validate the provider name.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "provider_name cannot be empty."
            )

        return value

    @property
    def observation_key(self) -> str:
        """
        Return a deterministic identifier for this observation.

        Unlike evidence_id, the observation key identifies the
        observation itself rather than the record storing it.

        Useful for:

            • Duplicate detection

            • Correlation

            • Replay protection

            • Future distributed synchronization
        """

        source = "|".join(

            [

                self.provider_name.casefold(),

                self.provider_platform.value,

                self.provider_version,

                self.observed_at.isoformat(),

            ]

        )

        return sha256(
            source.encode("utf-8")
        ).hexdigest()


# =============================================================================
# Evidence Indicator
# =============================================================================


class EvidenceIndicator(Gen2XModel):
    """
    Represents what the provider observed.

    Indicators describe observations.

    They do not describe conclusions.
    """

    indicator_type: IndicatorType

    indicator_value: str

    indicator_source: IndicatorSource

    condition: ThreatCondition

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator("indicator_value")
    @classmethod
    def validate_indicator_value(cls, value: str) -> str:
        """
        Normalize and validate the observed indicator value.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "indicator_value cannot be empty."
            )

        return value


# =============================================================================
# Evidence Source
# =============================================================================


class EvidenceSource(Gen2XModel):
    """
    Describes where the observation originated.

    These fields intentionally remain generic so they can
    represent AWS, Azure, GCP, GitHub, or on-premises systems.
    """

    account_id: str | None = None

    region: str | None = None

    resource_id: str | None = None

    repository: str | None = None

    hostname: str | None = None

    ip_address: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# =============================================================================
# Evidence Context
# =============================================================================


class EvidenceContext(Gen2XModel):
    """
    Provides additional context for an observation.

    Context represents provider knowledge at the time the
    observation was collected.

    Fusion may later combine multiple observations into a
    different assessment.
    """

    severity: ThreatSeverity = ThreatSeverity.UNKNOWN

    confidence: ThreatConfidence = (
        ThreatConfidence.UNKNOWN
    )

    provider_trust: ProviderTrustLevel = (
        ProviderTrustLevel.UNKNOWN
    )

    expires_at: datetime | None = None

    tags: set[str] = Field(
        default_factory=set
    )

    notes: str = ""


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Before there is
#
# a threat...
#
# there is
#
# an observation.
#
# Before there is
#
# a conclusion...
#
# there is
#
# evidence.
#
# Good engineers
#
# resist
#
# the temptation
#
# to skip
#
# directly
#
# to answers.
#
# They first ask:
#
# "What do we actually know?"
#
# Everything else
#
# should be built
#
# on that foundation.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================



# =============================================================================
# Threat Evidence
# =============================================================================


class ThreatEvidence(Gen2XModel):
    """
    Represents one normalized security observation.

    ThreatEvidence is the common language spoken by every provider
    within the Gen2X platform.

    Providers observe.

    Fusion reasons.

    Reports communicate.

    ThreatEvidence intentionally represents observations rather than
    conclusions.
    """

    identity: EvidenceIdentity

    indicator: EvidenceIndicator

    source: EvidenceSource = Field(
        default_factory=EvidenceSource
    )

    context: EvidenceContext = Field(
        default_factory=EvidenceContext
    )

    # =========================================================================
    # Validation
    # =========================================================================
    #
    # Field-level rules live on the component models:
    #
    #     EvidenceIdentity validates provider_name.
    #
    #     EvidenceIndicator validates indicator_value.
    #
    # Only the rule that spans components lives here.
    #
    # =========================================================================

    @model_validator(mode="after")
    def validate_expiry(self) -> "ThreatEvidence":
        """
        Validate rules that span multiple components.
        """

        if (
            self.context.expires_at is not None
            and
            self.context.expires_at
            <= self.identity.observed_at
        ):
            raise ValueError(
                "expires_at must occur after observed_at."
            )

        return self

    # =========================================================================
    # Forwarding Properties
    # =========================================================================

    @property
    def evidence_id(self) -> str:
        return self.identity.evidence_id

    @property
    def provider_name(self) -> str:
        return self.identity.provider_name

    @property
    def provider_platform(self) -> PlatformType:
        return self.identity.provider_platform

    @property
    def provider_type(self) -> ProviderType:
        return self.identity.provider_type

    @property
    def observation_key(self) -> str:
        return self.identity.observation_key

    @property
    def observed_at(self) -> datetime:
        return self.identity.observed_at

    @property
    def collected_at(self) -> datetime:
        return self.identity.collected_at

    @property
    def indicator_type(self) -> IndicatorType:
        return self.indicator.indicator_type

    @property
    def indicator_value(self) -> str:
        return self.indicator.indicator_value

    @property
    def indicator_source(self) -> IndicatorSource:
        return self.indicator.indicator_source

    @property
    def condition(self) -> ThreatCondition:
        return self.indicator.condition

    @property
    def severity(self) -> ThreatSeverity:
        return self.context.severity

    @property
    def confidence(self) -> ThreatConfidence:
        return self.context.confidence

    @property
    def provider_trust(self) -> ProviderTrustLevel:
        return self.context.provider_trust

    @property
    def expires_at(self) -> datetime | None:
        return self.context.expires_at

    # =========================================================================
    # Derived Properties
    # =========================================================================

    @property
    def age(self):
        """
        Return the age of the observation.
        """

        return utc_now() - self.observed_at

    @property
    def age_seconds(self) -> float:
        """
        Return the observation age in seconds.
        """

        return self.age.total_seconds()

    @property
    def is_expired(self) -> bool:
        """
        Return True if the evidence has expired.
        """

        if self.expires_at is None:
            return False

        return utc_now() >= self.expires_at

    @property
    def is_usable(self) -> bool:
        """
        Return True if the evidence is eligible for
        deterministic reasoning.
        """

        return not self.is_expired

    # =========================================================================
    # Matching Helpers
    # =========================================================================

    def matches_indicator(
        self,
        indicator: IndicatorType,
    ) -> bool:
        return self.indicator_type == indicator

    def matches_provider(
        self,
        provider_name: str,
    ) -> bool:
        return (
            self.provider_name.casefold()
            ==
            provider_name.casefold()
        )

    def matches_condition(
        self,
        condition: ThreatCondition,
    ) -> bool:
        return self.condition == condition

    def matches_platform(
        self,
        platform: PlatformType,
    ) -> bool:
        return self.provider_platform == platform

    def matches_tag(
        self,
        tag: str,
    ) -> bool:
        return tag in self.context.tags

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise human-readable description.
        """

        return (
            f"{self.provider_name} observed "
            f"{self.condition.value} "
            f"for "
            f"{self.indicator_value}"
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
    #     evidence == ThreatEvidence.from_dict(evidence.to_dict())
    #
    # =========================================================================


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Engineers
#
# naturally want
#
# answers.
#
# Fusion
#
# asks for
#
# observations
#
# first.
#
# Every conclusion
#
# begins
#
# as evidence.
#
# Every investigation
#
# begins
#
# as curiosity.
#
# Great engineers
#
# never stop asking
#
# one simple question.
#
# "What do we actually know?"
#
# Everything else
#
# follows from there.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================
