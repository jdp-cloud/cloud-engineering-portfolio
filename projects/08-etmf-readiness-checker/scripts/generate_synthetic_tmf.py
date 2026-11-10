"""Write a synthetic eTMF index and the site milestone calendar.

The output is deterministic. Re-running this script reproduces data/etmf_index.csv
and data/site_milestones.csv. Names, sites, and the compound are fictional.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checker.rules import applies_to_country, load_rules  # noqa: E402

EFFECTIVE_DATE = "2026-05-15"
FILED_DATE = "2026-05-20"
HEALTHY_EXPIRY = "2027-06-01"
MILESTONE_DATES = {
    "site_activation": "2026-06-01",
    "ongoing": "2026-09-01",
    "close_out": "2027-03-01",
}

SITES = (
    {"site_id": "101", "site_name": "Site 101 – Riverside Research Center", "country": "United States", "investigator": "Dr. A. Example"},
    {"site_id": "102", "site_name": "Site 102 – Harbor View Clinical", "country": "United States", "investigator": "Dr. B. Example"},
    {"site_id": "103", "site_name": "Site 103 – Lakewood Medical Research", "country": "United States", "investigator": "Dr. C. Example"},
    {"site_id": "104", "site_name": "Site 104 – Summit Clinical Site", "country": "United States", "investigator": "Dr. D. Example"},
    {"site_id": "105", "site_name": "Site 105 – Northbridge Research", "country": "United Kingdom", "investigator": "Dr. E. Example"},
    {"site_id": "106", "site_name": "Site 106 – Kingsford Clinical Unit", "country": "United Kingdom", "investigator": "Dr. F. Example"},
    {"site_id": "107", "site_name": "Site 107 – Meadow Clinical Centre", "country": "United Kingdom", "investigator": "Dr. G. Example"},
    {"site_id": "108", "site_name": "Site 108 – Portside Research", "country": "United Kingdom", "investigator": "Dr. H. Example"},
    {"site_id": "109", "site_name": "Site 109 – Sakura Hills Clinic", "country": "Japan", "investigator": "Dr. I. Example"},
    {"site_id": "110", "site_name": "Site 110 – Bay Clinical Research", "country": "Japan", "investigator": "Dr. J. Example"},
    {"site_id": "111", "site_name": "Site 111 – Cedar Trial Site", "country": "Japan", "investigator": "Dr. K. Example"},
    {"site_id": "112", "site_name": "Site 112 – Maple Investigative Site", "country": "Japan", "investigator": "Dr. L. Example"},
)

# Keys are (site_id, artifact name). These are the only intentional gaps.
GAPS = {
    ("101", "Form FDA 1572"): {"omit": True},
    ("104", "Form FDA 1572"): {"omit": True},
    ("102", "PI CV"): {"expiry_date": "2026-08-01"},
    ("109", "Medical license"): {"expiry_date": "2026-07-15"},
    ("111", "Lab certification (CAP/CLIA)"): {"expiry_date": "2026-09-01"},
    ("107", "Financial disclosure"): {"omit": True},
    ("105", "GCP training certificate"): {"status": "Draft"},
    ("103", "IRB/IEC approval letter"): {"filed_date": "2026-06-15"},
    ("106", "Lab certification (CAP/CLIA)"): {"expiry_date": "2026-12-01"},
    ("108", "Medical license"): {"expiry_date": "2027-01-05"},
}

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


def build_rows(rules):
    index_rows = []
    milestone_rows = []
    seen_gaps = set()
    for site in SITES:
        for milestone, milestone_date in MILESTONE_DATES.items():
            milestone_rows.append(
                {
                    "study_id": rules.study_id,
                    "country": site["country"],
                    "site_id": site["site_id"],
                    "site_name": site["site_name"],
                    "investigator": site["investigator"],
                    "milestone": milestone,
                    "milestone_date": milestone_date,
                }
            )
        for rule in rules.artifacts:
            if not applies_to_country(rule, site["country"]):
                continue
            key = (site["site_id"], rule.name)
            gap = GAPS.get(key, {})
            if key in GAPS:
                seen_gaps.add(key)
            if gap.get("omit"):
                continue
            expiry = ""
            if rule.expires:
                expiry = gap.get("expiry_date", HEALTHY_EXPIRY)
            index_rows.append(
                {
                    "study_id": rules.study_id,
                    "country": site["country"],
                    "site_id": site["site_id"],
                    "zone": rule.zone,
                    "artifact": rule.name,
                    "document_name": f"{rule.name} - {site['site_name']}.pdf",
                    "version": "1.0",
                    "effective_date": EFFECTIVE_DATE,
                    "expiry_date": expiry,
                    "status": gap.get("status", "Final"),
                    "filed_date": gap.get("filed_date", FILED_DATE),
                }
            )
    unused = set(GAPS) - seen_gaps
    if unused:
        raise SystemExit(f"A seeded gap did not match a site and artifact: {sorted(unused)}")
    return index_rows, milestone_rows


def write_study(out_dir: Path, rules_path: Path | None = None) -> None:
    rules = load_rules(rules_path or ROOT / "config" / "expected_artifacts.yaml")
    index_rows, milestone_rows = build_rows(rules)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(out_dir / "etmf_index.csv", INDEX_COLUMNS, index_rows)
    _write_csv(out_dir / "site_milestones.csv", MILESTONE_COLUMNS, milestone_rows)


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    write_study(ROOT / "data")


if __name__ == "__main__":
    main()
