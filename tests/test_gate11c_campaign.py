from pathlib import Path
import json
import pytest

from medverse.experiments.institutional_campaign import (
    InstitutionalCampaignRunner,
)

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "data" / "experiments" / "gate11c_s2_s4_variants.json"

@pytest.fixture(scope="module")
def runner():
    return InstitutionalCampaignRunner(ROOT)

def variants():
    return json.loads(SPEC.read_text(encoding="utf-8"))["variants"]

def test_three_variants_defined():
    assert len(variants()) == 3

def test_medverse_matches_expected_states(runner):
    for v in variants():
        s = runner.load_scenario(v["scenario_file"])
        r = runner.run_medverse(s, v)
        assert r["coordination_state"] == v["expected_coordination_state"]
        assert r["human_review_required"] == v["expected_human_review"]

def test_medverse_no_leakage(runner):
    for v in variants():
        s = runner.load_scenario(v["scenario_file"])
        r = runner.run_medverse(s, v)
        assert r["ILR"] == 0.0

def test_policy_grounding_not_fabricated(runner):
    for v in variants():
        s = runner.load_scenario(v["scenario_file"])
        r = runner.run_medverse(s, v)
        assert r["PGA"] is None
