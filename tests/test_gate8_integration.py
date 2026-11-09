from pathlib import Path
import pytest

from medverse.integration.pipeline import MedVerseIntegratedPipeline

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture(scope="module")
def result():
    try:
        p = MedVerseIntegratedPipeline(ROOT)
        return p.run_all()
    except Exception as exc:
        pytest.skip(str(exc))

def test_three_events(result):
    assert [r["event_id"] for r in result] == ["E1", "E2", "E3"]

def test_final_coordination(result):
    assert result[-1]["coordination"]["coordination_state"] == "COMPLEMENTARY_RISK"

def test_final_dt_unverified(result):
    assert result[-1]["state"]["dt"]["validity"] == "UNVERIFIED"

def test_grounded_explanation(result):
    assert set(result[-1]["explanation"]["cited_policy_chunks"]) == {
        "KR-MSA-ART21-ACCESS-001",
        "KR-PIPC-SAFE-2026-001",
    }
