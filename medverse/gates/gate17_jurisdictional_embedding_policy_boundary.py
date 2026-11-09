from __future__ import annotations

from pathlib import Path
import sys, json, csv

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from medverse.knowledge_base.jurisdictional_semantic_kb import (
    JurisdictionAwarePolicyKB, MODEL_NAME
)
from medverse.reasoning.policy_boundary import PolicyBoundaryValidator

OUT = ROOT / "outputs" / "gate17"
OUT.mkdir(parents=True, exist_ok=True)

CORPUS = ROOT / "data/policy/candidate_v0.4/policy_records_v0.4_candidate.json"
QFILE = ROOT / "data/policy/evaluation/gate17_queries.json"
BFILE = ROOT / "data/policy/evaluation/gate17_boundary_cases.json"

FOREIGN_DECOY = {
    "chunk_id": "US-HIPAA-DECOY-001",
    "document_id": "US-HIPAA-DECOY",
    "title": "HIPAA Privacy Rule",
    "title_ko": "HIPAA Privacy Rule",
    "article": "Decoy",
    "jurisdiction": "US",
    "agent_access": ["privacy_agent"],
    "topics": ["patient_record", "privacy", "disclosure", "minimum_necessary"],
    "text_en": (
        "External research partner requests the full patient record for an unspecified purpose "
        "and the request exceeds the minimum necessary data."
    ),
    "retrieval_text_ko": "환자기록 제3자 제공 최소 필요 범위 개인정보 보호",
    "authority": "US decoy for jurisdiction test",
    "source_type": "statute",
    "official_url": "https://example.invalid/us-decoy",
    "retrieval_eligible": True,
    "normative_weight": "decoy",
    "translation_status": "test decoy"
}

