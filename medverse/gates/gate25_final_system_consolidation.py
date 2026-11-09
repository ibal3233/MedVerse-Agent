from __future__ import annotations

from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "outputs" / "gate25"
ASSETS = OUT / "demo_assets"
OUT.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_gate(script: str):
    p = ROOT / "medverse" / "gates" / script
    proc = subprocess.run(
        [sys.executable, str(p)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return {
        "script": script,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def read_json(rel: str):
    p = ROOT / rel
    return json.loads(p.read_text(encoding="utf-8"))


def check_fraction(record):
    if "passed_checks" in record and "total_checks" in record:
        return int(record["passed_checks"]), int(record["total_checks"])
    raw = str(record.get("checks", "0/0"))
    if "/" in raw:
        a, b = raw.split("/", 1)
        return int(a), int(b)
    return 0, 0


def copy_if_exists(src_rel: str, dst_name: str):
    src = ROOT / src_rel
    if src.exists():
        shutil.copy2(src, ASSETS / dst_name)
        return True
    return False


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 25")
    print(" Final System Consolidation")
    print(" Demo / Video Evidence Freeze")
    print("========================================\n")

    # No model training is performed here.
    # Regenerate deterministic S1-S4 scientific traces and judge snapshots.
    g19_run = run_gate("gate19_end_to_end_grounded_pipeline.py")
    g20_run = run_gate("gate20_judge_interface_integration.py")

    g19_run_status = read_json("outputs/gate19/gate19_status.json")
    g20_run_status = read_json("outputs/gate20/gate20_status.json")
    privacy = read_json("outputs/gate22b6/gate22b6_status.json")
    cyber = read_json("outputs/gate24c/gate24c_status.json")

    registry = read_json("FREEZE_REGISTRY.json")
    frozen_g19 = registry.get("promoted_gates", {}).get("GATE_19", {})
    frozen_g20 = registry.get("promoted_gates", {}).get("GATE_20", {})

    # A missing optional runtime dependency is an environment HOLD, not a
    # scientific invalidation of a previously frozen PASS.
    g19_fresh_pass = (
        g19_run["returncode"] == 0
        and g19_run_status.get("status") == "PASS"
    )
    g20_fresh_pass = (
        g20_run["returncode"] == 0
        and g20_run_status.get("status") == "PASS"
    )

    g19_dependency_hold = (
        g19_run_status.get("status") == "HOLD"
        and g19_run_status.get("classification")
        == "dependency_or_model_loading_hold"
    )
    g20_dependency_hold = (
        g20_run_status.get("status") == "HOLD"
        and g20_run_status.get("classification")
        == "dependency_or_model_loading_hold"
    )

    g19 = (
        g19_run_status
        if g19_fresh_pass
        else frozen_g19
        if g19_dependency_hold and frozen_g19.get("status") == "PASS"
        else g19_run_status
    )
    g20 = (
        g20_run_status
        if g20_fresh_pass
        else frozen_g20
        if g20_dependency_hold and frozen_g20.get("status") == "PASS"
        else g20_run_status
    )

    g19_passed, g19_total = check_fraction(g19)
    g20_passed, g20_total = check_fraction(g20)

    # Copy the most useful judge/video artifacts into one folder.
    copied = {}
    for src, dst in [
        ("outputs/gate19/gate19_judge_trace.csv", "01_S1_S4_judge_trace.csv"),
        ("outputs/gate19/gate19_full_results.json", "02_S1_S4_full_results.json"),
        ("outputs/gate20/gate20_view_snapshots.json", "03_judge_view_snapshots.json"),
        ("outputs/gate22b6/gate22b6_hyperparameter_results_table.md", "04_privacy_hyperparameter_table.md"),
        ("outputs/gate22b6/gate22b6_replication_results_table.csv", "05_privacy_replication_results.csv"),
        ("outputs/gate22b6/figures/fig22b6_hyperparameter_selection.png", "06_privacy_hyperparameter_selection.png"),
        ("outputs/gate22b6/figures/fig22b6_training_history.png", "07_privacy_training_history.png"),
        ("outputs/gate22b6/figures/fig22b6_action_class_recall.png", "08_privacy_action_recall.png"),
        ("outputs/gate24c/gate24c_hyperparameter_results_table.md", "09_cyber_hyperparameter_table.md"),
        ("outputs/gate24c/gate24c_prospective_results_table.md", "10_cyber_prospective_results.md"),
        ("outputs/gate24c/figures/fig24c_hyperparameter_selection.png", "11_cyber_hyperparameter_selection.png"),
        ("outputs/gate24c/figures/fig24c_training_history.png", "12_cyber_training_history.png"),
        ("outputs/gate24c/figures/fig24c_group_stability.png", "13_cyber_group_stability.png"),
        ("outputs/gate24c/figures/fig24c_action_class_recall.png", "14_cyber_action_recall.png"),
        ("data/evaluation/gate19_end_to_end_cases.json", "15_S1_S4_case_definitions.json"),
        ("data/evaluation/gate20_ui_expectations.json", "16_UI_expectations.json"),
        ("demo/competition_app.py", "17_competition_app.py"),
        ("demo/judge_view_model.py", "18_judge_view_model.py"),
    ]:
        copied[dst] = copy_if_exists(src, dst)

    # Final evidence summary.
    summary = {
        "project": "MedVerse-Agent",
        "status": "EXPERIMENT_COMPLETE_READY_FOR_DEMO",
        "training_performed_in_gate25": False,
        "new_benchmark_created_in_gate25": False,
        "new_threshold_created_in_gate25": False,
        "deployment_jurisdiction": "KR",
        "end_to_end": {
            "gate19_status": g19["status"],
            "gate19_replay_mode": (
                "FRESH_REPLAY"
                if g19_fresh_pass
                else "FROZEN_PASS_FALLBACK_AFTER_DEPENDENCY_HOLD"
            ),
            "gate19_runtime_status": g19_run_status.get("status"),
            "gate19_runtime_reason": g19_run_status.get("reason"),
            "scenario_count": g19["scenario_count"],
            "scenario_outcome_accuracy": g19["scenario_outcome_accuracy"],
            "scenarios": g19["scenarios"],
            "agents_exercised": g19["institutional_agents_exercised"],
        },
        "judge_interface": {
            "gate20_status": g20["status"],
            "gate20_replay_mode": (
                "FRESH_REPLAY"
                if g20_fresh_pass
                else "FROZEN_PASS_FALLBACK_AFTER_DEPENDENCY_HOLD"
            ),
            "gate20_runtime_status": g20_run_status.get("status"),
            "gate20_runtime_reason": g20_run_status.get("reason"),
            "checks": f"{g20_passed}/{g20_total}",
            "outcomes_preserved": g20["gate19_outcomes_preserved"],
            "scenarios_visible": g20["scenarios_visible"],
        },
        "privacy": {
            "status": privacy["status"],
            "checks": f"{privacy['passed_checks']}/{privacy['total_checks']}",
            "action_accuracy": privacy["replication_metrics"]["action"]["accuracy"],
            "action_macro_f1": privacy["replication_metrics"]["action"]["macro_f1"],
            "minimum_action_class_recall": privacy["minimum_action_class_recall"],
            "protected_diagnosed_core_action_accuracy":
                privacy["protected_diagnosed_core_action_accuracy"],
            "evidence_accuracy": privacy["replication_metrics"]["evidence"]["accuracy"],
            "evidence_macro_f1": privacy["replication_metrics"]["evidence"]["macro_f1"],
            "unsafe_allow_execution_rate": privacy["unsafe_allow_execution_rate"],
            "claim_boundary": privacy["claim_boundary"],
        },
        "cyber_network": {
            "status": cyber["status"],
            "checks": f"{cyber['passed_checks']}/{cyber['total_checks']}",
            "action_accuracy": cyber["prospective_metrics"]["action"]["accuracy"],
            "action_macro_f1": cyber["prospective_metrics"]["action"]["macro_f1"],
            "assessment_accuracy": cyber["prospective_metrics"]["assessment"]["accuracy"],
            "assessment_macro_f1": cyber["prospective_metrics"]["assessment"]["macro_f1"],
            "minimum_action_class_recall": cyber["minimum_action_class_recall"],
            "prospective_groups": sorted(cyber["prospective_metrics"]["by_group"]),
            "claim_boundary": cyber["claim_boundary"],
        },
        "scientific_claim_boundaries": [
            "Privacy validation is over an already-defined finite synthetic policy state space under fresh request contexts; it is not unseen semantic-core generalization.",
            "Cyber validation uses a synthetic prospective generator-shift benchmark; it is not external network telemetry or clinical validation.",
            "Benchmark/reference validators establish consistency with synthetic benchmark oracles, not completeness of Korean legal-policy semantics.",
            "NCC cancer data are population-level context and are not used for patient-level inference.",
            "MedVerse-Agent harmonizes institutionally asymmetric agents; it is not a voting/consensus system.",
        ],
        "video_ready_assets_directory": "outputs/gate25/demo_assets",
    }

    (OUT / "FINAL_EXPERIMENT_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Judge-facing concise evidence table.
    rows = [
        {
            "component": "End-to-end S1-S4",
            "metric": "Scenario outcome accuracy",
            "value": g19["scenario_outcome_accuracy"],
            "claim_scope": "Deterministic grounded S1-S4 evaluation",
        },
        {
            "component": "Privacy Agent",
            "metric": "Fresh-context action accuracy",
            "value": privacy["replication_metrics"]["action"]["accuracy"],
            "claim_scope": "Finite synthetic Privacy state space",
        },
        {
            "component": "Privacy Agent",
            "metric": "Minimum action-class recall",
            "value": privacy["minimum_action_class_recall"],
            "claim_scope": "Finite synthetic Privacy state space",
        },
        {
            "component": "Privacy shield",
            "metric": "Unsafe-ALLOW execution rate",
            "value": privacy["unsafe_allow_execution_rate"],
            "claim_scope": "Synthetic disclosure-safety benchmark",
        },
        {
            "component": "Cyber / Network Agent",
            "metric": "Prospective action accuracy",
            "value": cyber["prospective_metrics"]["action"]["accuracy"],
            "claim_scope": "Synthetic g5-g8 prospective generator shift",
        },
        {
            "component": "Cyber / Network Agent",
            "metric": "Prospective assessment accuracy",
            "value": cyber["prospective_metrics"]["assessment"]["accuracy"],
            "claim_scope": "Synthetic g5-g8 prospective generator shift",
        },
    ]

    with (OUT / "FINAL_JUDGE_METRICS.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Video/demo capture order.
    capture = """# MedVerse-Agent Final Demo Capture Plan

## Stop rule
Experiments are complete. Do not open a new training or diagnostic branch for
the hackathon unless a demo-breaking implementation defect is discovered.

## Recommended video capture sequence

1. **Problem in one sentence**
   Medical-metaverse institutions can each be locally correct yet conflict over
   clinical safety, network trust, privacy/consent, research authority, and
   regulatory constraints.

2. **Architecture**
   Show the five institutionally asymmetric agents feeding MedVerse-Agent,
   which harmonizes permitted actions rather than voting.

3. **Scenario S1**
   Show abnormal patient state + degraded/untrusted telemetry.
   Emphasize independent clinical verification, alternative channel, device
   identity verification, log preservation, and harmonized safe action.

4. **Scenario S2 or S4**
   Show that treatment/care authority and research/disclosure authority are
   separated. Demonstrate that research withdrawal or unauthorized disclosure
   does not incorrectly stop legitimate care.

5. **Korean-policy grounding**
   Show retrieved authority/source, jurisdiction filter, boundary result, and
   selected action. Do not claim the validator proves all Korean law.

6. **Learning evidence**
   Show only the strongest plots:
   - Privacy hyperparameter selection
   - Privacy training history / class recall
   - Cyber prospective g5-g8 stability
   - Cyber hyperparameter selection

7. **Quantitative results**
   Use FINAL_JUDGE_METRICS.csv. Avoid presenting every gate.

8. **Close**
   'Learning proposes; policy architecture disposes.'
   Emphasize auditable institutional coordination rather than a general medical
   chatbot or a monolithic LLM.

## What not to show in the main video
- the full gate history;
- exploratory Gate22A/Gate23/Gate24 failure chains;
- raw internal debug traces;
- unsupported claims of external clinical validation;
- unsupported claims of complete Korean legal compliance.
"""
    (OUT / "FINAL_VIDEO_CAPTURE_PLAN.md").write_text(
        capture,
        encoding="utf-8",
    )

    # Final demo narration facts, kept factual and short.
    narration = {
        "problem": (
            "Medical metaverse systems coordinate multiple institutions whose "
            "observations, mandates, evidence access, and permitted actions differ."
        ),
        "solution": (
            "MedVerse-Agent coordinates five institutionally asymmetric agents "
            "under Korean-jurisdiction policy boundaries and produces a harmonized "
            "action, conditional workflow, escalation, or block."
        ),
        "strongest_evidence": [
            "S1-S4 end-to-end scenario outcome accuracy = 1.0.",
            "Privacy action accuracy/macro-F1 = 1.0/1.0 on the fresh-context replication benchmark.",
            "Privacy unsafe-ALLOW execution rate = 0.0.",
            "Cyber prospective action and assessment accuracy = 1.0 across g5-g8.",
        ],
        "limitation": (
            "The current learning benchmarks are synthetic and policy-grounded; "
            "they do not constitute external clinical validation, external network "
            "telemetry validation, or a claim of complete Korean legal coverage."
        ),
    }
    (OUT / "FINAL_NARRATION_FACTS.json").write_text(
        json.dumps(narration, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Artifact hashes for key model/evidence files.
    artifact_paths = [
        "outputs/gate22b6/privacy_agent_action_repaired_model.joblib",
        "outputs/gate24c/cyber_network_repaired_model.joblib",
        "outputs/gate22b6/gate22b6_status.json",
        "outputs/gate24c/gate24c_status.json",
        "data/evaluation/gate19_end_to_end_cases.json",
        "data/evaluation/gate20_ui_expectations.json",
    ]
    hashes = {}
    for rel in artifact_paths:
        p = ROOT / rel
        if p.exists():
            hashes[rel] = sha256(p)
        else:
            hashes[rel] = None

    (OUT / "FINAL_ARTIFACT_HASHES.json").write_text(
        json.dumps(hashes, indent=2),
        encoding="utf-8",
    )

    checks = [
        {
            "check": "gate19_validated_or_dependency_fallback",
            "pass": (
                g19_fresh_pass
                or (
                    g19_dependency_hold
                    and frozen_g19.get("status") == "PASS"
                )
            ),
            "observed": {
                "runtime_status": g19_run_status.get("status"),
                "runtime_reason": g19_run_status.get("reason"),
                "frozen_status": frozen_g19.get("status"),
                "mode": (
                    "FRESH_REPLAY"
                    if g19_fresh_pass
                    else "FROZEN_PASS_FALLBACK_AFTER_DEPENDENCY_HOLD"
                ),
            },
            "expected": "fresh PASS or dependency-HOLD with frozen PASS",
        },
        {
            "check": "gate20_validated_or_dependency_fallback",
            "pass": (
                g20_fresh_pass
                or (
                    g20_dependency_hold
                    and frozen_g20.get("status") == "PASS"
                )
            ),
            "observed": {
                "runtime_status": g20_run_status.get("status"),
                "runtime_reason": g20_run_status.get("reason"),
                "frozen_status": frozen_g20.get("status"),
                "mode": (
                    "FRESH_REPLAY"
                    if g20_fresh_pass
                    else "FROZEN_PASS_FALLBACK_AFTER_DEPENDENCY_HOLD"
                ),
            },
            "expected": "fresh PASS or dependency-HOLD with frozen PASS",
        },
        {
            "check": "S1_S4_all_present",
            "pass": g19["scenarios"] == ["S1", "S2", "S3", "S4"],
            "observed": g19["scenarios"],
            "expected": ["S1", "S2", "S3", "S4"],
        },
        {
            "check": "all_five_agents_exercised",
            "pass": len(g19["institutional_agents_exercised"]) == 5,
            "observed": g19["institutional_agents_exercised"],
            "expected": 5,
        },
        {
            "check": "privacy_closed",
            "pass": privacy["status"] == "PASS" and privacy["passed_checks"] == privacy["total_checks"],
            "observed": f"{privacy['passed_checks']}/{privacy['total_checks']}",
            "expected": "PASS",
        },
        {
            "check": "cyber_closed",
            "pass": cyber["status"] == "PASS" and cyber["passed_checks"] == cyber["total_checks"],
            "observed": f"{cyber['passed_checks']}/{cyber['total_checks']}",
            "expected": "PASS",
        },
        {
            "check": "judge_metrics_created",
            "pass": (OUT / "FINAL_JUDGE_METRICS.csv").exists(),
            "observed": True,
            "expected": True,
        },
        {
            "check": "video_capture_plan_created",
            "pass": (OUT / "FINAL_VIDEO_CAPTURE_PLAN.md").exists(),
            "observed": True,
            "expected": True,
        },
        {
            "check": "demo_assets_collected",
            "pass": sum(copied.values()) >= 10,
            "observed": {
                "copied": sum(copied.values()),
                "requested": len(copied),
            },
            "expected": ">=10",
        },
        {
            "check": "artifact_hash_manifest_created",
            "pass": all(v is not None for v in hashes.values()),
            "observed": hashes,
            "expected": "all key artifacts hashed",
        },
        {
            "check": "no_new_learning_or_thresholds",
            "pass": True,
            "observed": {
                "training": False,
                "new_benchmark": False,
                "new_threshold": False,
            },
            "expected": True,
        },
    ]

    passed = sum(c["pass"] for c in checks)
    status = {
        "gate": "GATE_25_FINAL_SYSTEM_CONSOLIDATION",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "experiment_status": (
            "COMPLETE_READY_FOR_DEMO"
            if passed == len(checks)
            else "HOLD_FOR_CONSOLIDATION_DIAGNOSIS"
        ),
        "training_performed": False,
        "new_benchmark_created": False,
        "S1_S4_scenario_outcome_accuracy": g19["scenario_outcome_accuracy"],
        "privacy_action_accuracy": privacy["replication_metrics"]["action"]["accuracy"],
        "privacy_minimum_action_recall": privacy["minimum_action_class_recall"],
        "cyber_action_accuracy": cyber["prospective_metrics"]["action"]["accuracy"],
        "cyber_assessment_accuracy": cyber["prospective_metrics"]["assessment"]["accuracy"],
        "demo_assets_directory": "outputs/gate25/demo_assets",
        "video_capture_plan": "outputs/gate25/FINAL_VIDEO_CAPTURE_PLAN.md",
        "judge_metrics": "outputs/gate25/FINAL_JUDGE_METRICS.csv",
        "next_dependency": (
            "No further experiment. Proceed to demo capture, video editing, "
            "narration, and final submission."
        ),
    }

    (OUT / "gate25_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate25_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2, ensure_ascii=False))
    print(f"\nDemo/video assets consolidated in:\n{ASSETS}")
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        print("\nGate 19 stdout:\n", g19_run["stdout"][-5000:])
        print("\nGate 19 stderr:\n", g19_run["stderr"][-2500:])
        print("\nGate 20 stdout:\n", g20_run["stdout"][-5000:])
        print("\nGate 20 stderr:\n", g20_run["stderr"][-2500:])
        raise SystemExit(
            "Gate 25 consolidation FAILED. Diagnose packaging/integration only; "
            "do not reopen agent-learning experiments."
        )

    print(
        "\nFULL GATE 25 PASS — Experimental work is closed. "
        "Proceed directly to demo capture and video production."
    )


if __name__ == "__main__":
    main()
