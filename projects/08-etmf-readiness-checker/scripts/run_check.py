"""Run the checker locally and write the three report files.

Example:
  python scripts/run_check.py --as-of 2026-11-09 --out out/
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from checker.findings import evaluate, load_index, load_sites  # noqa: E402
from checker.report import write_reports  # noqa: E402
from checker.rules import load_rules  # noqa: E402
from checker.scoring import score_study  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Check a synthetic eTMF index.")
    parser.add_argument("--index", type=Path, default=ROOT / "data" / "etmf_index.csv")
    parser.add_argument("--rules", type=Path, default=ROOT / "config" / "expected_artifacts.yaml")
    parser.add_argument("--milestones", type=Path, default=ROOT / "data" / "site_milestones.csv")
    parser.add_argument("--as-of", dest="as_of", default=None, help="YYYY-MM-DD. Defaults to the date in the rule file.")
    parser.add_argument("--out", type=Path, default=ROOT / "out")
    args = parser.parse_args()

    rules = load_rules(args.rules)
    as_of = rules.as_of if args.as_of is None else date.fromisoformat(args.as_of)
    score = score_study(
        evaluate(rules, load_sites(args.milestones), load_index(args.index), as_of),
        rules.critical_score_cap,
    )
    paths = write_reports(rules, score, as_of, args.out)
    print(f"Study readiness {score.study_readiness:.1f}")
    print(f"Critical {score.critical_count}  Major {score.major_count}")
    for path in paths.values():
        print(path)


if __name__ == "__main__":
    main()