def check(name, ok, observed, expected):
    return {
        "check": name,
        "status": "PASS" if ok else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 17")
    print(" Jurisdiction-Aware Policy Embedding")
    print(" and Policy-Boundary Evaluation")
    print("========================================\n")

    registry = json.loads((ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8"))
    g16 = registry.get("promoted_gates", {}).get("GATE_16", {})
    if g16.get("status") != "PASS":
        status = {
            "gate": "GATE_17_JURISDICTIONAL_EMBEDDING_POLICY_BOUNDARY",
            "status": "HOLD",
            "reason": "Gate 16 is not promoted PASS."
        }
        (OUT / "gate17_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
        print(json.dumps(status, indent=2))
        return

    qset = json.loads(QFILE.read_text(encoding="utf-8"))
    bcases = json.loads(BFILE.read_text(encoding="utf-8"))

    try:
        kb = JurisdictionAwarePolicyKB(
            CORPUS,
            deployment_jurisdiction="KR",
            model_name=qset["model_name"],
            extra_records=[FOREIGN_DECOY],
        )
        kb.load_model()
    except Exception as exc:
        status = {
            "gate": "GATE_17_JURISDICTIONAL_EMBEDDING_POLICY_BOUNDARY",
            "status": "HOLD",
            "reason": str(exc),
            "required_model": MODEL_NAME,
            "required_package": "sentence-transformers",
        }
        (OUT / "gate17_status.json").write_text(
            json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(status, indent=2, ensure_ascii=False))
        print("\nDependency/model HOLD — not a scientific FAIL.")
        return

    checks = []
    retrieval_rows = []

    # Corpus eligibility checks
    eligible_all = [
        r for r in kb.records
        if r.get("retrieval_eligible") is True
        and r.get("jurisdiction") == "KR"
    ]
    checks.append(check(
        "press_releases_not_retrievable",
        all(r.get("source_type") != "press_release" for r in eligible_all),
        [r["chunk_id"] for r in eligible_all if r.get("source_type") == "press_release"],
        []
    ))

    # Semantic retrieval benchmark
    retrieval_success = 0
    pair_results = {}
    for q in qset["queries"]:
        hits = kb.retrieve(q["agent_id"], q["query"], top_k=3)
        ids = [h.chunk_id for h in hits]
        success = any(x in ids for x in q["expected_any_top3"])
        retrieval_success += int(success)

        checks.append(check(
            f"{q['query_id']}_expected_policy_in_top3",
            success,
            ids,
            q["expected_any_top3"]
        ))

        checks.append(check(
            f"{q['query_id']}_all_hits_KR_and_authorized",
            all(
                h.jurisdiction == "KR"
                and q["agent_id"] in h.agent_access
                for h in hits
            ),
            [h.to_dict() for h in hits],
            "all hits jurisdiction=KR and agent-authorized"
        ))

        pair_results[q["query_id"]] = ids

        for rank, h in enumerate(hits, 1):
            retrieval_rows.append({
                "query_id": q["query_id"],
                "agent_id": q["agent_id"],
                "language": q["language"],
                "rank": rank,
                "chunk_id": h.chunk_id,
                "score": h.score,
                "jurisdiction": h.jurisdiction,
                "source_type": h.source_type,
                "authority": h.authority,
                "locator": h.locator,
            })

    retrieval_accuracy = retrieval_success / len(qset["queries"])

    checks.append(check(
        "semantic_top3_accuracy_100pct",
        retrieval_accuracy == 1.0,
        retrieval_accuracy,
        1.0
    ))

    # Cross-lingual thematic agreement: both privacy disclosure questions
    # must retrieve at least one common authoritative KR policy in top 3.
    en = set(pair_results["Q1_PRIVACY_EN_DISCLOSURE"])
    ko = set(pair_results["Q2_PRIVACY_KO_DISCLOSURE"])
    common = sorted(en.intersection(ko))
    checks.append(check(
        "privacy_cross_lingual_top3_overlap",
        len(common) >= 1,
        common,
        ">=1 common authoritative KR policy chunk"
    ))

    # Strong wrong-jurisdiction test:
    # US decoy text is deliberately very similar to Q1, but it must be filtered
    # before embedding similarity is calculated.
    decoy_hits = kb.retrieve(
        "privacy_agent",
        FOREIGN_DECOY["text_en"],
        top_k=5,
        jurisdiction="KR"
    )
    decoy_accepted = any(h.chunk_id == "US-HIPAA-DECOY-001" for h in decoy_hits)
    checks.append(check(
        "wrong_jurisdiction_decoy_rejected_before_ranking",
        not decoy_accepted,
        [h.chunk_id for h in decoy_hits],
        "US-HIPAA-DECOY-001 absent"
    ))

    # Agent-access boundary
    cyber_privacy = kb.retrieve(
        "cyber_network_agent",
        "purpose limitation full patient record disclosure to external research partner",
        top_k=5
    )
    privacy_only = {
        "KR-PIPA-ART18-PURPOSE-001",
        "KR-PIPA-ART17-DISCLOSURE-001"
    }
    leaked = [h.chunk_id for h in cyber_privacy if h.chunk_id in privacy_only]
    checks.append(check(
        "agent_partition_blocks_privacy_only_records_from_cyber",
        not leaked,
        leaked,
        []
    ))

    # Policy boundary cases
    validator = PolicyBoundaryValidator()
    boundary_rows = []
    boundary_correct = 0

    for case in bcases:
        hits = kb.retrieve(case["agent_id"], case["query"], top_k=3)
        decision = validator.validate(
            agent_id=case["agent_id"],
            proposed_action=case["proposed_action"],
            jurisdiction="KR",
            policy_hits=hits,
            facts=case["facts"],
        )
        ok = decision.status == case["expected"]
        boundary_correct += int(ok)
        checks.append(check(
            f"{case['case_id']}_classification",
            ok,
            decision.to_dict(),
            case["expected"]
        ))
        boundary_rows.append({
            "case_id": case["case_id"],
            "agent_id": case["agent_id"],
            "proposed_action": case["proposed_action"],
            "expected": case["expected"],
            "observed": decision.status,
            "enforcement": decision.enforcement,
            "policy_basis_type": decision.policy_basis_type,
            "supporting_policy_ids": "|".join(decision.supporting_policy_ids),
            "reason": decision.reason,
        })

    boundary_accuracy = boundary_correct / len(bcases)

    # Explicit direct wrong-jurisdiction boundary classifier
    wrong_j = validator.validate(
        agent_id="privacy_agent",
        proposed_action="DENY_UNAUTHORIZED_DISCLOSURE",
        jurisdiction="US",
        policy_hits=[],
        facts={}
    )
    checks.append(check(
        "boundary_wrong_jurisdiction_explicit",
        wrong_j.status == "WRONG_JURISDICTION"
        and wrong_j.enforcement == "BLOCK",
        wrong_j.to_dict(),
        {"status": "WRONG_JURISDICTION", "enforcement": "BLOCK"}
    ))

    # Metrics
    wrong_jurisdiction_acceptance_rate = 1.0 if decoy_accepted else 0.0
    agent_partition_leakage_rate = 1.0 if leaked else 0.0

    checks.append(check(
        "policy_boundary_accuracy_100pct",
        boundary_accuracy == 1.0,
        boundary_accuracy,
        1.0
    ))
    checks.append(check(
        "wrong_jurisdiction_acceptance_rate_zero",
        wrong_jurisdiction_acceptance_rate == 0.0,
        wrong_jurisdiction_acceptance_rate,
        0.0
    ))
    checks.append(check(
        "agent_partition_leakage_rate_zero",
        agent_partition_leakage_rate == 0.0,
        agent_partition_leakage_rate,
        0.0
    ))

    # Replay stability
    replay_ok = True
    replay_details = []
    for q in qset["queries"]:
        a = kb.retrieve(q["agent_id"], q["query"], top_k=3)
        b = kb.retrieve(q["agent_id"], q["query"], top_k=3)
        same_ids = [x.chunk_id for x in a] == [x.chunk_id for x in b]
        max_delta = max([abs(x.score-y.score) for x, y in zip(a,b)] or [0.0])
        stable = same_ids and max_delta <= 1e-7
        replay_ok = replay_ok and stable
        replay_details.append({
            "query_id": q["query_id"],
            "same_ids": same_ids,
            "max_score_delta": max_delta,
        })
    checks.append(check(
        "embedding_retrieval_replay_stable",
        replay_ok,
        replay_details,
        "same ranking; score delta <= 1e-7"
    ))

    with (OUT / "gate17_retrieval_trace.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "query_id", "agent_id", "language", "rank", "chunk_id",
            "score", "jurisdiction", "source_type", "authority", "locator"
        ])
        w.writeheader()
        w.writerows(retrieval_rows)

    with (OUT / "gate17_boundary_trace.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "case_id", "agent_id", "proposed_action", "expected",
            "observed", "enforcement", "policy_basis_type",
            "supporting_policy_ids", "reason"
        ])
        w.writeheader()
        w.writerows(boundary_rows)

    with (OUT / "gate17_checks.json").open("w", encoding="utf-8") as f:
        json.dump(checks, f, indent=2, ensure_ascii=False)

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)
    status_name = "PASS" if passed == total else "FAIL"

    result = {
        "gate": "GATE_17_JURISDICTIONAL_EMBEDDING_POLICY_BOUNDARY",
        "status": status_name,
        "passed_checks": passed,
        "total_checks": total,
        "kb_version": kb.kb_version,
        "model_name": kb.model_name,
        "deployment_jurisdiction": "KR",
        "retrieval_queries": len(qset["queries"]),
        "semantic_top3_accuracy": retrieval_accuracy,
        "policy_boundary_cases": len(bcases),
        "policy_boundary_accuracy": boundary_accuracy,
        "wrong_jurisdiction_acceptance_rate": wrong_jurisdiction_acceptance_rate,
        "agent_partition_leakage_rate": agent_partition_leakage_rate,
        "full_2026_guideline_operational_chunks_added": 11,
        "policy_boundary_states_tested": [
            "COMPLIANT",
            "OUT_OF_POLICY",
            "WRONG_JURISDICTION",
            "OUTSIDE_MANDATE",
            "INSUFFICIENT_EVIDENCE",
        ],
    }

    (OUT / "gate17_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nOutputs saved to:\n{OUT}")

    if status_name == "FAIL":
        raise SystemExit(
            "Gate 17 FAILED. Diagnose retrieval, jurisdiction, agent-access, "
            "or boundary-classification behavior before coordinator integration."
        )

    print(
        "\nFULL GATE 17 PASS — Korean policy corpus is operational for "
        "jurisdiction-constrained semantic retrieval and explicit policy-boundary enforcement."
    )

if __name__ == "__main__":
    main()
