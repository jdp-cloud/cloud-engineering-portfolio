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


print("=== Gen2X Cross-Model Composition Test ===")

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

print()
print("Threat created:", threat.identity.threat_id)
print("Threat severity:", threat.assessment.severity.value)
print("Evidence count:", threat.provenance.evidence_count)
print("Provider count:", threat.provenance.provider_count)

# ------------------------------------------------------------------
# Response recommendation
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
        rationale="Contain the affected repository until exposed credentials are reviewed.",
        expected_outcome="Prevent further use of the exposed credential.",
    ),
    governance=ResponseGovernance(
        approval_mode=ApprovalMode.SINGLE_APPROVER,
        approval_status=ResponseApproval.PENDING,
        execution_mode=ResponseMode.MANUAL,
    ),
)

print()
print("Response created:", response.response_id)
print("Linked threat:", response.threat_id)
print("Threat linkage valid:", response.threat_id == threat.identity.threat_id)
print("Recommended action:", response.action.value)
print("Requires approval:", response.requires_approval)
print("Pending approval:", response.is_pending_approval)
print("Executable before approval:", response.is_executable)

# ------------------------------------------------------------------
# Human authorization
# ------------------------------------------------------------------

response.approve(
    approved_by="security-lead",
    reason="Critical token exposure reviewed and containment authorized.",
)

print()
print("Approval status:", response.approval_status.value)
print("Approved by:", response.governance.approved_by)
print("Executable after approval:", response.is_executable)

print()
print("PASS: Threat and Response contracts composed successfully.")
