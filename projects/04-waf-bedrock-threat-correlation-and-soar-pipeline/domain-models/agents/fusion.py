#!/usr/bin/env python3

"""
===============================================================================

Gen2X Security Engineering Platform

Module:
    fusion.py

Agent:
    Fusion Agent

Part I:
    Evidence Collection

===============================================================================

Business Objective
-------------------------------------------------------------------------------

Security providers observe the world.

Fusion understands it.

Every provider specializes in collecting one type of information.

Examples include:

    • VirusTotal
    • Wiz
    • GuardDuty
    • Security Hub
    • AWS Inspector
    • GitHub Secret Scanning
    • Weak TLS Scanner
    • Internal Asset Inventory

Unfortunately...

Every provider also speaks a different language.

VirusTotal returns one schema.

GuardDuty returns another.

GitHub returns another.

Wiz returns another.

Fusion should never need to understand every API.

Instead, every provider translates its findings into one common evidence
model.

Fusion reasons about evidence.

Not provider implementations.

-------------------------------------------------------------------------------

Fusion Pipeline

                    Providers

                         │

        ┌────────────────┼────────────────┐

        ▼                ▼                ▼

   VirusTotal       GitHub        GuardDuty

        ▼                ▼                ▼

                ThreatEvidence

                        ▼

             EvidenceAggregator

                        ▼

             ThreatCorrelation

                        ▼

             ThreatClassifier

                        ▼

          ThreatAssessmentEngine

                        ▼

                ThreatSummary

                        ▼

                  report.py

-------------------------------------------------------------------------------

Responsibilities

Fusion intentionally separates investigation into three stages.

Part I

    Collect evidence.

Part II

    Reason about evidence.

Part III

    Communicate conclusions.

This file implements Part I.

Part I is responsible for:

    • Normalizing provider output

    • Preserving provider provenance

    • Recording observations

    • Validating evidence

    • Organizing evidence

Part I deliberately avoids:

    • Threat classification

    • Final severity calculation

    • Confidence calculation

    • Response recommendations

    • Executive reporting

Those responsibilities belong to later stages.

-------------------------------------------------------------------------------

Architectural Philosophy

Every provider answers one question.

"What did I observe?"

Fusion answers a different question.

"What does all of this mean?"

That separation allows providers to remain independent while Fusion
remains reusable.

New providers should never require Fusion to be rewritten.

Only new translators should be added.

-------------------------------------------------------------------------------

Example

Provider Output

        Wiz

            ↓

    Deprecated Library

            ↓

ThreatEvidence(
    provider="wiz",
    condition=ThreatCondition.DEPRECATED_LIBRARY,
    severity=ThreatSeverity.HIGH,
    confidence=ThreatConfidence.OBSERVED,
)

Provider Output

        GitHub

            ↓

Exposed Secret

            ↓

ThreatEvidence(
    provider="github",
    condition=ThreatCondition.TOKEN_EXPOSURE,
    severity=ThreatSeverity.CRITICAL,
    confidence=ThreatConfidence.VALIDATED,
)

Fusion now receives identical objects.

The provider no longer matters.

Only the evidence matters.

===============================================================================

Chewbacca's Commentary 🐾

Imagine interviewing witnesses.

One speaks English.

One speaks Japanese.

One speaks Klingon.

One speaks...

whatever printers speak.

Before detectives compare stories,
someone must translate them into
one common language.

That's exactly what Part I does.

Fusion doesn't care
where evidence came from.

Fusion cares
that every observation
arrives speaking
the same language.

Professional investigations
begin with organized evidence.

Not conclusions.

                                — Chewbacca
                                  Chief Wookiee Architect

===============================================================================
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

from models.enums import (
    IndicatorSource,
    IndicatorType,
    ProviderStatus,
    ProviderTrustLevel,
    ThreatCondition,
    ThreatConfidence,
    ThreatSeverity,
)


# =============================================================================
# Shared Helpers
# =============================================================================


def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC timestamp.

    Every evidence object within Gen2X should use UTC.

    Consistent timestamps make evidence easier to correlate across
    providers, cloud platforms, and geographic regions.
    """

    return datetime.now(timezone.utc)


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Security investigations
# eventually become
#
# timelines.
#
# One minute
#
# may explain
#
# an entire incident.
#
# Bad timestamps
#
# create
#
# bad investigations.
#
# Computers
# don't naturally agree
# what time it is.
#
# Engineers
# make them agree.
#
# =============================================================================


# =============================================================================
# Threat Evidence
# =============================================================================


