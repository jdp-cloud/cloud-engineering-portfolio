"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    report_enums.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This module defines the enumerations used by the Gen2X Reporting Framework.

The reporting framework is responsible for communicating the results of
security analysis.

Reports do not perform threat analysis.

Reports do not collect intelligence.

Reports do not calculate risk.

Reports communicate conclusions that were produced elsewhere in the platform.

Examples include:

    • Threat Intelligence Reports
    • Executive Dashboards
    • Compliance Evidence Reports
    • Incident Summaries
    • SOAR Response Reports
    • Threat Hunt Reports
    • Vulnerability Assessments

-------------------------------------------------------------------------------

Architectural Philosophy

Gen2X separates the investigation lifecycle into distinct responsibilities.

Indicators answer:

    "What did we observe?"

Providers answer:

    "What evidence did we collect?"

Threat Analysis answers:

    "What does the evidence mean?"

Reporting answers:

    "How should the conclusion be communicated?"

This separation allows one investigation to be presented in many formats
without recalculating or changing the underlying security assessment.

-------------------------------------------------------------------------------

Reporting Pipeline

Threat Summary

        ↓

Report Builder

        ↓

Structured Report Model

        ↓

Renderer

        ├── JSON
        ├── PDF
        ├── Markdown
        ├── HTML
        ├── CSV
        └── Console

The structured report remains the source of truth.

Renderers change presentation.

They do not change evidence.

===============================================================================

Chewbacca's Commentary 🐶

One investigation may produce:

    • A JSON document for another application

    • A PDF for leadership

    • Markdown for GitHub

    • HTML for a dashboard

    • Console output for CloudWatch

Every format should contain the same underlying facts.

Only the presentation changes.

Good software separates:

    Data

from

    Presentation

The report should never change the investigation.

It should only explain it.

                                — Chewbacca
                                  Chief Wookiee Architect

