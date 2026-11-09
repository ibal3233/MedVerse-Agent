from pathlib import Path

from medverse.knowledge_base.kb import PolicyKnowledgeBase

ROOT = Path(__file__).resolve().parents[1]
SEED = (
    ROOT / "data" / "policy" / "seed"
    / "policy_seed_records.json"
)

def kb():
    return PolicyKnowledgeBase(SEED)

def test_hospital_retrieves_medical_service_act():
    hits = kb().retrieve(
        "hospital_agent",
        "patient medical records access disclosure healthcare provider",
        top_k=1,
    )
    assert hits[0].chunk_id == "KR-MSA-ART21-ACCESS-001"

def test_cyber_retrieves_security_standard():
    hits = kb().retrieve(
        "cyber_network_agent",
        "personal information security safeguards access logs integrity",
        top_k=1,
    )
    assert hits[0].chunk_id == "KR-PIPC-SAFE-2026-001"

def test_access_partition_blocks_cross_policy():
    assert all(
        r["document_id"] != "KR_PIPC_SECURITY_MEASURES_2026"
        for r in kb().records_for_agent("hospital_agent")
    )
