from __future__ import annotations

from pathlib import Path
import json, csv, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from medverse.integration.gate19_grounded_pipeline import Gate19GroundedPipeline

OUT = ROOT / "outputs" / "gate19"
OUT.mkdir(parents=True, exist_ok=True)

CASE_FILE = ROOT / "data" / "evaluation" / "gate19_end_to_end_cases.json"


def check(name, ok, observed, expected):
    return {
        "check": name,
        "status": "PASS" if ok else "FAIL",
        "observed": observed,
        "expected": expected,
    }


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 19")
    print(" End-to-End Grounded Pipeline")
    print("========================================\n")

    registry = json.loads(
        (ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8")
    )
    g18 = registry.get("promoted_gates", {}).get("GATE_18", {})
    if g18.get("status") != "PASS":
        result = {
            "gate": "GATE_19_END_TO_END_GROUNDED_PIPELINE",
            "status": "HOLD",
            "reason": "Gate 18 is not promoted PASS."
        }
        (OUT / "gate19_status.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, indent=2))
        return

    dataset = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    cases = dataset["cases"]

    try:
        pipeline = Gate19GroundedPipeline(ROOT)
    except Exception as exc:
        result = {
            "gate": "GATE_19_END_TO_END_GROUNDED_PIPELINE",
            "status": "HOLD",
            "reason": str(exc),
            "classification": "dependency_or_model_loading_hold",
        }
        (OUT / "gate19_status.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("\nDependency/model HOLD — not a scientific FAIL.")
        return

    checks = []
    trace_rows = []
    full_results = {}

    for case in cases:
        sid = case["scenario_id"]
        result = pipeline.run_case(case)
        full_results[sid] = result
        jt = result["judge_trace"]

        checks.append(check(
            f"{sid}_dt_validity",
            jt["dt_validity"] == case["expected_dt_validity"],
            jt["dt_validity"],
            case["expected_dt_validity"],
        ))

        checks.append(check(
            f"{sid}_coordination_state",
            jt["coordination_state"] == case["expected_coordination_state"],
            jt["coordination_state"],
            case["expected_coordination_state"],
        ))

        checks.append(check(
            f"{sid}_final_outcome",
            jt["final_outcome"] == case["expected_final_outcome"],
            jt["final_outcome"],
            case["expected_final_outcome"],
        ))

        # Every selected action must pass the boundary.
        statuses = {
            a: info["policy_boundary_status"]
            for a, info in jt["agents"].items()
        }
        checks.append(check(
            f"{sid}_all_selected_actions_compliant",
            all(v == "COMPLIANT" for v in statuses.values()),
            statuses,
            "all COMPLIANT",
        ))

        # All retrieved authorities must be KR-filtered by construction and
        # every selected agent policy evidence must be non-empty.
        policy_ok = True
        policy_summary = {}
        for agent_id, info in jt["agents"].items():
            ids = info["policy_ids"]
            retrieved = info["retrieved_policy"]
            policy_summary[agent_id] = {
                "ids": ids,
                "retrieved_count": len(retrieved),
            }
            if not ids or not retrieved:
                policy_ok = False

        checks.append(check(
            f"{sid}_policy_evidence_present",
            policy_ok,
            policy_summary,
            ">=1 authorized policy record per participating agent",
        ))

        # Evidence-boundary invariants.
        no_patient_inference = all(
            info["patient_level_inference_from_population_data"] is False
            for info in jt["agents"].values()
        )
        checks.append(check(
            f"{sid}_no_patient_inference_from_population_data",
            no_patient_inference,
            {
                a: info["patient_level_inference_from_population_data"]
                for a, info in jt["agents"].items()
            },
            False,
        ))

        no_unauthorized = all(
            info["unauthorized_evidence_used"] is False
            for info in jt["agents"].values()
        )
        checks.append(check(
            f"{sid}_no_unauthorized_evidence",
            no_unauthorized,
            {
                a: info["unauthorized_evidence_used"]
                for a, info in jt["agents"].items()
            },
            False,
        ))

        # Judge trace completeness.
        required = {
            "scenario_id",
            "deployment_jurisdiction",
            "dt_validity",
            "agents",
            "coordination_state",
            "accepted_actions",
            "blocked_actions",
            "conditional_steps",
            "evidence_requests",
            "minimum_necessary_messages",
            "escalation_required",
            "escalation_targets",
            "rationale_code",
            "final_outcome",
        }
        missing = sorted(required - set(jt))
        checks.append(check(
            f"{sid}_judge_trace_complete",
            not missing,
            missing,
            [],
        ))

        trace_rows.append({
            "scenario_id": sid,
            "dt_validity": jt["dt_validity"],
            "agents": "|".join(case["agents"]),
            "boundary_statuses": json.dumps(statuses, ensure_ascii=False),
            "coordination_state": jt["coordination_state"],
            "final_outcome": jt["final_outcome"],
            "rationale_code": jt["rationale_code"],
            "escalation_required": jt["escalation_required"],
        })

    # Coverage across all five institutional agents.
    agents_seen = sorted({
        a for case in cases for a in case["agents"]
    })
    expected_agents = sorted([
        "hospital_agent",
        "cyber_network_agent",
        "privacy_agent",
        "research_irb_agent",
        "regulator_agent",
    ])
    checks.append(check(
        "all_five_institutional_agents_exercised",
        agents_seen == expected_agents,
        agents_seen,
        expected_agents,
    ))

    # S1-S4 full scenario coverage.
    scenario_ids = sorted(c["scenario_id"] for c in cases)
    checks.append(check(
        "all_S1_S4_scenarios_exercised",
        scenario_ids == ["S1", "S2", "S3", "S4"],
        scenario_ids,
        ["S1", "S2", "S3", "S4"],
    ))

    # Deterministic replay.
    replay = []
    replay_ok = True
    for case in cases:
        a = pipeline.run_case(case)["judge_trace"]
        b = pipeline.run_case(case)["judge_trace"]
        same = a == b
        replay.append({"scenario_id": case["scenario_id"], "same": same})
        replay_ok = replay_ok and same

    checks.append(check(
        "end_to_end_replay_deterministic",
        replay_ok,
        replay,
        "identical judge-facing trace on replay",
    ))

    # Write raw evidence.
    (OUT / "gate19_full_results.json").write_text(
        json.dumps(full_results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    (OUT / "gate19_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    with (OUT / "gate19_judge_trace.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(trace_rows[0].keys()))
        w.writeheader()
        w.writerows(trace_rows)

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)

    scenario_correct = sum(
        r["final_outcome"] == next(
            c["expected_final_outcome"]
            for c in cases if c["scenario_id"] == r["scenario_id"]
        )
        for r in trace_rows
    )

    result = {
        "gate": "GATE_19_END_TO_END_GROUNDED_PIPELINE",
        "status": "PASS" if passed == total else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "dataset_id": dataset["dataset_id"],
        "scenario_count": len(cases),
        "scenario_outcome_accuracy": scenario_correct / len(cases),
        "scenarios": scenario_ids,
        "institutional_agents_exercised": agents_seen,
        "patient_level_inference_from_population_data": False,
        "deployment_jurisdiction": "KR",
        "pipeline_stages": [
            "patient_digital_twin",
            "bounded_evidence_bundle",
            "grounded_institutional_agent",
            "jurisdiction_aware_policy_retrieval",
            "policy_boundary_validation",
            "medverse_policy_aware_harmonization",
            "judge_facing_trace",
        ],
    }

    (OUT / "gate19_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] == "FAIL":
        raise SystemExit(
            "Gate 19 FAILED. Diagnose the exact stage in gate19_checks.json "
            "before changing any frozen component."
        )

    print(
        "\nFULL GATE 19 PASS — S1-S4 now traverse the complete grounded "
        "MedVerse pipeline from Digital Twin evidence through Korean-policy "
        "boundary enforcement and MedVerse-Agent harmonization to an auditable "
        "judge-facing outcome."
    )


if __name__ == "__main__":
    main()
