from checker.report import render_html, write_reports


def _site(study, site_id):
    return next(site for site in study.sites if site.site_id == site_id)


def test_critical_finding_caps_the_site_and_a_late_filing_does_not(study):
    missing = _site(study, "101")
    assert missing.raw_completeness > 49
    assert missing.readiness == 49
    assert missing.capped is True

    late_irb = _site(study, "103")
    assert late_irb.raw_completeness == 100
    assert late_irb.readiness == 100
    assert late_irb.capped is False

    expiring = _site(study, "106")
    assert expiring.readiness == 100
    assert expiring.capped is False


def test_study_and_country_scores_use_capped_site_scores(study):
    assert study.study_readiness == sum(site.readiness for site in study.sites) / len(study.sites)
    united_states = next(country for country in study.countries if country.country == "United States")
    us_sites = [site for site in study.sites if site.country == "United States"]
    assert united_states.readiness == sum(site.readiness for site in us_sites) / len(us_sites)
    assert study.sites_with_critical == 6
    assert study.critical_count == 6
    assert study.major_count == 4


def test_zone_score_stays_raw(study):
    testing = next(zone for zone in study.zones if zone.zone.startswith("08"))
    assert testing.due == 24
    assert testing.satisfied == 23
    assert testing.critical == 1
    assert testing.major == 1


def test_html_report_is_self_contained(rules, study, tmp_path):
    page = render_html(rules, study, rules.as_of)
    lowered = page.lower()
    assert "<script" not in lowered
    assert "http://" not in lowered
    assert "https://" not in lowered
    assert "Site 101 – Riverside Research Center" in page
    assert 'style="width:49.0%"' in page
    paths = write_reports(rules, study, rules.as_of, tmp_path)
    assert paths["findings"].exists()
    assert paths["summary"].exists()
    assert paths["html"].exists()
