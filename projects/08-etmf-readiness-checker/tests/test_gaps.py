from datetime import date

AS_OF = date(2026, 11, 9)
ACTIVATION = date(2026, 6, 1)

EXPECTED = {
    ("101", "Form FDA 1572", "Critical", "Missing"),
    ("102", "PI CV", "Critical", "Expired"),
    ("103", "IRB/IEC approval letter", "Major", "Filed after site activation"),
    ("104", "Form FDA 1572", "Critical", "Missing"),
    ("105", "GCP training certificate", "Major", "Draft past due"),
    ("106", "Lab certification (CAP/CLIA)", "Major", "Expiring Soon"),
    ("107", "Financial disclosure", "Critical", "Missing"),
    ("108", "Medical license", "Major", "Expiring Soon"),
    ("109", "Medical license", "Critical", "Expired"),
    ("111", "Lab certification (CAP/CLIA)", "Critical", "Expired"),
}


def _findings(study):
    return [finding for site in study.sites for finding in site.findings]


def test_every_seeded_gap_is_found_and_nothing_else(study):
    found = {(item.site_id, item.artifact, item.severity, item.reason) for item in _findings(study)}
    assert found == EXPECTED


def test_seeded_day_counts(study):
    by_key = {(item.site_id, item.artifact): item for item in _findings(study)}
    assert by_key[("101", "Form FDA 1572")].days_overdue == (AS_OF - ACTIVATION).days
    assert by_key[("102", "PI CV")].days_overdue == (AS_OF - date(2026, 8, 1)).days
    assert by_key[("102", "PI CV")].days_to_expiry is None
    assert by_key[("103", "IRB/IEC approval letter")].days_overdue == 14
    assert by_key[("106", "Lab certification (CAP/CLIA)")].days_to_expiry == (date(2026, 12, 1) - AS_OF).days
    assert by_key[("106", "Lab certification (CAP/CLIA)")].days_overdue is None
    assert by_key[("108", "Medical license")].days_to_expiry == (date(2027, 1, 5) - AS_OF).days
    assert by_key[("109", "Medical license")].days_overdue == (AS_OF - date(2026, 7, 15)).days


def test_close_out_documents_are_not_findings(study):
    assert all(item.artifact != "IP return and destruction" for item in _findings(study))
    assert {site.site_id for site in study.sites if not site.findings} >= {"110", "112"}
