"""Write findings.csv, summary.json, and a self-contained HTML report."""

from __future__ import annotations

import csv
import html
import io
import json
from datetime import date
from pathlib import Path

from checker.rules import Ruleset
from checker.scoring import StudyScore

FINDING_COLUMNS = (
    "severity",
    "reason",
    "site_id",
    "site_name",
    "country",
    "zone",
    "artifact",
    "days_overdue",
    "days_to_expiry",
)


def write_reports(rules: Ruleset, score: StudyScore, as_of: date, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    findings_path = out_dir / "findings.csv"
    summary_path = out_dir / "summary.json"
    html_path = out_dir / "readiness_report.html"
    findings_path.write_text(_findings_csv(score), encoding="utf-8")
    summary_path.write_text(json.dumps(summary_payload(rules, score, as_of), indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(rules, score, as_of), encoding="utf-8")
    return {"findings": findings_path, "summary": summary_path, "html": html_path}


def summary_payload(rules: Ruleset, score: StudyScore, as_of: date) -> dict:
    return {
        "study_id": rules.study_id,
        "compound": rules.compound,
        "protocol": rules.protocol,
        "as_of": as_of.isoformat(),
        "expiry_soon_days": rules.expiry_soon_days,
        "critical_score_cap": rules.critical_score_cap,
        "study_readiness": _one_decimal(score.study_readiness),
        "sites_with_critical": score.sites_with_critical,
        "finding_counts": {"Critical": score.critical_count, "Major": score.major_count},
        "countries": [
            {
                "country": country.country,
                "readiness": _one_decimal(country.readiness),
                "sites": country.sites,
            }
            for country in score.countries
        ],
        "zones": [
            {
                "zone": zone.zone,
                "due": zone.due,
                "satisfied": zone.satisfied,
                "completeness": _one_decimal(zone.completeness),
                "critical": zone.critical,
                "major": zone.major,
            }
            for zone in score.zones
        ],
        "sites": [
            {
                "site_id": site.site_id,
                "site_name": site.site_name,
                "country": site.country,
                "investigator": site.investigator,
                "due": site.due,
                "satisfied": site.satisfied,
                "raw_completeness": _one_decimal(site.raw_completeness),
                "readiness": _one_decimal(site.readiness),
                "capped": site.capped,
            }
            for site in score.sites
        ],
    }


def render_html(rules: Ruleset, score: StudyScore, as_of: date) -> str:
    """One HTML file. CSS is inline. There is no script and no external asset."""
    site_rows = "\n".join(_site_row(site) for site in score.sites)
    country_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(country.country)}</td>"
        f"<td>{country.sites}</td>"
        f"<td>{_one_decimal(country.readiness):.1f}</td>"
        "</tr>"
        for country in score.countries
    )
    zone_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(zone.zone)}</td>"
        f"<td>{zone.satisfied}/{zone.due}</td>"
        f"<td>{_one_decimal(zone.completeness):.1f}</td>"
        f"<td>{zone.critical}</td>"
        f"<td>{zone.major}</td>"
        "</tr>"
        for zone in score.zones
    )
    finding_rows = "\n".join(_finding_row(finding) for finding in _all_findings(score))
    if not finding_rows:
        finding_rows = '<tr><td colspan="7">No findings.</td></tr>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>eTMF readiness {html.escape(rules.study_id)}</title>
