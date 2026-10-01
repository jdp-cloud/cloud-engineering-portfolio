# Query:
# ContextLines: 1

from models.enums import (
    IndicatorSource,
    IndicatorType,
    PlatformType,
    ProviderType,
    ThreatCondition,
    ThreatSeverity,
)
from models.evidence import (
    EvidenceContext,
    EvidenceIdentity,
    EvidenceIndicator,
    ThreatEvidence,
)

evidence = ThreatEvidence(
    identity=EvidenceIdentity(
        evidence_id="ev-001",
        provider_name="GitHub",
        provider_type=ProviderType.COMMERCIAL,
        provider_platform=PlatformType.GITHUB,
    ),
    indicator=EvidenceIndicator(
        indicator_type=IndicatorType.TOKEN_ID,
        indicator_value="ghp_example",
        indicator_source=IndicatorSource.EXTERNAL_API,
        condition=ThreatCondition.TOKEN_EXPOSURE,
    ),
    context=EvidenceContext(
        severity=ThreatSeverity.CRITICAL,
    ),
)

print(evidence.describe())

restored = ThreatEvidence.from_dict(evidence.to_dict())

print("Round trip:", restored == evidence)
