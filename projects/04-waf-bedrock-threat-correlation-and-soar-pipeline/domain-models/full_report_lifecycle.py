from pathlib import Path

from models.enums import (
    ApprovalMode,
    ReportAudience as ReportAudienceType,
    ReportTechnicalLevel,
    ReportType,
    ResponseAction,
    ResponseApproval,
    ResponseMode,
    ResponsePriority,
    ThreatCondition,
    ThreatConfidence,
    ThreatSeverity,
)

from models.threat import (
    Threat,
    ThreatAssessment,
    ThreatIdentity,
    ThreatProvenance,
)

from models.response import (
    Response,
    ResponseGovernance,
    ResponseIdentity,
    ResponseRecommendation,
    ResponseTarget,
)

from models.report import (
    ExecutiveSummary,
    Report,
    ReportAccountability,
    ReportAudience,
    ReportEvidenceSummary,
    ReportFinding,
    ReportIdentity,
    ResponseSummary,
    ThreatSummary,
)


print("=== Gen2X Complete Report Lifecycle Test ===")

# ------------------------------------------------------------------
# Threat
# ------------------------------------------------------------------

threat = Threat(
    identity=ThreatIdentity(
        threat_id="threat-token-exposure-001",
        condition=ThreatCondition.TOKEN_EXPOSURE,
    ),
    assessment=ThreatAssessment(
        severity=ThreatSeverity.CRITICAL,
        confidence=ThreatConfidence.VERIFIED,
    ),
    provenance=ThreatProvenance(
        evidence_ids={"ev-serialize-001"},
        provider_names={"GitHub"},
    ),
)

# ------------------------------------------------------------------
# Governed Response
# ------------------------------------------------------------------

response = Response(
    identity=ResponseIdentity(
        threat_id=threat.identity.threat_id,
    ),
    target=ResponseTarget(
        repository="example/security-repository",
    ),
    recommendation=ResponseRecommendation(
        action=ResponseAction.CONTAIN,
        priority=ResponsePriority.CRITICAL,
        rationale=(
            "Contain the affected repository until exposed "
            "credentials are reviewed."
        ),
        expected_outcome=(
            "Prevent further use of the exposed credential."
        ),
    ),
    governance=ResponseGovernance(
        approval_mode=ApprovalMode.SINGLE_APPROVER,
        approval_status=ResponseApproval.PENDING,
        execution_mode=ResponseMode.MANUAL,
    ),
)

response.approve(
    approved_by="security-lead",
    reason="Critical token exposure reviewed and containment authorized.",
)

# ------------------------------------------------------------------
# Report projections
# ------------------------------------------------------------------

threat_summary = ThreatSummary(
    title="Verified GitHub Token Exposure",
    summary=(
        "A GitHub authentication token exposure was verified "
        "through Gen2X security evidence."
    ),
    condition=threat.identity.condition,
    severity=threat.assessment.severity,
    confidence=threat.assessment.confidence,
    affected_resource=response.target.repository,
    evidence_count=threat.provenance.evidence_count,
    provider_count=threat.provenance.provider_count,
)

response_summary = ResponseSummary(
    action=response.action,
    priority=response.priority,
    rationale=response.rationale,
    expected_outcome=response.expected_outcome,
    investigation_status=response.investigation_status,
    approval_status=response.approval_status,
    approved_by=response.governance.approved_by,
    approved_at=response.governance.approved_at,
)

# ------------------------------------------------------------------
# Complete Report
# ------------------------------------------------------------------

report = Report(
    identity=ReportIdentity(
        report_type=ReportType.INCIDENT_SUMMARY,
        threat_id=threat.identity.threat_id,
        response_id=response.response_id,
    ),
    audience=ReportAudience(
        audience=ReportAudienceType.SECURITY_ENGINEER,
        technical_level=ReportTechnicalLevel.TECHNICAL,
        intended_for=["Security Engineering"],
    ),
    executive_summary=ExecutiveSummary(
        headline="Critical GitHub Token Exposure",
        summary=(
            "Gen2X verified an exposed authentication token "
            "requiring containment."
        ),
        severity=threat.assessment.severity,
        business_impact=(
            "An exposed credential may permit unauthorized access."
        ),
        recommended_action="Contain and rotate the exposed credential.",
        decision_required=False,
    ),
    threat_summary=threat_summary,
    response_summary=response_summary,
    evidence_summary=ReportEvidenceSummary(
        evidence_ids=list(threat.provenance.evidence_ids),
        providers=list(threat.provenance.provider_names),
        corroborated=False,
        conflicts_detected=False,
    ),
    accountability=ReportAccountability(
        investigation_owner=None,
        recommendation_created_by="Gen2X",
        approval_required=response.requires_approval,
        approval_status=response.approval_status,
        approved_by=response.governance.approved_by,
        approved_at=response.governance.approved_at,
        decision_reason=response.governance.decision_reason,
        generated_by="Gen2X Security Engineering Platform",
    ),
    findings=[
        ReportFinding(
            title="Exposed GitHub Authentication Token",
            description=(
                "A GitHub authentication token was identified "
                "as exposed."
            ),
            condition=threat.identity.condition,
            severity=threat.assessment.severity,
            confidence=threat.assessment.confidence,
            affected_resource=response.target.repository,
            recommendation=(
                "Contain access and rotate the exposed credential."
            ),
        )
    ],
)

print()
print("Initial status:", report.status.value)
print("Finding count:", report.finding_count)
print("Evidence count:", report.evidence_count)
print("Provider count:", report.provider_count)
print("Approval status:", report.approval_status.value)

# ------------------------------------------------------------------
# Controlled lifecycle
# ------------------------------------------------------------------

report.submit_for_review()
print()
print("After review submission:", report.status.value)

report.finalize()
print("After finalization:", report.status.value)

# ------------------------------------------------------------------
# Immutability test
# ------------------------------------------------------------------

try:
    report.add_finding(
        ReportFinding(
            title="Late Finding",
            description="This should not be accepted after finalization.",
            condition=ThreatCondition.TOKEN_EXPOSURE,
            severity=ThreatSeverity.CRITICAL,
            confidence=ThreatConfidence.VERIFIED,
        )
    )

    print("FAIL: Final report accepted a mutation.")

except ValueError as exc:
    print("PASS: Final report rejected mutation.")
    print("Mutation guard:", exc)

# ------------------------------------------------------------------
# Archive + serialization
# ------------------------------------------------------------------

report.archive()

print()
print("Archived status:", report.status.value)

output_path = Path(
    "evidence/lab12d-13-final-gen2x-report.json"
)

output_path.write_text(
    report.to_json(indent=2) + "\n",
    encoding="utf-8",
)

print("JSON artifact:", output_path)
print()
print("PASS: Complete Gen2X report lifecycle validated.")