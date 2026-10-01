"""
report.py

Agent 10 — Threat Intelligence Report Construction Engine

Purpose
-------
Transform the normalized output of the threat-intelligence fusion engine
into a structured investigation report.

Processing model
----------------

    ThreatSummary
    ThreatEvidence
    ProviderResult[]
    Indicator
           |
           v
    ThreatIntelligenceReportBuilder
           |
           v
    ThreatIntelligenceReport
           |
           +-------------------+
           |                   |
           v                   v
      JSON Renderer      Markdown Renderer
           |
           v
      Other Renderers
      PDF / HTML / S3

Architectural boundaries
------------------------

This module:

    - Builds a structured threat-intelligence report
    - Creates evidence-backed findings
    - Creates deterministic recommendations
    - Preserves provider provenance
    - Supports optional AI-generated narrative text
    - Renders reports into multiple presentation formats

This module does NOT:

    - Query external threat-intelligence providers
    - Calculate the final fusion risk
    - Recalculate confidence
    - Write to DynamoDB
    - Block indicators
    - Patch systems
    - Modify infrastructure

The fusion engine decides what the evidence means.

The reporting engine explains and presents that decision.
"""

from __future__ import annotations

import json
import logging
import uuid

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Mapping, Protocol, Sequence


LOGGER = logging.getLogger(__name__)


# ============================================================
# SECTION 1
# ENUMERATIONS
#
# Enumerations constrain the values used by findings,
# recommendations, and reports.
#
# This prevents inconsistent values such as:
#
#     "High"
#     "HIGH"
#     "high"
#
# Downstream systems therefore receive predictable output.
# ============================================================


class FindingSeverity(str, Enum):
    """Severity assigned to a report finding."""

    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationPriority(str, Enum):
    """Priority assigned to a recommended response action."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationCategory(str, Enum):
    """General category of a recommended action."""

    INVESTIGATE = "INVESTIGATE"
    CONTAIN = "CONTAIN"
    REMEDIATE = "REMEDIATE"
    MONITOR = "MONITOR"
    VALIDATE = "VALIDATE"
    DOCUMENT = "DOCUMENT"


class ReportStatus(str, Enum):
    """Lifecycle status of the generated report."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


# ============================================================
# SECTION 2
# INPUT CONTRACTS
#
# report.py should not depend tightly upon one exact
# implementation of fusion.py or providers.py.
#
# Protocols define only the fields needed by this module.
#
# Any compatible object may be supplied.
# ============================================================


class IndicatorProtocol(Protocol):
    """Minimum indicator interface required by report.py."""

    value: str
    indicator_type: str

    @property
    def indicator_id(self) -> str:
        """Return the normalized indicator identifier."""


class ThreatSummaryProtocol(Protocol):
    """Minimum ThreatSummary interface required by report.py."""

    overall_risk: str
    overall_confidence: int
    recommended_priority: str

    known_exploited: bool
    ransomware_associated: bool

    techniques: Sequence[str]
    cves: Sequence[str]

    sources_consulted: int
    successful_sources: int
    not_found_sources: int
    failed_sources: int

    supporting_reasons: Sequence[str]
    limitations: Sequence[str]

    analyzed_at: str
    policy_version: str

    def to_dict(self) -> dict[str, Any]:
        """Return the summary as a dictionary."""


