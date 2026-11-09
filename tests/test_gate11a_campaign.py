from pathlib import Path
import json
import pytest

from medverse.experiments.s1_campaign import S1CampaignRunner

ROOT = Path(__file__).resolve().parents[1]
SPEC = (
    ROOT / "data" / "experiments"
    / "gate11a_s1_variants.json"
)

@pytest.fixture(scope="module")
def runner():
    try:
        return S1CampaignRunner(ROOT)
    except Exception as exc:
        pytest.skip(str(exc))

def variants():
    return json.loads(
        SPEC.read_text(encoding="utf-8")
    )["variants"]

def test_all_five_s1_variants_defined():
    assert len(variants()) == 5

def test_medverse_matches_all_s1_expected_states(runner):
    for v in variants():
        result = runner.run_medverse(v)
        assert result["coordination_state"] == v["expected_coordination_state"]
        assert result["human_review_required"] == v["expected_human_review"]

def test_medverse_no_observation_leakage(runner):
    for v in variants():
        result = runner.run_medverse(v)
        assert result["ILR"] == 0.0
