from pydantic import ValidationError

from models.enums import PlatformType, ProviderType
from models.evidence import EvidenceIdentity


print("=== Gen2X Contract Failure Test ===")

try:
    EvidenceIdentity(
        evidence_id="ev-invalid-001",
        provider_name="GitHub",
        provider_type=ProviderType.COMMERCIAL,
        provider_platform=PlatformType.GITHUB,
        unexpected_field="this field does not belong here",
    )

    print("FAIL: Model accepted an unexpected field.")

except ValidationError as exc:
    print("PASS: Gen2X rejected the unexpected field.")
    print()
    print(exc)