from pathlib import Path

import pytest

from checker.findings import evaluate, load_index, load_sites
from checker.rules import load_rules
from checker.scoring import score_study

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def rules():
    return load_rules(ROOT / "config" / "expected_artifacts.yaml")


@pytest.fixture(scope="session")
def study(rules):
    sites = load_sites(ROOT / "data" / "site_milestones.csv")
    rows = load_index(ROOT / "data" / "etmf_index.csv")
    evaluations = evaluate(rules, sites, rows, rules.as_of)
    return score_study(evaluations, rules.critical_score_cap)
