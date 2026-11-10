from datetime import date, timedelta

from checker.findings import IndexRow, Site, evaluate
from checker.rules import ArtifactRule, Ruleset

AS_OF = date(2026, 11, 9)


def _rules() -> Ruleset:
    return Ruleset(
        study_id="SYNTH-PH3-001",
        compound="EX-100",
        protocol="EXAMPLE-001",
        as_of=AS_OF,
        expiry_soon_days=60,
        critical_score_cap=49,
        artifacts=(
            ArtifactRule("pi_cv", "05 Site Management", "PI CV", "site_activation", True, None, None),
            ArtifactRule(
                "ip_return",
                "06 IP",
                "IP return and destruction",
                "close_out",
                False,
                None,
                None,
            ),
        ),
    )


def _site() -> Site:
    return Site(
        study_id="SYNTH-PH3-001",
        country="United States",
        site_id="201",
        site_name="Site 201 – Example Clinic",
        investigator="Dr. A. Example",
        milestones={
            "site_activation": date(2026, 6, 1),
            "ongoing": date(2026, 9, 1),
            "close_out": date(2027, 3, 1),
        },
    )


def _row(expiry: date | None, status: str = "Final", artifact: str = "PI CV") -> IndexRow:
    return IndexRow(
        study_id="SYNTH-PH3-001",
        country="United States",
        site_id="201",
        zone="05 Site Management",
        artifact=artifact,
        document_name="synthetic.pdf",
        version="1.0",
        effective_date=date(2026, 5, 15),
        expiry_date=expiry,
        status=status,
        filed_date=date(2026, 5, 20),
    )


def _only_finding(expiry, status="Final"):
    evaluation = evaluate(_rules(), [_site()], [_row(expiry, status)], AS_OF)[0]
    return evaluation.findings, evaluation


def test_sixty_one_days_out_is_clean():
    findings, evaluation = _only_finding(AS_OF + timedelta(days=61))
    assert findings == ()
    assert evaluation.satisfied == 1


def test_sixty_days_out_is_expiring_soon_and_still_complete():
    findings, evaluation = _only_finding(AS_OF + timedelta(days=60))
    assert len(findings) == 1
    assert findings[0].severity == "Major"
    assert findings[0].reason == "Expiring Soon"
    assert findings[0].days_to_expiry == 60
    assert evaluation.satisfied == 1


def test_expiring_today_is_flagged_and_still_complete():
    findings, evaluation = _only_finding(AS_OF)
    assert findings[0].reason == "Expiring Soon"
    assert findings[0].days_to_expiry == 0
    assert evaluation.satisfied == 1


def test_expired_yesterday_is_critical_and_not_expiring_soon():
    findings, evaluation = _only_finding(AS_OF - timedelta(days=1))
    assert len(findings) == 1
    assert findings[0].severity == "Critical"
    assert findings[0].reason == "Expired"
    assert findings[0].reason != "Expiring Soon"
    assert findings[0].days_overdue == 1
    assert findings[0].days_to_expiry is None
    assert evaluation.satisfied == 0


def test_future_close_out_artifact_is_silent_even_if_missing():
    evaluation = evaluate(_rules(), [_site()], [], AS_OF)[0]
    assert all(item.artifact != "IP return and destruction" for item in evaluation.findings)
    assert evaluation.due == 1
    assert evaluation.findings[0].artifact == "PI CV"
    assert evaluation.findings[0].reason == "Missing"
