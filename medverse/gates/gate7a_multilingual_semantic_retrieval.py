from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.knowledge_base.semantic_kb import (
    MultilingualPolicyKnowledgeBase,
    MODEL_NAME,
)

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate7a"
OUT.mkdir(parents=True, exist_ok=True)

SEED = (
    ROOT / "data" / "policy" / "seed"
    / "policy_seed_records.json"
)
QUERIES = (
    ROOT / "data" / "policy" / "seed"
    / "gate7a_queries.json"
)

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 7A")
    print(" Multilingual Semantic Retrieval")
    print("========================================\n")

    qset = json.loads(
        QUERIES.read_text(encoding="utf-8")
    )

    try:
        kb = MultilingualPolicyKnowledgeBase(
            SEED,
            model_name=qset["model_name"],
        )
        kb.load_model()
    except Exception as exc:
        status = {
            "gate": "GATE_7A_MULTILINGUAL_SEMANTIC_RETRIEVAL",
            "status": "HOLD",
            "reason": str(exc),
            "required_model": MODEL_NAME,
            "required_package": "sentence-transformers",
        }
        (OUT / "gate7a_status.json").write_text(
            json.dumps(status, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2, ensure_ascii=False))
        print(
            "\nGate 7A is on HOLD until the embedding dependency/model "
            "is available. This is not a scientific FAIL."
        )
        return

    checks = []
    rows = []

    # Multilingual schema / provenance
    checks.append(check(
        "kb_version",
        kb.kb_version == "0.2",
        kb.kb_version,
        "0.2",
    ))

    checks.append(check(
        "all_records_have_korean_retrieval_descriptors",
        all(
            bool(r["title_ko"])
            and bool(r["retrieval_text_ko"])
            for r in kb.records
        ),
        True,
        True,
    ))

    checks.append(check(
        "translation_provenance_explicit",
        all(
            "paraphrase" in r["translation_status"].lower()
            for r in kb.records
        ),
        [r["translation_status"] for r in kb.records],
        "all explicitly labeled as paraphrase",
    ))

    # Retrieval correctness for Korean and English queries
    results = {}

    for q in qset["queries"]:
        hits = kb.retrieve(
            q["agent_id"],
            q["query"],
            top_k=3,
        )
        results[q["query_id"]] = hits

        top = hits[0] if hits else None
        top_chunk = top.chunk_id if top else None

        checks.append(check(
            f"{q['query_id']}_top1",
            top_chunk == q["expected_top_chunk"],
            top_chunk,
            q["expected_top_chunk"],
        ))

        checks.append(check(
            f"{q['query_id']}_provenance",
            top is not None
            and bool(top.official_url)
            and bool(top.effective_date)
            and bool(top.article)
            and bool(top.authority)
            and "paraphrase" in top.translation_status.lower(),
            top.to_dict() if top else None,
            "complete provenance and translation label",
        ))

        for rank, hit in enumerate(hits, start=1):
            rows.append({
                "query_id": q["query_id"],
                "agent_id": q["agent_id"],
                "language": q["language"],
                "query": q["query"],
                "rank": rank,
                "chunk_id": hit.chunk_id,
                "score": hit.score,
                "official_url": hit.official_url,
                "effective_date": hit.effective_date,
                "translation_status": hit.translation_status,
            })

    # Cross-lingual agreement:
    # Korean and English versions of the same institutional question
    # must retrieve the same expected chunk at rank 1.
    h_ko = results["Q1_HOSPITAL_KO"][0].chunk_id
    h_en = results["Q2_HOSPITAL_EN"][0].chunk_id
    c_ko = results["Q3_CYBER_KO"][0].chunk_id
    c_en = results["Q4_CYBER_EN"][0].chunk_id

    checks.append(check(
        "hospital_cross_lingual_top1_agreement",
        h_ko == h_en == "KR-MSA-ART21-ACCESS-001",
        {"ko": h_ko, "en": h_en},
        "KR-MSA-ART21-ACCESS-001",
    ))

    checks.append(check(
        "cyber_cross_lingual_top1_agreement",
        c_ko == c_en == "KR-PIPC-SAFE-2026-001",
        {"ko": c_ko, "en": c_en},
        "KR-PIPC-SAFE-2026-001",
    ))

    # Policy partition non-leakage under semantic retrieval
    h_wrong = kb.retrieve(
        "hospital_agent",
        "개인정보 접근통제 접속기록 보안 무결성",
        top_k=3,
    )
    checks.append(check(
        "semantic_hospital_partition_blocks_cyber_policy",
        all(
            h.chunk_id != "KR-PIPC-SAFE-2026-001"
            for h in h_wrong
        ),
        [h.chunk_id for h in h_wrong],
        "cyber-only policy absent",
    ))

    c_wrong = kb.retrieve(
        "cyber_network_agent",
        "환자 진료기록 열람과 사본 발급",
        top_k=3,
    )
    checks.append(check(
        "semantic_cyber_partition_blocks_hospital_policy",
        all(
            h.chunk_id != "KR-MSA-ART21-ACCESS-001"
            for h in c_wrong
        ),
        [h.chunk_id for h in c_wrong],
        "hospital-only policy absent",
    ))

    # Deterministic ranking replay (allow tiny floating tolerance only).
    replay_ok = True
    replay_details = []

    for q in qset["queries"]:
        a = kb.retrieve(q["agent_id"], q["query"], top_k=3)
        b = kb.retrieve(q["agent_id"], q["query"], top_k=3)

        same_ids = [x.chunk_id for x in a] == [x.chunk_id for x in b]
        max_delta = max(
            [abs(x.score - y.score) for x, y in zip(a, b)] or [0.0]
        )
        stable = same_ids and max_delta <= 1e-7

        replay_ok = replay_ok and stable
        replay_details.append({
            "query_id": q["query_id"],
            "same_ids": same_ids,
            "max_score_delta": max_delta,
        })

    checks.append(check(
        "semantic_retrieval_replay_stable",
        replay_ok,
        replay_details,
        "same ranking and score delta <= 1e-7",
    ))

    with (OUT / "gate7a_semantic_retrieval_trace.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query_id",
                "agent_id",
                "language",
                "query",
                "rank",
                "chunk_id",
                "score",
                "official_url",
                "effective_date",
                "translation_status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with (OUT / "gate7a_checks.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "check",
                "status",
                "observed",
                "expected",
            ],
        )
        writer.writeheader()
        writer.writerows(checks)

    passed = sum(
        c["status"] == "PASS"
        for c in checks
    )
    total = len(checks)
    gate_pass = passed == total

    status = {
        "gate": "GATE_7A_MULTILINGUAL_SEMANTIC_RETRIEVAL",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "kb_version": kb.kb_version,
        "model_name": kb.model_name,
        "queries": len(qset["queries"]),
    }

    (OUT / "gate7a_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2, ensure_ascii=False))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 7A FAILED. Diagnose language/ranking/access behavior "
            "before adding LLM policy reasoning."
        )

    print(
        "\nFULL GATE 7A PASS — eligible to proceed to Gate 7B."
    )

if __name__ == "__main__":
    main()
