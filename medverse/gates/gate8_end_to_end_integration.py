from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.integration.pipeline import MedVerseIntegratedPipeline

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate8"
OUT.mkdir(parents=True, exist_ok=True)

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 8")
    print(" End-to-End Integration")
    print("========================================\n")

    try:
        pipeline = MedVerseIntegratedPipeline(ROOT)
    except Exception as exc:
        status = {
            "gate": "GATE_8_END_TO_END_INTEGRATION",
            "status": "HOLD",
            "reason": str(exc),
        }
        (OUT / "gate8_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    checks = []
    outputs = pipeline.run_all()

    checks.append(check(
        "three_events_processed",
        len(outputs) == 3,
        len(outputs),
        3,
    ))

    checks.append(check(
        "event_order_preserved",
        [x["event_id"] for x in outputs] == ["E1", "E2", "E3"],
        [x["event_id"] for x in outputs],
        ["E1", "E2", "E3"],
    ))

    dt_path = [
        x["state"]["dt"]["validity"]
        for x in outputs
    ]
    checks.append(check(
        "gate2_dt_trajectory_preserved",
        dt_path == ["VALID", "DEGRADED", "UNVERIFIED"],
        dt_path,
        ["VALID", "DEGRADED", "UNVERIFIED"],
    ))

    checks.append(check(
        "gate3_routing_preserved",
        outputs[0]["visible_to"] == ["hospital_agent"]
        and outputs[1]["visible_to"] == ["cyber_network_agent"]
        and outputs[2]["visible_to"] == ["cyber_network_agent"],
        [x["visible_to"] for x in outputs],
        [
            ["hospital_agent"],
            ["cyber_network_agent"],
            ["cyber_network_agent"],
        ],
    ))

    checks.append(check(
        "gate4_assessments_preserved",
        outputs[0]["assessments"]["hospital_agent"]["assessment_code"]
            == "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION"
        and outputs[1]["assessments"]["cyber_network_agent"]["assessment_code"]
            == "TELEMETRY_RELIABILITY_DEGRADED"
        and outputs[2]["assessments"]["cyber_network_agent"]["assessment_code"]
            == "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN",
        {
            "E1": outputs[0]["assessments"]["hospital_agent"]["assessment_code"],
            "E2": outputs[1]["assessments"]["cyber_network_agent"]["assessment_code"],
            "E3": outputs[2]["assessments"]["cyber_network_agent"]["assessment_code"],
        },
        "all frozen Gate 4 assessment codes",
    ))

    final_coord = outputs[-1]["coordination"]
    checks.append(check(
        "gate5_coordination_preserved",
        final_coord is not None
        and final_coord["coordination_state"] == "COMPLEMENTARY_RISK"
        and final_coord["rationale_code"]
            == "HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST"
        and final_coord["human_review_required"] is True,
        final_coord,
        "Gate 5 coordination semantics preserved",
    ))

    final_explanation = outputs[-1]["explanation"]
    checks.append(check(
        "gate7b_reasoning_preserved",
        final_explanation is not None
        and final_explanation["coordination_state"] == "COMPLEMENTARY_RISK"
        and final_explanation["human_review_required"] is True
        and set(final_explanation["cited_policy_chunks"]) == {
            "KR-MSA-ART21-ACCESS-001",
            "KR-PIPC-SAFE-2026-001",
        },
        final_explanation,
        "bounded explanation with both supplied policy chunks",
    ))

    checks.append(check(
        "audit_log_complete",
        len(pipeline.audit_log) == 3
        and all("state" in x for x in pipeline.audit_log)
        and all("assessments" in x for x in pipeline.audit_log),
        len(pipeline.audit_log),
        3,
    ))

    # Replay exactness
    pipeline2 = MedVerseIntegratedPipeline(ROOT)
    outputs2 = pipeline2.run_all()

    checks.append(check(
        "end_to_end_replay_exact",
        outputs == outputs2,
        outputs == outputs2,
        True,
    ))

    (OUT / "gate8_full_audit.json").write_text(
        json.dumps(
            outputs,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with (OUT / "gate8_checks.csv").open(
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
        "gate": "GATE_8_END_TO_END_INTEGRATION",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "final_coordination_state": (
            final_coord["coordination_state"]
            if final_coord else None
        ),
        "final_dt_validity": dt_path[-1],
        "human_review_required": (
            final_coord["human_review_required"]
            if final_coord else None
        ),
    }

    (OUT / "gate8_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 8 FAILED. Diagnose the broken regression boundary "
            "before demo polishing or external LLM integration."
        )

    print(
        "\nFULL GATE 8 PASS — end-to-end deterministic demo pipeline validated."
    )

if __name__ == "__main__":
    main()
