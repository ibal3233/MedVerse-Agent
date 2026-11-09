from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.knowledge_base.kb import PolicyKnowledgeBase

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate6"
OUT.mkdir(parents=True, exist_ok=True)

SEED = (
    ROOT / "data" / "policy" / "seed"
    / "policy_seed_records.json"
)
QUERIES = (
    ROOT / "data" / "policy" / "seed"
    / "gate6_queries.json"
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
    print(" MedVerse-Agent — Gate 6")
    print(" Policy KB Ingestion and Retrieval")
    print("========================================\n")

    kb = PolicyKnowledgeBase(SEED)
    qset = json.loads(
        QUERIES.read_text(encoding="utf-8")
    )["queries"]

    checks = []
    retrieval_rows = []

    # Schema/provenance checks
    checks.append(check(
        "kb_record_count",
        len(kb.records) == 2,
        len(kb.records),
        2,
    ))

    checks.append(check(
        "all_sources_have_provenance",
        all(
            r["official_url"].startswith("https://")
            and r["effective_date"]
            and r["authority"]
            and r["article"]
            for r in kb.records
        ),
        True,
        True,
    ))

    checks.append(check(
        "all_seed_records_are_paraphrase_not_full_text",
        all(
            r["full_text_stored"] is False
            and "paraphrase" in r["translation_status"].lower()
            for r in kb.records
        ),
        True,
        True,
    ))

    # Access partition checks
    hospital_records = kb.records_for_agent(
        "hospital_agent"
    )
    cyber_records = kb.records_for_agent(
        "cyber_network_agent"
    )

    checks.append(check(
        "hospital_policy_partition",
        [r["chunk_id"] for r in hospital_records]
        == ["KR-MSA-ART21-ACCESS-001"],
        [r["chunk_id"] for r in hospital_records],
        ["KR-MSA-ART21-ACCESS-001"],
    ))

    checks.append(check(
        "cyber_policy_partition",
        [r["chunk_id"] for r in cyber_records]
        == ["KR-PIPC-SAFE-2026-001"],
        [r["chunk_id"] for r in cyber_records],
        ["KR-PIPC-SAFE-2026-001"],
    ))

    # Retrieval tests
    for q in qset:
        hits = kb.retrieve(
            q["agent_id"],
            q["query"],
            top_k=3,
        )

        top = hits[0] if hits else None
        top_chunk = top.chunk_id if top else None

        checks.append(check(
            f"{q['query_id']}_top1",
            top_chunk == q["expected_top_chunk"],
            top_chunk,
            q["expected_top_chunk"],
        ))

        checks.append(check(
            f"{q['query_id']}_has_provenance",
            top is not None
            and bool(top.official_url)
            and bool(top.effective_date)
            and bool(top.article)
            and bool(top.authority),
            top.to_dict() if top else None,
            "retrieval hit includes source URL, date, article, authority",
        ))

        for rank, hit in enumerate(hits, start=1):
            retrieval_rows.append({
                "query_id": q["query_id"],
                "agent_id": q["agent_id"],
                "query": q["query"],
                "rank": rank,
                "chunk_id": hit.chunk_id,
                "document_id": hit.document_id,
                "score": hit.score,
                "article": hit.article,
                "effective_date": hit.effective_date,
                "official_url": hit.official_url,
                "translation_status": hit.translation_status,
            })

    # Cross-agent leakage probes:
    hospital_wrong = kb.retrieve(
        "hospital_agent",
        "security access logs integrity technical safeguards",
        top_k=3,
    )
    checks.append(check(
        "hospital_cannot_retrieve_cyber_only_policy",
        all(
            h.chunk_id != "KR-PIPC-SAFE-2026-001"
            for h in hospital_wrong
        ),
        [h.chunk_id for h in hospital_wrong],
        "KR-PIPC-SAFE-2026-001 absent",
    ))

    cyber_wrong = kb.retrieve(
        "cyber_network_agent",
        "patient medical record disclosure",
        top_k=3,
    )
    checks.append(check(
        "cyber_cannot_retrieve_hospital_only_policy",
        all(
            h.chunk_id != "KR-MSA-ART21-ACCESS-001"
            for h in cyber_wrong
        ),
        [h.chunk_id for h in cyber_wrong],
        "KR-MSA-ART21-ACCESS-001 absent",
    ))

    # Deterministic retrieval replay
    replay_ok = True
    replay_details = []
    for q in qset:
        a = [
            h.to_dict()
            for h in kb.retrieve(
                q["agent_id"], q["query"], top_k=3
            )
        ]
        b = [
            h.to_dict()
            for h in kb.retrieve(
                q["agent_id"], q["query"], top_k=3
            )
        ]
        same = a == b
        replay_ok = replay_ok and same
        replay_details.append({
            "query_id": q["query_id"],
            "same": same,
        })

    checks.append(check(
        "deterministic_retrieval_replay",
        replay_ok,
        replay_details,
        "all exact match",
    ))

    # Save outputs
    with (OUT / "gate6_retrieval_trace.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query_id",
                "agent_id",
                "query",
                "rank",
                "chunk_id",
                "document_id",
                "score",
                "article",
                "effective_date",
                "official_url",
                "translation_status",
            ],
        )
        writer.writeheader()
        writer.writerows(retrieval_rows)

    with (OUT / "gate6_checks.csv").open(
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
        "gate": "GATE_6_POLICY_KB_INGESTION_RETRIEVAL",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "kb_version": kb.kb_version,
        "record_count": len(kb.records),
        "retrieval_queries": len(qset),
    }

    (OUT / "gate6_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 6 FAILED. Diagnose ingestion/access/retrieval "
            "before adding multilingual embeddings or LLM reasoning."
        )

    print(
        "\nFULL GATE 6 PASS — eligible to proceed to Gate 7."
    )

if __name__ == "__main__":
    main()