@dataclass(slots=True)
class ThreatEvidence:
    """
    Represents one normalized observation produced by one provider.

    ThreatEvidence answers one question:

        "What did this provider observe?"

    Every provider within Gen2X returns the same object.

    Providers collect.

    Fusion reasons.

    Reports communicate.

    Separating those responsibilities keeps the platform modular,
    extensible, and easier to maintain.
    """

    # -------------------------------------------------------------------------
    # Evidence Identity
    # -------------------------------------------------------------------------

    evidence_id: str = field(default_factory=lambda: str(uuid4()))

    # -------------------------------------------------------------------------
    # Provider Information
    # -------------------------------------------------------------------------

    provider_name: str = ""

    provider_status: ProviderStatus = ProviderStatus.UNKNOWN

    provider_trust: ProviderTrustLevel = ProviderTrustLevel.UNKNOWN

    # -------------------------------------------------------------------------
    # Indicator
    # -------------------------------------------------------------------------

    indicator_value: str = ""

    indicator_type: IndicatorType = IndicatorType.UNKNOWN

    indicator_source: IndicatorSource = IndicatorSource.UNKNOWN

    # -------------------------------------------------------------------------
    # Provider Observation
    # -------------------------------------------------------------------------

    condition: ThreatCondition = ThreatCondition.UNKNOWN

    severity: ThreatSeverity = ThreatSeverity.UNKNOWN

    confidence: ThreatConfidence = ThreatConfidence.UNKNOWN

    summary: str = ""

    # -------------------------------------------------------------------------
    # Time
    # -------------------------------------------------------------------------

    observed_at: datetime = field(default_factory=utc_now)

    expires_at: datetime | None = None

    # -------------------------------------------------------------------------
    # Provider Context
    # -------------------------------------------------------------------------

    metadata: dict[str, Any] = field(default_factory=dict)

    raw_reference: str | None = None

    # =========================================================================
    # Validation
    # =========================================================================

    def __post_init__(self) -> None:
        """
        Validate the structural integrity of the evidence object.

        Validation ensures consistency.

        It does not determine whether the provider is correct.
        """

        self.provider_name = self.provider_name.strip()
        self.indicator_value = self.indicator_value.strip()
        self.summary = self.summary.strip()

        if not self.provider_name:
            raise ValueError("provider_name cannot be empty")

        if not self.indicator_value:
            raise ValueError("indicator_value cannot be empty")

        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")

        if (
            self.expires_at is not None
            and self.expires_at <= self.observed_at
        ):
            raise ValueError(
                "expires_at must occur after observed_at"
            )

    # =========================================================================
    # Evidence State
    # =========================================================================

    @property
    def is_expired(self) -> bool:
        """Return True if the evidence has expired."""

        return (
            self.expires_at is not None
            and utc_now() >= self.expires_at
        )

    @property
    def provider_succeeded(self) -> bool:
        """Return True if the provider completed successfully."""

        return self.provider_status in {
            ProviderStatus.SUCCESS,
            ProviderStatus.PARTIAL_SUCCESS,
        }

    @property
    def is_usable(self) -> bool:
        """
        Determine whether this evidence may participate in analysis.

        Part II performs additional reasoning.

        Part I simply determines whether the evidence is structurally
        usable.
        """

        return (
            self.provider_succeeded
            and not self.is_expired
            and self.condition != ThreatCondition.UNKNOWN
        )

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the evidence object into a JSON-serializable dictionary.
        """

        return {
            "evidence_id": self.evidence_id,
            "provider_name": self.provider_name,
            "provider_status": self.provider_status.value,
            "provider_trust": self.provider_trust.value,
            "indicator_value": self.indicator_value,
            "indicator_type": self.indicator_type.value,
            "indicator_source": self.indicator_source.value,
            "condition": self.condition.value,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "summary": self.summary,
            "observed_at": self.observed_at.isoformat(),
            "expires_at": (
                self.expires_at.isoformat()
                if self.expires_at
                else None
            ),
            "metadata": dict(self.metadata),
            "raw_reference": self.raw_reference,
        }


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Every provider
# believes
# it is the center
# of the universe.
#
# It isn't.
#
# VirusTotal
# knows VirusTotal.
#
# Wiz
# knows Wiz.
#
# GitHub
# knows GitHub.
#
# GuardDuty
# knows GuardDuty.
#
# Fusion knows
#
# evidence.
#
# Great architectures
# don't force
# every component
# to speak
# the same language.
#
# They create
# a common language
# everyone shares.
#
# That's what
# ThreatEvidence
# becomes.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================

# =============================================================================
#
# EvidenceAggregator
#
# Part I — Construction and Collection Behavior
#
# =============================================================================
#
# Business Objective
# -----------------------------------------------------------------------------
#
# EvidenceAggregator is the central evidence repository used by Fusion.
#
# Every provider within Gen2X produces ThreatEvidence.
#
# EvidenceAggregator organizes that evidence while preserving:
#
#     • Provider provenance
#
#     • Indicator relationships
#
#     • Threat conditions
#
#     • Investigation context
#
#     • Collection integrity
#
#     • Query performance
#
# The aggregator intentionally performs NO threat analysis.
#
# Its responsibility is organization.
#
# Fusion reasons later.
#
# -----------------------------------------------------------------------------
#
# Responsibilities
#
# ✓ Store evidence
#
# ✓ Validate evidence
#
# ✓ Prevent duplicates
#
# ✓ Maintain indexes
#
# ✓ Support querying
#
# ✓ Preserve investigation state
#
# ✓ Generate snapshots
#
# ✓ Detect inconsistencies
#
# Does NOT
#
# ✗ Calculate severity
#
# ✗ Calculate confidence
#
# ✗ Recommend responses
#
# ✗ Generate reports
#
# ✗ Call Bedrock
#
# =============================================================================


# =============================================================================
# Evidence Query
# =============================================================================


@dataclass(slots=True, frozen=True)
class EvidenceQuery:
    """
    Describes evidence-selection criteria.

    Every field is optional.

    Multiple populated fields are combined using
    logical AND operations.
    """

    provider_names: frozenset[str] = frozenset()

    indicator_value: str | None = None

    indicator_type: IndicatorType | None = None

    conditions: frozenset[ThreatCondition] = frozenset()

    statuses: frozenset[ProviderStatus] = frozenset()

    include_expired: bool = False

    usable_only: bool = False

    observed_after: datetime | None = None

    observed_before: datetime | None = None


# =============================================================================
# Evidence Conflict
# =============================================================================


@dataclass(slots=True, frozen=True)
class EvidenceConflict:
    """
    Represents a disagreement discovered during
    evidence collection.

    Fusion reports disagreements.

    Fusion does not resolve them here.
    """

    indicator_value: str

    field_name: str

    observed_values: tuple[str, ...]

    evidence_ids: tuple[str, ...]


# =============================================================================
# Evidence Snapshot
# =============================================================================


@dataclass(slots=True, frozen=True)
class EvidenceSnapshot:
    """
    Immutable snapshot of one investigation.

    Snapshots guarantee deterministic reasoning.

    Part II should always reason over snapshots
    rather than mutable collections.
    """

    investigation_id: str

    created_at: datetime

    evidence: tuple[ThreatEvidence, ...]

    inventory: dict[str, Any]

    provenance: dict[str, Any]

    conflicts: tuple[EvidenceConflict, ...]


# =============================================================================
# Evidence Aggregator
# =============================================================================


class EvidenceAggregator:
    """
    Organize normalized ThreatEvidence objects.

    EvidenceAggregator answers one question:

        "What evidence exists?"

    It intentionally avoids answering:

        "What does the evidence mean?"

    That responsibility belongs to Part II.
    """

    # =========================================================================
    # Construction
    # =========================================================================

    def __init__(
        self,
        evidence: Iterable[ThreatEvidence] | None = None,
        *,
        investigation_id: str | None = None,
    ) -> None:
        """
        Initialize one investigation.

        Every investigation receives its own
        evidence repository.
        """

        self.investigation_id = (
            investigation_id or str(uuid4())
        )

        self.created_at = utc_now()

        self.updated_at = self.created_at

        #
        # Primary Evidence Storage
        #

        self._evidence: dict[
            str,
            ThreatEvidence,
        ] = {}

        #
        # Duplicate Detection
        #

        self._fingerprints: dict[
            str,
            str,
        ] = {}

        #
        # Internal Indexes
        #

        self._provider_index: dict[
            str,
            set[str],
        ] = defaultdict(set)

        self._indicator_index: dict[
            tuple[IndicatorType, str],
            set[str],
        ] = defaultdict(set)

        self._condition_index: dict[
            ThreatCondition,
            set[str],
        ] = defaultdict(set)

        self._status_index: dict[
            ProviderStatus,
            set[str],
        ] = defaultdict(set)

        #
        # Initial Evidence
        #

        if evidence is not None:
            self.extend(evidence)

    # =========================================================================
    # Collection Behavior
    # =========================================================================

    def __len__(self) -> int:
        """
        Return the number of stored evidence objects.
        """

        return len(self._evidence)

    def __iter__(self) -> Iterator[ThreatEvidence]:
        """
        Iterate over stored evidence.

        Evidence is returned in insertion order.
        """

        return iter(self._evidence.values())

    def __contains__(
        self,
        evidence_id: object,
    ) -> bool:
        """
        Return True if the evidence ID exists.
        """

        return evidence_id in self._evidence

    def __bool__(self) -> bool:
        """
        Truthiness helper.

        Empty aggregators evaluate to False.
        """

        return bool(self._evidence)

    # =========================================================================
    # Basic Retrieval
    # =========================================================================

    def get(
        self,
        evidence_id: str,
    ) -> ThreatEvidence | None:
        """
        Retrieve one evidence object.

        Returns None if the ID is unknown.
        """

        return self._evidence.get(evidence_id)

    def all(self) -> list[ThreatEvidence]:
        """
        Return every evidence object.

        A new list is returned to prevent
        accidental modification of internal
        state.
        """

        return list(self._evidence.values())

    def clear(self) -> None:
        """
        Remove every evidence object.

        All indexes are rebuilt.
        """

        self._evidence.clear()

        self._fingerprints.clear()

        self._provider_index.clear()

        self._indicator_index.clear()

        self._condition_index.clear()

        self._status_index.clear()

        self.updated_at = utc_now()

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    @staticmethod
    def _fingerprint(
        evidence: ThreatEvidence,
    ) -> str:
        """
        Produce a deterministic fingerprint.

        Fingerprints identify logically identical
        observations even if UUIDs differ.
        """

        source = "|".join(

            [

                evidence.provider_name.casefold(),

                evidence.indicator_type.value,

                evidence.indicator_value.casefold(),

                evidence.condition.value,

                evidence.observed_at.isoformat(),

            ]

        )

        return sha256(
            source.encode("utf-8")
        ).hexdigest()


# =============================================================================
#
# Chewbacca's Commentary 🐾
#
# Libraries
#
# organize
#
# books.
#
# Museums
#
# organize
#
# history.
#
# EvidenceAggregator
#
# organizes
#
# observations.
#
# Notice something.
#
# None of them
#
# change
#
# what they contain.
#
# Organization
#
# is not
#
# interpretation.
#
# That's why
#
# Fusion
#
# reasons later.
#
# Organization
#
# always comes first.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================

    # =========================================================================
    # Evidence Validation
    # =========================================================================

    @staticmethod
    def _validate_evidence_type(
        evidence: ThreatEvidence,
    ) -> None:
        """
        Confirm that the supplied object is ThreatEvidence.

        The aggregator accepts normalized evidence only.

        Provider-specific dictionaries, API responses, and raw event payloads
        should be translated before reaching this layer.
        """

        if not isinstance(evidence, ThreatEvidence):
            raise TypeError(
                "EvidenceAggregator accepts ThreatEvidence objects only; "
                f"received {type(evidence).__name__}"
            )

    def _validate_evidence_id(
        self,
        evidence: ThreatEvidence,
        *,
        known_ids: set[str] | None = None,
    ) -> None:
        """
        Confirm that the evidence ID is valid and unique.

        Parameters
        ----------
        evidence:
            The evidence record being validated.

        known_ids:
            Optional temporary ID collection used during atomic batch
            validation.
        """

        if not evidence.evidence_id:
            raise ValueError(
                "ThreatEvidence.evidence_id cannot be empty"
            )

        ids = (
            known_ids
            if known_ids is not None
            else set(self._evidence)
        )

        if evidence.evidence_id in ids:
            raise ValueError(
                "Duplicate evidence_id detected: "
                f"{evidence.evidence_id}"
            )

    def _validate_fingerprint(
        self,
        evidence: ThreatEvidence,
        *,
        known_fingerprints: set[str] | None = None,
    ) -> str:
        """
        Confirm that the logical observation is not already stored.

        Two records may have different UUIDs while still representing the
        same provider observation.

        The returned fingerprint may be reused during commit.
        """

        fingerprint = self._fingerprint(evidence)

        fingerprints = (
            known_fingerprints
            if known_fingerprints is not None
            else set(self._fingerprints)
        )

        if fingerprint in fingerprints:
            existing_id = self._fingerprints.get(fingerprint)

            message = "Duplicate evidence observation detected"

            if existing_id is not None:
                message += (
                    f"; existing evidence_id={existing_id}"
                )

            raise ValueError(message)

        return fingerprint

    @staticmethod
    def _validate_time_range(
        evidence: ThreatEvidence,
    ) -> None:
        """
        Validate evidence timestamps.

        ThreatEvidence already performs timestamp validation during object
        construction.

        This additional check protects the aggregator if an evidence object
        was modified after creation.
        """

        if evidence.observed_at.tzinfo is None:
            raise ValueError(
                "ThreatEvidence.observed_at must be timezone-aware"
            )

        if evidence.expires_at is not None:
            if evidence.expires_at.tzinfo is None:
                raise ValueError(
                    "ThreatEvidence.expires_at must be timezone-aware"
                )

            if evidence.expires_at <= evidence.observed_at:
                raise ValueError(
                    "ThreatEvidence.expires_at must occur after observed_at"
                )

    def _validate_for_insertion(
        self,
        evidence: ThreatEvidence,
        *,
        known_ids: set[str] | None = None,
        known_fingerprints: set[str] | None = None,
    ) -> str:
        """
        Run every validation required before insertion.

        Returns
        -------
        str
            The deterministic evidence fingerprint.
        """

        self._validate_evidence_type(evidence)

        self._validate_evidence_id(
            evidence,
            known_ids=known_ids,
        )

        self._validate_time_range(evidence)

        return self._validate_fingerprint(
            evidence,
            known_fingerprints=known_fingerprints,
        )

    # =========================================================================
    # Index Management
    # =========================================================================

    def _commit(
        self,
        evidence: ThreatEvidence,
        *,
        fingerprint: str | None = None,
    ) -> None:
        """
        Store evidence and update every internal index.

        This method assumes validation has already succeeded.

        Keeping index updates in one method prevents insertion paths from
        accidentally updating only part of the aggregator.
        """

        evidence_id = evidence.evidence_id

        if fingerprint is None:
            fingerprint = self._fingerprint(evidence)

        #
        # Primary storage
        #

        self._evidence[evidence_id] = evidence

        #
        # Duplicate index
        #

        self._fingerprints[fingerprint] = evidence_id

        #
        # Provider index
        #

        provider_key = evidence.provider_name.casefold()

        self._provider_index[
            provider_key
        ].add(evidence_id)

        #
        # Indicator index
        #

        indicator_key = (
            evidence.indicator_type,
            evidence.indicator_value.casefold(),
        )

        self._indicator_index[
            indicator_key
        ].add(evidence_id)

        #
        # Threat-condition index
        #

        self._condition_index[
            evidence.condition
        ].add(evidence_id)

        #
        # Provider-status index
        #

        self._status_index[
            evidence.provider_status
        ].add(evidence_id)

        self.updated_at = utc_now()

    @staticmethod
    def _discard_index_value(
        index: dict[Any, set[str]],
        key: Any,
        evidence_id: str,
    ) -> None:
        """
        Remove an evidence ID from one index.

        Empty index buckets are removed entirely.
        """

        bucket = index.get(key)

        if bucket is None:
            return

        bucket.discard(evidence_id)

        if not bucket:
            index.pop(key, None)

    def _remove_from_indexes(
        self,
        evidence: ThreatEvidence,
    ) -> None:
        """
        Remove one evidence record from every derived index.
        """

        evidence_id = evidence.evidence_id

        fingerprint = self._fingerprint(evidence)

        if self._fingerprints.get(fingerprint) == evidence_id:
            self._fingerprints.pop(fingerprint, None)

        provider_key = evidence.provider_name.casefold()

        self._discard_index_value(
            self._provider_index,
            provider_key,
            evidence_id,
        )

        indicator_key = (
            evidence.indicator_type,
            evidence.indicator_value.casefold(),
        )

        self._discard_index_value(
            self._indicator_index,
            indicator_key,
            evidence_id,
        )

        self._discard_index_value(
            self._condition_index,
            evidence.condition,
            evidence_id,
        )

        self._discard_index_value(
            self._status_index,
            evidence.provider_status,
            evidence_id,
        )

    def _rebuild_indexes(self) -> None:
        """
        Rebuild every derived index from primary evidence storage.

        This method is useful after integrity testing, migration work, or
        controlled evidence mutation.

        Primary storage remains the source of truth.
        """

        self._fingerprints.clear()
        self._provider_index.clear()
        self._indicator_index.clear()
        self._condition_index.clear()
        self._status_index.clear()

        for evidence in self._evidence.values():
            fingerprint = self._fingerprint(evidence)

            self._fingerprints[
                fingerprint
            ] = evidence.evidence_id

            self._provider_index[
                evidence.provider_name.casefold()
            ].add(evidence.evidence_id)

            self._indicator_index[
                (
                    evidence.indicator_type,
                    evidence.indicator_value.casefold(),
                )
            ].add(evidence.evidence_id)

            self._condition_index[
                evidence.condition
            ].add(evidence.evidence_id)

            self._status_index[
                evidence.provider_status
            ].add(evidence.evidence_id)

        self.updated_at = utc_now()

    # =========================================================================
    # Evidence Insertion
    # =========================================================================

    def add(
        self,
        evidence: ThreatEvidence,
    ) -> None:
        """
        Add one evidence record.

        Validation occurs before primary storage or indexes are modified.

        Raises
        ------
        TypeError
            The supplied object is not ThreatEvidence.

        ValueError
            The evidence ID or logical observation already exists, or the
            evidence timestamps are invalid.
        """

        fingerprint = self._validate_for_insertion(
            evidence
        )

        self._commit(
            evidence,
            fingerprint=fingerprint,
        )

    def extend(
        self,
        evidence_items: Iterable[ThreatEvidence],
    ) -> None:
        """
        Add multiple evidence records atomically.

        Either the complete batch is committed or none of it is committed.

        This prevents partially loaded provider responses from silently
        becoming part of an investigation.

        The input iterable is converted into a list so generators are
        evaluated exactly once.
        """

        pending = list(evidence_items)

        if not pending:
            return

        known_ids = set(self._evidence)

        known_fingerprints = set(
            self._fingerprints
        )

        validated: list[
            tuple[ThreatEvidence, str]
        ] = []

        #
        # Phase 1:
        #
        # Validate the complete batch without mutating aggregator state.
        #

        for evidence in pending:
            fingerprint = self._validate_for_insertion(
                evidence,
                known_ids=known_ids,
                known_fingerprints=known_fingerprints,
            )

            known_ids.add(
                evidence.evidence_id
            )

            known_fingerprints.add(
                fingerprint
            )

            validated.append(
                (
                    evidence,
                    fingerprint,
                )
            )

        #
        # Phase 2:
        #
        # Commit only after every record has passed validation.
        #

        for evidence, fingerprint in validated:
            self._commit(
                evidence,
                fingerprint=fingerprint,
            )

    # =========================================================================
    # Evidence Removal
    # =========================================================================

    def remove(
        self,
        evidence_id: str,
    ) -> ThreatEvidence:
        """
        Remove and return one evidence record.

        Raises
        ------
        KeyError
            The evidence ID does not exist.
        """

        evidence = self._evidence.get(
            evidence_id
        )

        if evidence is None:
            raise KeyError(
                f"Unknown evidence_id: {evidence_id}"
            )

        self._remove_from_indexes(
            evidence
        )

        removed = self._evidence.pop(
            evidence_id
        )

        self.updated_at = utc_now()

        return removed

    def discard(
        self,
        evidence_id: str,
    ) -> ThreatEvidence | None:
        """
        Remove and return evidence when present.

        Unlike remove(), this method does not raise an exception when the
        evidence ID is unknown.
        """

        evidence = self._evidence.get(
            evidence_id
        )

        if evidence is None:
            return None

        return self.remove(
            evidence_id
        )

    # =========================================================================
    # Indexed Retrieval
    # =========================================================================

    def _resolve_ids(
        self,
        evidence_ids: Iterable[str],
    ) -> list[ThreatEvidence]:
        """
        Resolve evidence IDs into records.

        Unknown IDs are ignored defensively because integrity validation is
        responsible for reporting orphaned index entries.
        """

        records = [
            self._evidence[evidence_id]
            for evidence_id in evidence_ids
            if evidence_id in self._evidence
        ]

        return sorted(
            records,
            key=lambda evidence: (
                evidence.observed_at,
                evidence.evidence_id,
            ),
        )

    def by_provider(
        self,
        provider_name: str,
    ) -> list[ThreatEvidence]:
        """
        Return evidence reported by one provider.

        Provider matching is case-insensitive.
        """

        provider_key = provider_name.strip().casefold()

        if not provider_key:
            return []

        return self._resolve_ids(
            self._provider_index.get(
                provider_key,
                set(),
            )
        )

    def by_indicator(
        self,
        indicator_value: str,
        *,
        indicator_type: IndicatorType | None = None,
    ) -> list[ThreatEvidence]:
        """
        Return evidence associated with one indicator.

        Supplying indicator_type enables an indexed lookup.

        Without indicator_type, every indicator-type bucket must be checked
        because the same textual value could represent different indicator
        classes.
        """

        normalized_value = (
            indicator_value.strip().casefold()
        )

        if not normalized_value:
            return []

        if indicator_type is not None:
            return self._resolve_ids(
                self._indicator_index.get(
                    (
                        indicator_type,
                        normalized_value,
                    ),
                    set(),
                )
            )

        evidence_ids: set[str] = set()

        for (
            indexed_type,
            indexed_value,
        ), indexed_ids in self._indicator_index.items():
            _ = indexed_type

            if indexed_value == normalized_value:
                evidence_ids.update(
                    indexed_ids
                )

        return self._resolve_ids(
            evidence_ids
        )

    def by_condition(
        self,
        condition: ThreatCondition,
    ) -> list[ThreatEvidence]:
        """
        Return evidence describing one threat condition.
        """

        if not isinstance(
            condition,
            ThreatCondition,
        ):
            raise TypeError(
                "condition must be ThreatCondition"
            )

        return self._resolve_ids(
            self._condition_index.get(
                condition,
                set(),
            )
        )

    def by_status(
        self,
        status: ProviderStatus,
    ) -> list[ThreatEvidence]:
        """
        Return evidence with one provider execution status.
        """

        if not isinstance(
            status,
            ProviderStatus,
        ):
            raise TypeError(
                "status must be ProviderStatus"
            )

        return self._resolve_ids(
            self._status_index.get(
                status,
                set(),
            )
        )

    # =========================================================================
    # Evidence-State Retrieval
    # =========================================================================

    def usable(self) -> list[ThreatEvidence]:
        """
        Return evidence eligible for current analysis.

        Final trust thresholds and investigation-specific policy remain the
        responsibility of EvidenceSelector in Part II.
        """

        return sorted(
            [
                evidence
                for evidence in self
                if evidence.is_usable
            ],
            key=lambda evidence: (
                evidence.observed_at,
                evidence.evidence_id,
            ),
        )

    def expired(self) -> list[ThreatEvidence]:
        """
        Return evidence whose validity period has ended.
        """

        return sorted(
            [
                evidence
                for evidence in self
                if evidence.is_expired
            ],
            key=lambda evidence: (
                evidence.observed_at,
                evidence.evidence_id,
            ),
        )

    def provider_failures(
        self,
    ) -> list[ThreatEvidence]:
        """
        Return evidence records associated with unsuccessful provider calls.

        These records may remain useful for diagnostics and audit history even
        when they cannot participate in current threat analysis.
        """

        successful_statuses = {
            ProviderStatus.SUCCESS,
            ProviderStatus.PARTIAL_SUCCESS,
        }

        return sorted(
            [
                evidence
                for evidence in self
                if evidence.provider_status
                not in successful_statuses
            ],
            key=lambda evidence: (
                evidence.observed_at,
                evidence.evidence_id,
            ),
        )

    # =========================================================================
    # Query Operations
    # =========================================================================

    @staticmethod
    def _validate_query_time(
        value: datetime | None,
        *,
        field_name: str,
    ) -> None:
        """
        Validate an optional query timestamp.
        """

        if value is not None and value.tzinfo is None:
            raise ValueError(
                f"{field_name} must be timezone-aware"
            )

    def query(
        self,
        criteria: EvidenceQuery,
    ) -> list[ThreatEvidence]:
        """
        Return evidence matching every populated query criterion.

        Query fields are combined using logical AND.

        The method intentionally favors clarity over premature query-engine
        complexity. Common single-field queries use indexes through the
        convenience methods above.
        """

        if not isinstance(
            criteria,
            EvidenceQuery,
        ):
            raise TypeError(
                "criteria must be EvidenceQuery"
            )

        self._validate_query_time(
            criteria.observed_after,
            field_name="observed_after",
        )

        self._validate_query_time(
            criteria.observed_before,
            field_name="observed_before",
        )

        if (
            criteria.observed_after is not None
            and criteria.observed_before is not None
            and criteria.observed_after
            > criteria.observed_before
        ):
            raise ValueError(
                "observed_after cannot occur after observed_before"
            )

        matches = list(
            self._evidence.values()
        )

        if criteria.provider_names:
            normalized_names = {
                provider_name.strip().casefold()
                for provider_name
                in criteria.provider_names
                if provider_name.strip()
            }

            matches = [
                evidence
                for evidence in matches
                if evidence.provider_name.casefold()
                in normalized_names
            ]

        if criteria.indicator_value is not None:
            normalized_indicator = (
                criteria.indicator_value
                .strip()
                .casefold()
            )

            matches = [
                evidence
                for evidence in matches
                if evidence.indicator_value.casefold()
                == normalized_indicator
            ]

        if criteria.indicator_type is not None:
            matches = [
                evidence
                for evidence in matches
                if evidence.indicator_type
                == criteria.indicator_type
            ]

        if criteria.conditions:
            matches = [
                evidence
                for evidence in matches
                if evidence.condition
                in criteria.conditions
            ]

        if criteria.statuses:
            matches = [
                evidence
                for evidence in matches
                if evidence.provider_status
                in criteria.statuses
            ]

        if not criteria.include_expired:
            matches = [
                evidence
                for evidence in matches
                if not evidence.is_expired
            ]

        if criteria.usable_only:
            matches = [
                evidence
                for evidence in matches
                if evidence.is_usable
            ]

        if criteria.observed_after is not None:
            matches = [
                evidence
                for evidence in matches
                if evidence.observed_at
                >= criteria.observed_after
            ]

        if criteria.observed_before is not None:
            matches = [
                evidence
                for evidence in matches
                if evidence.observed_at
                <= criteria.observed_before
            ]

        return sorted(
            matches,
            key=lambda evidence: (
                evidence.observed_at,
                evidence.evidence_id,
            ),
        )


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Adding evidence
# is easy.
#
# Adding evidence
# without losing
# integrity
#
# is engineering.
#
# Every insertion
# updates:
#
#     primary storage,
#
#     duplicate fingerprints,
#
#     provider indexes,
#
#     indicator indexes,
#
#     condition indexes,
#
#     and status indexes.
#
# That is why
# mutation happens
# through controlled methods.
#
# If every part
# of the application
# changes shared state
# however it wishes...
#
# eventually
# the evidence repository
# stops describing reality.
#
# One source of truth.
#
# Controlled changes.
#
# Explainable results.
#
#                               — Chewbacca
#                                 Chief Wookiee Architect
#
# =============================================================================

    # =========================================================================
    # Collection Statistics
    # =========================================================================

    def inventory(self) -> dict[str, Any]:
        """
        Return a factual inventory of the evidence collection.

        This method reports facts.

        It intentionally avoids drawing conclusions.

        Part II performs interpretation.
        """

        provider_counts = Counter(
            evidence.provider_name
            for evidence in self
        )

        condition_counts = Counter(
            evidence.condition.value
            for evidence in self
        )

        severity_counts = Counter(
            evidence.severity.value
            for evidence in self
        )

        confidence_counts = Counter(
            evidence.confidence.value
            for evidence in self
        )

        return {

            "investigation_id": self.investigation_id,

            "created_at": self.created_at.isoformat(),

            "updated_at": self.updated_at.isoformat(),

            "total_records": len(self),

            "usable_records": len(self.usable()),

            "expired_records": len(self.expired()),

            "provider_count": len(provider_counts),

            "providers": dict(provider_counts),

            "conditions": dict(condition_counts),

            "reported_severities": dict(severity_counts),

            "reported_confidences": dict(confidence_counts),

        }

    # =========================================================================
    # Provenance
    # =========================================================================

    def provider_names(self) -> set[str]:
        """
        Return every provider represented within
        the investigation.
        """

        return {

            evidence.provider_name

            for evidence in self

        }

    def provider_count(self) -> int:
        """
        Return the number of unique providers.
        """

        return len(self.provider_names())

    def provenance_summary(self) -> dict[str, Any]:
        """
        Summarize where evidence originated.

        Provenance answers:

            "Where did this evidence come from?"

        It intentionally avoids calculating confidence.

        Confidence belongs to Part II.
        """

        return {

            "provider_count": self.provider_count(),

            "providers": sorted(
                self.provider_names()
            ),

            "provider_status": dict(

                Counter(

                    evidence.provider_status.value

                    for evidence in self

                )

            ),

            "provider_trust": dict(

                Counter(

                    evidence.provider_trust.value

                    for evidence in self

                )

            ),

            "indicator_sources": dict(

                Counter(

                    evidence.indicator_source.value

                    for evidence in self

                )

            ),

        }

    # =========================================================================
    # Conflict Detection
    # =========================================================================

    def find_severity_conflicts(
        self,
    ) -> list[EvidenceConflict]:
        """
        Detect conflicting severity observations.

        The aggregator reports disagreement.

        It does not decide which provider is correct.
        """

        grouped = defaultdict(list)

        for evidence in self.usable():

            grouped[
                evidence.indicator_value
            ].append(evidence)

        conflicts = []

        for indicator, records in grouped.items():

            severities = {

                record.severity.value

                for record in records

                if record.severity != ThreatSeverity.UNKNOWN

            }

            if len(severities) <= 1:
                continue

            conflicts.append(

                EvidenceConflict(

                    indicator_value=indicator,

                    field_name="severity",

                    observed_values=tuple(

                        sorted(severities)

                    ),

                    evidence_ids=tuple(

                        record.evidence_id

                        for record in records

                    ),

                )

            )

        return conflicts

    # =========================================================================
    # Snapshots
    # =========================================================================

    def snapshot(
        self,
    ) -> EvidenceSnapshot:
        """
        Freeze the investigation.

        Snapshots provide deterministic input
        to Part II.

        Evidence may continue changing after
        the snapshot has been created.

        The snapshot does not.
        """

        return EvidenceSnapshot(

            investigation_id=self.investigation_id,

            created_at=utc_now(),

            evidence=tuple(

                sorted(

                    self.all(),

                    key=lambda evidence: (

                        evidence.observed_at,

                        evidence.evidence_id,

                    ),

                )

            ),

            inventory=self.inventory(),

            provenance=self.provenance_summary(),

            conflicts=tuple(

                self.find_severity_conflicts()

            ),

        )

    # =========================================================================
    # Integrity Validation
    # =========================================================================

    def validate_integrity(
        self,
    ) -> list[str]:
        """
        Validate the internal consistency of the repository.

        Returns

            Empty list

        if no problems are discovered.
        """

        problems = []

        for evidence_id, evidence in self._evidence.items():

            provider_key = evidence.provider_name.casefold()

            if evidence_id not in self._provider_index.get(
                provider_key,
                set(),
            ):

                problems.append(

                    f"{evidence_id}: missing provider index"

                )

            indicator_key = (

                evidence.indicator_type,

                evidence.indicator_value.casefold(),

            )

            if evidence_id not in self._indicator_index.get(
                indicator_key,
                set(),
            ):

                problems.append(

                    f"{evidence_id}: missing indicator index"

                )

            if evidence_id not in self._condition_index.get(
                evidence.condition,
                set(),
            ):

                problems.append(

                    f"{evidence_id}: missing condition index"

                )

        return sorted(problems)

    # =========================================================================
    # Serialization
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the complete repository.

        This representation is suitable for:

            • JSON

            • DynamoDB

            • S3

            • EventBridge

            • API responses
        """

        return {

            "inventory": self.inventory(),

            "provenance": self.provenance_summary(),

            "evidence": [

                evidence.to_dict()

                for evidence in self

            ],

        }


