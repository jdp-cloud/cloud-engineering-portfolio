from pathlib import Path

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


print("=== Gen2X Serialization Test ===")

evidence = ThreatEvidence(
    identity=EvidenceIdentity(
        evidence_id="ev-serialize-001",
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

payload = evidence.to_dict()

print("Original model:", evidence.model_name)
print("Serialized evidence_id:", payload["identity"]["evidence_id"])
print("Serialized severity:", payload["context"]["severity"])
print("Serialized timestamp:", payload["identity"]["observed_at"])

output_path = Path("evidence/lab12d-07-threat-evidence.json")
output_path.write_text(evidence.to_json(indent=2) + "\n", encoding="utf-8")

restored = ThreatEvidence.from_dict(payload)

print()
print("JSON artifact:", output_path)
print("Restored model:", restored.model_name)
print("Restored severity type:", type(restored.context.severity).__name__)
print("Round trip equal:", restored == evidence)