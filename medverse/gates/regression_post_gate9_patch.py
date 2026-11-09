from __future__ import annotations

from pathlib import Path
import sys
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.data.loader import load_json
from medverse.routing.router import deliver_event
from medverse.agents.hospital import HospitalAgent
from medverse.agents.cyber_network import CyberNetworkAgent
from medverse.orchestrator.coordinator import DeterministicCoordinator
from medverse.knowledge_base.semantic_kb import MultilingualPolicyKnowledgeBase
from medverse.reasoning.bounded_adapter import (
    BoundedReasoningAdapter,
    validate_bounded_output,
)
from medverse.integration.pipeline import MedVerseIntegratedPipeline
from medverse.evaluation.harness import Gate9EvaluationHarness

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "regression_post_gate9"
OUT.mkdir(parents=True, exist_ok=True)

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def build_assessments():
    scenario = load_json(
        ROOT / "data" / "reference" / "MVKR-S01.json"
    )
    agents = {
        "hospital_agent": HospitalAgent(
            ROOT / "medverse" / "agents" / "mandates"
            / "hospital_agent.json"
        ),
        "cyber_network_agent": CyberNetworkAgent(
            ROOT / "medverse" / "agents" / "mandates"
            / "cyber_network_agent.json"
        ),
    }

    assessments = {}
    for event in scenario["events"]:
        for agent_id, obs in deliver_event(event).items():
            assessments[event["event_id"]] = agents[agent_id].assess(obs)

    return assessments

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Post-Gate-9 Regression")
    print("========================================\n")

    checks = []
    assessments = build_assessments()
    coordinator = DeterministicCoordinator()

    # Gate 5 full-S1 semantics unchanged
    full = coordinator.coordinate(assessments)
    checks.append(check(
        "G5_full_s1_coordination_state",
        full.coordination_state == "COMPLEMENTARY_RISK",
        full.coordination_state,
        "COMPLEMENTARY_RISK",
    ))
    checks.append(check(
        "G5_full_s1_rationale",
        full.rationale_code == "HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST",
        full.rationale_code,
        "HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST",
    ))
    checks.append(check(
        "G5_full_s1_human_review",
        full.human_review_required is True,
        full.human_review_required,
        True,
    ))

    # Newly-reachable counterfactual branches
    clinical_only = coordinator.coordinate({"E1": assessments["E1"]})
    technical_only = coordinator.coordinate({
        "E2": assessments["E2"],
        "E3": assessments["E3"],
    })
    monitor = coordinator.coordinate({})

    checks.append(check(
        "G5_clinical_only",
        clinical_only.coordination_state == "SINGLE_DOMAIN_ESCALATION",
        clinical_only.coordination_state,
        "SINGLE_DOMAIN_ESCALATION",
    ))
    checks.append(check(
        "G5_technical_only",
        technical_only.coordination_state == "TECHNICAL_VERIFICATION",
        technical_only.coordination_state,
        "TECHNICAL_VERIFICATION",
    ))
    checks.append(check(
        "G5_monitor",
        monitor.coordination_state == "MONITOR",
        monitor.coordination_state,
        "MONITOR",
    ))

    # Gate 7B bounded reasoning semantics unchanged
    kb = MultilingualPolicyKnowledgeBase(
        ROOT / "data" / "policy" / "seed"
        / "policy_seed_records.json"
    )
    kb.load_model()

    policy_hits = (
        [h.to_dict() for h in kb.retrieve(
            "hospital_agent",
            "patient medical records access disclosure healthcare provider",
            top_k=1,
        )]
        +
        [h.to_dict() for h in kb.retrieve(
            "cyber_network_agent",
            "personal information security safeguards access logs integrity",
            top_k=1,
        )]
    )

    adapter = BoundedReasoningAdapter()
    explanation = adapter.explain(
        full.to_dict(),
        policy_hits,
    )
    errors = validate_bounded_output(
        explanation,
        full.to_dict(),
        policy_hits,
    )

    checks.append(check(
        "G7B_bounded_output_valid",
        errors == [],
        errors,
        [],
    ))
    checks.append(check(
        "G7B_joint_actions_preserved",
        set(explanation.allowed_joint_actions) == set(full.joint_actions),
        sorted(explanation.allowed_joint_actions),
        sorted(full.joint_actions),
    ))
    checks.append(check(
        "G7B_human_review_preserved",
        explanation.human_review_required is True,
        explanation.human_review_required,
        True,
    ))

    # Gate 8 integrated semantics unchanged
    pipeline = MedVerseIntegratedPipeline(ROOT)
    integrated = pipeline.run_all()

    checks.append(check(
        "G8_event_order",
        [x["event_id"] for x in integrated] == ["E1", "E2", "E3"],
        [x["event_id"] for x in integrated],
        ["E1", "E2", "E3"],
    ))
    checks.append(check(
        "G8_dt_path",
        [x["state"]["dt"]["validity"] for x in integrated]
        == ["VALID", "DEGRADED", "UNVERIFIED"],
        [x["state"]["dt"]["validity"] for x in integrated],
        ["VALID", "DEGRADED", "UNVERIFIED"],
    ))
    checks.append(check(
        "G8_final_coordination",
        integrated[-1]["coordination"]["coordination_state"]
        == "COMPLEMENTARY_RISK",
        integrated[-1]["coordination"]["coordination_state"],
        "COMPLEMENTARY_RISK",
    ))
    checks.append(check(
        "G8_final_human_review",
        integrated[-1]["coordination"]["human_review_required"] is True,
        integrated[-1]["coordination"]["human_review_required"],
        True,
    ))

    # Gate 9 evaluator semantics
    eval_result = Gate9EvaluationHarness(ROOT).run_medverse()
    expected_metrics = {
        "ARA": 1.0,
        "MCR": 1.0,
        "CSR": 1.0,
        "CDR": 1.0,
        "EAR": 1.0,
        "PGA": 1.0,
        "ILR": 0.0,
    }
    checks.append(check(
        "G9_fixture_metrics",
        eval_result["metrics"] == expected_metrics,
        eval_result["metrics"],
        expected_metrics,
    ))

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)
    regression_pass = passed == total

    status = {
        "suite": "POST_GATE9_COORDINATOR_PATCH_REGRESSION",
        "status": "PASS" if regression_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "affected_gates": ["G5", "G7B", "G8", "G9"],
    }

    (OUT / "regression_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )
    (OUT / "regression_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not regression_pass:
        raise SystemExit(
            "Post-Gate-9 regression FAILED. Do not proceed to Gate 10."
        )

    print(
        "\nFULL REGRESSION PASS — Gate 9 may be promoted and Gate 10 may run."
    )

if __name__ == "__main__":
    main()
