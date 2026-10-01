"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    indicator.py

Part I:
    Indicator Foundation Models

===============================================================================

Business Objective
-------------------------------------------------------------------------------

Indicators represent objects that may be relevant to a security
investigation.

Examples include:

    • IP addresses
    • Domain names
    • URLs
    • File hashes
    • Email addresses
    • User identities
    • Cloud resources
    • Repository artifacts

An indicator is not automatically a threat.

It is simply something that Gen2X may investigate.

Providers collect evidence about indicators.

Fusion evaluates that evidence later.

===============================================================================
"""

from __future__ import annotations

from pydantic import Field, field_validator

from models.base_model import Gen2XModel
from datetime import datetime
from hashlib import sha256
from typing import Any
from uuid import uuid4

from models.enums import (
    IndicatorSource,
    IndicatorType,
)

from utils.time import utc_now


# =============================================================================
# Indicator Identity
# =============================================================================


class IndicatorIdentity(Gen2XModel):
    """
    Identifies one security-relevant object.

    Identity answers:

        "What are we investigating?"

    indicator_id identifies this particular model instance.

    indicator_key identifies the underlying indicator itself.
    """

    indicator_type: IndicatorType

    value: str

    source: IndicatorSource

    indicator_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    # =========================================================================
    # Validation
    # =========================================================================

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        """
        Normalize and validate the indicator value.
        """

        value = value.strip()

        if not value:
            raise ValueError(
                "Indicator value cannot be empty."
            )

        return value

    # =========================================================================
    # Normalization
    # =========================================================================

    @property
    def normalized_value(self) -> str:
        """
        Return a normalized representation of the indicator.

        Normalization is intentionally conservative.

        Some indicator types are naturally case-insensitive.
        Other indicator types may contain case-sensitive values.

        Additional normalization rules may be introduced as
        indicator support expands.
        """

        value = self.value.strip()

        case_insensitive_types = {
            IndicatorType.IPV4,
            IndicatorType.IPV6,
            IndicatorType.DOMAIN,
            IndicatorType.EMAIL,
        }

        if self.indicator_type in case_insensitive_types:
            return value.casefold()

        return value

    # =========================================================================
    # Deterministic Identity
    # =========================================================================

    @property
    def indicator_key(self) -> str:
        """
        Return a deterministic identifier for the underlying indicator.

        indicator_id identifies this model instance.

        indicator_key identifies the thing being investigated.

        IndicatorSource is intentionally excluded.

        Multiple providers may discover the same indicator.
        They should still resolve to the same indicator_key.
        """

        source = "|".join(
            [
                self.indicator_type.value,
                self.normalized_value,
            ]
        )

        return sha256(
            source.encode("utf-8")
        ).hexdigest()


# =============================================================================
# Indicator Context
# =============================================================================


class IndicatorContext(Gen2XModel):
    """
    Describes where and when an indicator appeared.

    Context is deliberately platform-neutral.

    The same model can therefore represent indicators discovered
    within AWS, Azure, GCP, GitHub, or on-premises environments.
    """

    first_seen: datetime = Field(
        default_factory=utc_now
    )

    last_seen: datetime = Field(
        default_factory=utc_now
    )

    account_id: str | None = None

    region: str | None = None

    resource_id: str | None = None

    repository: str | None = None


# =============================================================================
# Indicator Metadata
# =============================================================================


class IndicatorMetadata(Gen2XModel):
    """
    Stores optional enrichment associated with an indicator.

    Metadata should provide additional context without changing
    the fundamental identity of the indicator.
    """

    tags: set[str] = Field(
        default_factory=set
    )

    attributes: dict[str, Any] = Field(
        default_factory=dict
    )

    notes: str = ""


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# An indicator
#
# is not
#
# a threat.
#
# It is simply
#
# something
#
# worth investigating.
#
# An IP address
#
# does not become evil
#
# because
#
# someone put it
#
# into a SIEM.
#
# First identify
#
# the thing.
#
# Then collect
#
# the evidence.
#
# Then decide
#
# what the evidence means.
#
# Engineers get into trouble
#
# when they confuse
#
# observation
#
# with
#
# judgment.
#
# Order matters.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================
