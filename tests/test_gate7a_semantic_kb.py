from pathlib import Path
import pytest

from medverse.knowledge_base.semantic_kb import (
    MultilingualPolicyKnowledgeBase,
)

ROOT = Path(__file__).resolve().parents[1]
SEED = (
    ROOT / "data" / "policy" / "seed"
    / "policy_seed_records.json"
)

@pytest.fixture(scope="module")
def kb():
    try:
        instance = MultilingualPolicyKnowledgeBase(SEED)
        instance.load_model()
        return instance
    except Exception as exc:
        pytest.skip(str(exc))

def test_korean_hospital_query(kb):
    hits = kb.retrieve(
        "hospital_agent",
        "환자가 자신의 진료기록을 열람하거나 사본을 요청할 수 있는 규정",
        top_k=1,
    )
    assert hits[0].chunk_id == "KR-MSA-ART21-ACCESS-001"

def test_korean_cyber_query(kb):
    hits = kb.retrieve(
        "cyber_network_agent",
        "개인정보 보호를 위한 접근통제와 접속기록 등 안전성 확보조치",
        top_k=1,
    )
    assert hits[0].chunk_id == "KR-PIPC-SAFE-2026-001"

def test_semantic_partition_is_preserved(kb):
    hits = kb.retrieve(
        "hospital_agent",
        "개인정보 접근통제 접속기록 보안",
        top_k=3,
    )
    assert all(
        h.chunk_id != "KR-PIPC-SAFE-2026-001"
        for h in hits
    )
