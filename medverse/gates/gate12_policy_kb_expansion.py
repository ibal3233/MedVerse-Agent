from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.knowledge_base.semantic_kb import MultilingualPolicyKnowledgeBase

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate12"
OUT.mkdir(parents=True, exist_ok=True)

SEED = (
    ROOT / "data" / "policy" / "seed"
    / "policy_seed_records.json"
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
    print(" MedVerse-Agent — Gate 12")
    print(" Authoritative Policy-KB Expansion")
    print("========================================\n")

    registry = json.loads(
        (ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8")
    )
    g11c = registry.get("promoted_gates", {}).get("GATE_11C", {})
    if g11c.get("status") != "PASS":
        status = {
            "gate": "GATE_12_POLICY_KB_EXPANSION",
            "status": "HOLD",
            "reason": "Gate 11C is not promoted PASS in FREEZE_REGISTRY.json.",
        }
        (OUT / "gate12_status.json").write_text(
            json.dumps(status, indent=2), encoding="utf-8"
        )
        print(json.dumps(status, indent=2))
        return

    kb = MultilingualPolicyKnowledgeBase(SEED)
    kb.load_model()

    cases = [
        {
            "agent_id": "privacy_agent",
            "query_ko": "개인정보를 원래 목적과 다르게 외부 기관에 제공할 수 있는가",
            "query_en": "Can personal information be disclosed to an external institution beyond the original purpose?",
            "expected": {
                "KR-PIPA-ART18-PURPOSE-001",
                "KR-PIPA-ART17-DISCLOSURE-001",
            },
        },
        {
            "agent_id": "research_irb_agent",
            "query_ko": "연구대상자의 동의와 연구 동의 철회는 어떻게 다뤄야 하는가",
            "query_en": "How should research participant consent and withdrawal be handled?",
            "expected": {
                "KR-BIOETHICS-ART16-CONSENT-001",
                "KR-BIOETHICS-ART37-WITHDRAWAL-001",
            },
        },
        {
            "agent_id": "regulator_agent",
            "query_ko": "디지털의료기기 소프트웨어의 안전성 검증과 규제 검토에 필요한 근거는 무엇인가",
            "query_en": "What evidence supports safety validation and regulatory review of digital medical device software?",
            "expected": {
                "KR-DMPA-ART2-DIGITALDEVICE-001",
                "KR-DMPA-RULE14-SAFETY-001",
            },
        },
    ]

    checks = []
    trace = []

    for case in cases:
        ko = kb.retrieve(case["agent_id"], case["query_ko"], top_k=2)
        en = kb.retrieve(case["agent_id"], case["query_en"], top_k=2)

        ko_ids = [h.chunk_id for h in ko]
        en_ids = [h.chunk_id for h in en]

        checks.append(check(
            f"{case['agent_id']}_ko_expected_hit",
            bool(set(ko_ids) & case["expected"]),
            ko_ids,
            sorted(case["expected"]),
        ))
        checks.append(check(
            f"{case['agent_id']}_en_expected_hit",
            bool(set(en_ids) & case["expected"]),
            en_ids,
            sorted(case["expected"]),
        ))
        checks.append(check(
            f"{case['agent_id']}_crosslingual_top1_same",
            ko_ids[0] == en_ids[0],
            {"ko": ko_ids[0], "en": en_ids[0]},
            "same top-1",
        ))

        trace.append({
            "agent_id": case["agent_id"],
            "ko_query": case["query_ko"],
            "en_query": case["query_en"],
            "ko_hits": [h.to_dict() for h in ko],
            "en_hits": [h.to_dict() for h in en],
        })

    # Access partition non-leakage
    forbidden_queries = [
        ("privacy_agent", "software validation cyber protection clinical trial digital medical device"),
        ("research_irb_agent", "third party disclosure personal information purpose limitation"),
        ("regulator_agent", "research consent withdrawal participant human subjects"),
    ]

    seed_lookup = {
        r["chunk_id"]: r
        for r in json.loads(SEED.read_text(encoding="utf-8"))["records"]
    }

    for agent_id, query in forbidden_queries:
        hits = kb.retrieve(agent_id, query, top_k=3)
        wrong = [
            h for h in hits
            if agent_id not in seed_lookup[h.chunk_id]["agent_access"]
        ]
        checks.append(check(
            f"{agent_id}_partition_nonleakage",
            len(wrong) == 0,
            [h.to_dict() for h in wrong],
            [],
        ))

    # Provenance completeness
    required_fields = {
        "chunk_id", "document_id", "agent_access", "title",
        "article", "official_url", "effective_date",
        "authority", "translation_status",
        "text_en", "retrieval_text_ko", "topics"
    }

    seed = json.loads(SEED.read_text(encoding="utf-8"))
    new_agents = {"privacy_agent", "research_irb_agent", "regulator_agent"}
    new_records = [
        r for r in seed["records"]
        if set(r.get("agent_access", [])) & new_agents
    ]

    provenance_ok = all(required_fields.issubset(r.keys()) for r in new_records)
    checks.append(check(
        "new_records_provenance_complete",
        provenance_ok,
        len(new_records),
        "all new records contain required provenance fields",
    ))

    checks.append(check(
        "new_records_translation_status_explicit",
        all(r["translation_status"] == "source-grounded English paraphrase"
            for r in new_records),
        sorted(set(r["translation_status"] for r in new_records)),
        ["source-grounded English paraphrase"],
    ))

    # Conservative regulator scope: no claim that statute literally requires fresh DT verification.
    regulator_records = [
        r for r in new_records
        if "regulator_agent" in r.get("agent_access", [])
    ]
    literal_overclaim = any(
        "fresh DT verification" in r.get("text_en", "")
        or "BLOCK_AUTOMATED_HIGH_IMPACT_ACTION" in r.get("text_en", "")
        for r in regulator_records
    )
    checks.append(check(
        "regulator_source_mapping_not_overclaimed",
        not literal_overclaim,
        literal_overclaim,
        False,
    ))

    # Replay stability
    replay_ok = True
    for case in cases:
        a = kb.retrieve(case["agent_id"], case["query_en"], top_k=2)
        b = kb.retrieve(case["agent_id"], case["query_en"], top_k=2)
        sig_a = [(x.chunk_id, round(float(x.score), 10)) for x in a]
        sig_b = [(x.chunk_id, round(float(x.score), 10)) for x in b]
        replay_ok = replay_ok and (sig_a == sig_b)

    checks.append(check(
        "semantic_replay_stable",
        replay_ok,
        replay_ok,
        True,
    ))

    (OUT / "gate12_retrieval_trace.json").write_text(
        json.dumps(trace, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with (OUT / "gate12_checks.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "observed", "expected"],
        )
        writer.writeheader()
        writer.writerows(checks)

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)
    gate_pass = passed == total

    status = {
        "gate": "GATE_12_POLICY_KB_EXPANSION",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "kb_version": "0.3",
        "new_agents_grounded": [
            "privacy_agent",
            "research_irb_agent",
            "regulator_agent",
        ],
        "authoritative_new_records": len(new_records),
        "policy_grounding_final_results_generated": False,
    }

    (OUT / "gate12_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2, ensure_ascii=False))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 12 FAILED. Diagnose policy retrieval/provenance before scoring PGA."
        )

    print(
        "\nFULL GATE 12 PASS — authoritative policy grounding for Privacy, "
        "Research/IRB, and Regulator agents is validated. Eligible for final PGA campaign."
    )

if __name__ == "__main__":
    main()