# =============================================================================
#
# Chewbacca's Final Thoughts 🐾
#
# If you've reached this point...
#
# congratulations.
#
# You've just built
#
# something many engineers
#
# never think about.
#
# Before algorithms...
#
# comes organization.
#
# Before intelligence...
#
# comes structure.
#
# Before conclusions...
#
# comes evidence.
#
# EvidenceAggregator
#
# doesn't perform
# threat analysis.
#
# It performs
#
# something equally important.
#
# It preserves truth.
#
# Future classes
#
# will classify,
# correlate,
# assess,
# report,
# and communicate.
#
# None of those jobs
#
# are possible
#
# without trustworthy evidence.
#
# Never underestimate
#
# the engineer
#
# who quietly builds
#
# solid foundations.
#
# Fancy dashboards
#
# eventually become obsolete.
#
# Well-designed architecture
#
# lasts for years.
#
# If these comments
#
# helped you become
#
# a better engineer...
#
# then one day
#
# leave comments
#
# for someone else.
#
# Software is built
#
# by people.
#
# Great software
#
# is built by engineers
#
# who care about
#
# the next engineer.
#
# May your indexes
# always stay synchronized.
#
# May your evidence
# remain trustworthy.
#
# And may production
#
# always wait
#
# until after
#
# your coffee.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================


