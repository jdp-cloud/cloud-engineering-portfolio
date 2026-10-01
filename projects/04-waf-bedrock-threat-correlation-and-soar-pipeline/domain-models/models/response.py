"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    response.py

Part I:
    Response Foundation Models

===============================================================================

Business Objective
-------------------------------------------------------------------------------

Response models describe recommended security actions.

A response begins only after evidence has been evaluated and a threat has
been identified.

The response layer answers three initial questions:

    1. Which response are we discussing?
    2. What system, identity, resource, or indicator would be affected?
    3. What action is being recommended?

Part I intentionally does NOT determine:

    • Whether the recommendation is approved
    • Whether execution is authorized
    • Whether the action has been performed
    • Whether the action succeeded
    • Whether the investigation is complete

Those responsibilities belong to later response and execution layers.

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

from models.enums import (
    ResponseAction,
    ResponsePriority,
)

from utils.time import utc_now


# =============================================================================
# Response Identity
# =============================================================================


class ResponseIdentity(Gen2XModel):
    """
    Identifies one response recommendation known to Gen2X.

    response_id identifies the response itself.

    threat_id connects the response to the Threat that caused the
    recommendation to be created.

    assessment_id optionally connects the response to the Fusion
    assessment responsible for the recommendation.
    """

    response_id: UUID = Field(
        default_factory=uuid4
    )

    threat_id: str

    assessment_id: str | None = None

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
        Update the response modification timestamp.
        """

        self.updated_at = utc_now()


# =============================================================================
# Response Target
# =============================================================================


class ResponseTarget(Gen2XModel):
    """
    Describes the object that would be affected by a response.

    ResponseTarget is intentionally provider-neutral.

    The same model may therefore describe targets in:

        • AWS
        • Azure
        • GCP
        • GitHub
        • On-premises environments

    A target may represent a resource, identity, repository,
    endpoint, indicator, or some combination of those concepts.
    """

    indicator_key: str | None = None

    account_id: str | None = None

    region: str | None = None

    resource_id: str | None = None

    user_id: str | None = None

    repository: str | None = None

    endpoint: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    # =========================================================================
    # Normalization
    # =========================================================================

    @field_validator(
        "indicator_key",
        "account_id",
        "region",
        "resource_id",
        "user_id",
        "repository",
        "endpoint",
    )
    @classmethod
    def normalize_optional_string(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize optional target strings.

        Blank strings become None.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    # =========================================================================
    # Derived State
    # =========================================================================

    @property
    def has_target(self) -> bool:
        """
        Return True when at least one concrete target identifier
        is available.

        metadata alone does not constitute a response target.
        """

        return any(
            (
                self.indicator_key,
                self.account_id,
                self.resource_id,
                self.user_id,
                self.repository,
                self.endpoint,
            )
        )

    @property
    def is_identity_target(self) -> bool:
        """
        Return True when the response targets a user identity.
        """

        return self.user_id is not None

    @property
    def is_resource_target(self) -> bool:
        """
        Return True when the response targets a resource.
        """

        return self.resource_id is not None

    @property
    def is_repository_target(self) -> bool:
        """
        Return True when the response targets a repository.
        """

        return self.repository is not None

    @property
    def is_indicator_target(self) -> bool:
        """
        Return True when the response is associated with an
        indicator.
        """

        return self.indicator_key is not None


# =============================================================================
# Response Recommendation
# =============================================================================


class ResponseRecommendation(Gen2XModel):
    """
    Represents what Gen2X recommends doing about a threat.

    A recommendation is advisory.

    It does not imply:

        • Approval
        • Authorization
        • Execution
        • Success

    Governance determines whether the recommendation may proceed.

    Execution belongs to a separate response executor.
    """

    action: ResponseAction

    priority: ResponsePriority

    rationale: str

    expected_outcome: str = ""

    recommended_at: datetime = Field(
        default_factory=utc_now
    )

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
        Require a meaningful response rationale.

        Gen2X should never recommend an action without recording
        why that action was recommended.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Response rationale cannot be empty."
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
        Normalize the optional expected outcome.
        """

        return value.strip()

    # =========================================================================
    # Description
    # =========================================================================

    def describe(self) -> str:
        """
        Return a concise description of the recommendation.

        This is intended for logs, diagnostics, CLI output,
        and testing.

        It is not an execution instruction.
        """

        return (
            f"{self.action.value} "
            f"[priority={self.priority.value}]"
        )


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Finding
#
# a threat
#
# is not
#
# the end
#
# of an investigation.
#
# Eventually
#
# someone asks:
#
# "What should
# we do?"
#
# That question
#
# sounds simple.
#
# It isn't.
#
# Disable
#
# an account?
#
# Rotate
#
# a credential?
#
# Isolate
#
# a system?
#
# Block
#
# an endpoint?
#
# Remove
#
# a repository secret?
#
# Every action
#
# changes
#
# something
#
# in the real world.
#
# And changing
#
# the real world
#
# has consequences.
#
# A technically
#
# correct response
#
# performed
#
# against
#
# the wrong target
#
# is still
#
# a failure.
#
# A technically
#
# correct response
#
# performed
#
# without authority
#
# may become
#
# an incident
#
# of its own.
#
# So before
#
# automation
#
# reaches
#
# for the button...
#
# it should know
#
# three things:
#
# Which response
#
# are we discussing?
#
# What exactly
#
# would we change?
#
# And why
#
# do we believe
#
# that change
#
# should happen?
#
# Recommendation
#
# is not
#
# authorization.
#
# Recommendation
#
# is not
#
# execution.
#
# Recommendation
#
# is judgment
#
# waiting
#
# for governance.
#
# A good system
#
# knows
#
# what it recommends.
#
# A great system
#
# also knows
#
# that knowing
#
# what should
#
# be done
#
# does not
#
# automatically
#
# give it
#
# permission
#
# to do it.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Porg Sushi Risk Committee
#
# =============================================================================


