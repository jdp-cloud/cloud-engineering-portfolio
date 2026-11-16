"""Load the expected-artifact checklist and decide what is due."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from checker.yaml_subset import loads

MILESTONES = ("site_activation", "ongoing", "close_out")
_TOP_KEYS = {
    "study_id",
    "compound",
    "protocol",
    "as_of",
    "expiry_soon_days",
    "critical_score_cap",
    "artifacts",
}
_ARTIFACT_KEYS = {
    "id",
    "zone",
    "name",
    "required_at",
    "expires",
    "countries",
    "timing_check",
}
_TIMING_CHECKS = {"filed_on_or_before_activation"}


@dataclass(frozen=True)
class ArtifactRule:
    id: str
    zone: str
    name: str
    required_at: str
    expires: bool
    countries: tuple[str, ...] | None
    timing_check: str | None


@dataclass(frozen=True)
class Ruleset:
    study_id: str
    compound: str
    protocol: str
    as_of: date
    expiry_soon_days: int
    critical_score_cap: int
    artifacts: tuple[ArtifactRule, ...]


def load_rules(path: str | Path) -> Ruleset:
    return load_rules_text(Path(path).read_text(encoding="utf-8"))


def load_rules_text(text: str) -> Ruleset:
    data = loads(text)
    if not isinstance(data, dict):
        raise ValueError("The rule file must be a mapping.")
    unknown = set(data) - _TOP_KEYS
    if unknown:
        raise ValueError(f"Unknown rule-file keys: {sorted(unknown)}")
    artifacts = tuple(_artifact(item) for item in data["artifacts"])
    names = [item.name for item in artifacts]
    if len(names) != len(set(names)):
        raise ValueError("Artifact names must be unique. The index joins on the name.")
    return Ruleset(
        study_id=str(data["study_id"]),
        compound=str(data["compound"]),
        protocol=str(data["protocol"]),
        as_of=date.fromisoformat(str(data["as_of"])),
        expiry_soon_days=int(data["expiry_soon_days"]),
        critical_score_cap=int(data["critical_score_cap"]),
        artifacts=artifacts,
    )


def applies_to_country(rule: ArtifactRule, country: str) -> bool:
    if rule.countries is None:
        return True
    return country in rule.countries


def is_due(rule: ArtifactRule, milestone_dates: dict[str, date], as_of: date) -> bool:
    milestone = milestone_dates[rule.required_at]
    return milestone <= as_of


def _artifact(item: dict) -> ArtifactRule:
    if not isinstance(item, dict):
        raise ValueError("Each artifact must be a mapping.")
    unknown = set(item) - _ARTIFACT_KEYS
    if unknown:
        raise ValueError(f"Unknown keys on artifact {item.get('id')}: {sorted(unknown)}")
    required_at = str(item["required_at"])
    if required_at not in MILESTONES:
        raise ValueError(f"Artifact {item.get('id')} has unknown milestone {required_at}.")
    timing = item.get("timing_check")
    if timing is not None and timing not in _TIMING_CHECKS:
        raise ValueError(f"Artifact {item.get('id')} has unknown timing check {timing}.")
    countries = item.get("countries")
    country_tuple = None if not countries else tuple(str(country) for country in countries)
    return ArtifactRule(
        id=str(item["id"]),
        zone=str(item["zone"]),
        name=str(item["name"]),
        required_at=required_at,
        expires=bool(item["expires"]),
        countries=country_tuple,
        timing_check=None if timing is None else str(timing),
    )