# =============================================================================
#
# Part II — Threat Reasoning
#
# =============================================================================
#
# Business Objective
# -----------------------------------------------------------------------------
#
# Part I collected evidence.
#
# Part II transforms that evidence into deterministic security analysis.
#
# Fusion intentionally separates reasoning into four independent stages.
#
#     Evidence Selection
#
#             ↓
#
#     Threat Correlation
#
#             ↓
#
#     Threat Classification
#
#             ↓
#
#     Threat Assessment
#
# Each stage answers one architectural question.
#
# This separation keeps Fusion explainable, testable, and easy to extend.
#
# Unlike many security products, Fusion intentionally avoids "magic scores."
#
# Every recommendation can be traced back to explicit evidence.
#
# =============================================================================

from dataclasses import dataclass, field
from uuid import uuid4

from models.enums import (
    ThreatAssessment,
    ThreatCondition,
    ThreatConfidence,
    ThreatDomain,
    ThreatSeverity,
    ThreatType,
)


# =============================================================================
# Assessment Result
# =============================================================================


@dataclass(slots=True)
class AssessmentResult:
    """
    Represents the deterministic conclusion produced by Fusion.

    AssessmentResult forms the contract between:

        Part II
            Threat Reasoning

    and

        Part III
            Threat Communication

    The object intentionally contains structured data rather than prose.

    Report generation and Bedrock explanations occur later.
    """

    assessment_id: str = field(default_factory=lambda: str(uuid4()))

    threat_type: ThreatType = ThreatType.UNKNOWN

    threat_domain: ThreatDomain = ThreatDomain.UNKNOWN

    conditions: list[ThreatCondition] = field(default_factory=list)

    severity: ThreatSeverity = ThreatSeverity.UNKNOWN

    confidence: ThreatConfidence = ThreatConfidence.UNKNOWN

    assessment: ThreatAssessment = ThreatAssessment.UNKNOWN

    rationale: list[str] = field(default_factory=list)

    supporting_evidence: list[ThreatEvidence] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Evidence Selector