<style>
body {{ margin: 0; font-family: "Segoe UI", Helvetica, Arial, sans-serif; color: #1c2833; background: #f4f7f8; }}
header {{ background: #1f4e79; color: #fff; padding: 28px 32px; }}
header p {{ margin: 6px 0 0; color: #d6e2ee; }}
main {{ padding: 24px 32px 48px; max-width: 1100px; }}
.score {{ font-size: 42px; font-weight: 700; margin: 0; }}
.note {{ color: #3d4f5f; }}
section {{ margin-top: 28px; }}
h2 {{ font-size: 18px; margin-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; }}
th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid #d9e2ec; vertical-align: top; }}
th {{ background: #e8eef3; font-weight: 600; }}
.track {{ background: #d9e2ec; height: 12px; width: 140px; }}
.fill {{ background: #1f4e79; height: 12px; }}
.fill.capped {{ background: #9b2335; }}
.critical {{ color: #9b2335; font-weight: 700; }}
.major {{ color: #8a5a00; font-weight: 700; }}
</style>
</head>
<body>
<header>
<h1>eTMF readiness</h1>
<p>{html.escape(rules.study_id)} · {html.escape(rules.protocol)} · compound {html.escape(rules.compound)}</p>
<p>As of {as_of.isoformat()}. Synthetic data only. This report is not a validated record.</p>
</header>
<main>
<p class="score">{_one_decimal(score.study_readiness):.1f}</p>
<p class="note">Study readiness is the average of the site scores. A site with a critical finding cannot score above {rules.critical_score_cap}. Documents expiring within {rules.expiry_soon_days} days are marked Expiring Soon and still count as present.</p>
<section>
<h2>By country</h2>
<table>
<thead><tr><th>Country</th><th>Sites</th><th>Readiness</th></tr></thead>
<tbody>
{country_rows}
</tbody>
</table>
</section>
<section>
<h2>By zone</h2>
<table>
<thead><tr><th>Zone</th><th>Satisfied</th><th>Completeness</th><th>Critical</th><th>Major</th></tr></thead>
<tbody>
{zone_rows}
</tbody>
</table>
</section>
<section>
<h2>By site</h2>
<table>
<thead><tr><th>Site</th><th>Country</th><th>Investigator</th><th>Complete</th><th>Readiness</th></tr></thead>
<tbody>
{site_rows}
</tbody>
</table>
</section>
<section>
<h2>Findings</h2>
<table>
<thead><tr><th>Severity</th><th>Reason</th><th>Site</th><th>Artifact</th><th>Zone</th><th>Days overdue</th><th>Days to expiry</th></tr></thead>
<tbody>
{finding_rows}
</tbody>
</table>
</section>
</main>
</body>
</html>
"""


def _findings_csv(score: StudyScore) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FINDING_COLUMNS, lineterminator="\n")
    writer.writeheader()
    for finding in _all_findings(score):
        writer.writerow(
            {
                "severity": finding.severity,
                "reason": finding.reason,
                "site_id": finding.site_id,
                "site_name": finding.site_name,
                "country": finding.country,
                "zone": finding.zone,
                "artifact": finding.artifact,
                "days_overdue": "" if finding.days_overdue is None else finding.days_overdue,
                "days_to_expiry": "" if finding.days_to_expiry is None else finding.days_to_expiry,
            }
        )
    return buffer.getvalue()


def _all_findings(score: StudyScore):
    rank = {"Critical": 0, "Major": 1}
    findings = [finding for site in score.sites for finding in site.findings]
    return sorted(findings, key=lambda item: (rank.get(item.severity, 9), int(item.site_id), item.artifact))


def _site_row(site) -> str:
    css = "fill capped" if site.capped else "fill"
    width = f"{_one_decimal(site.readiness):.1f}"
    label = html.escape(f"{site.site_name} readiness {width} percent")
    return (
        "<tr>"
        f"<td>{html.escape(site.site_name)}</td>"
        f"<td>{html.escape(site.country)}</td>"
        f"<td>{html.escape(site.investigator)}</td>"
        f"<td>{site.satisfied}/{site.due}</td>"
        "<td>"
        f'<div class="track" role="img" aria-label="{label}">'
        f'<div class="{css}" style="width:{width}%"></div>'
        "</div>"
        f"<div>{width}</div>"
        "</td>"
        "</tr>"
    )


def _finding_row(finding) -> str:
    css = "critical" if finding.severity == "Critical" else "major"
    overdue = "" if finding.days_overdue is None else str(finding.days_overdue)
    remaining = "" if finding.days_to_expiry is None else str(finding.days_to_expiry)
    return (
        "<tr>"
        f'<td class="{css}">{html.escape(finding.severity)}</td>'
        f"<td>{html.escape(finding.reason)}</td>"
        f"<td>{html.escape(finding.site_name)}</td>"
        f"<td>{html.escape(finding.artifact)}</td>"
        f"<td>{html.escape(finding.zone)}</td>"
        f"<td>{overdue}</td>"
        f"<td>{remaining}</td>"
        "</tr>"
    )


def _one_decimal(value: float) -> float:
    return round(value + 1e-9, 1)
