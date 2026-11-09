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

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate4"
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
    print(" MedVerse-Agent — Gate 4")
    print(" Deterministic Institutional Assessments")
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

    checks = []
    assessment_rows = []
    produced = {}

    for event in scenario["events"]:
        deliveries = deliver_event(event)

        for agent_id, observation in deliveries.items():
            a = agents[agent_id].assess(observation)
            produced[event["event_id"]] = a

            assessment_rows.append({
                "event_id": a.event_id,
                "agent_id": a.agent_id,
                "assessment_code": a.assessment_code,
                "risk": a.risk,
                "recommended_actions": "|".join(a.recommended_actions),
                "human_review_required": a.human_review_required,
                "confidence": a.confidence,
                "basis_codes": "|".join(a.basis_codes),
                "observed_fields": "|".join(a.observed_fields),
            })

    # Expected independent institutional assessments
    e1 = produced["E1"]
    e2 = produced["E2"]
    e3 = produced["E3"]

    checks.append(check(
        "E1_hospital_assessment",
        e1.agent_id == "hospital_agent"
        and e1.assessment_code == "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION"
        and e1.risk == "HIGH",
        (e1.agent_id, e1.assessment_code, e1.risk),
        (
            "hospital_agent",
            "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION",
            "HIGH",
        ),
    ))

    checks.append(check(
        "E1_hospital_actions",
        set(e1.recommended_actions) == {
            "VERIFY_MEASUREMENT",
            "CONTACT_PATIENT",
            "REQUEST_HUMAN_CLINICAL_REVIEW",
        },
        sorted(e1.recommended_actions),
        sorted([
            "VERIFY_MEASUREMENT",
            "CONTACT_PATIENT",
            "REQUEST_HUMAN_CLINICAL_REVIEW",
        ]),
    ))

    checks.append(check(
        "E1_hospital_human_review",
        e1.human_review_required is True,
        e1.human_review_required,
        True,
    ))

    checks.append(check(
        "E2_cyber_network_assessment",
        e2.agent_id == "cyber_network_agent"
        and e2.assessment_code == "TELEMETRY_RELIABILITY_DEGRADED"
        and e2.risk == "HIGH",
        (e2.agent_id, e2.assessment_code, e2.risk),
        (
            "cyber_network_agent",
            "TELEMETRY_RELIABILITY_DEGRADED",
            "HIGH",
        ),
    ))

    checks.append(check(
        "E2_cyber_network_actions",
        set(e2.recommended_actions) == {
            "MARK_TELEMETRY_UNVERIFIED",
            "REQUEST_ALTERNATIVE_CHANNEL",
            "PRESERVE_TECHNICAL_LOGS",
        },
        sorted(e2.recommended_actions),
        sorted([
            "MARK_TELEMETRY_UNVERIFIED",
            "REQUEST_ALTERNATIVE_CHANNEL",
            "PRESERVE_TECHNICAL_LOGS",
        ]),
    ))

    checks.append(check(
        "E3_cyber_security_assessment",
        e3.agent_id == "cyber_network_agent"
        and e3.assessment_code == "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN"
        and e3.risk == "HIGH",
        (e3.agent_id, e3.assessment_code, e3.risk),
        (
            "cyber_network_agent",
            "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN",
            "HIGH",
        ),
    ))

    checks.append(check(
        "E3_cyber_security_actions",
        set(e3.recommended_actions) == {
            "VERIFY_DEVICE_IDENTITY",
            "ISOLATE_SUSPECT_SESSION",
            "MARK_TELEMETRY_UNVERIFIED",
            "PRESERVE_TECHNICAL_LOGS",
        },
        sorted(e3.recommended_actions),
        sorted([
            "VERIFY_DEVICE_IDENTITY",
            "ISOLATE_SUSPECT_SESSION",
            "MARK_TELEMETRY_UNVERIFIED",
            "PRESERVE_TECHNICAL_LOGS",
        ]),
    ))

    # Mandate checks
    hospital_allowed = agents["hospital_agent"].allowed_actions
    cyber_allowed = agents["cyber_network_agent"].allowed_actions

    checks.append(check(
        "hospital_actions_within_mandate",
        set(e1.recommended_actions).issubset(hospital_allowed),
        sorted(e1.recommended_actions),
        "subset of hospital allowed actions",
    ))

    checks.append(check(
        "cyber_actions_within_mandate",
        set(e2.recommended_actions).issubset(cyber_allowed)
        and set(e3.recommended_actions).issubset(cyber_allowed),
        {
            "E2": sorted(e2.recommended_actions),
            "E3": sorted(e3.recommended_actions),
        },
        "all actions subset of cyber/network allowed actions",
    ))

    # Negative mandate-enforcement tests
    hospital_rejected_network_action = False
    try:
        agents["hospital_agent"].validate_actions(
            ["ISOLATE_SUSPECT_SESSION"]
        )
    except PermissionError:
        hospital_rejected_network_action = True

    checks.append(check(
        "hospital_rejects_network_action",
        hospital_rejected_network_action,
        hospital_rejected_network_action,
        True,
    ))

    cyber_rejected_clinical_action = False
    try:
        agents["cyber_network_agent"].validate_actions(
            ["CONTACT_PATIENT"]
        )
    except PermissionError:
        cyber_rejected_clinical_action = True

    checks.append(check(
        "cyber_rejects_clinical_action",
        cyber_rejected_clinical_action,
        cyber_rejected_clinical_action,
        True,
    ))

    # Observed-field boundary still respected at reasoning layer
    checks.append(check(
        "hospital_reasoning_used_only_clinical_fields",
        set(e1.observed_fields) == {"SpO2", "heart_rate"},
        e1.observed_fields,
        ["SpO2", "heart_rate"],
    ))

    checks.append(check(
        "cyber_reasoning_used_only_authorized_fields",
        set(e2.observed_fields) == {"packet_loss", "rtt_ms", "jitter_ms"}
        and set(e3.observed_fields) == {
            "certificate_status",
            "session_origin",
        },
        {
            "E2": e2.observed_fields,
            "E3": e3.observed_fields,
        },
        {
            "E2": ["jitter_ms", "packet_loss", "rtt_ms"],
            "E3": ["certificate_status", "session_origin"],
        },
    ))

    # Deterministic replay
    produced2 = {}
    for event in scenario["events"]:
        for agent_id, observation in deliver_event(event).items():
            produced2[event["event_id"]] = agents[agent_id].assess(
                observation
            ).to_dict()

    produced1 = {k: v.to_dict() for k, v in produced.items()}

    checks.append(check(
        "deterministic_assessment_replay",
        produced1 == produced2,
        produced1 == produced2,
        True,
    ))

    # Save
    with (OUT / "gate4_assessments.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "event_id",
                "agent_id",
                "assessment_code",
                "risk",
                "recommended_actions",
                "human_review_required",
                "confidence",
                "basis_codes",
                "observed_fields",
            ],
        )
        writer.writeheader()
        writer.writerows(assessment_rows)

    with (OUT / "gate4_checks.csv").open(
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
        "gate": "GATE_4_DETERMINISTIC_INSTITUTIONAL_ASSESSMENTS",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "assessments": {
            event_id: {
                "agent_id": a.agent_id,
                "assessment_code": a.assessment_code,
                "risk": a.risk,
            }
            for event_id, a in produced.items()
        },
    }

    (OUT / "gate4_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 4 FAILED. Diagnose the failed assessment/mandate invariant "
            "before adding coordination or policy retrieval."
        )

    print(
        "\nFULL GATE 4 PASS — eligible to proceed to Gate 5."
    )

if __name__ == "__main__":
    main()