# =============================================================================


class EvidenceSelector:
    """
    Select evidence eligible for deterministic reasoning.

    EvidenceSelector answers one question:

        "Which evidence deserves to participate?"

    Responsibilities
    ----------------

        ✓ Remove expired evidence

        ✓ Remove failed provider results

        ✓ Filter duplicate observations

        ✓ Apply minimum provider trust

        ✓ Group related evidence

    This class deliberately performs no threat analysis.
    """

    def select(
        self,
        aggregator: EvidenceAggregator,
    ) -> list[ThreatEvidence]:
        """
        Return evidence eligible for analysis.
        """

        usable = []

        for evidence in aggregator.usable():

            if evidence.provider_trust == ProviderTrustLevel.UNTRUSTED:
                continue

            usable.append(evidence)

        return usable


# =============================================================================
# Chewbacca's Commentary 🐾
#
# More evidence
#
# does not automatically mean
#
# better evidence.
#
# One verified observation
#
# is often worth more
#
# than twenty stale reports.
#
# Great investigations
#
# begin by deciding
#
# what deserves attention.
#
# =============================================================================


# =============================================================================
# Threat Correlation
# =============================================================================


@dataclass(slots=True)
class CorrelationGroup:
    """
    Represents evidence believed to belong to the same investigation.
    """

    correlation_id: str = field(default_factory=lambda: str(uuid4()))

    evidence: list[ThreatEvidence] = field(default_factory=list)

    rationale: list[str] = field(default_factory=list)


