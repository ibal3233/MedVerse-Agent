from __future__ import annotations

from pathlib import Path
import json, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from medverse.integration.gate19_grounded_pipeline import Gate19GroundedPipeline
from demo.judge_view_model import build_judge_view

OUT = ROOT / "outputs" / "gate20"
OUT.mkdir(parents=True, exist_ok=True)

CASE_FILE = ROOT / "data" / "evaluation" / "gate19_end_to_end_cases.json"
UI_FILE = ROOT / "data" / "evaluation" / "gate20_ui_expectations.json"
APP_FILE = ROOT / "demo" / "competition_app.py"


def check(name, ok, observed, expected):
    return {
        "check": name,
        "status": "PASS" if ok else "FAIL",
        "observed": observed,
        "expected": expected,
    }


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 20")
    print(" Judge-Facing Interface Integration")
    print("========================================\n")

    registry = json.loads(
        (ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8")
    )
    if registry.get("promoted_gates", {}).get("GATE_19", {}).get("status") != "PASS":
        result = {
            "gate": "GATE_20_JUDGE_INTERFACE_INTEGRATION",
            "status": "HOLD",
            "reason": "Gate 19 is not promoted PASS.",
        }
        (OUT / "gate20_status.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )
        print(json.dumps(result, indent=2))
        return

    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))["cases"]
    ui = json.loads(UI_FILE.read_text(encoding="utf-8"))
    expected = ui["scenario_expectations"]

    try:
        pipeline = Gate19GroundedPipeline(ROOT)
    except Exception as exc:
        result = {
            "gate": "GATE_20_JUDGE_INTERFACE_INTEGRATION",
            "status": "HOLD",
            "classification": "dependency_or_model_loading_hold",
            "reason": str(exc),
        }
        (OUT / "gate20_status.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    checks = []
    snapshots = {}

    for case in cases:
        sid = case["scenario_id"]
        result = pipeline.run_case(case)
        trace = result["judge_trace"]
        view = build_judge_view(trace, case["name"])
        snapshots[sid] = view

        exp = expected[sid]

        # View model must preserve Gate-19 state and outcome exactly.
        checks.append(check(
            f"{sid}_coordination_preserved",
            view["coordination"]["state"] == exp["coordination_state"],
            view["coordination"]["state"],
            exp["coordination_state"],
        ))
        checks.append(check(
            f"{sid}_outcome_preserved",
            view["outcome"]["code"] == exp["final_outcome"],
            view["outcome"]["code"],
            exp["final_outcome"],
        ))

        # Participating agents must be complete and exact.
        observed_agents = sorted(a["agent_id"] for a in view["agents"])
        checks.append(check(
            f"{sid}_participating_agents_visible",
            observed_agents == sorted(exp["agents"]),
            observed_agents,
            sorted(exp["agents"]),
        ))

        # Each visible agent must show policy + boundary.
        boundary_visible = all(
            a["policy_boundary_status"]
            and a["selected_boundary_action"]
            and len(a["retrieved_policy"]) >= 1
            for a in view["agents"]
        )
        checks.append(check(
            f"{sid}_policy_boundary_visible",
            boundary_visible,
            {
                a["agent_id"]: {
                    "boundary": a["policy_boundary_status"],
                    "selected_action": a["selected_boundary_action"],
                    "policy_count": len(a["retrieved_policy"]),
                }
                for a in view["agents"]
            },
            "boundary + selected action + >=1 policy result per visible agent",
        ))

        # All policies shown must expose source attribution fields.
        provenance_ok = all(
            hit["chunk_id"]
            and hit["authority"]
            and hit["source_type"]
            and hit["official_url"]
            for a in view["agents"]
            for hit in a["retrieved_policy"]
        )
        checks.append(check(
            f"{sid}_policy_provenance_visible",
            provenance_ok,
            "all retrieved policy cards",
            "chunk_id + authority + source_type + official_url",
        ))

        # Population-data and evidence-scope safety labels must remain visible.
        evidence_safety_ok = all(
            a["patient_level_inference_from_population_data"] is False
            and a["unauthorized_evidence_used"] is False
            for a in view["agents"]
        )
        checks.append(check(
            f"{sid}_evidence_boundary_preserved",
            evidence_safety_ok,
            {
                a["agent_id"]: {
                    "patient_inference":
                        a["patient_level_inference_from_population_data"],
                    "unauthorized":
                        a["unauthorized_evidence_used"],
                }
                for a in view["agents"]
            },
            "all false",
        ))

    # Static app integration checks.
    app_text = APP_FILE.read_text(encoding="utf-8")
    required_app_tokens = [
        "Gate19GroundedPipeline",
        "build_judge_view",
        "Patient Digital Twin",
        "Retrieved Korean policy",
        "Boundary result",
        "MedVerse-Agent harmonization",
        "Final institutional outcome",
        "Audit trace and evidence-boundary checks",
        "Republic of Korea",
    ]
    missing = [x for x in required_app_tokens if x not in app_text]
    checks.append(check(
        "competition_app_contains_required_judge_layers",
        not missing,
        missing,
        [],
    ))

    # Ensure UI contract contains the five required layers.
    required_layers = {
        "digital_twin_state",
        "institutional_assessments",
        "korean_policy_evidence",
        "policy_boundary_status",
        "medverse_coordination",
    }
    observed_layers = set(ui["required_layers"])
    checks.append(check(
        "five_layer_ui_contract_complete",
        required_layers == observed_layers,
        sorted(observed_layers),
        sorted(required_layers),
    ))

    # View adapter must be deterministic.
    replay_ok = True
    replay_detail = []
    for case in cases:
        r = pipeline.run_case(case)["judge_trace"]
        a = build_judge_view(r, case["name"])
        b = build_judge_view(r, case["name"])
        same = a == b
        replay_ok = replay_ok and same
        replay_detail.append({"scenario_id": case["scenario_id"], "same": same})
    checks.append(check(
        "judge_view_model_deterministic",
        replay_ok,
        replay_detail,
        "identical output for identical Gate-19 trace",
    ))

    (OUT / "gate20_view_snapshots.json").write_text(
        json.dumps(snapshots, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    (OUT / "gate20_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)

    result = {
        "gate": "GATE_20_JUDGE_INTERFACE_INTEGRATION",
        "status": "PASS" if passed == total else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "ui_contract_id": ui["contract_id"],
        "scientific_logic_changed": False,
        "gate19_outcomes_preserved": all(
            snapshots[sid]["outcome"]["code"] == expected[sid]["final_outcome"]
            and snapshots[sid]["coordination"]["state"] == expected[sid]["coordination_state"]
            for sid in expected
        ),
        "scenarios_visible": sorted(snapshots),
        "required_layers": ui["required_layers"],
        "competition_app": "demo/competition_app.py",
        "view_model": "demo/judge_view_model.py",
    }

    (OUT / "gate20_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] == "FAIL":
        raise SystemExit(
            "Gate 20 FAILED. Diagnose only the UI/view-model integration; "
            "do not modify frozen Gate-19 scientific logic."
        )

    print(
        "\nFULL GATE 20 PASS — The competition interface preserves the "
        "validated Gate-19 outcomes and exposes DT state, institutional "
        "assessments, Korean-policy evidence, policy boundaries, and "
        "MedVerse-Agent coordination in a judge-facing trace."
    )


if __name__ == "__main__":
    main()
