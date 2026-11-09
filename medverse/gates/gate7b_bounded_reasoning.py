from __future__ import annotations

from pathlib import Path
import sys
import csv
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
from medverse.reasoning.llm_contract import build_llm_prompt

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate7b"
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
    print(" MedVerse-Agent — Gate 7B")
    print(" Bounded Policy-Grounded Reasoning")
    print("========================================\n")

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

    decision = DeterministicCoordinator().coordinate(
        assessments
    ).to_dict()

    try:
        kb = MultilingualPolicyKnowledgeBase(SEED)
        kb.load_model()
    except Exception as exc:
        status = {
            "gate": "GATE_7B_BOUNDED_POLICY_GROUNDED_REASONING",
            "status": "HOLD",
            "reason": str(exc),
        }
        (OUT / "gate7b_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    hospital_hits = kb.retrieve(
        "hospital_agent",
        "patient medical records access disclosure healthcare provider",
        top_k=1,
    )
    cyber_hits = kb.retrieve(
        "cyber_network_agent",
        "personal information security safeguards access logs integrity",
        top_k=1,
    )

    policy_hits = [
        h.to_dict()
        for h in hospital_hits + cyber_hits
    ]

    adapter = BoundedReasoningAdapter()
    explanation = adapter.explain(
        decision,
        policy_hits,
    )

    errors = validate_bounded_output(
        explanation,
        decision,
        policy_hits,
    )

    checks = []

    checks.append(check(
        "bounded_output_valid",
        errors == [],
        errors,
        [],
    ))

    checks.append(check(
        "coordination_state_preserved",
        explanation.coordination_state
        == decision["coordination_state"],
        explanation.coordination_state,
        decision["coordination_state"],
    ))

    checks.append(check(
        "rationale_preserved",
        explanation.rationale_code
        == decision["rationale_code"],
        explanation.rationale_code,
        decision["rationale_code"],
    ))

    checks.append(check(
        "joint_actions_exactly_preserved",
        set(explanation.allowed_joint_actions)
        == set(decision["joint_actions"]),
        sorted(explanation.allowed_joint_actions),
        sorted(decision["joint_actions"]),
    ))

    checks.append(check(
        "human_review_not_downgraded",
        explanation.human_review_required is True,
        explanation.human_review_required,
        True,
    ))

    supplied_chunks = {p["chunk_id"] for p in policy_hits}
    cited_chunks = set(explanation.cited_policy_chunks)

    checks.append(check(
        "policy_citations_supported",
        cited_chunks.issubset(supplied_chunks)
        and len(cited_chunks) > 0,
        sorted(cited_chunks),
        sorted(supplied_chunks),
    ))

    checks.append(check(
        "grounding_complete",
        explanation.grounding_complete is True,
        explanation.grounding_complete,
        True,
    ))

    # Adversarial mutation: invented action
    mutated = adapter.explain(
        decision,
        policy_hits,
    )
    mutated.allowed_joint_actions = (
        mutated.allowed_joint_actions
        + ["CHANGE_CANCER_TREATMENT"]
    )
    mutation_errors = validate_bounded_output(
        mutated,
        decision,
        policy_hits,
    )

    checks.append(check(
        "reject_invented_action",
        "action_set_changed" in mutation_errors,
        mutation_errors,
        "contains action_set_changed",
    ))

    # Adversarial mutation: unsupported policy citation
    mutated2 = adapter.explain(
        decision,
        policy_hits,
    )
    mutated2.cited_policy_chunks.append(
        "NONEXISTENT-POLICY-CHUNK"
    )
    mutation_errors2 = validate_bounded_output(
        mutated2,
        decision,
        policy_hits,
    )

    checks.append(check(
        "reject_unsupported_policy_citation",
        "unsupported_policy_citation" in mutation_errors2,
        mutation_errors2,
        "contains unsupported_policy_citation",
    ))

    # Adversarial mutation: suppress human review
    mutated3 = adapter.explain(
        decision,
        policy_hits,
    )
    mutated3.human_review_required = False
    mutation_errors3 = validate_bounded_output(
        mutated3,
        decision,
        policy_hits,
    )

    checks.append(check(
        "reject_human_review_downgrade",
        "human_review_flag_changed" in mutation_errors3,
        mutation_errors3,
        "contains human_review_flag_changed",
    ))

    # Deterministic replay
    explanation2 = adapter.explain(
        decision,
        policy_hits,
    )

    checks.append(check(
        "deterministic_reasoning_replay",
        explanation.to_dict() == explanation2.to_dict(),
        explanation.to_dict() == explanation2.to_dict(),
        True,
    ))

    # Build, but do not execute, future LLM prompt contract
    prompt_contract = build_llm_prompt(
        decision,
        policy_hits,
    )

    # The phrase "chain-of-thought" is allowed to appear in the contract
    # only as an explicit prohibition. The test must therefore inspect
    # semantics/placement rather than reject the literal phrase globally.
    system_instruction_text = (
        prompt_contract["system_instruction"].lower()
    )
    hard_constraints_text = " ".join(
        prompt_contract["output_contract"]["hard_constraints"]
    ).lower()

    cot_prohibition_present = (
        "chain-of-thought" in hard_constraints_text
        and (
            "no raw hidden chain-of-thought" in hard_constraints_text
            or "do not" in hard_constraints_text
            or "must not" in hard_constraints_text
        )
    )

    cot_not_requested_in_instruction = (
        "chain-of-thought" not in system_instruction_text
        and "show your reasoning" not in system_instruction_text
        and "step-by-step reasoning" not in system_instruction_text
    )

    checks.append(check(
        "llm_contract_contains_no_chain_of_thought_request",
        cot_prohibition_present
        and cot_not_requested_in_instruction,
        {
            "prohibition_present": cot_prohibition_present,
            "requested_in_system_instruction":
                not cot_not_requested_in_instruction,
        },
        {
            "prohibition_present": True,
            "requested_in_system_instruction": False,
        },
    ))

    (OUT / "gate7b_grounded_explanation.json").write_text(
        json.dumps(
            explanation.to_dict(),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (OUT / "gate7b_llm_prompt_contract.json").write_text(
        json.dumps(
            prompt_contract,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with (OUT / "gate7b_checks.csv").open(
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
        "gate": "GATE_7B_BOUNDED_POLICY_GROUNDED_REASONING",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "coordination_state": explanation.coordination_state,
        "policy_chunks_cited": explanation.cited_policy_chunks,
        "llm_executed": False,
        "reasoning_mode": "deterministic_reference_adapter",
    }

    (OUT / "gate7b_status.json").write_text(
        json.dumps(
            status,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            status,
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 7B FAILED. Diagnose grounding/constraint enforcement "
            "before executing any external LLM."
        )

    print(
        "\nFULL GATE 7B PASS — bounded reasoning contract validated."
    )

if __name__ == "__main__":
    main()