class ThreatCorrelation:
    """
    Correlate observations that appear related.

    ThreatCorrelation answers:

        "Which observations belong together?"

    Correlation identifies relationships.

    Correlation does not determine guilt.
    """

    def correlate(
        self,
        evidence: list[ThreatEvidence],
    ) -> list[CorrelationGroup]:
        """
        Produce correlation groups.

        Sample implementation.

        Students are encouraged to experiment with additional correlation
        strategies.
        """

        groups = []

        #
        # Placeholder implementation.
        #
        # Future labs may correlate by:
        #
        #   • Identity
        #   • Asset
        #   • Repository
        #   • Account
        #   • Time Window
        #   • Provider Agreement
        #

        return groups


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Correlation
#
# explains
#
# relationships.
#
# It does not explain
#
# intent.
#
# Two events
#
# occurring together
#
# may simply have
#
# terrible timing.
#
# Engineers should always
#
# explain
#
# why evidence
#
# was grouped.
#
# =============================================================================


# =============================================================================
# Threat Classifier
# =============================================================================


class ThreatClassifier:
    """
    Translate correlated evidence into the Gen2X threat vocabulary.

    ThreatClassifier answers:

        "What kind of security problem
        best describes this investigation?"
    """

    CONDITION_TYPE_MAP = {

        ThreatCondition.UNUSED_ACCOUNT:
            ThreatType.IDENTITY_EXPOSURE,

        ThreatCondition.UNUSED_TOKEN:
            ThreatType.IDENTITY_EXPOSURE,

        ThreatCondition.TOKEN_EXPOSURE:
            ThreatType.IDENTITY_EXPOSURE,

        ThreatCondition.DEPRECATED_LIBRARY:
            ThreatType.VULNERABILITY_EXPOSURE,

        ThreatCondition.EXPOSED_ENDPOINT:
            ThreatType.MISCONFIGURATION,

    }

    CONDITION_DOMAIN_MAP = {

        ThreatCondition.UNUSED_ACCOUNT:
            ThreatDomain.IDENTITY,

        ThreatCondition.UNUSED_TOKEN:
            ThreatDomain.IDENTITY,

        ThreatCondition.TOKEN_EXPOSURE:
            ThreatDomain.IDENTITY,

        ThreatCondition.DEPRECATED_LIBRARY:
            ThreatDomain.APPLICATION,

        ThreatCondition.EXPOSED_ENDPOINT:
            ThreatDomain.API,

    }

    def classify(
        self,
        group: CorrelationGroup,
    ) -> tuple[ThreatType, ThreatDomain]:
        """
        Return the deterministic threat classification.

        Sample implementation.

        Future labs may extend these mapping tables without changing the
        Fusion architecture.
        """

        return (
            ThreatType.UNKNOWN,
            ThreatDomain.UNKNOWN,
        )


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Classification
#
# gives evidence
#
# a name.
#
# Naming
#
# creates order.
#
# It does not create
#
# certainty.
#
# Classification
#
# is vocabulary.
#
# Assessment
#
# is judgment.
#
# =============================================================================


