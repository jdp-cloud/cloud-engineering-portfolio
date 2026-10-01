"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    report.py

Part I:
    Human Communication Models

===============================================================================

Business Objective
-------------------------------------------------------------------------------

Reports translate security domain state into information that humans can
understand, review, communicate, and act upon.

The report layer does not determine security facts.

It presents facts already established by:

    • Evidence
    • Fusion
    • Threat assessment
    • Response recommendation
    • Governance

Part I defines the human-facing foundation of a report:

    • ReportIdentity
    • ReportAudience
    • ExecutiveSummary
    • ThreatSummary
    • ResponseSummary

Summarization changes presentation.

It must never silently change the underlying facts.

===============================================================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import (
    Field,
    field_validator,
)

from models.base_model import Gen2XModel

# Aliased imports:
#
#   ResponseApproval is the approval-state vocabulary; report models
#   refer to it as ApprovalStatus.
#
#   The ReportAudience enum is aliased because this module defines a
#   ReportAudience model of its own.
from models.enums import ReportAudience as ReportAudienceType
from models.enums import ResponseApproval as ApprovalStatus
from models.enums import (
    InvestigationStatus,
    ReportTechnicalLevel,
    ReportType,
    ResponseAction,
    ResponsePriority,
    ThreatCondition,
    ThreatConfidence,
    ThreatSeverity,
)

from utils.time import utc_now


# =============================================================================
# Report Identity
# =============================================================================


