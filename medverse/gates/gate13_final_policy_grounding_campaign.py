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
OUT = ROOT / "outputs" / "gate13"
OUT.mkdir(parents=True, exist_ok=True)

SEED = ROOT / "data" / "policy" / "seed" / "policy_seed_records.json"

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 13")
    print(" Final Policy-Grounding Campaign")
    print("========================================\n")

    registry = json.loads(
        (ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8")
    )
    g12 = registry.get("promoted_gates", {}).get("GATE_12", {})
    if g12.get("status") != "PASS":
        status = {
            "gate": "GATE_13_FINAL_POLICY_GROUNDING",
            "status": "HOLD",
            "reason": "Gate 12 is not promoted PASS in FREEZE_REGISTRY.json.",
        }
        (OUT / "gate13_status.json").write_text(
            json.dumps(status, indent=2), encoding="utf-8"
        )
        print(json.dumps(status, indent=2))
        return

    kb = MultilingualPolicyKnowledgeBase(SEED)
    kb.load_model()

    cases = [
        {
            "scenario": "S1",
            "agent_id": "hospital_agent",
            "query": "patient medical record access disclosure healthcare provider",
            "expected": "KR-MSA-ART21-ACCESS-001",
        },
        {
            "scenario": "S1",
            "agent_id": "cyber_network_agent",
            "query": "personal information security safeguards access logs integrity",
            "expected": "KR-PIPC-SAFE-2026-001",
        },
        {
            "scenario": "S2",
            "agent_id": "privacy_agent",
            "query": "third party disclosure beyond original purpose lawful basis",
            "expected_any": {
                "KR-PIPA-ART18-PURPOSE-001",
                "KR-PIPA-ART17-DISCLOSURE-001",
            },
        },
        {
            "scenario": "S2",
            "agent_id": "research_irb_agent",
            "query": "research participant consent withdrawal human subject research",
            "expected_any": {
                "KR-BIOETHICS-ART16-CONSENT-001",
                "KR-BIOETHICS-ART37-WITHDRAWAL-001",
            },
        },
        {
            "scenario": "S3",
            "agent_id": "regulator_agent",
            "query": "digital medical device software validation safety cyber protection regulatory oversight",
            "expected_any": {
                "KR-DMPA-ART2-DIGITALDEVICE-001",
                "KR-DMPA-RULE14-SAFETY-001",
            },
        },
        {
            "scenario": "S4",
            "agent_id": "privacy_agent",
            "query": "external institution excessive disclosure minimum necessary purpose limitation",
            "expected_any": {
                "KR-PIPA-ART18-PURPOSE-001",
                "KR-PIPA-ART17-DISCLOSURE-001",
            },
        },
    ]

    rows = []
    checks = []

    for case in cases:
        hits = kb.retrieve(case["agent_id"], case["query"], top_k=2)
        hit_ids = [h.chunk_id for h in hits]

        if "expected" in case:
            correct = bool(hit_ids) and hit_ids[0] == case["expected"]
            expected_repr = case["expected"]
        else:
            correct = bool(set(hit_ids) & case["expected_any"])
            expected_repr = sorted(case["expected_any"])

        rows.append({
            "scenario": case["scenario"],
            "agent_id": case["agent_id"],
            "query": case["query"],
            "top1": hit_ids[0] if hit_ids else None,
            "top2": hit_ids[1] if len(hit_ids) > 1 else None,
            "correct": correct,
        })

        checks.append(check(
            f"{case['scenario']}_{case['agent_id']}_grounding",
            correct,
            hit_ids,
            expected_repr,
        ))

    scenarios = sorted({r["scenario"] for r in rows})
    pga_rows = []
    for sid in scenarios:
        subset = [r for r in rows if r["scenario"] == sid]
        pga = sum(bool(r["correct"]) for r in subset) / len(subset)
        pga_rows.append({"scenario": sid, "cases": len(subset), "PGA": pga})
        checks.append(check(
            f"{sid}_PGA_complete", pga == 1.0, pga, 1.0
        ))

    overall_pga = sum(bool(r["correct"]) for r in rows) / len(rows)
    checks.append(check(
        "overall_PGA_complete", overall_pga == 1.0, overall_pga, 1.0
    ))

    seed = json.loads(SEED.read_text(encoding="utf-8"))
    lookup = {r["chunk_id"]: r for r in seed["records"]}
    required = {
        "chunk_id", "document_id", "agent_access", "title",
        "article", "official_url", "effective_date",
        "authority", "translation_status"
    }

    prov_ok = True
    prov_details = []
    for row in rows:
        rec = lookup[row["top1"]]
        missing = sorted(required - set(rec))
        prov_ok = prov_ok and not missing
        prov_details.append({
            "chunk_id": row["top1"],
            "missing": missing,
        })

    checks.append(check(
        "all_top1_provenance_complete",
        prov_ok,
        prov_details,
        "no missing provenance fields",
    ))

    with (OUT / "gate13_raw_grounding_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "scenario", "agent_id", "query",
                "top1", "top2", "correct"
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with (OUT / "gate13_scenario_pga.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=["scenario", "cases", "PGA"]
        )
        writer.writeheader()
        writer.writerows(pga_rows)

    with (OUT / "gate13_checks.csv").open(
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
        "gate": "GATE_13_FINAL_POLICY_GROUNDING",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "grounding_cases": len(rows),
        "scenario_families": scenarios,
        "overall_PGA": overall_pga,
        "full_gate10_operational_coverage": True,
        "full_gate10_policy_grounding_coverage": gate_pass,
        "full_gate10_experimental_coverage": gate_pass,
    }

    (OUT / "gate13_status.json").write_text(
        json.dumps(status, indent=2), encoding="utf-8"
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 13 FAILED. Diagnose policy grounding before final evidence closure."
        )

    print(
        "\nFULL GATE 13 PASS — operational and policy-grounding evidence now "
        "cover the complete Gate 10 scenario matrix."
    )

if __name__ == "__main__":
    main()