# =============================================================================
# Threat Assessment Engine
# =============================================================================


class ThreatAssessmentEngine:
    """
    Produce deterministic threat assessments.

    ThreatAssessmentEngine answers:

        • How severe?

        • How confident?

        • What recommendation?
    """

    def assess(
        self,
        group: CorrelationGroup,
    ) -> AssessmentResult:
        """
        Produce the deterministic assessment.

        Sample implementation.

        Future labs may implement organization-specific assessment
        policies here.
        """

        result = AssessmentResult()

        #
        # Example policy.
        #
        # Future assessment matrices may consider:
        #
        #   • Multiple provider agreement
        #   • Provider trust
        #   • Asset criticality
        #   • Internet exposure
        #   • Identity exposure
        #   • Secret exposure
        #   • Known exploitation
        #

        result.severity = ThreatSeverity.UNKNOWN

        result.confidence = ThreatConfidence.UNKNOWN

        result.assessment = ThreatAssessment.UNKNOWN

        return result


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Dashboards
#
# love
#
# one score.
#
# Engineers
#
# shouldn't.
#
# Severity answers:
#
#     "How bad?"
#
# Confidence answers:
#
#     "How sure?"
#
# Assessment answers:
#
#     "What recommendation
#      is justified?"
#
# Three questions.
#
# Three answers.
#
# Keep them separate.
#
# Future-you,
#
# reviewing
# an incident
#
# at 2:17 AM,
#
# will appreciate
# the difference.
#
# =============================================================================