class ReportIdentity(Gen2XModel):
    """
    Identifies one report produced by Gen2X.

    ReportIdentity provides traceability between the report and the
    domain objects responsible for its contents.

    A report may reference:

        • The Fusion assessment
        • The resulting Threat
        • The recommended Response

    response_id remains optional because a report may be created before
    a response recommendation exists.
    """

    report_id: UUID = Field(
        default_factory=uuid4
    )

    report_type: ReportType

    threat_id: str

    assessment_id: str | None = None

    response_id: UUID | None = None

    created_at: datetime = Field(
        default_factory=utc_now
    )

    updated_at: datetime = Field(
        default_factory=utc_now
    )

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator(
        "threat_id",
    )
    @classmethod
    def validate_threat_id(
        cls,
        value: str,
    ) -> str:
        """
        Normalize and validate the associated threat identifier.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "threat_id cannot be empty."
            )

        return value

    @field_validator(
        "assessment_id",
    )
    @classmethod
    def normalize_assessment_id(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize the optional assessment identifier.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def touch(self) -> None:
        """
        Update the report modification timestamp.
        """

        self.updated_at = utc_now()


# =============================================================================
# Report Audience
# =============================================================================


class ReportAudience(Gen2XModel):
    """
    Describes the intended audience for a report.

    The same security facts may require different presentation
    depending on the reader.

    Examples include:

        • Executive leadership
        • SOC analysts
        • Security engineers
        • Cloud engineers
        • Auditors
        • Incident responders

    Audience changes presentation.

    Audience must never change facts.
    """

    audience: ReportAudienceType

    technical_level: ReportTechnicalLevel

    intended_for: list[str] = Field(
        default_factory=list
    )

    distribution: list[str] = Field(
        default_factory=list
    )

    # =========================================================================
    # Normalization
    # =========================================================================

    @field_validator(
        "intended_for",
        "distribution",
    )
    @classmethod
    def normalize_string_list(
        cls,
        values: list[str],
    ) -> list[str]:
        """
        Normalize human or distribution identifiers.

        Blank values are discarded while original ordering
        is preserved.
        """

        normalized: list[str] = []

        for value in values:

            value = value.strip()

            if value and value not in normalized:
                normalized.append(
                    value
                )

        return normalized


# =============================================================================
# Executive Summary
# =============================================================================


class ExecutiveSummary(Gen2XModel):
    """
    Provides a concise leadership-facing summary of the report.

    ExecutiveSummary intentionally answers only the questions most
    leaders need answered immediately:

        • What happened?
        • How serious is it?
        • What is the business impact?
        • What are we doing about it?
        • Is a leadership decision required?

    Detailed technical evidence belongs elsewhere in the report.

    ExecutiveSummary is a presentation model.

    It must not independently calculate severity or invent facts.
    """

    headline: str

    summary: str

    severity: ThreatSeverity

    business_impact: str = ""

    recommended_action: str = ""

    decision_required: bool = False

    decision_request: str = ""

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator(
        "headline",
        "summary",
    )
    @classmethod
    def require_text(
        cls,
        value: str,
    ) -> str:
        """
        Require the minimum useful executive communication.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Executive summary text cannot be empty."
            )

        return value

    @field_validator(
        "business_impact",
        "recommended_action",
        "decision_request",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str,
    ) -> str:
        """
        Normalize optional executive-facing text.
        """

        return value.strip()

    # =========================================================================
    # Derived State
    # =========================================================================

    @property
    def requires_attention(self) -> bool:
        """
        Return True when executive action or decision is required.
        """

        return self.decision_required

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return the shortest useful representation of the
        executive summary.
        """

        return (
            f"{self.headline} "
            f"[severity={self.severity.value}, "
            f"decision_required={self.decision_required}]"
        )


# =============================================================================
# Threat Summary
# =============================================================================


class ThreatSummary(Gen2XModel):
    """
    Provides a human-readable projection of a Threat.

    ThreatSummary communicates the threat conclusion without requiring
    the reader to inspect the complete Threat domain object.

    It does not replace Threat.

    Threat remains the authoritative domain representation.
    """

    title: str

    summary: str

    condition: ThreatCondition

    severity: ThreatSeverity

    confidence: ThreatConfidence

    affected_resource: str | None = None

    evidence_count: int = Field(
        default=0,
        ge=0,
    )

    provider_count: int = Field(
        default=0,
        ge=0,
    )

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator(
        "title",
        "summary",
    )
    @classmethod
    def require_summary_text(
        cls,
        value: str,
    ) -> str:
        """
        Require meaningful threat summary text.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Threat summary text cannot be empty."
            )

        return value

    @field_validator(
        "affected_resource",
    )
    @classmethod
    def normalize_affected_resource(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize the optional affected resource.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise threat summary description.
        """

        return (
            f"{self.title} "
            f"[condition={self.condition.value}, "
            f"severity={self.severity.value}, "
            f"confidence={self.confidence.value}]"
        )


# =============================================================================
# Response Summary
# =============================================================================


class ResponseSummary(Gen2XModel):
    """
    Provides a human-readable projection of a Response.

    ResponseSummary communicates:

        • What action is recommended
        • How urgently it should be considered
        • Why it is recommended
        • Where the investigation currently stands
        • Whether the action has been approved

    It does not execute the response.

    It does not independently determine authorization.
    """

    action: ResponseAction

    priority: ResponsePriority

    rationale: str

    expected_outcome: str = ""

    investigation_status: InvestigationStatus

    approval_status: ApprovalStatus

    approved_by: str | None = None

    approved_at: datetime | None = None

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator(
        "rationale",
    )
    @classmethod
    def validate_rationale(
        cls,
        value: str,
    ) -> str:
        """
        Require the response rationale to remain visible in
        human-facing reporting.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Response summary rationale cannot be empty."
            )

        return value

    @field_validator(
        "expected_outcome",
    )
    @classmethod
    def normalize_expected_outcome(
        cls,
        value: str,
    ) -> str:
        """
        Normalize expected outcome text.
        """

        return value.strip()

    @field_validator(
        "approved_by",
    )
    @classmethod
    def normalize_approved_by(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize the optional approving actor.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    # =========================================================================
    # Derived State
    # =========================================================================

    @property
    def has_approval_record(self) -> bool:
        """
        Return True when an approving actor and timestamp
        are both available.

        This property describes recorded report data.

        ResponseGovernance remains authoritative for authorization.
        """

        return (
            self.approved_by is not None
            and
            self.approved_at is not None
        )

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise response summary description.
        """

        return (
            f"{self.action.value} "
            f"[priority={self.priority.value}, "
            f"investigation={self.investigation_status.value}, "
            f"approval={self.approval_status.value}]"
        )


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Engineers
#
# like details.
#
# Logs.
#
# Evidence.
#
# Provider results.
#
# Confidence.
#
# Correlation.
#
# Timestamps.
#
# Resource identifiers.
#
# Beautiful.
#
# Give an engineer
#
# twelve thousand
#
# lines
#
# of telemetry
#
# and coffee
#
# and they may
#
# become
#
# strangely happy.
#
# Humans
#
# outside engineering
#
# are different.
#
# They usually ask:
#
# "Is this bad?"
#
# "What does it affect?"
#
# "What are we doing?"
#
# And sometimes:
#
# "Do you need
# me to decide
# something?"
#
# Those are not
#
# inferior questions.
#
# They are
#
# different questions.
#
# Good communication
#
# does not force
#
# every human
#
# to become
#
# a security engineer
#
# before they can
#
# understand
#
# security.
#
# But simplification
#
# creates
#
# a danger.
#
# When we shorten
#
# an explanation,
#
# we may accidentally
#
# change
#
# the meaning.
#
# So remember:
#
# The executive
#
# receives
#
# fewer details.
#
# Not
#
# different facts.
#
# The analyst
#
# receives
#
# more details.
#
# Not
#
# different facts.
#
# The auditor
#
# receives
#
# provenance.
#
# Not
#
# different facts.
#
# Presentation
#
# may change.
#
# Truth
#
# must not.
#
# A summary
#
# should therefore
#
# point toward
#
# the underlying
#
# domain state.
#
# Never replace it.
#
# And when
#
# leadership
#
# has thirty seconds...
#
# tell them:
#
# what happened,
#
# how bad it is,
#
# what it affects,
#
# what security
#
# recommends,
#
# and whether
#
# someone needs
#
# their authority.
#
# Then stop.
#
# If they want
#
# the evidence...
#
# there are engineers
#
# waiting nearby
#
# with coffee
#
# and seventeen
#
# browser tabs
#
# already open.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Executive Communications Office
#                                Porg Sushi Investor Relations
#
# =============================================================================

# =============================================================================
# Part II
# Findings, Evidence, and Accountability
# =============================================================================


# =============================================================================
# Report Finding
# =============================================================================


class ReportFinding(Gen2XModel):
    """
    Represents one security finding contained within a report.

    A report may contain multiple findings.

    ReportFinding is a human-facing representation of an established
    security conclusion.

    It does not perform threat assessment.

    Severity and confidence should originate from the authoritative
    Threat or assessment domain state.
    """

    finding_id: UUID = Field(
        default_factory=uuid4
    )

    title: str

    description: str

    condition: ThreatCondition

    severity: ThreatSeverity

    confidence: ThreatConfidence

    affected_resource: str | None = None

    recommendation: str = ""

    created_at: datetime = Field(
        default_factory=utc_now
    )

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator(
        "title",
        "description",
    )
    @classmethod
    def require_finding_text(
        cls,
        value: str,
    ) -> str:
        """
        Require meaningful finding text.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Finding text cannot be empty."
            )

        return value

    @field_validator(
        "affected_resource",
    )
    @classmethod
    def normalize_affected_resource(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize the optional affected resource.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    @field_validator(
        "recommendation",
    )
    @classmethod
    def normalize_recommendation(
        cls,
        value: str,
    ) -> str:
        """
        Normalize recommendation text.
        """

        return value.strip()

    # =========================================================================
    # Derived State
    # =========================================================================

    @property
    def has_recommendation(self) -> bool:
        """
        Return True when the finding contains a recommendation.
        """

        return bool(
            self.recommendation
        )

    @property
    def has_affected_resource(self) -> bool:
        """
        Return True when a specific affected resource is recorded.
        """

        return (
            self.affected_resource
            is not None
        )

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise description of the finding.
        """

        return (
            f"{self.title} "
            f"[condition={self.condition.value}, "
            f"severity={self.severity.value}, "
            f"confidence={self.confidence.value}]"
        )


# =============================================================================
# Report Evidence Summary
# =============================================================================


class ReportEvidenceSummary(Gen2XModel):
    """
    Provides a concise representation of the evidence supporting
    the report.

    ReportEvidenceSummary preserves traceability without embedding
    every complete ThreatEvidence object into the human-facing report.

    Detailed evidence remains authoritative elsewhere in the
    evidence domain.

    This model answers:

        • How much evidence exists?
        • Which providers contributed?
        • Which evidence records support the report?
        • Was corroboration observed?
        • Were conflicts detected?
    """

    evidence_ids: list[str] = Field(
        default_factory=list
    )

    providers: list[str] = Field(
        default_factory=list
    )

    corroborated: bool = False

    conflicts_detected: bool = False

    notes: list[str] = Field(
        default_factory=list
    )

    # =========================================================================
    # Normalization
    # =========================================================================

    @field_validator(
        "evidence_ids",
        "providers",
        "notes",
    )
    @classmethod
    def normalize_string_list(
        cls,
        values: list[str],
    ) -> list[str]:
        """
        Normalize list values.

        Blank entries are removed.

        Duplicate values are removed while preserving original order.
        """

        normalized: list[str] = []

        for value in values:

            value = value.strip()

            if (
                value
                and
                value not in normalized
            ):
                normalized.append(
                    value
                )

        return normalized

    # =========================================================================
    # Derived State
    # =========================================================================

    @property
    def evidence_count(self) -> int:
        """
        Return the number of evidence records represented
        by the report.
        """

        return len(
            self.evidence_ids
        )

    @property
    def provider_count(self) -> int:
        """
        Return the number of contributing providers.
        """

        return len(
            self.providers
        )

    @property
    def has_evidence(self) -> bool:
        """
        Return True when evidence identifiers are present.
        """

        return self.evidence_count > 0

    @property
    def has_multiple_providers(self) -> bool:
        """
        Return True when evidence originates from multiple providers.

        Multiple providers do not automatically imply corroboration.

        Corroboration is an analytical conclusion and is therefore
        recorded separately.
        """

        return self.provider_count > 1

    @property
    def has_conflicts(self) -> bool:
        """
        Return True when conflicting evidence has been recorded.
        """

        return self.conflicts_detected

    # =========================================================================
    # Evidence Management
    # =========================================================================

    def add_evidence_id(
        self,
        evidence_id: str,
    ) -> None:
        """
        Add an evidence identifier when it is not already present.
        """

        evidence_id = evidence_id.strip()

        if not evidence_id:
            raise ValueError(
                "evidence_id cannot be empty."
            )

        if (
            evidence_id
            not in self.evidence_ids
        ):
            self.evidence_ids.append(
                evidence_id
            )

    def add_provider(
        self,
        provider: str,
    ) -> None:
        """
        Add a contributing provider when it is not already present.
        """

        provider = provider.strip()

        if not provider:
            raise ValueError(
                "provider cannot be empty."
            )

        target = provider.casefold()

        if not any(
            existing.casefold() == target
            for existing
            in self.providers
        ):
            self.providers.append(
                provider
            )

    def add_note(
        self,
        note: str,
    ) -> None:
        """
        Add an evidence summary note.
        """

        note = note.strip()

        if not note:
            raise ValueError(
                "Evidence note cannot be empty."
            )

        self.notes.append(
            note
        )

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise description of report evidence.
        """

        return (
            f"Evidence "
            f"[records={self.evidence_count}, "
            f"providers={self.provider_count}, "
            f"corroborated={self.corroborated}, "
            f"conflicts={self.conflicts_detected}]"
        )


# =============================================================================
# Report Accountability
# =============================================================================


class ReportAccountability(Gen2XModel):
    """
    Records human and system accountability associated with a report.

    Accountability answers:

        • Who owned the investigation?
        • Who created the recommendation?
        • Was approval required?
        • Who approved or rejected the response?
        • When was that decision made?
        • What system or actor generated the report?

    This model intentionally records responsibility without inventing
    execution history.

    Execution accountability should be added only when the response
    execution layer exists.
    """

    investigation_owner: str | None = None

    recommendation_created_by: str | None = None

    approval_required: bool = False

    approval_status: ApprovalStatus

    approved_by: str | None = None

    approved_at: datetime | None = None

    rejected_by: str | None = None

    rejected_at: datetime | None = None

    decision_reason: str = ""

    generated_by: str

    generated_at: datetime = Field(
        default_factory=utc_now
    )

    # =========================================================================
    # Normalization
    # =========================================================================

    @field_validator(
        "investigation_owner",
        "recommendation_created_by",
        "approved_by",
        "rejected_by",
    )
    @classmethod
    def normalize_optional_actor(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize optional actor identifiers.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    @field_validator(
        "generated_by",
    )
    @classmethod
    def validate_generated_by(
        cls,
        value: str,
    ) -> str:
        """
        Require identification of the actor or system responsible
        for generating the report.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "generated_by cannot be empty."
            )

        return value

    @field_validator(
        "decision_reason",
    )
    @classmethod
    def normalize_decision_reason(
        cls,
        value: str,
    ) -> str:
        """
        Normalize governance decision text.
        """

        return value.strip()

    # =========================================================================
    # Derived State
    # =========================================================================

    @property
    def has_investigation_owner(self) -> bool:
        """
        Return True when an investigation owner is recorded.
        """

        return (
            self.investigation_owner
            is not None
        )

    @property
    def has_recommendation_owner(self) -> bool:
        """
        Return True when the recommendation creator is recorded.
        """

        return (
            self.recommendation_created_by
            is not None
        )

    @property
    def has_approval_record(self) -> bool:
        """
        Return True when approval attribution is recorded.

        This describes report data.

        ResponseGovernance remains authoritative for authorization.
        """

        return (
            self.approved_by is not None
            and
            self.approved_at is not None
        )

    @property
    def has_rejection_record(self) -> bool:
        """
        Return True when rejection attribution is recorded.
        """

        return (
            self.rejected_by is not None
            and
            self.rejected_at is not None
        )

    @property
    def has_decision_record(self) -> bool:
        """
        Return True when either an approval or rejection record exists.
        """

        return (
            self.has_approval_record
            or
            self.has_rejection_record
        )

    @property
    def is_attributed(self) -> bool:
        """
        Return True when the report contains the minimum attribution
        necessary to identify who or what generated it.

        This is intentionally a modest requirement.

        Full accountability depends on the workflow represented by
        the report.
        """

        return bool(
            self.generated_by
        )

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise accountability description.
        """

        return (
            f"Accountability "
            f"[owner={self.investigation_owner}, "
            f"approval={self.approval_status.value}, "
            f"generated_by={self.generated_by}]"
        )


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Reports
#
# should not
#
# merely say:
#
# "Something bad
# happened."
#
# They should
#
# be able
#
# to answer:
#
# "What?"
#
# "Why?"
#
# "According to whom?"
#
# "Based on what?"
#
# "Who decided?"
#
# "Who approved?"
#
# "When?"
#
# Those questions
#
# are sometimes
#
# uncomfortable.
#
# Good.
#
# Accountability
#
# is supposed
#
# to survive
#
# uncomfortable
#
# questions.
#
# Anyone
#
# can build
#
# automation
#
# that says:
#
# "CRITICAL."
#
# Mature systems
#
# can explain
#
# why.
#
# Anyone
#
# can build
#
# automation
#
# that says:
#
# "Disable
# the account."
#
# Mature systems
#
# preserve
#
# who recommended
#
# that action.
#
# Secure systems
#
# preserve
#
# who authorized it.
#
# And accountable
#
# systems
#
# preserve
#
# enough history
#
# that six months
#
# from now
#
# someone can ask:
#
# "Why did we
# do this?"
#
# and receive
#
# something better
#
# than:
#
# "I think
# Bob said
# it was okay."
#
# Evidence
#
# without attribution
#
# is weaker.
#
# Decisions
#
# without attribution
#
# are dangerous.
#
# Authority
#
# without accountability
#
# becomes
#
# privilege.
#
# And privilege
#
# without accountability
#
# eventually becomes
#
# somebody else's
#
# incident report.
#
# So record
#
# what mattered.
#
# Record
#
# who knew.
#
# Record
#
# who decided.
#
# Record
#
# who authorized.
#
# But do not
#
# invent
#
# history
#
# simply because
#
# a report field
#
# would look
#
# prettier
#
# if populated.
#
# Unknown
#
# is better
#
# than fictional.
#
# Missing
#
# is better
#
# than fabricated.
#
# Accountability
#
# begins
#
# with truth.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Galactic Audit Committee
#                                Porg Sushi Compliance Officer
#
# =============================================================================

# =============================================================================
# Part III
# Report Domain Object
# =============================================================================


from models.enums import ReportStatus


# =============================================================================
# Report
# =============================================================================


class Report(Gen2XModel):
    """
    Represents one complete human-facing security report.

    Report composes:

        • ReportIdentity
        • ReportAudience
        • ExecutiveSummary
        • ThreatSummary
        • ResponseSummary
        • ReportEvidenceSummary
        • ReportAccountability
        • ReportFinding

    into one durable reporting artifact.

    Report does not determine security facts.

    It preserves and communicates facts established elsewhere
    in the Gen2X domain model.

    Reports follow a controlled lifecycle:

        DRAFT
            Report may be constructed and modified.

        REVIEW
            Report is being examined before publication.

        FINAL
            Report becomes a historical record.

        ARCHIVED
            Final report has moved into long-term retention.

    A finalized report should not be silently rewritten.

    Material corrections should result in a new report or revision.
    """

    identity: ReportIdentity

    audience: ReportAudience

    executive_summary: ExecutiveSummary

    threat_summary: ThreatSummary

    response_summary: ResponseSummary | None = None

    evidence_summary: ReportEvidenceSummary = Field(
        default_factory=ReportEvidenceSummary
    )

    accountability: ReportAccountability

    findings: list[ReportFinding] = Field(
        default_factory=list
    )

    analyst_notes: list[str] = Field(
        default_factory=list
    )

    status: ReportStatus = ReportStatus.DRAFT

    finalized_at: datetime | None = None

    archived_at: datetime | None = None

    # =========================================================================
    # Identity Properties
    # =========================================================================

    @property
    def report_id(self) -> UUID:
        """
        Return the report identifier.
        """

        return self.identity.report_id

    @property
    def report_type(self) -> ReportType:
        """
        Return the report type.
        """

        return self.identity.report_type

    @property
    def threat_id(self) -> str:
        """
        Return the associated threat identifier.
        """

        return self.identity.threat_id

    @property
    def assessment_id(self) -> str | None:
        """
        Return the associated Fusion assessment identifier.
        """

        return self.identity.assessment_id

    @property
    def response_id(self) -> UUID | None:
        """
        Return the associated response identifier.
        """

        return self.identity.response_id

    @property
    def created_at(self) -> datetime:
        """
        Return the report creation timestamp.
        """

        return self.identity.created_at

    @property
    def updated_at(self) -> datetime:
        """
        Return the report modification timestamp.
        """

        return self.identity.updated_at

    # =========================================================================
    # Threat Properties
    # =========================================================================

    @property
    def severity(self) -> ThreatSeverity:
        """
        Return the reported threat severity.

        ThreatSummary remains the source for this report projection.
        """

        return self.threat_summary.severity

    @property
    def confidence(self) -> ThreatConfidence:
        """
        Return the reported threat confidence.
        """

        return self.threat_summary.confidence

    @property
    def condition(self) -> ThreatCondition:
        """
        Return the reported threat condition.
        """

        return self.threat_summary.condition

    # =========================================================================
    # Report Content Properties
    # =========================================================================

    @property
    def finding_count(self) -> int:
        """
        Return the number of report findings.
        """

        return len(
            self.findings
        )

    @property
    def has_findings(self) -> bool:
        """
        Return True when the report contains findings.
        """

        return self.finding_count > 0

    @property
    def has_response(self) -> bool:
        """
        Return True when the report contains a response summary.
        """

        return self.response_summary is not None

    @property
    def evidence_count(self) -> int:
        """
        Return the number of referenced evidence records.
        """

        return self.evidence_summary.evidence_count

    @property
    def provider_count(self) -> int:
        """
        Return the number of contributing evidence providers.
        """

        return self.evidence_summary.provider_count

    # =========================================================================
    # Lifecycle Properties
    # =========================================================================

    @property
    def is_draft(self) -> bool:
        """
        Return True when the report remains a draft.
        """

        return (
            self.status
            == ReportStatus.DRAFT
        )

    @property
    def is_under_review(self) -> bool:
        """
        Return True when the report is under review.
        """

        return (
            self.status
            == ReportStatus.REVIEW
        )

    @property
    def is_final(self) -> bool:
        """
        Return True when the report has been finalized.
        """

        return (
            self.status
            == ReportStatus.FINAL
        )

    @property
    def is_archived(self) -> bool:
        """
        Return True when the report has been archived.
        """

        return (
            self.status
            == ReportStatus.ARCHIVED
        )

    @property
    def is_mutable(self) -> bool:
        """
        Return True while ordinary report content may still change.

        Draft and review reports remain editable.

        Final and archived reports are historical artifacts.
        """

        return self.status in {
            ReportStatus.DRAFT,
            ReportStatus.REVIEW,
        }

    # =========================================================================
    # Decision Properties
    # =========================================================================

    @property
    def decision_required(self) -> bool:
        """
        Return True when the executive summary indicates that
        leadership action or authority is required.
        """

        return (
            self.executive_summary.decision_required
        )

    @property
    def approval_required(self) -> bool:
        """
        Return the approval requirement recorded in accountability.
        """

        return (
            self.accountability.approval_required
        )

    @property
    def approval_status(self) -> ApprovalStatus:
        """
        Return the approval state recorded by the report.

        ResponseGovernance remains authoritative for live
        authorization decisions.
        """

        return (
            self.accountability.approval_status
        )

    # =========================================================================
    # Internal Mutation Guard
    # =========================================================================

    def _require_mutable(self) -> None:
        """
        Require the report to remain editable.

        Final and archived reports should not be silently modified.

        Material corrections should result in a new report or
        formal revision.
        """

        if not self.is_mutable:
            raise ValueError(
                "Finalized or archived reports cannot be modified. "
                "Issue a new report or revision instead."
            )

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def touch(self) -> None:
        """
        Update the report modification timestamp.

        Only mutable reports may be touched.
        """

        self._require_mutable()

        self.identity.touch()

    def submit_for_review(self) -> None:
        """
        Move a draft report into review.
        """

        if not self.is_draft:
            raise ValueError(
                "Only draft reports may be submitted for review."
            )

        self.status = ReportStatus.REVIEW

        self.identity.touch()

    def return_to_draft(self) -> None:
        """
        Return a report under review to draft status.

        This allows corrections before finalization.
        """

        if not self.is_under_review:
            raise ValueError(
                "Only reports under review may return to draft."
            )

        self.status = ReportStatus.DRAFT

        self.identity.touch()

    def finalize(self) -> None:
        """
        Finalize the report.

        Finalization turns the report into a historical artifact.

        Once finalized, ordinary content mutation is prohibited.
        """

        if not self.is_under_review:
            raise ValueError(
                "Only reports under review may be finalized."
            )

        timestamp = utc_now()

        # Touch before changing status because FINAL reports
        # are no longer mutable.
        self.identity.updated_at = timestamp

        self.finalized_at = timestamp

        self.status = ReportStatus.FINAL

    def archive(self) -> None:
        """
        Archive a finalized report.

        Archiving represents retention state.

        It does not alter the report's historical contents.
        """

        if not self.is_final:
            raise ValueError(
                "Only finalized reports may be archived."
            )

        timestamp = utc_now()

        self.archived_at = timestamp

        self.status = ReportStatus.ARCHIVED

    # =========================================================================
    # Finding Management
    # =========================================================================

    def add_finding(
        self,
        finding: ReportFinding,
    ) -> None:
        """
        Add a finding to a mutable report.
        """

        self._require_mutable()

        existing_ids = {
            item.finding_id
            for item
            in self.findings
        }

        if finding.finding_id in existing_ids:
            raise ValueError(
                "Finding already exists in report."
            )

        self.findings.append(
            finding
        )

        self.identity.touch()

    def remove_finding(
        self,
        finding_id: UUID,
    ) -> None:
        """
        Remove a finding from a mutable report.

        Findings cannot be removed after finalization.
        """

        self._require_mutable()

        original_count = len(
            self.findings
        )

        self.findings = [
            finding
            for finding
            in self.findings
            if finding.finding_id != finding_id
        ]

        if len(self.findings) != original_count:
            self.identity.touch()

    def get_finding(
        self,
        finding_id: UUID,
    ) -> ReportFinding | None:
        """
        Return a finding by identifier when present.
        """

        return next(
            (
                finding
                for finding
                in self.findings
                if finding.finding_id == finding_id
            ),
            None,
        )

    # =========================================================================
    # Analyst Notes
    # =========================================================================

    def add_analyst_note(
        self,
        note: str,
    ) -> None:
        """
        Add an analyst note to a mutable report.
        """

        self._require_mutable()

        note = note.strip()

        if not note:
            raise ValueError(
                "Analyst note cannot be empty."
            )

        self.analyst_notes.append(
            note
        )

        self.identity.touch()

    # =========================================================================
    # Matching Helpers
    # =========================================================================

    def matches_threat(
        self,
        threat_id: str,
    ) -> bool:
        """
        Return True when the report belongs to the supplied threat.
        """

        return (
            self.threat_id
            == threat_id.strip()
        )

    def matches_report_type(
        self,
        report_type: ReportType,
    ) -> bool:
        """
        Return True when the report has the supplied report type.
        """

        return (
            self.report_type
            == report_type
        )

    def has_finding_condition(
        self,
        condition: ThreatCondition,
    ) -> bool:
        """
        Return True when at least one finding has the supplied
        threat condition.
        """

        return any(
            finding.condition == condition
            for finding
            in self.findings
        )

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise human-readable description.

        Intended for:

            • Logs
            • Diagnostics
            • CLI output
            • Testing
        """

        return (
            f"{self.report_type.value} "
            f"[status={self.status.value}, "
            f"severity={self.severity.value}, "
            f"findings={self.finding_count}, "
            f"evidence={self.evidence_count}]"
        )

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Return a JSON-friendly representation of the report.

        Pydantic serializes the nested report models.

        Derived values are included for operational convenience.
        """

        data = self.model_dump(
            mode="json"
        )

        data["derived"] = {
            "finding_count":
                self.finding_count,

            "evidence_count":
                self.evidence_count,

            "provider_count":
                self.provider_count,

            "has_findings":
                self.has_findings,

            "has_response":
                self.has_response,

            "decision_required":
                self.decision_required,

            "approval_required":
                self.approval_required,

            "is_mutable":
                self.is_mutable,
        }

        return data


# =============================================================================
#
# Chewbacca's Final Thoughts 🐾
#
# Humans
#
# make mistakes.
#
# Engineers
#
# make mistakes.
#
# Analysts
#
# make mistakes.
#
# Automation
#
# makes mistakes.
#
# Even reports
#
# can be wrong.
#
# The answer
#
# is not
#
# to pretend
#
# mistakes
#
# never happened.
#
# The answer
#
# is to preserve
#
# what happened
#
# and correct
#
# the record
#
# honestly.
#
# A draft
#
# may change.
#
# A review
#
# may discover
#
# problems.
#
# That is why
#
# review exists.
#
# But once
#
# a report
#
# becomes
#
# the official
#
# record...
#
# history
#
# should not
#
# quietly
#
# rewrite itself.
#
# If yesterday
#
# we believed
#
# a threat
#
# was HIGH
#
# and today
#
# new evidence
#
# proves
#
# it was CRITICAL,
#
# do not
#
# erase
#
# yesterday.
#
# Preserve
#
# yesterday's
#
# conclusion.
#
# Preserve
#
# the evidence
#
# available
#
# at that time.
#
# Then issue
#
# today's
#
# correction.
#
# Because
#
# accountability
#
# does not mean
#
# always being
#
# right.
#
# Accountability
#
# means being
#
# able
#
# to explain
#
# what you knew,
#
# what you believed,
#
# what you decided,
#
# and why.
#
# Revision
#
# is not
#
# weakness.
#
# Silent alteration
#
# is.
#
# Good systems
#
# preserve
#
# truth.
#
# Great systems
#
# preserve
#
# how our
#
# understanding
#
# of truth
#
# changed
#
# over time.
#
# And if
#
# someone asks
#
# six months later:
#
# "Who changed
# the report?"
#
# the answer
#
# should never
#
# be:
#
# "Nobody knows."
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Keeper of the Historical Record
#                                Porg Sushi Internal Audit
#
# =============================================================================