# =============================================================================
# Part II
# Investigation State and Response Governance
# =============================================================================


# Aliased imports:
#
#   ResponseApproval is the approval-state vocabulary; response models
#   refer to it as ApprovalStatus (ApprovalMode holds the requirement).
#
#   ResponseMode describes how a response is executed; response models
#   refer to it as ExecutionMode.
from models.enums import ResponseApproval as ApprovalStatus
from models.enums import ResponseMode as ExecutionMode
from models.enums import (
    ApprovalMode,
    InvestigationStatus,
)


# =============================================================================
# Investigation State
# =============================================================================


class InvestigationState(Gen2XModel):
    """
    Represents the operational lifecycle of a security investigation.

    InvestigationState answers:

        "Where are we in the investigation?"

    It does not describe:

        • Threat severity
        • Threat confidence
        • Response authorization
        • Response execution success

    Investigation state and response governance are intentionally
    modeled separately.

    Security investigations are not perfectly linear.

    New evidence may cause an investigation to move backward,
    reopen, or continue after remediation.
    """

    status: InvestigationStatus = (
        InvestigationStatus.NEW
    )

    opened_at: datetime = Field(
        default_factory=utc_now
    )

    updated_at: datetime = Field(
        default_factory=utc_now
    )

    resolved_at: datetime | None = None

    closed_at: datetime | None = None

    reopened_at: datetime | None = None

    owner: str | None = None

    notes: list[str] = Field(
        default_factory=list
    )

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator(
        "owner",
    )
    @classmethod
    def normalize_owner(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize the optional investigation owner.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    # =========================================================================
    # Derived State
    # =========================================================================

    @property
    def is_open(self) -> bool:
        """
        Return True when the investigation remains operationally open.
        """

        return self.status not in {
            InvestigationStatus.CLOSED,
        }

    @property
    def is_resolved(self) -> bool:
        """
        Return True when the investigation has been resolved.

        Resolved and closed are intentionally different states.

        A resolved investigation may remain open for monitoring,
        verification, documentation, or administrative review.
        """

        return self.resolved_at is not None

    @property
    def is_closed(self) -> bool:
        """
        Return True when the investigation is administratively closed.
        """

        return (
            self.status == InvestigationStatus.CLOSED
        )

    @property
    def was_reopened(self) -> bool:
        """
        Return True when the investigation has been reopened
        at least once.
        """

        return self.reopened_at is not None

    @property
    def age(self):
        """
        Return the age of the investigation.
        """

        return utc_now() - self.opened_at

    @property
    def age_seconds(self) -> float:
        """
        Return the investigation age in seconds.
        """

        return self.age.total_seconds()

    # =========================================================================
    # Lifecycle
    # =========================================================================

    def touch(self) -> None:
        """
        Update the investigation modification timestamp.
        """

        self.updated_at = utc_now()

    def transition_to(
        self,
        status: InvestigationStatus,
    ) -> None:
        """
        Move the investigation to another lifecycle state.

        This method intentionally provides guardrails rather than
        enforcing an inflexible workflow.

        Real security investigations may move forward, backward,
        or revisit earlier stages as new evidence appears.
        """

        if self.status == status:
            return

        self.status = status
        self.touch()

    def begin_triage(self) -> None:
        """
        Move the investigation into triage.
        """

        self.transition_to(
            InvestigationStatus.TRIAGE
        )

    def begin_investigation(self) -> None:
        """
        Move into active investigation.
        """

        self.transition_to(
            InvestigationStatus.INVESTIGATING
        )

    def begin_evidence_collection(self) -> None:
        """
        Move into evidence collection.
        """

        self.transition_to(
            InvestigationStatus.EVIDENCE_COLLECTION
        )

    def begin_analysis(self) -> None:
        """
        Move into analysis.
        """

        self.transition_to(
            InvestigationStatus.ANALYSIS
        )

    def mark_response_pending(self) -> None:
        """
        Indicate that the investigation is awaiting response activity.
        """

        self.transition_to(
            InvestigationStatus.RESPONSE_PENDING
        )

    def mark_response_in_progress(self) -> None:
        """
        Indicate that response activity is underway.
        """

        self.transition_to(
            InvestigationStatus.RESPONSE_IN_PROGRESS
        )

    def begin_monitoring(self) -> None:
        """
        Move the investigation into monitoring.
        """

        self.transition_to(
            InvestigationStatus.MONITORING
        )

    def resolve(self) -> None:
        """
        Mark the security condition as resolved.

        Resolution does not automatically close the investigation.
        """

        timestamp = utc_now()

        self.status = (
            InvestigationStatus.RESOLVED
        )

        self.resolved_at = timestamp
        self.updated_at = timestamp

    def close(self) -> None:
        """
        Administratively close the investigation.

        Closing an investigation is intentionally separate from
        resolving the underlying security condition.
        """

        timestamp = utc_now()

        self.status = (
            InvestigationStatus.CLOSED
        )

        self.closed_at = timestamp
        self.updated_at = timestamp

    def reopen(self) -> None:
        """
        Reopen a previously resolved or closed investigation.

        Historical resolution and closure timestamps are preserved.

        They describe events that actually occurred and therefore
        remain useful for audit and investigation history.
        """

        timestamp = utc_now()

        self.status = (
            InvestigationStatus.REOPENED
        )

        self.reopened_at = timestamp
        self.updated_at = timestamp

    # =========================================================================
    # Ownership
    # =========================================================================

    def assign_owner(
        self,
        owner: str,
    ) -> None:
        """
        Assign an owner to the investigation.
        """

        owner = owner.strip()

        if not owner:
            raise ValueError(
                "Investigation owner cannot be empty."
            )

        if self.owner != owner:
            self.owner = owner
            self.touch()

    def clear_owner(self) -> None:
        """
        Remove the current investigation owner.
        """

        if self.owner is not None:
            self.owner = None
            self.touch()

    # =========================================================================
    # Notes
    # =========================================================================

    def add_note(
        self,
        note: str,
    ) -> None:
        """
        Add an investigation note.
        """

        note = note.strip()

        if not note:
            raise ValueError(
                "Investigation note cannot be empty."
            )

        self.notes.append(
            note
        )

        self.touch()


# =============================================================================
# Response Governance
# =============================================================================


class ResponseGovernance(Gen2XModel):
    """
    Represents the authorization boundary surrounding a response.

    ResponseGovernance answers:

        "Are we authorized to perform this recommendation?"

    Governance is intentionally separate from recommendation.

    A response may be technically appropriate while still requiring
    human approval, business authorization, or manual execution.
    """

    approval_mode: ApprovalMode

    approval_status: ApprovalStatus

    execution_mode: ExecutionMode

    requested_by: str | None = None

    requested_at: datetime | None = None

    approved_by: str | None = None

    approved_at: datetime | None = None

    rejected_by: str | None = None

    rejected_at: datetime | None = None

    decision_reason: str = ""

    # =========================================================================
    # Normalization
    # =========================================================================

    @field_validator(
        "requested_by",
        "approved_by",
        "rejected_by",
    )
    @classmethod
    def normalize_actor(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize optional governance actor identifiers.
        """

        if value is None:
            return None

        value = value.strip()

        return value or None

    @field_validator(
        "decision_reason",
    )
    @classmethod
    def normalize_decision_reason(
        cls,
        value: str,
    ) -> str:
        """
        Normalize the governance decision reason.
        """

        return value.strip()

    # =========================================================================
    # Derived State
    # =========================================================================

    @property
    def requires_approval(self) -> bool:
        """
        Return True when the configured approval mode requires
        explicit approval before execution.

        Adjust the exact enum member during integration if the
        project's ApprovalMode vocabulary differs.
        """

        return self.approval_mode not in {
            ApprovalMode.NONE,
        }

    @property
    def is_approved(self) -> bool:
        """
        Return True when governance records an approved response.
        """

        return (
            self.approval_status
            == ApprovalStatus.APPROVED
        )

    @property
    def is_rejected(self) -> bool:
        """
        Return True when governance records a rejected response.
        """

        return (
            self.approval_status
            == ApprovalStatus.REJECTED
        )

    @property
    def is_pending(self) -> bool:
        """
        Return True when an approval decision remains pending.
        """

        return (
            self.approval_status
            == ApprovalStatus.PENDING
        )

    @property
    def approval_satisfied(self) -> bool:
        """
        Return True when the approval requirement has been satisfied.

        Responses that do not require approval are immediately
        considered satisfied from the governance perspective.
        """

        if not self.requires_approval:
            return True

        return self.is_approved

    # =========================================================================
    # Approval Lifecycle
    # =========================================================================

    def request_approval(
        self,
        requested_by: str,
    ) -> None:
        """
        Record an approval request.
        """

        requested_by = requested_by.strip()

        if not requested_by:
            raise ValueError(
                "requested_by cannot be empty."
            )

        self.requested_by = requested_by
        self.requested_at = utc_now()

        self.approval_status = (
            ApprovalStatus.PENDING
        )

        self.approved_by = None
        self.approved_at = None

        self.rejected_by = None
        self.rejected_at = None

        self.decision_reason = ""

    def approve(
        self,
        approved_by: str,
        reason: str = "",
    ) -> None:
        """
        Approve the recommended response.

        Approval records authorization.

        It does not execute the response.
        """

        approved_by = approved_by.strip()

        if not approved_by:
            raise ValueError(
                "approved_by cannot be empty."
            )

        timestamp = utc_now()

        self.approval_status = (
            ApprovalStatus.APPROVED
        )

        self.approved_by = approved_by
        self.approved_at = timestamp

        self.rejected_by = None
        self.rejected_at = None

        self.decision_reason = (
            reason.strip()
        )

    def reject(
        self,
        rejected_by: str,
        reason: str,
    ) -> None:
        """
        Reject the recommended response.

        A rejection reason is required because security decisions
        should preserve why an authorized actor declined an action.
        """

        rejected_by = rejected_by.strip()
        reason = reason.strip()

        if not rejected_by:
            raise ValueError(
                "rejected_by cannot be empty."
            )

        if not reason:
            raise ValueError(
                "A rejection reason is required."
            )

        timestamp = utc_now()

        self.approval_status = (
            ApprovalStatus.REJECTED
        )

        self.rejected_by = rejected_by
        self.rejected_at = timestamp

        self.approved_by = None
        self.approved_at = None

        self.decision_reason = reason


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Investigations
#
# are journeys.
#
# Authorization
#
# is permission.
#
# They are not
#
# the same thing.
#
# An investigation
#
# may begin
#
# with one alert.
#
# Then another.
#
# Then evidence.
#
# Then conflicting
#
# evidence.
#
# Then someone says:
#
# "We understand
# what happened."
#
# And five minutes later
#
# someone else
#
# finds something new.
#
# Welcome
#
# to security.
#
# This is why
#
# investigations
#
# should not
#
# pretend
#
# to be
#
# perfectly linear.
#
# Humans investigate
#
# by learning.
#
# Learning
#
# changes
#
# understanding.
#
# Understanding
#
# changes
#
# decisions.
#
# But decisions
#
# create
#
# another question:
#
# "Who gave us
# permission
# to do this?"
#
# Knowing
#
# that an account
#
# should be disabled
#
# does not mean
#
# every engineer
#
# may disable it.
#
# Knowing
#
# that a workload
#
# should be isolated
#
# does not mean
#
# an autonomous agent
#
# should immediately
#
# pull the network cable.
#
# Good automation
#
# understands
#
# capability.
#
# Secure automation
#
# understands
#
# authority.
#
# Capability asks:
#
# "Can I?"
#
# Governance asks:
#
# "May I?"
#
# Mature engineering
#
# knows
#
# that these
#
# are profoundly
#
# different questions.
#
# And when
#
# the answer
#
# is uncertain...
#
# the correct action
#
# may simply be:
#
# wait
#
# for a human.
#
# That is not
#
# weak automation.
#
# That is
#
# automation
#
# that understands
#
# its place
#
# in a system
#
# built by
#
# and accountable
#
# to people.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Governance Review Board
#                                Porg Sushi Quality Assurance
#
# =============================================================================

# =============================================================================
# Part III
# Response Domain Object
# =============================================================================


class Response(Gen2XModel):
    """
    Represents one complete response recommendation within Gen2X.

    Response composes:

        • ResponseIdentity
        • ResponseTarget
        • ResponseRecommendation
        • InvestigationState
        • ResponseGovernance

    into one domain object.

    A Response represents what Gen2X recommends,
    where the recommendation applies,
    where the investigation currently stands,
    and whether the recommendation is authorized.

    Response does NOT execute actions.

    Execution belongs to a separate response executor.
    """

    identity: ResponseIdentity

    target: ResponseTarget

    recommendation: ResponseRecommendation

    investigation: InvestigationState = Field(
        default_factory=InvestigationState
    )

    governance: ResponseGovernance

    # =========================================================================
    # Identity Properties
    # =========================================================================

    @property
    def response_id(self) -> UUID:
        """
        Return the response identifier.
        """

        return self.identity.response_id

    @property
    def threat_id(self) -> str:
        """
        Return the threat associated with this response.
        """

        return self.identity.threat_id

    @property
    def assessment_id(self) -> str | None:
        """
        Return the associated Fusion assessment identifier.
        """

        return self.identity.assessment_id

    @property
    def created_at(self) -> datetime:
        """
        Return the response creation timestamp.
        """

        return self.identity.created_at

    @property
    def updated_at(self) -> datetime:
        """
        Return the most recent response update timestamp.
        """

        return self.identity.updated_at

    # =========================================================================
    # Recommendation Properties
    # =========================================================================

    @property
    def action(self) -> ResponseAction:
        """
        Return the recommended response action.
        """

        return self.recommendation.action

    @property
    def priority(self) -> ResponsePriority:
        """
        Return the response priority.
        """

        return self.recommendation.priority

    @property
    def rationale(self) -> str:
        """
        Return the engineering rationale supporting the recommendation.
        """

        return self.recommendation.rationale

    @property
    def expected_outcome(self) -> str:
        """
        Return the expected outcome of the recommended action.
        """

        return self.recommendation.expected_outcome

    # =========================================================================
    # Investigation Properties
    # =========================================================================

    @property
    def investigation_status(
        self,
    ) -> InvestigationStatus:
        """
        Return the current investigation lifecycle state.
        """

        return self.investigation.status

    @property
    def investigation_owner(
        self,
    ) -> str | None:
        """
        Return the current investigation owner.
        """

        return self.investigation.owner

    # =========================================================================
    # Governance Properties
    # =========================================================================

    @property
    def approval_mode(self) -> ApprovalMode:
        """
        Return the configured approval mode.
        """

        return self.governance.approval_mode

    @property
    def approval_status(self) -> ApprovalStatus:
        """
        Return the current approval status.
        """

        return self.governance.approval_status

    @property
    def execution_mode(self) -> ExecutionMode:
        """
        Return the configured execution mode.
        """

        return self.governance.execution_mode

    @property
    def requires_approval(self) -> bool:
        """
        Return True when explicit approval is required.
        """

        return self.governance.requires_approval

    @property
    def is_approved(self) -> bool:
        """
        Return True when governance has approved the response.
        """

        return self.governance.is_approved

    @property
    def is_rejected(self) -> bool:
        """
        Return True when governance has rejected the response.
        """

        return self.governance.is_rejected

    # =========================================================================
    # Target Properties
    # =========================================================================

    @property
    def has_target(self) -> bool:
        """
        Return True when the response has a concrete target.
        """

        return self.target.has_target

    # =========================================================================
    # Derived Execution State
    # =========================================================================

    @property
    def is_executable(self) -> bool:
        """
        Return True when the response is eligible for execution.

        This property does NOT execute anything.

        It only evaluates whether the model state indicates that
        execution may proceed.

        Execution requires:

            • A concrete target
            • Approval requirements to be satisfied
            • The recommendation not to be rejected
            • The investigation to remain open
        """

        return (
            self.has_target
            and
            self.governance.approval_satisfied
            and
            not self.is_rejected
            and
            self.investigation.is_open
        )

    @property
    def is_pending_approval(self) -> bool:
        """
        Return True when execution is blocked by pending approval.
        """

        return (
            self.requires_approval
            and
            self.governance.is_pending
        )

    @property
    def is_blocked(self) -> bool:
        """
        Return True when the response cannot currently proceed.
        """

        return not self.is_executable

    # =========================================================================
    # Lifecycle Coordination
    # =========================================================================

    def touch(self) -> None:
        """
        Update the response modification timestamp.
        """

        self.identity.touch()

    def assign_owner(
        self,
        owner: str,
    ) -> None:
        """
        Assign an investigation owner.
        """

        self.investigation.assign_owner(
            owner
        )

        self.touch()

    def request_approval(
        self,
        requested_by: str,
    ) -> None:
        """
        Request authorization for the recommended response.
        """

        self.governance.request_approval(
            requested_by
        )

        self.investigation.mark_response_pending()

        self.touch()

    def approve(
        self,
        approved_by: str,
        reason: str = "",
    ) -> None:
        """
        Approve the response recommendation.

        Approval changes governance state.

        It does not execute the response.
        """

        self.governance.approve(
            approved_by=approved_by,
            reason=reason,
        )

        self.touch()

    def reject(
        self,
        rejected_by: str,
        reason: str,
    ) -> None:
        """
        Reject the response recommendation.
        """

        self.governance.reject(
            rejected_by=rejected_by,
            reason=reason,
        )

        self.touch()

    def mark_response_in_progress(
        self,
    ) -> None:
        """
        Record that an authorized response has entered execution.

        This method changes investigation state only.

        It does not perform the response.
        """

        if not self.is_executable:
            raise ValueError(
                "Response is not currently executable."
            )

        self.investigation.mark_response_in_progress()

        self.touch()

    def begin_monitoring(
        self,
    ) -> None:
        """
        Move the investigation into post-response monitoring.
        """

        self.investigation.begin_monitoring()

        self.touch()

    def resolve(
        self,
    ) -> None:
        """
        Mark the underlying security condition as resolved.
        """

        self.investigation.resolve()

        self.touch()

    def close(
        self,
    ) -> None:
        """
        Administratively close the investigation.
        """

        self.investigation.close()

        self.touch()

    def reopen(
        self,
    ) -> None:
        """
        Reopen the investigation when new evidence or concerns appear.
        """

        self.investigation.reopen()

        self.touch()

    # =========================================================================
    # Matching Helpers
    # =========================================================================

    def matches_threat(
        self,
        threat_id: str,
    ) -> bool:
        """
        Return True when this response belongs to the supplied threat.
        """

        return (
            self.threat_id
            == threat_id.strip()
        )

    def matches_action(
        self,
        action: ResponseAction,
    ) -> bool:
        """
        Return True when the recommendation uses the supplied action.
        """

        return self.action == action

    def matches_priority(
        self,
        priority: ResponsePriority,
    ) -> bool:
        """
        Return True when the response has the supplied priority.
        """

        return self.priority == priority

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

        It is not a formal response report.
        """

        return (
            f"{self.action.value} "
            f"[priority={self.priority.value}, "
            f"investigation={self.investigation_status.value}, "
            f"approval={self.approval_status.value}, "
            f"executable={self.is_executable}]"
        )

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Return a JSON-friendly representation of the response.

        Pydantic performs the nested serialization.

        Derived execution state is added for operational convenience.
        """

        data = self.model_dump(
            mode="json"
        )

        data["derived"] = {
            "requires_approval":
                self.requires_approval,

            "is_approved":
                self.is_approved,

            "is_rejected":
                self.is_rejected,

            "is_pending_approval":
                self.is_pending_approval,

            "has_target":
                self.has_target,

            "is_executable":
                self.is_executable,

            "is_blocked":
                self.is_blocked,
        }

        return data


# =============================================================================
#
# Chewbacca's Final Thoughts 🐾
#
# Engineers
#
# love
#
# powerful systems.
#
# Systems
#
# that can
#
# disable accounts.
#
# Rotate secrets.
#
# Block traffic.
#
# Isolate workloads.
#
# Revoke tokens.
#
# Change production.
#
# Power
#
# is exciting.
#
# Authority
#
# is quieter.
#
# But authority
#
# is what makes
#
# power
#
# legitimate.
#
# A system
#
# may possess
#
# credentials
#
# capable
#
# of changing
#
# an entire environment.
#
# That does not mean
#
# it should
#
# use them
#
# whenever
#
# it wishes.
#
# Credentials
#
# grant
#
# capability.
#
# Governance
#
# grants
#
# permission.
#
# And good engineering
#
# requires
#
# both.
#
# The same
#
# is true
#
# for people.
#
# Access
#
# should be
#
# earned.
#
# Authority
#
# should be
#
# explicitly granted.
#
# Actions
#
# should be
#
# attributable.
#
# Decisions
#
# should be
#
# explainable.
#
# And powerful
#
# automation
#
# should always
#
# remember
#
# that having
#
# the keys
#
# does not mean
#
# owning
#
# the building.
#
# This is why
#
# Response
#
# does not contain
#
# execute().
#
# The model
#
# may determine
#
# that execution
#
# is permitted.
#
# Another component
#
# must still
#
# perform
#
# the action.
#
# Separation
#
# creates
#
# boundaries.
#
# Boundaries
#
# create
#
# control.
#
# Control
#
# creates
#
# trust.
#
# And trust
#
# should never
#
# be confused
#
# with
#
# unlimited access.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#                                Keeper of the Keys
#                                Porg Sushi Authorization Board
#
# =============================================================================