# =============================================================================
#
# Part III — Threat Communication
#
# =============================================================================
#
# Business Objective
# -----------------------------------------------------------------------------
#
# Part I organized evidence.
#
# Part II transformed evidence into deterministic engineering reasoning.
#
# Part III communicates those engineering conclusions without changing them.
#
# Fusion intentionally separates:
#
#     Engineering
#
# from
#
#     Presentation.
#
# Reports,
# dashboards,
# PDFs,
# Markdown,
# Slack notifications,
# Jira tickets,
# ServiceNow incidents,
# and AI-generated explanations
#
# are all communication mechanisms.
#
# None of them should alter the engineering conclusions produced by
# Part II.
#
# -----------------------------------------------------------------------------
#
# Communication Pipeline
#
#             AssessmentResult
#
#                     │
#
#                     ▼
#
#          ThreatSummaryBuilder
#
#                     │
#
#                     ▼
#
#              ThreatSummary
#
#                     │
#
# ────────────────────┼──────────────────────────────────────────────
#
#                     ▼
#
#             NarrativeAdapter
#
#                     │
#
# ────────────────────┼──────────────────────────────────────────────
#
#                     ▼
#
#             SummaryExporter
#
#        ┌────────────┼─────────────┐
#        ▼            ▼             ▼
#
#      JSON        Markdown        PDF
#
#        ▼            ▼             ▼
#
#     Slack        EventBridge     HTML
#
# -----------------------------------------------------------------------------
#
# Architectural Philosophy
#
# Communication should never modify engineering conclusions.
#
# It should only make them easier for humans to understand.
#
# Fusion produces structured understanding.
#
# Exporters determine presentation.
#
# =============================================================================


# =============================================================================
# Threat Summary
# =============================================================================


@dataclass(slots=True)
class ThreatSummary:
    """
    Represents the complete engineering summary produced by Fusion.

    ThreatSummary is the communication contract between Fusion and every
    downstream component.

    Report generators, AI services, dashboards, and notification systems all
    consume this object.

    None of those systems should modify the engineering conclusions.
    """

    summary_id: str = field(default_factory=lambda: str(uuid4()))

    title: str = ""

    executive_summary: str = ""

    assessment: AssessmentResult = field(
        default_factory=AssessmentResult
    )

    findings: list[str] = field(default_factory=list)

    recommendations: list[str] = field(default_factory=list)

    evidence_count: int = 0

    provider_count: int = 0

    generated_at: datetime = field(default_factory=utc_now)

    metadata: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Reports
#
# come in
#
# many formats.
#
# PDFs.
#
# Dashboards.
#
# Slack.
#
# ServiceNow.
#
# Jira.
#
# Email.
#
# Engineers
#
# should never
#
# rewrite
#
# an investigation
#
# simply because
#
# someone requested
#
# another output format.
#
# Build
#
# one
#
# complete summary.
#
# Everything else
#
# becomes formatting.
#
# =============================================================================


# =============================================================================
# Threat Summary Builder
# =============================================================================


class ThreatSummaryBuilder:
    """
    Build a structured ThreatSummary.

    Responsibilities
    ----------------

        ✓ Organize assessment results

        ✓ Summarize findings

        ✓ Generate recommendations

        ✓ Count evidence

        ✓ Preserve engineering reasoning

    Does NOT

        • Generate PDFs

        • Generate Markdown

        • Send Slack notifications

        • Call Bedrock

        • Create Jira tickets
    """

    def build(
        self,
        assessment: AssessmentResult,
    ) -> ThreatSummary:
        """
        Construct the communication model.

        Sample implementation.

        Future labs may enrich this summary using organizational
        requirements while preserving the underlying engineering
        conclusions.
        """

        summary = ThreatSummary()

        summary.assessment = assessment

        summary.title = (
            f"{assessment.threat_type.value} Investigation"
        )

        summary.executive_summary = (
            "Deterministic threat assessment completed."
        )

        summary.findings = list(assessment.rationale)

        summary.recommendations = [
            assessment.assessment.describe()
            if hasattr(assessment.assessment, "describe")
            else assessment.assessment.value
        ]

        summary.evidence_count = len(
            assessment.supporting_evidence
        )

        summary.provider_count = len({
            evidence.provider_name
            for evidence in assessment.supporting_evidence
        })

        return summary


# =============================================================================
# Chewbacca's Commentary 🐾
#
# Fusion
#
# already knows
#
# what happened.
#
# This class
#
# simply prepares
#
# that understanding
#
# for humans.
#
# Communication
#
# should clarify.
#
# Never reinterpret.
#
# =============================================================================


# =============================================================================
# Narrative Adapter
# =============================================================================


class NarrativeAdapter:
    """
    Prepare deterministic engineering results for natural-language
    explanation.

    NarrativeAdapter does not perform analysis.

    It prepares prompts for language models after engineering has
    already reached a conclusion.

    Python determines.

    AI explains.
    """

    def create_prompt(
        self,
        summary: ThreatSummary,
    ) -> str:
        """
        Produce a prompt suitable for an LLM.

        The prompt contains engineering conclusions that should be
        explained rather than reconsidered.
        """

        return f"""
Explain the following engineering assessment.

Threat Type:
    {summary.assessment.threat_type.value}

Threat Domain:
    {summary.assessment.threat_domain.value}

Severity:
    {summary.assessment.severity.value}

Confidence:
    {summary.assessment.confidence.value}

Assessment:
    {summary.assessment.assessment.value}

Key Findings:

{chr(10).join(f'- {finding}' for finding in summary.findings)}

Produce an executive summary suitable for a security manager.

Do not modify the engineering conclusions.
"""


# =============================================================================
# Chewbacca's Commentary 🐾
#
# AI
#
# is an excellent
#
# communicator.
#
# It should never
#
# become
#
# the investigator.
#
# Fusion
#
# reaches
#
# the conclusion.
#
# AI
#
# explains
#
# the conclusion.
#
# That's assistance.
#
# Not delegation.
#
# =============================================================================


# =============================================================================
# Summary Exporter
# =============================================================================


class SummaryExporter:
    """
    Base class for all communication exporters.

    Exporters change presentation.

    They never change engineering meaning.

    Future implementations may include:

        • JSON

        • Markdown

        • PDF

        • HTML

        • Slack

        • EventBridge

        • ServiceNow

        • Jira

        • Teams

    Fusion remains completely independent from those implementations.
    """

    def export(
        self,
        summary: ThreatSummary,
    ) -> Any:
        """
        Export a ThreatSummary.

        Derived classes implement the desired presentation format.
        """

        raise NotImplementedError


# =============================================================================
#
# Architect's Reflection
#
# Fusion is not a reporting engine.
#
# Fusion is not an AI agent.
#
# Fusion is an engineering reasoning engine.
#
# Providers observe.
#
# Fusion understands.
#
# Reports explain.
#
# Engineers decide.
#
# Every stage exists to preserve engineering integrity while making
# complex security investigations easier to understand.
#
# Communication should improve understanding.
#
# It should never change truth.
#
# The platform recommends.
#
# Accountability remains human.
#
#                              — Chewbacca
#                                Chief Wookiee Architect
#
# =============================================================================
