"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    response_enums.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This module defines the enumerations used by the Gen2X Response Framework.

A Response represents the actions recommended after analysis has been
completed.

Unlike threat analysis, response planning is concerned with:

    • What action should occur?
    • Who owns that action?
    • Does the action require approval?
    • How urgent is the action?
    • How will the action be performed?
    • What happened after execution?

The response framework intentionally separates planning from execution.

This allows Gen2X to support:

    • AWS
    • Azure
    • Google Cloud Platform
    • Kubernetes
    • VMware
    • On-premises environments

without changing the framework itself.

-------------------------------------------------------------------------------

Architectural Philosophy

Indicators answer:

    "What did we observe?"

Providers answer:

    "What evidence exists?"

Threat Analysis answers:

    "What does the evidence mean?"

Reporting answers:

    "How do we communicate it?"

Response answers:

    "What should happen next?"

Execution engines decide HOW those actions occur.

-------------------------------------------------------------------------------

Response Workflow

Threat Summary

        ↓

Response Recommendation

        ↓

Approval

        ↓

Execution Engine

        ↓

Verification

        ↓

Audit Trail

===============================================================================

Chewbacca's Commentary 🐾

Many new engineers believe automation means:

    "Do everything automatically."

Enterprise security usually means something different.

Automation removes repetitive work.

Humans make difficult decisions.

A good framework knows where automation should stop.

Gen2X models decisions.

Execution engines perform actions.

Keeping those responsibilities separate allows the same framework to
support many different cloud providers.

                                — Chewbacca
                                  Chief Wookiee Architect