===============================================================================
"""

from __future__ import annotations

from .base_enum import Gen2XEnum


# =============================================================================
# Report Type
# =============================================================================


class ReportType(Gen2XEnum):
    """
    Describes the purpose and subject of a report.

    ReportType answers one question:

        "What kind of report is this?"

    ReportType does not describe:

        • Whether the report generated successfully
        • The severity of its findings
        • The intended audience
        • The output file format

    Those concepts are represented by separate enumerations.
    """

    # -------------------------------------------------------------------------
    # Threat Intelligence
    # -------------------------------------------------------------------------

    THREAT_INTELLIGENCE = "THREAT_INTELLIGENCE"

    # -------------------------------------------------------------------------
    # Incident Response
    # -------------------------------------------------------------------------

    INCIDENT_SUMMARY = "INCIDENT_SUMMARY"

    INCIDENT_TIMELINE = "INCIDENT_TIMELINE"

    FORENSIC_SUMMARY = "FORENSIC_SUMMARY"

    # -------------------------------------------------------------------------
    # Security Operations
    # -------------------------------------------------------------------------

    SOAR_RESPONSE = "SOAR_RESPONSE"

    THREAT_HUNT = "THREAT_HUNT"

    PROVIDER_HEALTH = "PROVIDER_HEALTH"

    # -------------------------------------------------------------------------
    # Executive Reporting
    # -------------------------------------------------------------------------

    EXECUTIVE_DASHBOARD = "EXECUTIVE_DASHBOARD"

    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"

    # -------------------------------------------------------------------------
    # Compliance and Audit
    # -------------------------------------------------------------------------

    COMPLIANCE_EVIDENCE = "COMPLIANCE_EVIDENCE"

    AUDIT_EVIDENCE = "AUDIT_EVIDENCE"

    CONTROL_ASSESSMENT = "CONTROL_ASSESSMENT"

    # -------------------------------------------------------------------------
    # Vulnerability Management
    # -------------------------------------------------------------------------

    VULNERABILITY_ASSESSMENT = "VULNERABILITY_ASSESSMENT"

    REMEDIATION_SUMMARY = "REMEDIATION_SUMMARY"

    # -------------------------------------------------------------------------
    # Cloud Security
    # -------------------------------------------------------------------------

    CLOUD_SECURITY_ASSESSMENT = "CLOUD_SECURITY_ASSESSMENT"

    IAM_ASSESSMENT = "IAM_ASSESSMENT"

    ASSET_EXPOSURE = "ASSET_EXPOSURE"

    # -------------------------------------------------------------------------
    # General
    # -------------------------------------------------------------------------

    CUSTOM = "CUSTOM"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """
        Return a human-readable description of the report type.

        The descriptions can later support:

            • Documentation
            • User interfaces
            • API schemas
            • Report headers
            • Student exploration
        """

        descriptions = {
            ReportType.THREAT_INTELLIGENCE: (
                "A report containing enriched threat intelligence, "
                "evidence, findings, and recommendations."
            ),
            ReportType.INCIDENT_SUMMARY: (
                "A structured summary of a security incident."
            ),
            ReportType.INCIDENT_TIMELINE: (
                "A chronological report describing incident activity."
            ),
            ReportType.FORENSIC_SUMMARY: (
                "A report summarizing forensic observations and evidence."
            ),
            ReportType.SOAR_RESPONSE: (
                "A report describing security orchestration and response results."
            ),
            ReportType.THREAT_HUNT: (
                "A report documenting a threat-hunting investigation."
            ),
            ReportType.PROVIDER_HEALTH: (
                "A report describing the health of intelligence providers."
            ),
            ReportType.EXECUTIVE_DASHBOARD: (
                "A leadership-focused security dashboard report."
            ),
            ReportType.EXECUTIVE_SUMMARY: (
                "A concise management summary of security findings."
            ),
            ReportType.COMPLIANCE_EVIDENCE: (
                "A report presenting deterministic control evidence."
            ),
            ReportType.AUDIT_EVIDENCE: (
                "A report preserving evidence for audit review."
            ),
            ReportType.CONTROL_ASSESSMENT: (
                "A report evaluating one or more security controls."
            ),
            ReportType.VULNERABILITY_ASSESSMENT: (
                "A report describing vulnerabilities and associated risk."
            ),
            ReportType.REMEDIATION_SUMMARY: (
                "A report describing remediation work and current status."
            ),
            ReportType.CLOUD_SECURITY_ASSESSMENT: (
                "A report evaluating cloud-security posture and findings."
            ),
            ReportType.IAM_ASSESSMENT: (
                "A report evaluating identity and access-management findings."
            ),
            ReportType.ASSET_EXPOSURE: (
                "A report describing exposed or externally reachable assets."
            ),
            ReportType.CUSTOM: (
                "A custom report defined by the application."
            ),
            ReportType.UNKNOWN: (
                "A report whose purpose has not been classified."
            ),
        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐶
#
# ReportType describes PURPOSE.
#
# It does not describe audience.
#
# Example:
#
#     ReportType.THREAT_INTELLIGENCE
#
# could be produced for:
#
#     • A SOC analyst
#     • A security engineer
#     • An executive
#
# Same report purpose.
#
# Different audience.
#
# Keeping those concepts separate allows the reporting framework to adapt
# presentation without changing the investigation itself.
#
# =============================================================================


# =============================================================================
# Report Status
# =============================================================================


class ReportStatus(Gen2XEnum):
    """
    Describes the current lifecycle state of a report.

    ReportStatus answers:

        "What happened during report generation?"

    ReportStatus does not describe security posture.

    A report may generate successfully while describing a critical incident.

    A report may fail to generate even when no threat exists.
    """

    DRAFT = "DRAFT"

    REVIEW = "REVIEW"

    FINAL = "FINAL"

    QUEUED = "QUEUED"

    GENERATING = "GENERATING"

    COMPLETE = "COMPLETE"

    PARTIAL = "PARTIAL"

    FAILED = "FAILED"

    ARCHIVED = "ARCHIVED"

    SUPERSEDED = "SUPERSEDED"

    CANCELLED = "CANCELLED"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """Return a human-readable explanation of the report status."""

        descriptions = {
            ReportStatus.DRAFT: (
                "The report exists but has not been finalized."
            ),
            ReportStatus.REVIEW: (
                "The report is under review before finalization."
            ),
            ReportStatus.FINAL: (
                "The report has been finalized as a historical record."
            ),
            ReportStatus.QUEUED: (
                "The report is waiting to be generated."
            ),
            ReportStatus.GENERATING: (
                "The reporting process is currently running."
            ),
            ReportStatus.COMPLETE: (
                "The report was generated successfully."
            ),
            ReportStatus.PARTIAL: (
                "The report was generated, but some data or sources were unavailable."
            ),
            ReportStatus.FAILED: (
                "The reporting process did not complete successfully."
            ),
            ReportStatus.ARCHIVED: (
                "The report has been retained for historical or audit purposes."
            ),
            ReportStatus.SUPERSEDED: (
                "A newer report has replaced this report."
            ),
            ReportStatus.CANCELLED: (
                "Report generation was intentionally stopped."
            ),
            ReportStatus.UNKNOWN: (
                "The report lifecycle state has not been determined."
            ),
        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐶
#
# COMPLETE does not mean:
#
#     "Everything is secure."
#
# COMPLETE means:
#
#     "The reporting process finished successfully."
#
# A completed report may contain:
#
#     Critical findings
#
# A failed report may contain:
#
#     No security findings at all
#
# Report status describes document production.
#
# It does not describe threat severity.
#
# =============================================================================


# =============================================================================
# Report Format
# =============================================================================


class ReportFormat(Gen2XEnum):
    """
    Describes the rendering format used to present a report.

    ReportFormat answers:

        "How should this report be rendered?"

    The format should not change the report's underlying evidence,
    findings, recommendations, or assessment.
    """

    JSON = "JSON"

    PDF = "PDF"

    MARKDOWN = "MARKDOWN"

    HTML = "HTML"

    CSV = "CSV"

    TEXT = "TEXT"

    CONSOLE = "CONSOLE"

    YAML = "YAML"

    XML = "XML"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """Return a human-readable explanation of the report format."""

        descriptions = {
            ReportFormat.JSON: (
                "Structured JSON suitable for APIs, automation, and storage."
            ),
            ReportFormat.PDF: (
                "A portable document intended primarily for human readers."
            ),
            ReportFormat.MARKDOWN: (
                "Markdown suitable for GitHub, documentation, and tickets."
            ),
            ReportFormat.HTML: (
                "HTML suitable for dashboards and web applications."
            ),
            ReportFormat.CSV: (
                "Tabular comma-separated data suitable for analysis tools."
            ),
            ReportFormat.TEXT: (
                "Plain-text output suitable for simple systems."
            ),
            ReportFormat.CONSOLE: (
                "Compact output intended for terminals and CloudWatch logs."
            ),
            ReportFormat.YAML: (
                "Structured YAML suitable for readable configuration-style output."
            ),
            ReportFormat.XML: (
                "Structured XML suitable for systems requiring XML integration."
            ),
            ReportFormat.UNKNOWN: (
                "A report format that has not been classified."
            ),
        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐶
#
# The report object should not care whether it becomes:
#
#     PDF
#
#     JSON
#
#     Markdown
#
#     HTML
#
# That is the renderer's responsibility.
#
# The report contains information.
#
# The renderer controls presentation.
#
# If adding a new output format requires changing the threat-analysis engine,
# the architecture is probably too tightly coupled.
#
# =============================================================================


# =============================================================================
# Report Audience
# =============================================================================


class ReportAudience(Gen2XEnum):
    """
    Describes the intended audience for a report.

    ReportAudience answers:

        "Who is expected to read or consume this report?"

    The audience may influence:

        • Narrative detail
        • Terminology
        • Report length
        • Evidence visibility
        • Recommended-action language

    The audience must not alter the underlying facts.
    """

    SOC_ANALYST = "SOC_ANALYST"

    INCIDENT_RESPONDER = "INCIDENT_RESPONDER"

    SECURITY_ENGINEER = "SECURITY_ENGINEER"

    CLOUD_ENGINEER = "CLOUD_ENGINEER"

    PLATFORM_ENGINEER = "PLATFORM_ENGINEER"

    DEVELOPER = "DEVELOPER"

    EXECUTIVE = "EXECUTIVE"

    AUDITOR = "AUDITOR"

    COMPLIANCE_TEAM = "COMPLIANCE_TEAM"

    RISK_TEAM = "RISK_TEAM"

    LEGAL = "LEGAL"

    STUDENT = "STUDENT"

    INSTRUCTOR = "INSTRUCTOR"

    GENERAL = "GENERAL"

    MACHINE = "MACHINE"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """Return a human-readable explanation of the report audience."""

        descriptions = {
            ReportAudience.SOC_ANALYST: (
                "Security operations personnel who require detailed evidence."
            ),
            ReportAudience.INCIDENT_RESPONDER: (
                "Responders who need actionable incident details and timelines."
            ),
            ReportAudience.SECURITY_ENGINEER: (
                "Security engineers who require technical findings and remediation."
            ),
            ReportAudience.CLOUD_ENGINEER: (
                "Cloud engineers responsible for cloud resources and configuration."
            ),
            ReportAudience.PLATFORM_ENGINEER: (
                "Platform engineers responsible for shared infrastructure."
            ),
            ReportAudience.DEVELOPER: (
                "Software developers responsible for application changes."
            ),
            ReportAudience.EXECUTIVE: (
                "Leadership requiring concise business impact and risk summaries."
            ),
            ReportAudience.AUDITOR: (
                "Auditors requiring traceable evidence and control results."
            ),
            ReportAudience.COMPLIANCE_TEAM: (
                "Compliance professionals reviewing control evidence."
            ),
            ReportAudience.RISK_TEAM: (
                "Risk professionals evaluating organizational exposure."
            ),
            ReportAudience.LEGAL: (
                "Legal personnel reviewing relevant facts and documented limitations."
            ),
            ReportAudience.STUDENT: (
                "Students who benefit from explanatory and educational commentary."
            ),
            ReportAudience.INSTRUCTOR: (
                "Instructors reviewing technical and educational material."
            ),
            ReportAudience.GENERAL: (
                "A general audience without a specialized technical role."
            ),
            ReportAudience.MACHINE: (
                "Another application, agent, API, or automated workflow."
            ),
            ReportAudience.UNKNOWN: (
                "An audience that has not been identified."
            ),
        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐶
#
# Imagine explaining SQL injection.
#
# To a SOC analyst:
#
#     Include request details, source IPs, rules, and timestamps.
#
# To an executive:
#
#     Explain affected systems, business impact, and required decisions.
#
# Same investigation.
#
# Different communication.
#
# Professional communication adapts to the reader without changing facts.
#
# =============================================================================


# =============================================================================
# Finding Severity
# =============================================================================


class FindingSeverity(Gen2XEnum):
    """
    Describes the severity assigned to an individual report finding.

    FindingSeverity answers:

        "How important is this finding?"

    A report may contain several findings with different severity levels.

    FindingSeverity does not necessarily equal:

        • Overall threat risk
        • Incident priority
        • Recommendation priority
        • Report status
    """

    INFORMATIONAL = "INFORMATIONAL"

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    CRITICAL = "CRITICAL"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """Return a human-readable explanation of finding severity."""

        descriptions = {
            FindingSeverity.INFORMATIONAL: (
                "A useful observation that does not currently indicate material risk."
            ),
            FindingSeverity.LOW: (
                "A minor issue with limited expected impact."
            ),
            FindingSeverity.MEDIUM: (
                "A meaningful issue that should receive normal investigation."
            ),
            FindingSeverity.HIGH: (
                "A serious issue requiring expedited investigation or remediation."
            ),
            FindingSeverity.CRITICAL: (
                "A severe issue requiring immediate attention."
            ),
            FindingSeverity.UNKNOWN: (
                "The finding severity has not been determined."
            ),
        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐶
#
# One report may contain:
#
#     Finding 1
#         Known exploited CVE
#         CRITICAL
#
#     Finding 2
#         Provider timeout
#         INFORMATIONAL
#
#     Finding 3
#         TOR association
#         MEDIUM
#
# Not every observation has the same importance.
#
# Structured findings allow the report to preserve those differences.
#
# =============================================================================


# =============================================================================
# Recommendation Priority
# =============================================================================


class RecommendationPriority(Gen2XEnum):
    """
    Describes the urgency assigned to a recommended action.

    RecommendationPriority answers:

        "How quickly should this recommendation be considered?"

    Recommendation priority may depend on:

        • Business context
        • Asset ownership
        • Existing controls
        • Operational impact
        • Threat confidence
        • Organizational policy

    It should not be derived from severity alone.
    """

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    CRITICAL = "CRITICAL"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """Return a human-readable explanation of recommendation priority."""

        descriptions = {
            RecommendationPriority.LOW: (
                "The recommendation may be handled during normal maintenance."
            ),
            RecommendationPriority.MEDIUM: (
                "The recommendation should enter the standard work queue."
            ),
            RecommendationPriority.HIGH: (
                "The recommendation should receive expedited attention."
            ),
            RecommendationPriority.CRITICAL: (
                "The recommendation requires immediate attention."
            ),
            RecommendationPriority.UNKNOWN: (
                "The recommendation priority has not been determined."
            ),
        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐶
#
# Recommendation priority is not the same as finding severity.
#
# Example:
#
# A critical vulnerability exists on a development server that will be
# destroyed tonight.
#
# Finding severity:
#
#     CRITICAL
#
# Recommendation priority:
#
#     LOW or MEDIUM
#
# Why?
#
# Context matters.
#
# Security engineering is not just assigning labels.
#
# It is understanding the environment around the finding.
#
# =============================================================================


# =============================================================================
# Recommendation Category
# =============================================================================


class RecommendationCategory(Gen2XEnum):
    """
    Describes the general purpose of a recommended action.

    RecommendationCategory answers:

        "What kind of action is being proposed?"

    Categories allow recommendations to be filtered, grouped, reported,
    and eventually routed into workflows.
    """

    INVESTIGATE = "INVESTIGATE"

    VALIDATE = "VALIDATE"

    MONITOR = "MONITOR"

    CONTAIN = "CONTAIN"

    REMEDIATE = "REMEDIATE"

    RECOVER = "RECOVER"

    ESCALATE = "ESCALATE"

    NOTIFY = "NOTIFY"

    DOCUMENT = "DOCUMENT"

    PRESERVE_EVIDENCE = "PRESERVE_EVIDENCE"

    ACCEPT_RISK = "ACCEPT_RISK"

    CLOSE = "CLOSE"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """Return a human-readable explanation of the recommendation category."""

        descriptions = {
            RecommendationCategory.INVESTIGATE: (
                "Collect and analyze additional evidence."
            ),
            RecommendationCategory.VALIDATE: (
                "Confirm the finding using independent evidence or ownership context."
            ),
            RecommendationCategory.MONITOR: (
                "Continue observing the indicator, asset, or behavior."
            ),
            RecommendationCategory.CONTAIN: (
                "Limit or stop potentially harmful activity."
            ),
            RecommendationCategory.REMEDIATE: (
                "Correct the vulnerability, misconfiguration, or control weakness."
            ),
            RecommendationCategory.RECOVER: (
                "Restore affected systems or services."
            ),
            RecommendationCategory.ESCALATE: (
                "Transfer the issue to a team or authority with greater responsibility."
            ),
            RecommendationCategory.NOTIFY: (
                "Inform relevant stakeholders."
            ),
            RecommendationCategory.DOCUMENT: (
                "Record the decision, evidence, or action."
            ),
            RecommendationCategory.PRESERVE_EVIDENCE: (
                "Retain evidence for investigation, audit, or legal review."
            ),
            RecommendationCategory.ACCEPT_RISK: (
                "Formally acknowledge and accept the identified risk."
            ),
            RecommendationCategory.CLOSE: (
                "Conclude the recommendation or associated investigation."
            ),
            RecommendationCategory.UNKNOWN: (
                "The recommendation category has not been classified."
            ),
        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐶
#
# Findings and recommendations are different.
#
# Finding:
#
#     A public S3 bucket was identified.
#
# Recommendation:
#
#     Validate the business requirement and restrict public access.
#
# The finding describes what was observed.
#
# The recommendation describes what should be considered next.
#
# Never hide a decision inside an observation.
#
# =============================================================================


# =============================================================================
# Report Technical Level
# =============================================================================


class ReportTechnicalLevel(Gen2XEnum):
    """
    Describes the depth of technical detail a report should contain.

    ReportTechnicalLevel answers:

        "How deep should the explanation go?"

    Technical level complements ReportAudience.

    Audience describes WHO reads the report.

    Technical level describes HOW MUCH technical detail they receive.
    """

    EXECUTIVE = "EXECUTIVE"

    STRATEGIC = "STRATEGIC"

    OPERATIONAL = "OPERATIONAL"

    TECHNICAL = "TECHNICAL"

    FORENSIC = "FORENSIC"

    UNKNOWN = "UNKNOWN"

    def describe(self) -> str:
        """Return a human-readable explanation of the technical level."""

        descriptions = {
            ReportTechnicalLevel.EXECUTIVE: (
                "Business impact and decisions. Minimal technical detail."
            ),
            ReportTechnicalLevel.STRATEGIC: (
                "Trends, risk posture, and planning-level detail."
            ),
            ReportTechnicalLevel.OPERATIONAL: (
                "Actionable detail for day-to-day security operations."
            ),
            ReportTechnicalLevel.TECHNICAL: (
                "Full technical findings, evidence, and remediation detail."
            ),
            ReportTechnicalLevel.FORENSIC: (
                "Complete evidentiary detail suitable for legal or audit review."
            ),
            ReportTechnicalLevel.UNKNOWN: (
                "The technical level has not been classified."
            ),
        }

        return descriptions[self]


# =============================================================================
# Chewbacca's Commentary 🐶
#
# The same investigation
#
# can be explained
#
# in one sentence...
#
# or in forty pages.
#
# Neither is wrong.
#
# It depends on
#
# who is reading
#
# and what decision
#
# they must make.
#
# =============================================================================


# =============================================================================
# Public Module Interface
# =============================================================================
#
# __all__ defines the supported public objects exposed by this module.
#
# Other parts of Gen2X should normally import these values through:
#
#     from models.enums import ReportType
#
# rather than:
#
#     from models.enums.report_enums import ReportType
#
# The package-level import provides a stable public API while allowing the
# internal module structure to evolve.
#
# =============================================================================


__all__ = [
    "ReportType",
    "ReportStatus",
    "ReportFormat",
    "ReportAudience",
    "ReportTechnicalLevel",
    "FindingSeverity",
    "RecommendationPriority",
    "RecommendationCategory",
]


# =============================================================================
# Architect's Reflection
# =============================================================================
#
# Notice how this file contains no:
#
#     • ReportLab
#     • boto3
#     • S3 logic
#     • Bedrock prompts
#     • PDF generation
#     • JSON serialization
#     • Threat scoring
#
# That is intentional.
#
# This module defines vocabulary.
#
# Builders construct reports.
#
# Renderers present reports.
#
# Storage components publish reports.
#
# Threat engines calculate conclusions.
#
# Each part of the framework has one responsibility.
#
# As the platform grows, this separation allows:
#
#     • New report formats
#     • New audiences
#     • New report types
#     • New renderers
#
# without rewriting the investigation engine.
#
# Framework architecture is often less about writing more code.
#
# It is about placing code where it belongs.
#
#                                — Chewbacca
#                                  Chief Wookiee Architect
#
# =============================================================================
