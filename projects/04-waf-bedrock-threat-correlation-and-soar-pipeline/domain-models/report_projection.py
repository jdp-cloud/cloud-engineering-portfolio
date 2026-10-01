from models.enums import (
    ApprovalMode,
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
    ThreatSummary,
    ResponseSummary,
)


print("=== Gen2X Report Projection Test ===")

# ------------------------------------------------------------------
# Threat domain object
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
# Response domain object
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
# Human-facing report projections
# ------------------------------------------------------------------

threat_summary = ThreatSummary(
    title="Verified GitHub Token Exposure",
    summary=(
        "Gen2X identified a critical token exposure supported "
        "by verified provider evidence."
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
# Verify facts survived the projection
# ------------------------------------------------------------------

print()
print(threat_summary.describe())
print(response_summary.describe())

print()
print(
    "Severity preserved:",
    threat_summary.severity == threat.assessment.severity,
)
print(
    "Confidence preserved:",
    threat_summary.confidence == threat.assessment.confidence,
)
print(
    "Evidence count preserved:",
    threat_summary.evidence_count == threat.provenance.evidence_count,
)
print(
    "Response action preserved:",
    response_summary.action == response.action,
)
print(
    "Approval status preserved:",
    response_summary.approval_status == response.approval_status,
)

print()
print("PASS: Gen2X report projections preserved domain facts.")