===============================================================================
"""

from .base_enum import Gen2XEnum


class ResponseAction(Gen2XEnum):
    """
    Describes the recommended action.

    ResponseAction answers:

        "What should happen?"

    The action intentionally describes intent rather than implementation.

    Example

        CONTAIN

    does not imply HOW containment occurs.
    """

    INVESTIGATE = "INVESTIGATE"

    VALIDATE = "VALIDATE"

    MONITOR = "MONITOR"

    NOTIFY = "NOTIFY"

    ESCALATE = "ESCALATE"

    CONTAIN = "CONTAIN"

    REMEDIATE = "REMEDIATE"

    RECOVER = "RECOVER"

    DOCUMENT = "DOCUMENT"

    ACCEPT_RISK = "ACCEPT_RISK"

    NO_ACTION = "NO_ACTION"

    UNKNOWN = "UNKNOWN"

# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# "Contain the threat."
#
# is an architectural decision.
#
# "Disable an EC2 instance."
#
# is an implementation.
#
# Tomorrow you might migrate to Azure.
#
# Or Kubernetes.
#
# Or GCP.
#
# The response recommendation should remain identical.
#
# Good abstractions survive cloud migrations.
#
# =============================================================================

class ResponseMode(Gen2XEnum):
    """
    Describes how a response should be executed.

    ResponseMode answers:

        "Who performs the work?"
    """

    MANUAL = "MANUAL"

    ASSISTED = "ASSISTED"

    SEMI_AUTOMATED = "SEMI_AUTOMATED"

    AUTOMATED = "AUTOMATED"

    DRY_RUN = "DRY_RUN"

    SIMULATION = "SIMULATION"

    UNKNOWN = "UNKNOWN"

# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# One of the biggest mistakes new engineers make is testing automation
# directly against production systems.
#
# DRY_RUN exists because learning should happen before automation.
#
# Simulate.
#
# Review.
#
# Automate.
#
# Sleep better.
#
# =============================================================================

class ResponseApproval(Gen2XEnum):
    """
    Describes whether human approval is required before execution.

    ResponseApproval answers:

        "Can we proceed?"
    """

    NOT_REQUIRED = "NOT_REQUIRED"

    REQUIRED = "REQUIRED"

    PENDING = "PENDING"

    APPROVED = "APPROVED"

    REJECTED = "REJECTED"

    EXPIRED = "EXPIRED"

    UNKNOWN = "UNKNOWN"

# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Frameworks should never assume every action is safe.
#
# Restarting a development container...
#
# probably doesn't require approval.
#
# Deleting a production database...
#
# definitely deserves a conversation.
#
# Good automation understands organizational policy.
#
# =============================================================================

class ApprovalMode(Gen2XEnum):
    """
    Describes the approval requirement configured for a response.

    ApprovalMode answers:

        "What approval does this action require?"

    ApprovalMode is configuration.

    ResponseApproval is the current state of the decision.

    Example

        approval_mode   = ApprovalMode.SINGLE_APPROVER

        approval_status = ResponseApproval.PENDING
    """

    NONE = "NONE"

    SINGLE_APPROVER = "SINGLE_APPROVER"

    DUAL_APPROVER = "DUAL_APPROVER"

    CHANGE_BOARD = "CHANGE_BOARD"

    UNKNOWN = "UNKNOWN"

# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Mode is the rule.
#
# Status is the moment.
#
# "This action requires two approvers."
#
# is a rule.
#
# "One approver has said yes."
#
# is a moment.
#
# Keep rules and moments separate,
# and audits become easy.
#
# =============================================================================

class ResponseOwner(Gen2XEnum):
    """
    Describes who is accountable for a response.

    ResponseOwner answers:

        "Who owns this action?"
    """

    SECURITY_ANALYST = "SECURITY_ANALYST"

    SOC_TEAM = "SOC_TEAM"

    INCIDENT_RESPONSE_TEAM = "INCIDENT_RESPONSE_TEAM"

    PLATFORM_TEAM = "PLATFORM_TEAM"

    APPLICATION_TEAM = "APPLICATION_TEAM"

    AUTOMATION = "AUTOMATION"

    EXTERNAL_PARTNER = "EXTERNAL_PARTNER"

    UNASSIGNED = "UNASSIGNED"

    UNKNOWN = "UNKNOWN"

# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Ownership answers:
#
#     "Who is accountable?"
#
# not
#
#     "Who clicked Execute?"
#
# Accountability survives automation.
#
# =============================================================================


class ResponsePriority(Gen2XEnum):
    """
    Describes response urgency.
    """

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    CRITICAL = "CRITICAL"

    UNKNOWN = "UNKNOWN"



# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Priority is often determined by business impact.
#
# Severity is usually determined by technical analysis.
#
# Those are different conversations.
#
# =============================================================================

class ResponseStatus(Gen2XEnum):
    """
    Describes workflow progress.

    ResponseStatus answers:

        "Where are we in the process?"
    """

    NOT_STARTED = "NOT_STARTED"

    WAITING_APPROVAL = "WAITING_APPROVAL"

    QUEUED = "QUEUED"

    IN_PROGRESS = "IN_PROGRESS"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"

    CANCELLED = "CANCELLED"

    UNKNOWN = "UNKNOWN"

class ResponseOutcome(Gen2XEnum):
    """
    Describes the outcome after execution.

    ResponseOutcome answers:

        "How did execution finish?"
    """

    SUCCESS = "SUCCESS"

    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"

    FAILED = "FAILED"

    TIMED_OUT = "TIMED_OUT"

    ROLLED_BACK = "ROLLED_BACK"

    SKIPPED = "SKIPPED"

    UNKNOWN = "UNKNOWN"

# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Status and Outcome are different.
#
# Status:
#
#     IN_PROGRESS
#
# Outcome:
#
#     does not exist yet.
#
# Separating lifecycle from outcome makes workflow engines much easier
# to understand and maintain.
#
# =============================================================================

class ResponseVerification(Gen2XEnum):
    """
    Describes whether the intended effect of the response has been verified.

    ResponseVerification answers:

        "Did the response achieve its intended goal?"
    """

    NOT_VERIFIED = "NOT_VERIFIED"

    VERIFIED = "VERIFIED"

    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"

    FAILED_VERIFICATION = "FAILED_VERIFICATION"

    UNKNOWN = "UNKNOWN"

# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# AWS returning HTTP 200 does not necessarily mean the problem is solved.
#
# A command can execute successfully while failing to achieve its goal.
#
# Good engineers verify outcomes.
#
# Great engineers automate verification.
#
# Frameworks should always leave room for verification before declaring
# victory.
#
# Build software that earns trust through evidence—not assumptions.
#
#                                — Chewbacca
#                                  Chief Wookiee Architect
#
# =============================================================================

__all__ = [
    "ResponseAction",
    "ResponseMode",
    "ResponseApproval",
    "ApprovalMode",
    "ResponseOwner",
    "ResponsePriority",
    "ResponseStatus",
    "ResponseOutcome",
    "ResponseVerification",
]
