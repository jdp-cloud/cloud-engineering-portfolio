"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    test_models_roundtrip.py

===============================================================================

Overview
-------------------------------------------------------------------------------

This test guards the serialization contract of the models package:

    model == type(model).from_dict(model.to_dict())

for every domain model, including nested models, enumerations,
datetimes, and sets.

Historically from_dict() returned nested dictionaries instead of nested
models, plain strings instead of enumerations, and ISO strings instead
of datetimes. These tests prevent that regression.

Run with pytest:

    pytest tests/test_models_roundtrip.py

Or directly:

    python tests/test_models_roundtrip.py

===============================================================================
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent

if str(LAB_ROOT) not in sys.path:
    sys.path.insert(0, str(LAB_ROOT))

from models.enums import (  # noqa: E402
    IndicatorSource,
    IndicatorType,
    PlatformType,
    ProviderStatus,
    ProviderTrustLevel,
    ProviderType,
    ThreatCondition,
    ThreatConfidence,
    ThreatSeverity,
)
from models.evidence import (  # noqa: E402
    EvidenceContext,
    EvidenceIdentity,
    EvidenceIndicator,
    EvidenceSource,
    ThreatEvidence,
)
from models.provider import (  # noqa: E402
    Provider,
    ProviderCapabilities,
    ProviderConfiguration,
    ProviderIdentity,
)
from models.time_utils import utc_now  # noqa: E402


def build_evidence() -> ThreatEvidence:
    """Build one fully populated ThreatEvidence object."""

    return ThreatEvidence(
        identity=EvidenceIdentity(
            evidence_id="e-1",
            provider_name="Wiz",
            provider_type=ProviderType.COMMERCIAL,
            provider_platform=PlatformType.AWS,
        ),
        indicator=EvidenceIndicator(
            indicator_type=IndicatorType.LIBRARY,
            indicator_value="requests==2.5",
            indicator_source=IndicatorSource.EXTERNAL_API,
            condition=ThreatCondition.DEPRECATED_LIBRARY,
        ),
        source=EvidenceSource(
            account_id="123456789012",
            region="us-east-1",
        ),
        context=EvidenceContext(
            severity=ThreatSeverity.HIGH,
            confidence=ThreatConfidence.OBSERVED,
            provider_trust=ProviderTrustLevel.HIGH,
            expires_at=utc_now() + timedelta(hours=1),
            tags={"lab12", "supply-chain"},
        ),
    )


def build_provider() -> Provider:
    """Build one fully populated Provider object."""

    return Provider(
        identity=ProviderIdentity(
            name="wiz",
            display_name="Wiz",
            platform=PlatformType.AWS,
            provider_type=ProviderType.COMMERCIAL,
        ),
        capabilities=ProviderCapabilities(
            supported_indicators={IndicatorType.LIBRARY},
            supported_conditions={
                ThreatCondition.DEPRECATED_LIBRARY,
            },
            supports_batch=True,
        ),
        configuration=ProviderConfiguration(
            timeout_seconds=15,
        ),
    )


def test_evidence_roundtrip():
    """ThreatEvidence must survive to_dict() -> from_dict() intact."""

    evidence = build_evidence()

    restored = ThreatEvidence.from_dict(evidence.to_dict())

    assert restored == evidence

    # Types must be revived, not just values.
    assert isinstance(restored.identity, EvidenceIdentity)
    assert isinstance(restored.severity, ThreatSeverity)
    assert isinstance(restored.observed_at, datetime)
    assert restored.observed_at.tzinfo is not None
    assert isinstance(restored.context.tags, set)


def test_evidence_json_roundtrip():
    """ThreatEvidence must survive a full JSON round trip."""

    evidence = build_evidence()

    payload = json.loads(evidence.to_json())

    restored = ThreatEvidence.from_dict(payload)

    assert restored == evidence


def test_provider_roundtrip():
    """Provider must survive to_dict() -> from_dict() intact."""

    provider = build_provider()

    provider.increment_success()
    provider.increment_failure("timeout")
    provider.record_latency(120.0)

    restored = Provider.from_dict(provider.to_dict())

    assert restored == provider

    assert restored.health.status is ProviderStatus.ERROR
    assert restored.health.last_failure.tzinfo is not None
    assert isinstance(
        next(iter(restored.capabilities.supported_indicators)),
        IndicatorType,
    )


def test_unknown_fields_ignored():
    """from_dict() must ignore unknown top-level fields."""

    evidence = build_evidence()

    payload = evidence.to_dict()
    payload["bogus_field"] = "ignore me"

    assert ThreatEvidence.from_dict(payload) == evidence


def test_invalid_data_raises_value_error():
    """from_dict() must reject values that violate field types."""

    payload = build_evidence().to_dict()
    payload["context"]["severity"] = "NOT_A_SEVERITY"

    try:
        ThreatEvidence.from_dict(payload)
    except ValueError:
        return

    raise AssertionError("invalid enum value was accepted")


def test_validation_hook_runs_on_from_dict():
    """Business validation must run during reconstruction."""

    payload = build_evidence().to_dict()
    payload["identity"]["provider_name"] = "   "

    try:
        ThreatEvidence.from_dict(payload)
    except ValueError:
        return

    raise AssertionError("empty provider_name was accepted")


if __name__ == "__main__":

    test_evidence_roundtrip()

    test_evidence_json_roundtrip()

    test_provider_roundtrip()

    test_unknown_fields_ignored()

    test_invalid_data_raises_value_error()

    test_validation_hook_runs_on_from_dict()

    print("All model round-trip tests passed.")
