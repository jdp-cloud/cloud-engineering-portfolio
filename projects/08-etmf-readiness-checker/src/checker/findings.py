"""Compare an eTMF index with the artifacts that are due on a given date."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date

from checker.rules import ArtifactRule, Ruleset, applies_to_country, is_due

INDEX_COLUMNS = (
    "study_id",
    "country",
    "site_id",
    "zone",
    "artifact",
    "document_name",
    "version",
    "effective_date",
    "expiry_date",
    "status",
    "filed_date",
)
MILESTONE_COLUMNS = (
    "study_id",
    "country",
    "site_id",
    "site_name",
    "investigator",
    "milestone",
    "milestone_date",
)


@dataclass(frozen=True)
class IndexRow:
    study_id: str
    country: str
    site_id: str
    zone: str
    artifact: str
    document_name: str
    version: str
    effective_date: date | None
    expiry_date: date | None
    status: str
    filed_date: date | None


@dataclass(frozen=True)
class Site:
    study_id: str
    country: str
    site_id: str
    site_name: str
    investigator: str
    milestones: dict[str, date]


@dataclass(frozen=True)
class Finding:
    severity: str
    reason: str
    site_id: str
    site_name: str
    country: str
    zone: str
    artifact: str
    days_overdue: int | None
    days_to_expiry: int | None


@dataclass(frozen=True)
class ArtifactOutcome:
    zone: str
    artifact: str
    satisfied: bool


@dataclass(frozen=True)
class SiteEvaluation:
    site: Site
    due: int
    satisfied: int
    outcomes: tuple[ArtifactOutcome, ...]
    findings: tuple[Finding, ...] = field(default_factory=tuple)


def load_index(path) -> list[IndexRow]:
    return load_index_text(path.read_text(encoding="utf-8"))


def load_index_text(text: str) -> list[IndexRow]:
    return [_index_row(row) for row in _rows(text, INDEX_COLUMNS)]


def load_sites(path) -> list[Site]:
    return load_sites_text(path.read_text(encoding="utf-8"))


def load_sites_text(text: str) -> list[Site]:
    grouped: dict[str, dict] = {}
    for row in _rows(text, MILESTONE_COLUMNS):
        site_id = row["site_id"]
        current = grouped.setdefault(
            site_id,
            {
                "study_id": row["study_id"],
                "country": row["country"],
                "site_id": site_id,
                "site_name": row["site_name"],
                "investigator": row["investigator"],
                "milestones": {},
            },
        )
        current["milestones"][row["milestone"]] = date.fromisoformat(row["milestone_date"])
    sites = [
        Site(
            study_id=item["study_id"],
            country=item["country"],
            site_id=item["site_id"],
            site_name=item["site_name"],
            investigator=item["investigator"],
            milestones=item["milestones"],
        )
        for item in grouped.values()
    ]
    return sorted(sites, key=lambda site: int(site.site_id))


def evaluate(
    rules: Ruleset,
    sites: list[Site],
    rows: list[IndexRow],
    as_of: date,
) -> list[SiteEvaluation]:
    by_key: dict[tuple[str, str], list[IndexRow]] = {}
    for row in rows:
        by_key.setdefault((row.site_id, row.artifact), []).append(row)

    evaluations = []
    for site in sites:
        outcomes: list[ArtifactOutcome] = []
        findings: list[Finding] = []
        for rule in rules.artifacts:
            if not applies_to_country(rule, site.country):
                continue
            if not is_due(rule, site.milestones, as_of):
                continue
            matched = by_key.get((site.site_id, rule.name), [])
            artifact_findings, satisfied = _judge(rule, site, matched, as_of, rules.expiry_soon_days)
            findings.extend(artifact_findings)
            outcomes.append(ArtifactOutcome(rule.zone, rule.name, satisfied))
        evaluations.append(
            SiteEvaluation(
                site=site,
                due=len(outcomes),
                satisfied=sum(1 for outcome in outcomes if outcome.satisfied),
                outcomes=tuple(outcomes),
                findings=tuple(_sort_findings(findings)),
            )
        )
    return evaluations


def _judge(
    rule: ArtifactRule,
    site: Site,
    matched: list[IndexRow],
    as_of: date,
    expiry_soon_days: int,
) -> tuple[list[Finding], bool]:
    chosen = _choose_final(matched, rule, as_of)
    if chosen is None:
        drafts = [row for row in matched if row.status == "Draft"]
        milestone = site.milestones[rule.required_at]
        days_overdue = (as_of - milestone).days
        if drafts:
            return [_finding(site, rule, "Major", "Draft past due", days_overdue, None)], False
        return [_finding(site, rule, "Critical", "Missing", days_overdue, None)], False

    findings: list[Finding] = []
    satisfied = True
    if rule.expires and chosen.expiry_date is not None:
        days_to_expiry = (chosen.expiry_date - as_of).days
        if days_to_expiry < 0:
            findings.append(
                _finding(site, rule, "Critical", "Expired", (as_of - chosen.expiry_date).days, None)
            )
            satisfied = False
        elif days_to_expiry <= expiry_soon_days:
            # Valid today, including a document that expires today.
            # The Monday run uses a later date, so this warning moves on its own.
            findings.append(_finding(site, rule, "Major", "Expiring Soon", None, days_to_expiry))

    if rule.timing_check == "filed_on_or_before_activation" and chosen.filed_date is not None:
        activation = site.milestones["site_activation"]
        if chosen.filed_date > activation:
            days_late = (chosen.filed_date - activation).days
            findings.append(
                _finding(site, rule, "Major", "Filed after site activation", days_late, None)
            )
    return findings, satisfied


def _choose_final(matched: list[IndexRow], rule: ArtifactRule, as_of: date) -> IndexRow | None:
    finals = [row for row in matched if row.status == "Final"]
    if not finals:
        return None

    def sort_key(row: IndexRow):
        expired = bool(rule.expires and row.expiry_date is not None and row.expiry_date < as_of)
        expiry_rank = -(row.expiry_date.toordinal()) if row.expiry_date else 0
        filed_rank = -(row.filed_date.toordinal()) if row.filed_date else 0
        return (expired, expiry_rank, filed_rank)

    return min(finals, key=sort_key)


def _finding(
    site: Site,
    rule: ArtifactRule,
    severity: str,
    reason: str,
    days_overdue: int | None,
    days_to_expiry: int | None,
) -> Finding:
    return Finding(
        severity=severity,
        reason=reason,
        site_id=site.site_id,
        site_name=site.site_name,
        country=site.country,
        zone=rule.zone,
        artifact=rule.name,
        days_overdue=days_overdue,
        days_to_expiry=days_to_expiry,
    )


def _sort_findings(findings: list[Finding]) -> list[Finding]:
    rank = {"Critical": 0, "Major": 1}
    return sorted(findings, key=lambda item: (rank.get(item.severity, 9), item.site_id, item.artifact))


def _rows(text: str, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no header.")
    missing = [column for column in columns if column not in reader.fieldnames]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")
    return list(reader)


def _index_row(row: dict[str, str]) -> IndexRow:
    return IndexRow(
        study_id=row["study_id"],
        country=row["country"],
        site_id=row["site_id"],
        zone=row["zone"],
        artifact=row["artifact"],
        document_name=row["document_name"],
        version=row["version"],
        effective_date=_optional_date(row["effective_date"]),
        expiry_date=_optional_date(row["expiry_date"]),
        status=row["status"],
        filed_date=_optional_date(row["filed_date"]),
    )


def _optional_date(value: str | None) -> date | None:
    if value is None or value.strip() == "":
        return None
    return date.fromisoformat(value.strip())
