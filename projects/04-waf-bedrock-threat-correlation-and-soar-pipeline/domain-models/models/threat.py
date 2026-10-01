"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    threat.py

Part I:
    Threat Foundation Models

===============================================================================

Business Objective
-------------------------------------------------------------------------------

Threats represent security conclusions produced from evaluated evidence.

Providers create observations.

ThreatEvidence preserves those observations.

EvidenceAggregator organizes them.

Fusion evaluates them.

Threat models preserve the resulting conclusion.

A Threat therefore represents what Gen2X currently believes the available
evidence means.

It does not perform threat analysis itself.

===============================================================================
"""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from models.base_model import Gen2XModel
from datetime import datetime
from typing import Any
from uuid import uuid4

# ThreatAssessment (the enum) is imported under an alias because this
# module defines a ThreatAssessment dataclass of its own.
from models.enums import ThreatAssessment as ThreatAssessmentType
from models.enums import (
    ThreatCondition,
    ThreatConfidence,
    ThreatSeverity,
)

from utils.time import utc_now


# =============================================================================
# Threat Identity
# =============================================================================


class ThreatIdentity(Gen2XModel):
    """
    Identifies one threat known to Gen2X.

    threat_id identifies this particular threat record.

    indicator_key optionally connects the threat to the Indicator
    associated with the investigation.

    Not every threat must map to one indicator.

    Future threats may represent:

        • Account compromise
        • Identity compromise
        • Cloud resource exposure
        • Repository compromise
        • Multi-indicator campaigns
    """

    condition: ThreatCondition

    threat_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    indicator_key: str | None = None

    created_at: datetime = Field(
        default_factory=utc_now
    )

    updated_at: datetime = Field(
        default_factory=utc_now
    )

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator("threat_id")
    @classmethod
    def validate_threat_id(cls, value: str) -> str:
        """
        Normalize and validate the threat identifier.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "threat_id cannot be empty."
            )

        return value

    @field_validator("indicator_key")
    @classmethod
    def normalize_indicator_key(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize the optional indicator key.

        Blank values become None.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    @model_validator(mode="after")
    def validate_timeline(self) -> "ThreatIdentity":
        """
        Validate that the identity timeline is coherent.
        """

        if self.updated_at < self.created_at:
            raise ValueError(
                "updated_at cannot occur before created_at."
            )

        return self


# =============================================================================
# Threat Assessment
# =============================================================================


class ThreatAssessment(Gen2XModel):
    """
    Represents Fusion's current assessment of a threat.

    Assessment values are conclusions derived from evidence.

    They should not be confused with values reported by an
    individual provider.

    Example:

        Provider A reports:

            severity = HIGH

        Provider B reports:

            severity = CRITICAL

        Fusion may conclude:

            severity = CRITICAL
            confidence = HIGH

    The Threat stores Fusion's conclusion.

    It does not calculate that conclusion.
    """

    severity: ThreatSeverity = (
        ThreatSeverity.UNKNOWN
    )

    confidence: ThreatConfidence = (
        ThreatConfidence.UNKNOWN
    )

    assessment: ThreatAssessmentType = (
        ThreatAssessmentType.UNKNOWN
    )


# =============================================================================
# Threat Context
# =============================================================================


class ThreatContext(Gen2XModel):
    """
    Describes the environment affected by a threat.

    Context remains provider-neutral.

    This allows the same Threat model to represent security
    conditions affecting:

        • AWS
        • Azure
        • GCP
        • GitHub
        • On-premises environments

    Fields are optional because not every threat will have every
    form of environmental context.
    """

    account_id: str | None = None

    region: str | None = None

    resource_id: str | None = None

    repository: str | None = None

    user_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


# =============================================================================
# Threat Provenance
# =============================================================================


class ThreatProvenance(Gen2XModel):
    """
    Records the evidence supporting a threat.

    Provenance answers:

        "Why does Gen2X believe this threat exists?"

    It preserves the relationship between a threat and the evidence
    used to produce the assessment.

    Provenance does not determine whether the evidence is correct.

    Fusion owns that responsibility.
    """

    evidence_ids: set[str] = Field(
        default_factory=set
    )

    provider_names: set[str] = Field(
        default_factory=set
    )

    assessment_id: str | None = None

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator("assessment_id")
    @classmethod
    def normalize_assessment_id(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize the optional assessment identifier.

        Blank values become None.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    # =========================================================================
    # Derived Properties
    # =========================================================================

    @property
    def evidence_count(self) -> int:
        """
        Return the number of evidence records supporting
        the threat.

        The count is derived rather than stored so the value
        cannot become inconsistent with evidence_ids.
        """

        return len(
            self.evidence_ids
        )

    @property
    def provider_count(self) -> int:
        """
        Return the number of providers supporting the threat.

        The count is derived from provider_names.
        """

        return len(
            self.provider_names
        )


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Evidence
#
# and conclusions
#
# are not
#
# the same thing.
#
# A provider
#
# may observe
#
# an exposed token.
#
# Another provider
#
# may observe
#
# unusual authentication.
#
# Another
#
# may observe
#
# unexpected network activity.
#
# Those are
#
# observations.
#
# Important observations...
#
# but observations
#
# nonetheless.
#
# Fusion
#
# has a different job.
#
# It asks:
#
# "What do these observations
# mean together?"
#
# That question
#
# is where
#
# evidence
#
# becomes
#
# assessment.
#
# And assessment
#
# may eventually
#
# become
#
# a Threat.
#
# Good engineers
#
# preserve
#
# the distance
#
# between
#
# what was observed
#
# and
#
# what they believe.
#
# Because sometimes
#
# new evidence
#
# changes
#
# what we believe.
#
# That isn't
#
# failure.
#
# That is
#
# investigation.
#
# Systems
#
# should therefore
#
# preserve
#
# not only
#
# the conclusion...
#
# but also
#
# the evidence
#
# that allowed
#
# humans
#
# and machines
#
# to reach it.
#
# Conclusions
#
# without provenance
#
# are assertions.
#
# Conclusions
#
# with provenance
#
# can be examined.
#
# And security engineering
#
# should always
#
# leave room
#
# for examination.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Steak Acquisition Division
#
# =============================================================================


# =============================================================================
# Threat
# =============================================================================


class Threat(Gen2XModel):
    """
    Represents one security threat known to Gen2X.

    Threat combines:

        • Identity
        • Assessment
        • Context
        • Provenance

    into one reusable domain object.

    A Threat represents a conclusion derived from evaluated evidence.

    Fusion determines what the evidence means.

    Threat preserves that conclusion.
    """

    identity: ThreatIdentity

    assessment: ThreatAssessment

    context: ThreatContext = Field(
        default_factory=ThreatContext
    )

    provenance: ThreatProvenance = Field(
        default_factory=ThreatProvenance
    )

    # =========================================================================
    # Validation
    # =========================================================================
    #
    # Validation lives where the fields live:
    #
    #     ThreatIdentity validates threat_id, indicator_key, and the
    #     created_at / updated_at timeline.
    #
    #     ThreatProvenance normalizes assessment_id.
    #
    # Composing validated components requires no additional rules here.
    #
    # =========================================================================

    # =========================================================================
    # Identity Properties
    # =========================================================================

    @property
    def threat_id(self) -> str:
        """
        Return the unique threat identifier.
        """

        return self.identity.threat_id

    @property
    def condition(self) -> ThreatCondition:
        """
        Return the threat condition.
        """

        return self.identity.condition

    @property
    def indicator_key(self) -> str | None:
        """
        Return the associated indicator key when one exists.
        """

        return self.identity.indicator_key

    @property
    def created_at(self) -> datetime:
        """
        Return the threat creation timestamp.
        """

        return self.identity.created_at

    @property
    def updated_at(self) -> datetime:
        """
        Return the most recent threat update timestamp.
        """

        return self.identity.updated_at

    # =========================================================================
    # Assessment Properties
    # =========================================================================

    @property
    def severity(self) -> ThreatSeverity:
        """
        Return Fusion's current severity assessment.
        """

        return self.assessment.severity

    @property
    def confidence(self) -> ThreatConfidence:
        """
        Return Fusion's current confidence assessment.
        """

        return self.assessment.confidence

    @property
    def assessment_type(self) -> ThreatAssessmentType:
        """
        Return Fusion's current assessment classification.
        """

        return self.assessment.assessment

    # =========================================================================
    # Provenance Properties
    # =========================================================================

    @property
    def evidence_count(self) -> int:
        """
        Return the number of supporting evidence records.
        """

        return self.provenance.evidence_count

    @property
    def provider_count(self) -> int:
        """
        Return the number of supporting providers.
        """

        return self.provenance.provider_count

    @property
    def evidence_ids(self) -> set[str]:
        """
        Return the evidence identifiers supporting the threat.
        """

        return self.provenance.evidence_ids

    @property
    def provider_names(self) -> set[str]:
        """
        Return the providers supporting the threat.
        """

        return self.provenance.provider_names

    @property
    def assessment_id(self) -> str | None:
        """
        Return the assessment responsible for the current threat
        conclusion when available.
        """

        return self.provenance.assessment_id

    # =========================================================================
    # Derived Properties
    # =========================================================================

    @property
    def age(self):
        """
        Return the amount of time since the threat was created.
        """

        return utc_now() - self.created_at

    @property
    def age_seconds(self) -> float:
        """
        Return the threat age in seconds.
        """

        return self.age.total_seconds()

    @property
    def time_since_update(self):
        """
        Return the amount of time since the threat was updated.
        """

        return utc_now() - self.updated_at

    @property
    def has_evidence(self) -> bool:
        """
        Return True when supporting evidence is present.
        """

        return self.evidence_count > 0

    @property
    def has_multiple_providers(self) -> bool:
        """
        Return True when more than one provider supports the threat.

        This property reports provenance diversity.

        It does not automatically imply higher confidence.
        """

        return self.provider_count > 1

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def touch(self) -> None:
        """
        Update the threat modification timestamp.

        This method records that the threat changed.

        It does not change the threat assessment.
        """

        self.identity.updated_at = utc_now()

    # =========================================================================
    # Evidence Management
    # =========================================================================

    def add_evidence(
        self,
        evidence_id: str,
    ) -> None:
        """
        Associate supporting evidence with the threat.

        Adding evidence does not automatically modify severity,
        confidence, or assessment.

        Fusion remains responsible for interpreting evidence.
        """

        evidence_id = evidence_id.strip()

        if not evidence_id:
            raise ValueError(
                "evidence_id cannot be empty."
            )

        previous_count = self.evidence_count

        self.provenance.evidence_ids.add(
            evidence_id
        )

        if self.evidence_count != previous_count:
            self.touch()

    def remove_evidence(
        self,
        evidence_id: str,
    ) -> None:
        """
        Remove an evidence association when present.

        Removing evidence does not automatically recalculate the
        threat assessment.

        The threat should be reassessed by Fusion when appropriate.
        """

        evidence_id = evidence_id.strip()

        if not evidence_id:
            return

        if evidence_id in self.provenance.evidence_ids:

            self.provenance.evidence_ids.remove(
                evidence_id
            )

            self.touch()

    def has_evidence_id(
        self,
        evidence_id: str,
    ) -> bool:
        """
        Return True when the supplied evidence record supports
        the threat.
        """

        return (
            evidence_id.strip()
            in self.provenance.evidence_ids
        )

    # =========================================================================
    # Provider Management
    # =========================================================================

    def add_provider(
        self,
        provider_name: str,
    ) -> None:
        """
        Associate a supporting provider with the threat.

        Provider participation is provenance.

        It is not itself a confidence calculation.
        """

        provider_name = provider_name.strip()

        if not provider_name:
            raise ValueError(
                "provider_name cannot be empty."
            )

        previous_count = self.provider_count

        self.provenance.provider_names.add(
            provider_name
        )

        if self.provider_count != previous_count:
            self.touch()

    def remove_provider(
        self,
        provider_name: str,
    ) -> None:
        """
        Remove a provider association when present.
        """

        provider_name = provider_name.strip()

        if not provider_name:
            return

        target = provider_name.casefold()

        matching_provider = next(
            (
                provider
                for provider
                in self.provenance.provider_names
                if provider.casefold() == target
            ),
            None,
        )

        if matching_provider is not None:

            self.provenance.provider_names.remove(
                matching_provider
            )

            self.touch()

    def supported_by_provider(
        self,
        provider_name: str,
    ) -> bool:
        """
        Return True when the threat is supported by the
        supplied provider.
        """

        target = provider_name.strip().casefold()

        if not target:
            return False

        return any(
            provider.casefold() == target
            for provider
            in self.provenance.provider_names
        )

    # =========================================================================
    # Assessment Association
    # =========================================================================

    def associate_assessment(
        self,
        assessment_id: str,
    ) -> None:
        """
        Associate the threat with the assessment that produced
        or updated its current conclusion.

        This method records provenance.

        It does not modify the assessment itself.
        """

        assessment_id = assessment_id.strip()

        if not assessment_id:
            raise ValueError(
                "assessment_id cannot be empty."
            )

        if (
            self.provenance.assessment_id
            != assessment_id
        ):
            self.provenance.assessment_id = (
                assessment_id
            )

            self.touch()

    # =============================================================================
    # Threat Matching
    # =============================================================================


    def matches_condition(
        self,
        condition: ThreatCondition,
    ) -> bool:
        """
        Return True when the threat matches the supplied condition.
        """

        return self.condition == condition


    def matches_indicator(
        self,
        indicator_key: str,
    ) -> bool:
        """
        Return True when the threat is associated with the
        supplied indicator key.
        """

        if self.indicator_key is None:
            return False

        return (
            self.indicator_key
            == indicator_key.strip()
        )


    def matches_severity(
        self,
        severity: ThreatSeverity,
    ) -> bool:
        """
        Return True when the threat has the supplied severity.
        """

        return self.severity == severity


    def matches_confidence(
        self,
        confidence: ThreatConfidence,
    ) -> bool:
        """
        Return True when the threat has the supplied confidence.
        """

        return self.confidence == confidence


    # =============================================================================
    # Context Matching
    # =============================================================================


    def affects_account(
        self,
        account_id: str,
    ) -> bool:
        """
        Return True when the threat affects the supplied account.
        """

        if self.context.account_id is None:
            return False

        return (
            self.context.account_id
            == account_id.strip()
        )


    def affects_resource(
        self,
        resource_id: str,
    ) -> bool:
        """
        Return True when the threat affects the supplied resource.
        """

        if self.context.resource_id is None:
            return False

        return (
            self.context.resource_id
            == resource_id.strip()
        )


    def affects_repository(
        self,
        repository: str,
    ) -> bool:
        """
        Return True when the threat affects the supplied repository.
        """

        if self.context.repository is None:
            return False

        return (
            self.context.repository.casefold()
            == repository.strip().casefold()
        )


    def affects_user(
        self,
        user_id: str,
    ) -> bool:
        """
        Return True when the threat affects the supplied identity.
        """

        if self.context.user_id is None:
            return False

        return (
            self.context.user_id.casefold()
            == user_id.strip().casefold()
        )


    # =============================================================================
    # Description
    # =============================================================================


    def describe(self) -> str:
        """
        Return a concise human-readable description of the threat.

        This method is intended for:

            • Logs
            • Diagnostics
            • CLI output
            • Testing

        It is not a ThreatSummary.

        ThreatSummary is a communication model intended for
        human-facing reporting.
        """

        return (
            f"{self.condition.value} "
            f"[severity={self.severity.value}, "
            f"confidence={self.confidence.value}, "
            f"evidence={self.evidence_count}, "
            f"providers={self.provider_count}]"
        )


    # =============================================================================
    # Serialization
    # =============================================================================


    # to_dict(), to_json(), and from_dict() are inherited from Gen2XModel.
    #
    # The inherited implementations understand nested models,
    # enumerations, and datetimes in both directions:
    #
    #     threat == Threat.from_dict(threat.to_dict())
    #
    # Derived counts (evidence_count, provider_count) remain available
    # as properties rather than serialized fields, so the round trip
    # stays lossless.


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# A Threat
#
# is not
#
# an algorithm.
#
# It does not
#
# discover evidence.
#
# It does not
#
# calculate severity.
#
# It does not
#
# decide confidence.
#
# Those jobs
#
# belong elsewhere.
#
# A Threat
#
# has a quieter
#
# responsibility.
#
# It remembers
#
# what was concluded,
#
# what evidence
#
# supported
#
# that conclusion,
#
# and which providers
#
# helped us
#
# understand it.
#
# This matters
#
# because conclusions
#
# change.
#
# New evidence
#
# appears.
#
# Old evidence
#
# disappears.
#
# Providers
#
# disagree.
#
# Investigations
#
# evolve.
#
# A good system
#
# does not pretend
#
# that knowledge
#
# is permanent.
#
# It preserves
#
# what we believed
#
# and why
#
# we believed it.
#
# The model
#
# holds
#
# the conclusion.
#
# Fusion
#
# earns
#
# the conclusion.
#
# Never make
#
# the container
#
# pretend
#
# to be
#
# the thinker.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Porg Sushi Connoisseur
#
# =============================================================================


# =============================================================================
#
# Chewbacca's Final Thoughts 🐾
#
# Security engineering
#
# is filled
#
# with certainty.
#
# "This is malicious."
#
# "This account
# is compromised."
#
# "This system
# is vulnerable."
#
# Those sentences
#
# sound powerful.
#
# But good engineers
#
# ask another question:
#
# "Why?"
#
# A Threat
#
# should always
#
# have an answer.
#
# Not because
#
# the engineer
#
# must always
#
# be correct.
#
# Engineers
#
# will be wrong.
#
# Providers
#
# will be wrong.
#
# Fusion
#
# will sometimes
#
# be wrong.
#
# New evidence
#
# may completely
#
# change
#
# an investigation.
#
# That is
#
# the human condition.
#
# We observe.
#
# We reason.
#
# We decide.
#
# We discover
#
# something new.
#
# And sometimes
#
# we change
#
# our minds.
#
# Good architecture
#
# should permit
#
# that humility.
#
# Preserve
#
# the observation.
#
# Preserve
#
# the evidence.
#
# Preserve
#
# the conclusion.
#
# Preserve
#
# why
#
# the conclusion
#
# was reached.
#
# Then when
#
# the conclusion
#
# changes,
#
# we have not
#
# lost
#
# the journey
#
# that brought us
#
# there.
#
# Software
#
# should not pretend
#
# that humans
#
# possess
#
# perfect knowledge.
#
# Great software
#
# should reflect
#
# how humans
#
# actually understand
#
# the world:
#
# imperfectly,
#
# incrementally,
#
# and with
#
# the capacity
#
# to learn.
#
# Also...
#
# never allow
#
# Mandalorians
#
# to control
#
# the Porg Sushi
#
# supply chain.
#
# Monopolies
#
# are bad
#
# for consumers.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Porg Sushi Entrepreneur
#                                Definitely Not An Economist
#
# =============================================================================