class ThreatEvidenceProtocol(Protocol):
    """Minimum ThreatEvidence interface required by report.py."""

    providers_consulted: set[str]
    successful_providers: set[str]
    not_found_providers: set[str]
    failed_providers: set[str]

    techniques: set[str]
    cves: set[str]

    confidence_scores: list[int]
    abuse_scores: list[int]
    provider_risks: list[str]

    known_exploited: bool
    ransomware_associated: bool
    tor_observed: bool
    whitelisted: bool

    total_reports: int
    distinct_reporting_users: int

    provider_evidence: Mapping[str, Any]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return the evidence as a dictionary."""


class ProviderResultProtocol(Protocol):
    """Minimum provider result interface required by report.py."""

    provider: str
    indicator_id: str
    indicator: str
    indicator_type: str

    status: str
    retrieved_at: str
    expires_at: Any

    data: Mapping[str, Any]
    error: str | None

    def to_source_record(self) -> dict[str, Any]:
        """Return a normalized provider source record."""


class NarrativeProviderProtocol(Protocol):
    """
    Interface for optional AI or template-based narrative generation.

    The provider receives facts and returns text.

    It must not modify risk, priority, confidence, findings,
    or recommendations.
    """

    def generate(
        self,
        *,
        indicator: Mapping[str, Any],
        executive_summary: Mapping[str, Any],
        findings: Sequence[Mapping[str, Any]],
        recommendations: Sequence[Mapping[str, Any]],
        limitations: Sequence[str],
    ) -> str:
        """Generate an explanatory narrative from report facts."""


# ============================================================
# SECTION 3
# REPORT DATA MODELS
#
# These dataclasses contain report data.
#
# They do not query providers, calculate fusion risk, invoke
# Bedrock, or render PDF files.
#
# They are the stable internal representation consumed by
# every renderer.
# ============================================================


@dataclass(frozen=True)
class IndicatorRecord:
    """Normalized representation of the investigated indicator."""

    indicator_id: str
    value: str
    indicator_type: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)


@dataclass(frozen=True)
class ExecutiveSummary:
    """
    Concise SOC and leadership view of the investigation.
    """

    overall_risk: str
    overall_confidence: int
    recommended_priority: str

    known_exploited: bool
    ransomware_associated: bool

    sources_consulted: int
    successful_sources: int
    failed_sources: int

    technique_count: int
    cve_count: int

    primary_assessment: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return asdict(self)


@dataclass(frozen=True)
class Finding:
    """
    Evidence-backed observation produced by the report builder.

    A finding describes what was observed.

    It does not describe what action must be taken.
    """

    finding_id: str
    title: str
    severity: str
    description: str

    source: str
    evidence: Mapping[str, Any]

    technique_ids: tuple[str, ...] = ()
    cve_ids: tuple[str, ...] = ()

    confidence: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        result = asdict(self)

        result["evidence"] = dict(self.evidence)
        result["technique_ids"] = list(self.technique_ids)
        result["cve_ids"] = list(self.cve_ids)

        return result


@dataclass(frozen=True)
class Recommendation:
    """
    Deterministic action recommendation.

    A recommendation describes what an analyst or operator should
    consider doing in response to the findings.
    """

    recommendation_id: str
    title: str
    priority: str
    category: str
    action: str
    rationale: str

    related_findings: tuple[str, ...] = ()
    requires_human_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        result = asdict(self)
        result["related_findings"] = list(self.related_findings)

        return result


@dataclass(frozen=True)
class ProviderAppendixEntry:
    """
    Provider-level detail retained for audit and investigation.
    """

    provider: str
    status: str
    retrieved_at: str | None
    expires_at: Any

    data: Mapping[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""

        return {
            "provider": self.provider,
            "status": self.status,
            "retrieved_at": self.retrieved_at,
            "expires_at": make_json_safe(self.expires_at),
            "data": make_json_safe(dict(self.data)),
            "error": self.error,
        }


@dataclass
class ThreatIntelligenceReport:
    """
    Complete structured threat-intelligence investigation report.

    Every renderer consumes this object.
    """

    report_id: str
    report_type: str
    report_version: str
    status: str

    generated_at: str
    analyzed_at: str | None

    indicator: IndicatorRecord

    executive_summary: ExecutiveSummary
    threat_summary: Mapping[str, Any]
    evidence_summary: Mapping[str, Any]

    findings: list[Finding]
    recommendations: list[Recommendation]

    narrative: str | None = None

    limitations: list[str] = field(default_factory=list)
    provider_appendix: list[ProviderAppendixEntry] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(
        self,
        *,
        include_provider_appendix: bool = True,
    ) -> dict[str, Any]:
        """
        Return the complete report as a JSON-safe dictionary.
        """

        report = {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "report_version": self.report_version,
            "status": self.status,
            "generated_at": self.generated_at,
            "analyzed_at": self.analyzed_at,
            "indicator": self.indicator.to_dict(),
            "executive_summary": self.executive_summary.to_dict(),
            "threat_summary": make_json_safe(
                dict(self.threat_summary)
            ),
            "evidence_summary": make_json_safe(
                dict(self.evidence_summary)
            ),
            "findings": [
                finding.to_dict()
                for finding in self.findings
            ],
            "recommendations": [
                recommendation.to_dict()
                for recommendation in self.recommendations
            ],
            "narrative": self.narrative,
            "limitations": list(self.limitations),
            "metadata": make_json_safe(self.metadata),
        }

        if include_provider_appendix:
            report["provider_appendix"] = [
                entry.to_dict()
                for entry in self.provider_appendix
            ]

        return report


# ============================================================
# SECTION 4
# REPORT CONFIGURATION
#
# Configuration is kept separate from builder logic.
#
# Future versions may load these values from:
#
#     - Environment variables
#     - AWS AppConfig
#     - Systems Manager Parameter Store
#     - Tenant-specific configuration
# ============================================================


@dataclass(frozen=True)
class ReportConfiguration:
    """Configuration for report construction."""

    report_type: str = "THREAT_INTELLIGENCE"
    report_version: str = "1.0"

    include_provider_appendix: bool = True
    include_raw_provider_data: bool = True
    include_evidence_summary: bool = True

    generate_narrative: bool = False

    maximum_narrative_characters: int = 6000

    default_requires_human_approval: bool = True


# ============================================================
# SECTION 5
# EXECUTIVE SUMMARY BUILDER
#
# The executive summary contains final assessment facts.
#
# It does not reproduce provider payloads.
# ============================================================


class ExecutiveSummaryBuilder:
    """Build a concise executive summary from ThreatSummary."""

    def build(
        self,
        summary: ThreatSummaryProtocol,
    ) -> ExecutiveSummary:
        """Create the executive summary."""

        primary_assessment = self._build_primary_assessment(
            summary
        )

        return ExecutiveSummary(
            overall_risk=normalize_text(
                summary.overall_risk,
                default="UNKNOWN",
            ),
            overall_confidence=clamp_integer(
                summary.overall_confidence,
                minimum=0,
                maximum=100,
            ),
            recommended_priority=normalize_text(
                summary.recommended_priority,
                default="LOW",
            ),
            known_exploited=bool(
                summary.known_exploited
            ),
            ransomware_associated=bool(
                summary.ransomware_associated
            ),
            sources_consulted=max(
                0,
                int(summary.sources_consulted),
            ),
            successful_sources=max(
                0,
                int(summary.successful_sources),
            ),
            failed_sources=max(
                0,
                int(summary.failed_sources),
            ),
            technique_count=len(
                set(summary.techniques)
            ),
            cve_count=len(
                set(summary.cves)
            ),
            primary_assessment=primary_assessment,
        )

    @staticmethod
    def _build_primary_assessment(
        summary: ThreatSummaryProtocol,
    ) -> str:
        """Build a deterministic one-sentence assessment."""

        risk = normalize_text(
            summary.overall_risk,
            default="UNKNOWN",
        )

        confidence = clamp_integer(
            summary.overall_confidence,
            minimum=0,
            maximum=100,
        )

        priority = normalize_text(
            summary.recommended_priority,
            default="LOW",
        )

        if summary.known_exploited:
            return (
                f"The indicator is assessed as {risk} risk with "
                f"{confidence}% confidence and is associated with "
                "known exploitation."
            )

        if summary.ransomware_associated:
            return (
                f"The indicator is assessed as {risk} risk with "
                f"{confidence}% confidence and has ransomware-related "
                "intelligence."
            )

        return (
            f"The indicator is assessed as {risk} risk with "
            f"{confidence}% confidence and a recommended response "
            f"priority of {priority}."
        )


# ============================================================
# SECTION 6
# FINDINGS BUILDER
#
# Findings are deterministic and evidence-backed.
#
# Findings answer:
#
#     "What did the investigation observe?"
#
# Findings do not answer:
#
#     "What should we do?"
# ============================================================


class FindingsBuilder:
    """Build structured findings from evidence and summary data."""

    def build(
        self,
        *,
        summary: ThreatSummaryProtocol,
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Build all applicable findings."""

        findings: list[Finding] = []

        findings.extend(
            self._build_known_exploitation_findings(
                summary=summary,
                evidence=evidence,
            )
        )

        findings.extend(
            self._build_ransomware_findings(
                summary=summary,
                evidence=evidence,
            )
        )

        findings.extend(
            self._build_abuse_findings(evidence)
        )

        findings.extend(
            self._build_report_volume_findings(evidence)
        )

        findings.extend(
            self._build_tor_findings(evidence)
        )

        findings.extend(
            self._build_whitelist_findings(evidence)
        )

        findings.extend(
            self._build_technique_findings(summary)
        )

        findings.extend(
            self._build_cve_findings(summary)
        )

        findings.extend(
            self._build_provider_failure_findings(evidence)
        )

        findings.extend(
            self._build_no_intelligence_findings(evidence)
        )

        return deduplicate_findings(findings)

    def _build_known_exploitation_findings(
        self,
        *,
        summary: ThreatSummaryProtocol,
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Create a finding for known exploitation."""

        if not summary.known_exploited:
            return []

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "known-exploitation",
                ),
                title="Known Exploitation Identified",
                severity=FindingSeverity.CRITICAL.value,
                description=(
                    "Threat-intelligence evidence indicates that the "
                    "associated vulnerability is known to be exploited "
                    "in real-world attacks."
                ),
                source=find_evidence_source(
                    evidence,
                    preferred_names=(
                        "cisa_kev",
                        "cisa",
                    ),
                    default="Threat Intelligence Fusion",
                ),
                evidence={
                    "known_exploited": True,
                    "cves": sorted(summary.cves),
                },
                cve_ids=tuple(
                    sorted(set(summary.cves))
                ),
                confidence=summary.overall_confidence,
            )
        ]

    def _build_ransomware_findings(
        self,
        *,
        summary: ThreatSummaryProtocol,
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Create a finding for ransomware association."""

        if not summary.ransomware_associated:
            return []

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "ransomware-association",
                ),
                title="Ransomware Association Identified",
                severity=FindingSeverity.CRITICAL.value,
                description=(
                    "Threat-intelligence evidence associates the "
                    "indicator or vulnerability with ransomware activity."
                ),
                source=find_evidence_source(
                    evidence,
                    preferred_names=(
                        "cisa_kev",
                        "cisa",
                    ),
                    default="Threat Intelligence Fusion",
                ),
                evidence={
                    "ransomware_associated": True,
                    "cves": sorted(summary.cves),
                },
                cve_ids=tuple(
                    sorted(set(summary.cves))
                ),
                confidence=summary.overall_confidence,
            )
        ]

    @staticmethod
    def _build_abuse_findings(
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Create findings from IP abuse scores."""

        if not evidence.abuse_scores:
            return []

        maximum_score = max(evidence.abuse_scores)

        if maximum_score >= 75:
            severity = FindingSeverity.HIGH
            title = "High Abuse Confidence"
        elif maximum_score >= 25:
            severity = FindingSeverity.MEDIUM
            title = "Elevated Abuse Confidence"
        else:
            severity = FindingSeverity.LOW
            title = "Low Abuse Confidence"

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    f"abuse-score-{maximum_score}",
                ),
                title=title,
                severity=severity.value,
                description=(
                    "A threat-intelligence provider reported an abuse "
                    f"confidence score of {maximum_score} out of 100."
                ),
                source=find_evidence_source(
                    evidence,
                    preferred_names=(
                        "abuseipdb",
                        "abuse_ip_db",
                    ),
                    default="Threat Intelligence Provider",
                ),
                evidence={
                    "maximum_abuse_score": maximum_score,
                    "all_abuse_scores": list(
                        evidence.abuse_scores
                    ),
                },
                confidence=maximum_score,
            )
        ]

    @staticmethod
    def _build_report_volume_findings(
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Create a finding for independent abuse reports."""

        if evidence.total_reports <= 0:
            return []

        if evidence.total_reports >= 25:
            severity = FindingSeverity.HIGH
        elif evidence.total_reports >= 5:
            severity = FindingSeverity.MEDIUM
        else:
            severity = FindingSeverity.LOW

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "independent-abuse-reports",
                ),
                title="Independent Abuse Reports Observed",
                severity=severity.value,
                description=(
                    "Threat-intelligence sources reported multiple "
                    "observations associated with this indicator."
                ),
                source=find_evidence_source(
                    evidence,
                    preferred_names=("abuseipdb",),
                    default="Threat Intelligence Provider",
                ),
                evidence={
                    "total_reports": evidence.total_reports,
                    "distinct_reporting_users": (
                        evidence.distinct_reporting_users
                    ),
                },
            )
        ]

    @staticmethod
    def _build_tor_findings(
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Create a contextual TOR finding."""

        if not evidence.tor_observed:
            return []

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "tor-infrastructure",
                ),
                title="TOR Infrastructure Association",
                severity=FindingSeverity.MEDIUM.value,
                description=(
                    "A provider identified the indicator as being "
                    "associated with TOR infrastructure. TOR usage is "
                    "contextual evidence and does not independently prove "
                    "malicious activity."
                ),
                source="Threat Intelligence Provider",
                evidence={
                    "tor_observed": True,
                },
            )
        ]

    @staticmethod
    def _build_whitelist_findings(
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Create a whitelist-context finding."""

        if not evidence.whitelisted:
            return []

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "whitelisted-indicator",
                ),
                title="Whitelist Status Reported",
                severity=FindingSeverity.INFORMATIONAL.value,
                description=(
                    "A provider reported the indicator as whitelisted. "
                    "Whitelist status should be validated against the "
                    "organization's own approved asset inventory."
                ),
                source="Threat Intelligence Provider",
                evidence={
                    "whitelisted": True,
                },
            )
        ]

    @staticmethod
    def _build_technique_findings(
        summary: ThreatSummaryProtocol,
    ) -> list[Finding]:
        """Create one finding for mapped ATT&CK techniques."""

        techniques = sorted(
            set(summary.techniques)
        )

        if not techniques:
            return []

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "mitre-techniques",
                ),
                title="MITRE ATT&CK Techniques Mapped",
                severity=FindingSeverity.MEDIUM.value,
                description=(
                    "The investigation identified one or more MITRE "
                    "ATT&CK techniques associated with the observed "
                    "behavior or threat context."
                ),
                source="MITRE ATT&CK",
                evidence={
                    "technique_count": len(techniques),
                    "technique_ids": techniques,
                },
                technique_ids=tuple(techniques),
                confidence=summary.overall_confidence,
            )
        ]

    @staticmethod
    def _build_cve_findings(
        summary: ThreatSummaryProtocol,
    ) -> list[Finding]:
        """Create one finding for associated CVEs."""

        cves = sorted(
            set(summary.cves)
        )

        if not cves:
            return []

        severity = (
            FindingSeverity.HIGH
            if summary.known_exploited
            else FindingSeverity.MEDIUM
        )

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "associated-cves",
                ),
                title="Associated Vulnerabilities Identified",
                severity=severity.value,
                description=(
                    "The investigation identified one or more CVEs "
                    "associated with the indicator or threat context."
                ),
                source="Threat Intelligence Fusion",
                evidence={
                    "cve_count": len(cves),
                    "cves": cves,
                },
                cve_ids=tuple(cves),
                confidence=summary.overall_confidence,
            )
        ]

    @staticmethod
    def _build_provider_failure_findings(
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Create an informational finding for provider failures."""

        failed = sorted(
            evidence.failed_providers
        )

        if not failed:
            return []

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "provider-failures",
                ),
                title="Threat-Intelligence Coverage Incomplete",
                severity=FindingSeverity.INFORMATIONAL.value,
                description=(
                    "One or more providers failed to return usable "
                    "intelligence. The assessment may therefore have "
                    "incomplete source coverage."
                ),
                source="Report Construction Engine",
                evidence={
                    "failed_providers": failed,
                    "failed_provider_count": len(failed),
                },
            )
        ]

    @staticmethod
    def _build_no_intelligence_findings(
        evidence: ThreatEvidenceProtocol,
    ) -> list[Finding]:
        """Create a finding when no provider succeeded."""

        if evidence.successful_providers:
            return []

        return [
            Finding(
                finding_id=create_stable_id(
                    "finding",
                    "no-successful-intelligence",
                ),
                title="Insufficient Threat Intelligence",
                severity=FindingSeverity.INFORMATIONAL.value,
                description=(
                    "No provider returned a successful intelligence "
                    "result. The absence of intelligence does not prove "
                    "that the indicator is benign."
                ),
                source="Report Construction Engine",
                evidence={
                    "providers_consulted": sorted(
                        evidence.providers_consulted
                    ),
                    "failed_providers": sorted(
                        evidence.failed_providers
                    ),
                    "not_found_providers": sorted(
                        evidence.not_found_providers
                    ),
                },
            )
        ]


# ============================================================
# SECTION 7
# RECOMMENDATION BUILDER
#
# Recommendations answer:
#
#     "What should the organization consider doing?"
#
# Recommendations remain deterministic.
#
# They are separated from findings because two organizations
# may agree on the evidence but apply different response policy.
# ============================================================


class RecommendationBuilder:
    """Build deterministic recommendations from report facts."""

    def __init__(
        self,
        *,
        require_human_approval: bool = True,
    ) -> None:
        self.require_human_approval = require_human_approval

    def build(
        self,
        *,
        summary: ThreatSummaryProtocol,
        evidence: ThreatEvidenceProtocol,
        findings: Sequence[Finding],
    ) -> list[Recommendation]:
        """Build applicable recommendations."""

        recommendations: list[Recommendation] = []

        finding_ids = {
            finding.title: finding.finding_id
            for finding in findings
        }

        if summary.known_exploited:
            recommendations.extend(
                self._known_exploitation_recommendations(
                    summary=summary,
                    finding_ids=finding_ids,
                )
            )

        if summary.ransomware_associated:
            recommendations.extend(
                self._ransomware_recommendations(
                    finding_ids=finding_ids
                )
            )

        if maximum_or_zero(
            evidence.abuse_scores
        ) >= 75:
            recommendations.extend(
                self._high_abuse_recommendations(
                    finding_ids=finding_ids
                )
            )

        if summary.techniques:
            recommendations.append(
                Recommendation(
                    recommendation_id=create_stable_id(
                        "recommendation",
                        "validate-mitre-techniques",
                    ),
                    title="Validate Mapped ATT&CK Techniques",
                    priority=RecommendationPriority.MEDIUM.value,
                    category=RecommendationCategory.VALIDATE.value,
                    action=(
                        "Review the mapped MITRE ATT&CK techniques "
                        "against CloudTrail, VPC Flow Logs, operating "
                        "system logs, identity telemetry, and workload "
                        "activity."
                    ),
                    rationale=(
                        "Technique mappings provide investigative "
                        "direction but should be confirmed using "
                        "environment-specific telemetry."
                    ),
                    related_findings=tuple(
                        filter(
                            None,
                            [
                                finding_ids.get(
                                    "MITRE ATT&CK Techniques Mapped"
                                )
                            ],
                        )
                    ),
                    requires_human_approval=(
                        self.require_human_approval
                    ),
                )
            )

        if evidence.failed_providers:
            recommendations.append(
                Recommendation(
                    recommendation_id=create_stable_id(
                        "recommendation",
                        "retry-failed-providers",
                    ),
                    title="Retry Failed Intelligence Sources",
                    priority=RecommendationPriority.LOW.value,
                    category=RecommendationCategory.INVESTIGATE.value,
                    action=(
                        "Retry failed providers and verify API keys, "
                        "rate limits, network connectivity, and provider "
                        "availability."
                    ),
                    rationale=(
                        "Restoring provider coverage may materially "
                        "change the confidence or risk assessment."
                    ),
                    related_findings=tuple(
                        filter(
                            None,
                            [
                                finding_ids.get(
                                    "Threat-Intelligence "
                                    "Coverage Incomplete"
                                )
                            ],
                        )
                    ),
                    requires_human_approval=False,
                )
            )

        if not evidence.successful_providers:
            recommendations.append(
                Recommendation(
                    recommendation_id=create_stable_id(
                        "recommendation",
                        "manual-investigation",
                    ),
                    title="Perform Manual Investigation",
                    priority=RecommendationPriority.MEDIUM.value,
                    category=RecommendationCategory.INVESTIGATE.value,
                    action=(
                        "Investigate the indicator manually using "
                        "internal telemetry and approved intelligence "
                        "sources."
                    ),
                    rationale=(
                        "Automated enrichment did not produce sufficient "
                        "intelligence to support a reliable conclusion."
                    ),
                    related_findings=tuple(
                        filter(
                            None,
                            [
                                finding_ids.get(
                                    "Insufficient Threat Intelligence"
                                )
                            ],
                        )
                    ),
                    requires_human_approval=False,
                )
            )

        if normalize_text(
            summary.overall_risk,
            default="UNKNOWN",
        ) in {"LOW", "UNKNOWN"}:
            recommendations.append(
                Recommendation(
                    recommendation_id=create_stable_id(
                        "recommendation",
                        "continue-monitoring",
                    ),
                    title="Continue Monitoring",
                    priority=RecommendationPriority.LOW.value,
                    category=RecommendationCategory.MONITOR.value,
                    action=(
                        "Continue monitoring for new activity, new "
                        "provider intelligence, and repeated observations "
                        "of the indicator."
                    ),
                    rationale=(
                        "Low or unknown current risk does not guarantee "
                        "that the indicator will remain benign."
                    ),
                    requires_human_approval=False,
                )
            )

        recommendations.append(
            Recommendation(
                recommendation_id=create_stable_id(
                    "recommendation",
                    "preserve-evidence",
                ),
                title="Preserve Investigation Evidence",
                priority=RecommendationPriority.LOW.value,
                category=RecommendationCategory.DOCUMENT.value,
                action=(
                    "Retain the provider observations, normalized "
                    "evidence, fusion summary, and report identifier "
                    "for audit and future correlation."
                ),
                rationale=(
                    "Preserved evidence supports repeatable analysis, "
                    "auditability, and comparison with future events."
                ),
                requires_human_approval=False,
            )
        )

        return deduplicate_recommendations(
            recommendations
        )

    def _known_exploitation_recommendations(
        self,
        *,
        summary: ThreatSummaryProtocol,
        finding_ids: Mapping[str, str],
    ) -> list[Recommendation]:
        """Build recommendations for known exploitation."""

        cve_text = (
            ", ".join(sorted(summary.cves))
            if summary.cves
            else "the associated vulnerability"
        )

        related = tuple(
            filter(
                None,
                [
                    finding_ids.get(
                        "Known Exploitation Identified"
                    ),
                    finding_ids.get(
                        "Associated Vulnerabilities Identified"
                    ),
                ],
            )
        )

        return [
            Recommendation(
                recommendation_id=create_stable_id(
                    "recommendation",
                    "known-exploited-patch",
                ),
                title="Prioritize Vulnerability Remediation",
                priority=RecommendationPriority.CRITICAL.value,
                category=RecommendationCategory.REMEDIATE.value,
                action=(
                    f"Identify assets affected by {cve_text} and apply "
                    "vendor remediation, compensating controls, or "
                    "workload isolation according to emergency change "
                    "procedures."
                ),
                rationale=(
                    "Known exploitation materially increases the "
                    "likelihood of active adversary use."
                ),
                related_findings=related,
                requires_human_approval=(
                    self.require_human_approval
                ),
            ),
            Recommendation(
                recommendation_id=create_stable_id(
                    "recommendation",
                    "known-exploited-hunt",
                ),
                title="Conduct Targeted Threat Hunt",
                priority=RecommendationPriority.CRITICAL.value,
                category=RecommendationCategory.INVESTIGATE.value,
                action=(
                    "Search historical and current telemetry for signs "
                    "of exploitation, persistence, credential access, "
                    "lateral movement, and command-and-control activity."
                ),
                rationale=(
                    "Patching prevents future exploitation but does not "
                    "determine whether compromise already occurred."
                ),
                related_findings=related,
                requires_human_approval=False,
            ),
        ]

    def _ransomware_recommendations(
        self,
        *,
        finding_ids: Mapping[str, str],
    ) -> list[Recommendation]:
        """Build recommendations for ransomware association."""

        related = tuple(
            filter(
                None,
                [
                    finding_ids.get(
                        "Ransomware Association Identified"
                    )
                ],
            )
        )

        return [
            Recommendation(
                recommendation_id=create_stable_id(
                    "recommendation",
                    "ransomware-escalation",
                ),
                title="Escalate to Incident Response",
                priority=RecommendationPriority.CRITICAL.value,
                category=RecommendationCategory.INVESTIGATE.value,
                action=(
                    "Escalate the investigation to the incident "
                    "response team and validate endpoint, identity, "
                    "backup, and lateral-movement telemetry."
                ),
                rationale=(
                    "Ransomware association increases potential impact "
                    "and requires rapid validation."
                ),
                related_findings=related,
                requires_human_approval=False,
            )
        ]

    def _high_abuse_recommendations(
        self,
        *,
        finding_ids: Mapping[str, str],
    ) -> list[Recommendation]:
        """Build recommendations for a high IP abuse score."""

        related = tuple(
            filter(
                None,
                [
                    finding_ids.get(
                        "High Abuse Confidence"
                    )
                ],
            )
        )

        return [
            Recommendation(
                recommendation_id=create_stable_id(
                    "recommendation",
                    "validate-indicator-activity",
                ),
                title="Validate Indicator Activity",
                priority=RecommendationPriority.HIGH.value,
                category=RecommendationCategory.INVESTIGATE.value,
                action=(
                    "Search VPC Flow Logs, load balancer logs, WAF logs, "
                    "authentication logs, and host telemetry for activity "
                    "associated with the indicator."
                ),
                rationale=(
                    "A high external abuse score should be validated "
                    "against internal evidence before containment."
                ),
                related_findings=related,
                requires_human_approval=False,
            ),
            Recommendation(
                recommendation_id=create_stable_id(
                    "recommendation",
                    "consider-blocking-indicator",
                ),
                title="Consider Indicator Containment",
                priority=RecommendationPriority.HIGH.value,
                category=RecommendationCategory.CONTAIN.value,
                action=(
                    "After validating business impact and ownership, "
                    "consider blocking the indicator using appropriate "
                    "network, WAF, security group, firewall, or endpoint "
                    "controls."
                ),
                rationale=(
                    "Containment may reduce continued malicious activity, "
                    "but blocking should be validated to avoid disrupting "
                    "legitimate services."
                ),
                related_findings=related,
                requires_human_approval=(
                    self.require_human_approval
                ),
            ),
        ]


# ============================================================
# SECTION 8
# PROVIDER APPENDIX BUILDER
#
# The provider appendix preserves provenance.
#
# Analysts may inspect the provider-level observations without
# forcing future agents to consume provider-specific schemas.
# ============================================================


class ProviderAppendixBuilder:
    """Build provider appendix entries."""

    def __init__(
        self,
        *,
        include_raw_provider_data: bool = True,
    ) -> None:
        self.include_raw_provider_data = (
            include_raw_provider_data
        )

    def build(
        self,
        provider_results: Iterable[ProviderResultProtocol],
    ) -> list[ProviderAppendixEntry]:
        """Build provider appendix records."""

        entries: list[ProviderAppendixEntry] = []

        for result in provider_results:
            data = (
                safe_mapping(result.data)
                if self.include_raw_provider_data
                else {}
            )

            entries.append(
                ProviderAppendixEntry(
                    provider=normalize_provider_name(
                        result.provider
                    ),
                    status=normalize_text(
                        result.status,
                        default="ERROR",
                    ),
                    retrieved_at=getattr(
                        result,
                        "retrieved_at",
                        None,
                    ),
                    expires_at=getattr(
                        result,
                        "expires_at",
                        None,
                    ),
                    data=data,
                    error=getattr(
                        result,
                        "error",
                        None,
                    ),
                )
            )

        return sorted(
            entries,
            key=lambda entry: entry.provider,
        )


# ============================================================
# SECTION 9
# NARRATIVE BUILDER
#
# The narrative builder may use Bedrock or another model.
#
# AI is allowed to explain the report.
#
# AI is not allowed to:
#
#     - Change risk
#     - Change priority
#     - Recalculate confidence
#     - Invent findings
#     - Invent recommendations
# ============================================================


class NarrativeBuilder:
    """Build an optional narrative from structured report facts."""

    def __init__(
        self,
        provider: NarrativeProviderProtocol | None = None,
        *,
        maximum_characters: int = 6000,
    ) -> None:
        self.provider = provider
        self.maximum_characters = maximum_characters

    def build(
        self,
        *,
        indicator: IndicatorRecord,
        executive_summary: ExecutiveSummary,
        findings: Sequence[Finding],
        recommendations: Sequence[Recommendation],
        limitations: Sequence[str],
    ) -> str | None:
        """
        Generate narrative text when a provider is configured.
        """

        if self.provider is None:
            return None

        try:
            narrative = self.provider.generate(
                indicator=indicator.to_dict(),
                executive_summary=(
                    executive_summary.to_dict()
                ),
                findings=[
                    finding.to_dict()
                    for finding in findings
                ],
                recommendations=[
                    recommendation.to_dict()
                    for recommendation in recommendations
                ],
                limitations=list(limitations),
            )
        except Exception:
            LOGGER.exception(
                "Narrative generation failed."
            )

            return None

        if not isinstance(narrative, str):
            LOGGER.warning(
                "Narrative provider returned a non-string value."
            )

            return None

        narrative = narrative.strip()

        if not narrative:
            return None

        return narrative[
            : self.maximum_characters
        ]


# ============================================================
# SECTION 10
# REPORT BUILDER
#
# ThreatIntelligenceReportBuilder orchestrates construction.
#
# It does not implement provider lookup, fusion, or rendering.
# ============================================================


class ThreatIntelligenceReportBuilder:
    """Build complete structured threat-intelligence reports."""

    def __init__(
        self,
        *,
        configuration: ReportConfiguration | None = None,
        executive_summary_builder: (
            ExecutiveSummaryBuilder | None
        ) = None,
        findings_builder: FindingsBuilder | None = None,
        recommendation_builder: (
            RecommendationBuilder | None
        ) = None,
        appendix_builder: (
            ProviderAppendixBuilder | None
        ) = None,
        narrative_builder: NarrativeBuilder | None = None,
    ) -> None:
        self.configuration = (
            configuration or ReportConfiguration()
        )

        self.executive_summary_builder = (
            executive_summary_builder
            or ExecutiveSummaryBuilder()
        )

        self.findings_builder = (
            findings_builder
            or FindingsBuilder()
        )

        self.recommendation_builder = (
            recommendation_builder
            or RecommendationBuilder(
                require_human_approval=(
                    self.configuration
                    .default_requires_human_approval
                )
            )
        )

        self.appendix_builder = (
            appendix_builder
            or ProviderAppendixBuilder(
                include_raw_provider_data=(
                    self.configuration
                    .include_raw_provider_data
                )
            )
        )

        self.narrative_builder = (
            narrative_builder
            or NarrativeBuilder(
                maximum_characters=(
                    self.configuration
                    .maximum_narrative_characters
                )
            )
        )

    def build(
        self,
        *,
        indicator: IndicatorProtocol,
        summary: ThreatSummaryProtocol,
        evidence: ThreatEvidenceProtocol,
        provider_results: Iterable[ProviderResultProtocol],
        metadata: Mapping[str, Any] | None = None,
    ) -> ThreatIntelligenceReport:
        """
        Build one complete threat-intelligence report.
        """

        provider_results_list = list(
            provider_results
        )

        LOGGER.info(
            "Building threat-intelligence report for indicator %s.",
            getattr(
                indicator,
                "indicator_id",
                indicator.value,
            ),
        )

        indicator_record = IndicatorRecord(
            indicator_id=get_indicator_id(
                indicator
            ),
            value=normalize_text(
                indicator.value,
                default="UNKNOWN",
            ),
            indicator_type=normalize_text(
                indicator.indicator_type,
                default="UNKNOWN",
            ),
        )

        executive_summary = (
            self.executive_summary_builder.build(
                summary
            )
        )

        findings = self.findings_builder.build(
            summary=summary,
            evidence=evidence,
        )

        recommendations = (
            self.recommendation_builder.build(
                summary=summary,
                evidence=evidence,
                findings=findings,
            )
        )

        limitations = self._build_limitations(
            summary=summary,
            evidence=evidence,
        )

        provider_appendix = (
            self.appendix_builder.build(
                provider_results_list
            )
            if self.configuration.include_provider_appendix
            else []
        )

        narrative = None

        if self.configuration.generate_narrative:
            narrative = self.narrative_builder.build(
                indicator=indicator_record,
                executive_summary=executive_summary,
                findings=findings,
                recommendations=recommendations,
                limitations=limitations,
            )

        report_status = self._determine_status(
            evidence=evidence,
            provider_results=provider_results_list,
        )

        report = ThreatIntelligenceReport(
            report_id=create_report_id(),
            report_type=self.configuration.report_type,
            report_version=(
                self.configuration.report_version
            ),
            status=report_status.value,
            generated_at=utc_now_iso(),
            analyzed_at=getattr(
                summary,
                "analyzed_at",
                None,
            ),
            indicator=indicator_record,
            executive_summary=executive_summary,
            threat_summary=object_to_mapping(
                summary
            ),
            evidence_summary=(
                object_to_mapping(evidence)
                if self.configuration
                .include_evidence_summary
                else {}
            ),
            findings=findings,
            recommendations=recommendations,
            narrative=narrative,
            limitations=limitations,
            provider_appendix=provider_appendix,
            metadata={
                "policy_version": getattr(
                    summary,
                    "policy_version",
                    None,
                ),
                "provider_result_count": len(
                    provider_results_list
                ),
                **make_json_safe(
                    dict(metadata or {})
                ),
            },
        )

        LOGGER.info(
            (
                "Threat-intelligence report completed: "
                "report_id=%s status=%s findings=%d "
                "recommendations=%d"
            ),
            report.report_id,
            report.status,
            len(report.findings),
            len(report.recommendations),
        )

        return report

    @staticmethod
    def _build_limitations(
        *,
        summary: ThreatSummaryProtocol,
        evidence: ThreatEvidenceProtocol,
    ) -> list[str]:
        """Merge summary and evidence limitations."""

        limitations: list[str] = []

        limitations.extend(
            list(
                getattr(
                    summary,
                    "limitations",
                    [],
                )
            )
        )

        limitations.extend(
            list(
                getattr(
                    evidence,
                    "warnings",
                    [],
                )
            )
        )

        if not evidence.successful_providers:
            limitations.append(
                "No provider returned successful intelligence."
            )

        if evidence.not_found_providers:
            limitations.append(
                "A NOT_FOUND provider result does not prove that "
                "the indicator is benign."
            )

        if evidence.failed_providers:
            limitations.append(
                "Provider failures may have reduced intelligence "
                "coverage."
            )

        limitations.append(
            "External threat intelligence should be validated "
            "against internal telemetry before automated containment "
            "or remediation."
        )

        return deduplicate_strings(limitations)

    @staticmethod
    def _determine_status(
        *,
        evidence: ThreatEvidenceProtocol,
        provider_results: Sequence[
            ProviderResultProtocol
        ],
    ) -> ReportStatus:
        """Determine report completion status."""

        if not provider_results:
            return ReportStatus.FAILED

        if not evidence.successful_providers:
            return ReportStatus.PARTIAL

        if evidence.failed_providers:
            return ReportStatus.PARTIAL

        return ReportStatus.COMPLETE


# ============================================================
# SECTION 11
# JSON RENDERER
#
# The JSON renderer is useful for:
#
#     - S3 storage
#     - API responses
#     - DynamoDB references
#     - EventBridge events
#     - Future agents
# ============================================================


class JsonReportRenderer:
    """Render ThreatIntelligenceReport as JSON."""

    def __init__(
        self,
        *,
        indent: int | None = 2,
        sort_keys: bool = True,
        include_provider_appendix: bool = True,
    ) -> None:
        self.indent = indent
        self.sort_keys = sort_keys
        self.include_provider_appendix = (
            include_provider_appendix
        )

    def render(
        self,
        report: ThreatIntelligenceReport,
    ) -> str:
        """Return the report as a JSON string."""

        return json.dumps(
            report.to_dict(
                include_provider_appendix=(
                    self.include_provider_appendix
                )
            ),
            indent=self.indent,
            sort_keys=self.sort_keys,
            ensure_ascii=False,
            default=json_default,
        )


# ============================================================
# SECTION 12
# MARKDOWN RENDERER
#
# Markdown is useful for:
#
#     - Git repositories
#     - Tickets
#     - Wikis
#     - Analyst notes
#     - Classroom review
# ============================================================


class MarkdownReportRenderer:
    """Render a report as readable Markdown."""

    def __init__(
        self,
        *,
        include_provider_appendix: bool = False,
    ) -> None:
        self.include_provider_appendix = (
            include_provider_appendix
        )

    def render(
        self,
        report: ThreatIntelligenceReport,
    ) -> str:
        """Return the report as Markdown."""

        lines: list[str] = []

        lines.append(
            "# Threat Intelligence Investigation"
        )
        lines.append("")

        lines.append(
            f"**Report ID:** `{report.report_id}`"
        )
        lines.append(
            f"**Status:** {report.status}"
        )
        lines.append(
            f"**Generated:** {report.generated_at}"
        )
        lines.append("")

        lines.append("## Indicator")
        lines.append("")
        lines.append(
            f"- **Value:** `{report.indicator.value}`"
        )
        lines.append(
            f"- **Type:** {report.indicator.indicator_type}"
        )
        lines.append(
            f"- **Identifier:** "
            f"`{report.indicator.indicator_id}`"
        )
        lines.append("")

        summary = report.executive_summary

        lines.append("## Executive Summary")
        lines.append("")
        lines.append(
            f"- **Overall risk:** {summary.overall_risk}"
        )
        lines.append(
            f"- **Confidence:** "
            f"{summary.overall_confidence}%"
        )
        lines.append(
            f"- **Recommended priority:** "
            f"{summary.recommended_priority}"
        )
        lines.append(
            f"- **Known exploited:** "
            f"{yes_no(summary.known_exploited)}"
        )
        lines.append(
            f"- **Ransomware associated:** "
            f"{yes_no(summary.ransomware_associated)}"
        )
        lines.append("")
        lines.append(summary.primary_assessment)
        lines.append("")

        if report.narrative:
            lines.append("## Investigation Narrative")
            lines.append("")
            lines.append(report.narrative)
            lines.append("")

        lines.append("## Findings")
        lines.append("")

        if not report.findings:
            lines.append(
                "No structured findings were generated."
            )
            lines.append("")
        else:
            for index, finding in enumerate(
                report.findings,
                start=1,
            ):
                lines.append(
                    f"### {index}. {finding.title}"
                )
                lines.append("")
                lines.append(
                    f"- **Severity:** {finding.severity}"
                )
                lines.append(
                    f"- **Source:** {finding.source}"
                )

                if finding.confidence is not None:
                    lines.append(
                        f"- **Confidence:** "
                        f"{finding.confidence}%"
                    )

                lines.append("")
                lines.append(finding.description)
                lines.append("")

                if finding.technique_ids:
                    lines.append(
                        "- **ATT&CK techniques:** "
                        + ", ".join(
                            f"`{value}`"
                            for value in finding.technique_ids
                        )
                    )

                if finding.cve_ids:
                    lines.append(
                        "- **CVEs:** "
                        + ", ".join(
                            f"`{value}`"
                            for value in finding.cve_ids
                        )
                    )

                lines.append("")

        lines.append("## Recommendations")
        lines.append("")

        if not report.recommendations:
            lines.append(
                "No recommendations were generated."
            )
            lines.append("")
        else:
            for index, recommendation in enumerate(
                report.recommendations,
                start=1,
            ):
                lines.append(
                    f"### {index}. {recommendation.title}"
                )
                lines.append("")
                lines.append(
                    f"- **Priority:** "
                    f"{recommendation.priority}"
                )
                lines.append(
                    f"- **Category:** "
                    f"{recommendation.category}"
                )
                lines.append(
                    f"- **Human approval required:** "
                    f"{yes_no(recommendation.requires_human_approval)}"
                )
                lines.append("")
                lines.append(
                    f"**Action:** {recommendation.action}"
                )
                lines.append("")
                lines.append(
                    f"**Rationale:** {recommendation.rationale}"
                )
                lines.append("")

        lines.append("## Limitations")
        lines.append("")

        for limitation in report.limitations:
            lines.append(f"- {limitation}")

        lines.append("")

        if self.include_provider_appendix:
            lines.extend(
                self._render_provider_appendix(
                    report.provider_appendix
                )
            )

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def _render_provider_appendix(
        entries: Sequence[ProviderAppendixEntry],
    ) -> list[str]:
        """Render provider appendix entries."""

        lines = [
            "## Provider Appendix",
            "",
        ]

        if not entries:
            lines.append(
                "No provider appendix entries were included."
            )
            lines.append("")

            return lines

        for entry in entries:
            lines.append(
                f"### {entry.provider}"
            )
            lines.append("")
            lines.append(
                f"- **Status:** {entry.status}"
            )
            lines.append(
                f"- **Retrieved:** "
                f"{entry.retrieved_at or 'Unknown'}"
            )

            if entry.error:
                lines.append(
                    f"- **Error:** {entry.error}"
                )

            lines.append("")
            lines.append("```json")
            lines.append(
                json.dumps(
                    make_json_safe(dict(entry.data)),
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                )
            )
            lines.append("```")
            lines.append("")

        return lines


# ============================================================
# SECTION 13
# CONSOLE RENDERER
#
# Console output is useful for:
#
#     - CloudWatch logs
#     - Local testing
#     - Demonstrations
#     - Lambda debugging
# ============================================================


class ConsoleReportRenderer:
    """Render a compact console summary."""

    def render(
        self,
        report: ThreatIntelligenceReport,
    ) -> str:
        """Return a compact text representation."""

        summary = report.executive_summary

        lines = [
            "=" * 64,
            "THREAT INTELLIGENCE REPORT",
            "=" * 64,
            f"Report ID:   {report.report_id}",
            f"Status:      {report.status}",
            f"Indicator:   {report.indicator.value}",
            f"Type:        {report.indicator.indicator_type}",
            f"Risk:        {summary.overall_risk}",
            f"Confidence:  {summary.overall_confidence}%",
            f"Priority:    {summary.recommended_priority}",
            f"Findings:    {len(report.findings)}",
            f"Actions:     {len(report.recommendations)}",
            "-" * 64,
            summary.primary_assessment,
            "=" * 64,
        ]

        return "\n".join(lines)


# ============================================================
# SECTION 14
# REPORT SERVICE
#
# ThreatIntelligenceReportService provides one convenient
# interface for report construction and rendering.
#
# The Lambda handler may use this class directly.
# ============================================================


class ThreatIntelligenceReportService:
    """Coordinate report building and rendering."""

    def __init__(
        self,
        *,
        builder: ThreatIntelligenceReportBuilder | None = None,
    ) -> None:
        self.builder = (
            builder
            or ThreatIntelligenceReportBuilder()
        )

    def create_report(
        self,
        *,
        indicator: IndicatorProtocol,
        summary: ThreatSummaryProtocol,
        evidence: ThreatEvidenceProtocol,
        provider_results: Iterable[ProviderResultProtocol],
        metadata: Mapping[str, Any] | None = None,
    ) -> ThreatIntelligenceReport:
        """Build and return a structured report."""

        return self.builder.build(
            indicator=indicator,
            summary=summary,
            evidence=evidence,
            provider_results=provider_results,
            metadata=metadata,
        )

    @staticmethod
    def render_json(
        report: ThreatIntelligenceReport,
        *,
        include_provider_appendix: bool = True,
    ) -> str:
        """Render a report as JSON."""

        renderer = JsonReportRenderer(
            include_provider_appendix=(
                include_provider_appendix
            )
        )

        return renderer.render(report)

    @staticmethod
    def render_markdown(
        report: ThreatIntelligenceReport,
        *,
        include_provider_appendix: bool = False,
    ) -> str:
        """Render a report as Markdown."""

        renderer = MarkdownReportRenderer(
            include_provider_appendix=(
                include_provider_appendix
            )
        )

        return renderer.render(report)

    @staticmethod
    def render_console(
        report: ThreatIntelligenceReport,
    ) -> str:
        """Render a compact console report."""

        return ConsoleReportRenderer().render(
            report
        )


# ============================================================
# SECTION 15
# HELPER FUNCTIONS
#
# These functions normalize input and keep builder code focused
# upon business logic.
# ============================================================


def create_report_id() -> str:
    """Create a globally unique report identifier."""

    return f"tir-{uuid.uuid4()}"


def create_stable_id(
    prefix: str,
    name: str,
) -> str:
    """
    Create a readable deterministic-style identifier.

    This is not intended to be globally unique.

    It identifies a finding or recommendation category inside
    one report.
    """

    normalized = "".join(
        character
        if character.isalnum()
        else "-"
        for character in name.lower()
    )

    normalized = "-".join(
        part
        for part in normalized.split("-")
        if part
    )

    return f"{prefix}-{normalized}"


def utc_now_iso() -> str:
    """Return the current UTC time in ISO-8601 format."""

    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def get_indicator_id(
    indicator: IndicatorProtocol,
) -> str:
    """Return or construct a normalized indicator identifier."""

    existing = getattr(
        indicator,
        "indicator_id",
        None,
    )

    if isinstance(existing, str) and existing.strip():
        return existing.strip()

    indicator_type = normalize_text(
        indicator.indicator_type,
        default="UNKNOWN",
    )

    value = normalize_text(
        indicator.value,
        default="UNKNOWN",
    )

    return f"{indicator_type}:{value}"


def normalize_text(
    value: Any,
    *,
    default: str,
) -> str:
    """Normalize an arbitrary value into non-empty text."""

    if not isinstance(value, str):
        return default

    normalized = value.strip()

    return normalized or default


def normalize_provider_name(
    value: Any,
) -> str:
    """Normalize a provider name."""

    if not isinstance(value, str):
        return "unknown_provider"

    normalized = value.strip().lower()

    return normalized or "unknown_provider"


def safe_mapping(
    value: Any,
) -> Mapping[str, Any]:
    """Return a mapping or an empty dictionary."""

    if isinstance(value, Mapping):
        return value

    return {}


def object_to_mapping(
    value: Any,
) -> dict[str, Any]:
    """
    Convert a dataclass, compatible model, or mapping into a
    JSON-safe dictionary.
    """

    if value is None:
        return {}

    to_dict = getattr(
        value,
        "to_dict",
        None,
    )

    if callable(to_dict):
        result = to_dict()

        if isinstance(result, Mapping):
            return make_json_safe(
                dict(result)
            )

    if is_dataclass(value):
        return make_json_safe(
            asdict(value)
        )

    if isinstance(value, Mapping):
        return make_json_safe(
            dict(value)
        )

    attributes = getattr(
        value,
        "__dict__",
        None,
    )

    if isinstance(attributes, Mapping):
        return make_json_safe(
            dict(attributes)
        )

    return {
        "value": make_json_safe(value)
    }


def make_json_safe(
    value: Any,
) -> Any:
    """Recursively convert values into JSON-safe structures."""

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, datetime):
        return (
            value.astimezone(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )

    if is_dataclass(value):
        return make_json_safe(
            asdict(value)
        )

    if isinstance(value, Mapping):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            make_json_safe(item)
            for item in value
        ]

    return str(value)


def json_default(
    value: Any,
) -> Any:
    """Fallback serializer used by json.dumps."""

    return make_json_safe(value)


def clamp_integer(
    value: Any,
    *,
    minimum: int,
    maximum: int,
) -> int:
    """Convert and constrain an integer."""

    try:
        converted = int(value)
    except (TypeError, ValueError):
        converted = minimum

    return max(
        minimum,
        min(maximum, converted),
    )


def maximum_or_zero(
    values: Sequence[int],
) -> int:
    """Return the maximum value or zero."""

    return max(values, default=0)


def yes_no(
    value: bool,
) -> str:
    """Render a boolean as Yes or No."""

    return "Yes" if value else "No"


def deduplicate_strings(
    values: Iterable[str],
) -> list[str]:
    """Remove duplicate strings while preserving order."""

    return list(
        dict.fromkeys(
            value
            for value in values
            if isinstance(value, str)
            and value.strip()
        )
    )


def deduplicate_findings(
    findings: Iterable[Finding],
) -> list[Finding]:
    """Remove duplicate findings by finding identifier."""

    unique: dict[str, Finding] = {}

    for finding in findings:
        unique.setdefault(
            finding.finding_id,
            finding,
        )

    return list(unique.values())


def deduplicate_recommendations(
    recommendations: Iterable[Recommendation],
) -> list[Recommendation]:
    """Remove duplicate recommendations by identifier."""

    unique: dict[str, Recommendation] = {}

    for recommendation in recommendations:
        unique.setdefault(
            recommendation.recommendation_id,
            recommendation,
        )

    return list(unique.values())


def find_evidence_source(
    evidence: ThreatEvidenceProtocol,
    *,
    preferred_names: Sequence[str],
    default: str,
) -> str:
    """Find a matching provider name in the evidence."""

    providers = {
        provider.lower(): provider
        for provider in evidence.providers_consulted
    }

    for preferred in preferred_names:
        normalized = preferred.lower()

        if normalized in providers:
            return providers[normalized]

    return default


# ============================================================
# SECTION 16
# CONVENIENCE FUNCTION
#
# This function supports callers that do not need a customized
# report builder or report service.
# ============================================================


def build_threat_intelligence_report(
    *,
    indicator: IndicatorProtocol,
    summary: ThreatSummaryProtocol,
    evidence: ThreatEvidenceProtocol,
    provider_results: Iterable[ProviderResultProtocol],
    configuration: ReportConfiguration | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ThreatIntelligenceReport:
    """
    Build a threat-intelligence report using the default
    construction pipeline.
    """

    builder = ThreatIntelligenceReportBuilder(
        configuration=configuration
    )

    return builder.build(
        indicator=indicator,
        summary=summary,
        evidence=evidence,
        provider_results=provider_results,
        metadata=metadata,
    )
