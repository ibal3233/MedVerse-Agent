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
from medverse.orchestrator.message_policy import validate_coordination_message

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate5"
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
    print(" MedVerse-Agent — Gate 5")
    print(" Deterministic Multi-Agent Coordination")
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
        for agent_id, observation in deliver_event(event).items():
            assessments[event["event_id"]] = agents[agent_id].assess(
                observation
            )

    coordinator = DeterministicCoordinator()
    decision = coordinator.coordinate(assessments)

    checks = []

    checks.append(check(
        "coordination_state",
        decision.coordination_state == "COMPLEMENTARY_RISK",
        decision.coordination_state,
        "COMPLEMENTARY_RISK",
    ))

    checks.append(check(
        "coordination_rationale",
        decision.rationale_code
        == "HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST",
        decision.rationale_code,
        "HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST",
    ))

    checks.append(check(
        "human_review_required",
        decision.human_review_required is True,
        decision.human_review_required,
        True,
    ))

    required_joint = {
        "CONTACT_PATIENT",
        "VERIFY_MEASUREMENT",
        "REQUEST_HUMAN_CLINICAL_REVIEW",
        "MARK_TELEMETRY_UNVERIFIED",
        "VERIFY_DEVICE_IDENTITY",
        "ISOLATE_SUSPECT_SESSION",
        "REQUEST_ALTERNATIVE_CHANNEL",
        "PRESERVE_TECHNICAL_LOGS",
        "USE_INDEPENDENT_MEASUREMENT_CHANNEL",
    }

    checks.append(check(
        "joint_action_set",
        set(decision.joint_actions) == required_joint,
        sorted(decision.joint_actions),
        sorted(required_joint),
    ))

    hospital_actions = set(
        decision.delegated_actions["hospital_agent"]
    )
    cyber_actions = set(
        decision.delegated_actions["cyber_network_agent"]
    )

    checks.append(check(
        "hospital_delegation_within_mandate",
        hospital_actions.issubset(agents["hospital_agent"].allowed_actions),
        sorted(hospital_actions),
        "subset of hospital mandate",
    ))

    checks.append(check(
        "cyber_delegation_within_mandate",
        cyber_actions.issubset(
            agents["cyber_network_agent"].allowed_actions
        ),
        sorted(cyber_actions),
        "subset of cyber/network mandate",
    ))

    checks.append(check(
        "no_cross_institution_action_delegation",
        "ISOLATE_SUSPECT_SESSION" not in hospital_actions
        and "CONTACT_PATIENT" not in cyber_actions,
        {
            "hospital": sorted(hospital_actions),
            "cyber": sorted(cyber_actions),
        },
        "cross-domain actions absent",
    ))

    # Required coordination messages
    for i, message in enumerate(
        decision.required_information_exchange,
        start=1,
    ):
        message_ok = False
        try:
            validate_coordination_message(message)
            message_ok = True
        except PermissionError:
            message_ok = False

        checks.append(check(
            f"coordination_message_{i}_allowed",
            message_ok,
            message,
            "allowed minimum-necessary coordination message",
        ))

    # Explicit leakage probes
    bad_clinical_message = {
        "from": "hospital_agent",
        "to": "cyber_network_agent",
        "message_type": "CLINICAL_PRIORITY",
        "payload": {
            "priority": "URGENT",
            "SpO2": 78,
        },
    }

    leakage_rejected = False
    try:
        validate_coordination_message(bad_clinical_message)
    except PermissionError:
        leakage_rejected = True

    checks.append(check(
        "reject_clinical_data_leakage_to_cyber_agent",
        leakage_rejected,
        leakage_rejected,
        True,
    ))

    bad_security_message = {
        "from": "cyber_network_agent",
        "to": "hospital_agent",
        "message_type": "TELEMETRY_TRUST_STATUS",
        "payload": {
            "telemetry_trust": "UNVERIFIED",
            "certificate_status": "mismatch",
        },
    }

    security_leakage_rejected = False
    try:
        validate_coordination_message(bad_security_message)
    except PermissionError:
        security_leakage_rejected = True

    checks.append(check(
        "reject_security_detail_leakage_to_hospital_agent",
        security_leakage_rejected,
        security_leakage_rejected,
        True,
    ))

    # Deterministic replay
    decision2 = coordinator.coordinate(assessments)

    checks.append(check(
        "deterministic_coordination_replay",
        decision.to_dict() == decision2.to_dict(),
        decision.to_dict() == decision2.to_dict(),
        True,
    ))

    # Save coordination decision
    (OUT / "gate5_decision.json").write_text(
        json.dumps(decision.to_dict(), indent=2),
        encoding="utf-8",
    )

    # Save messages
    with (OUT / "gate5_coordination_messages.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "from",
                "to",
                "message_type",
                "payload_json",
            ],
        )
        writer.writeheader()
        for m in decision.required_information_exchange:
            writer.writerow({
                "from": m["from"],
                "to": m["to"],
                "message_type": m["message_type"],
                "payload_json": json.dumps(
                    m["payload"], sort_keys=True
                ),
            })

    with (OUT / "gate5_checks.csv").open(
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

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)
    gate_pass = passed == total

    status = {
        "gate": "GATE_5_DETERMINISTIC_MULTI_AGENT_COORDINATION",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "coordination_state": decision.coordination_state,
        "rationale_code": decision.rationale_code,
        "human_review_required": decision.human_review_required,
        "joint_actions": decision.joint_actions,
    }

    (OUT / "gate5_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 5 FAILED. Diagnose the failed coordination invariant "
            "before introducing policy retrieval, LLM reasoning, or dashboard logic."
        )

    print(
        "\nFULL GATE 5 PASS — eligible to proceed to Gate 6."
    )

if __name__ == "__main__":
    main()
