from pydantic import ValidationError

from models.enums import PlatformType, ProviderType
from models.evidence import EvidenceIdentity


print("=== Gen2X Assignment Validation Test ===")

identity = EvidenceIdentity(
    evidence_id="ev-mutate-001",
    provider_name="GitHub",
    provider_type=ProviderType.COMMERCIAL,
    provider_platform=PlatformType.GITHUB,
)

print("Original provider:", identity.provider_name)

try:
    identity.provider_name = "   "

    print("FAIL: Invalid mutation was accepted.")

except ValidationError as exc:
    print("PASS: Gen2X rejected the invalid mutation.")
    print()
    print(exc)

print()
print("Provider after failed mutation:", identity.provider_name)