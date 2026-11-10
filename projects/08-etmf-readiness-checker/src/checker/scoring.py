"""Roll site findings into readiness scores.

A critical finding caps that site. Country and study scores are the mean of the
capped site scores, so the cap is still visible after the roll-up. Zone scores
stay raw: they show where the missing documents sit.
"""

from __future__ import annotations

from dataclasses import dataclass

from checker.findings import SiteEvaluation


@dataclass(frozen=True)
class ScoredSite:
    site_id: str
    site_name: str
    country: str
    investigator: str
    due: int
    satisfied: int
    raw_completeness: float
    readiness: float
    capped: bool
    findings: tuple


@dataclass(frozen=True)
class CountryScore:
    country: str
    readiness: float
    sites: int


@dataclass(frozen=True)
class ZoneScore:
    zone: str
    due: int
    satisfied: int
    completeness: float
    critical: int
    major: int


@dataclass(frozen=True)
class StudyScore:
    study_readiness: float
    sites: tuple[ScoredSite, ...]
    countries: tuple[CountryScore, ...]
    zones: tuple[ZoneScore, ...]
    critical_count: int
    major_count: int
    sites_with_critical: int


def score_study(evaluations: list[SiteEvaluation], critical_score_cap: int) -> StudyScore:
    scored = tuple(_score_site(evaluation, critical_score_cap) for evaluation in evaluations)
    study_readiness = sum(site.readiness for site in scored) / len(scored) if scored else 0.0
    return StudyScore(
        study_readiness=study_readiness,
        sites=scored,
        countries=tuple(_countries(scored)),
        zones=tuple(_zones(evaluations)),
        critical_count=sum(1 for site in scored for finding in site.findings if finding.severity == "Critical"),
        major_count=sum(1 for site in scored for finding in site.findings if finding.severity == "Major"),
        sites_with_critical=sum(1 for site in scored if site.capped),
    )


def _score_site(evaluation: SiteEvaluation, cap: int) -> ScoredSite:
    raw = 100.0 * evaluation.satisfied / evaluation.due if evaluation.due else 100.0
    has_critical = any(finding.severity == "Critical" for finding in evaluation.findings)
    readiness = min(raw, float(cap)) if has_critical else raw
    site = evaluation.site
    return ScoredSite(
        site_id=site.site_id,
        site_name=site.site_name,
        country=site.country,
        investigator=site.investigator,
        due=evaluation.due,
        satisfied=evaluation.satisfied,
        raw_completeness=raw,
        readiness=readiness,
        capped=has_critical,
        findings=evaluation.findings,
    )


def _countries(sites: tuple[ScoredSite, ...]) -> list[CountryScore]:
    order: list[str] = []
    for site in sites:
        if site.country not in order:
            order.append(site.country)
    scores = []
    for country in order:
        group = [site for site in sites if site.country == country]
        readiness = sum(site.readiness for site in group) / len(group)
        scores.append(CountryScore(country, readiness, len(group)))
    return scores


def _zones(evaluations: list[SiteEvaluation]) -> list[ZoneScore]:
    order: list[str] = []
    due: dict[str, int] = {}
    satisfied: dict[str, int] = {}
    critical: dict[str, int] = {}
    major: dict[str, int] = {}
    for evaluation in evaluations:
        for outcome in evaluation.outcomes:
            if outcome.zone not in order:
                order.append(outcome.zone)
                due[outcome.zone] = 0
                satisfied[outcome.zone] = 0
                critical[outcome.zone] = 0
                major[outcome.zone] = 0
            due[outcome.zone] += 1
            satisfied[outcome.zone] += int(outcome.satisfied)
        for finding in evaluation.findings:
            if finding.severity == "Critical":
                critical[finding.zone] = critical.get(finding.zone, 0) + 1
            elif finding.severity == "Major":
                major[finding.zone] = major.get(finding.zone, 0) + 1
    scores = []
    for zone in order:
        completeness = 100.0 * satisfied[zone] / due[zone] if due[zone] else 100.0
        scores.append(
            ZoneScore(zone, due[zone], satisfied[zone], completeness, critical[zone], major[zone])
        )
    return scores
