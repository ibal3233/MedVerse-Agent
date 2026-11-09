from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.data.loader import load_json
from medverse.routing.router import (
    route_event,
    build_observation,
    deliver_event,
)

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate3"
OUT.mkdir(parents=True, exist_ok=True)

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def flatten_observation(obs):
    return {
        "agent_id": obs["agent_id"],
        "event_id": obs["event_id"],
        "t": obs["t"],
        "event_type": obs["event_type"],
        "payload_json": json.dumps(obs["payload"], sort_keys=True),
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 3")
    print(" Routing and Asymmetric Observations")
    print("========================================\n")

    scenario = load_json(
        ROOT / "data" / "reference" / "MVKR-S01.json"
    )

    checks = []
    observation_rows = []
    routing_rows = []

    expected_routes = {
        "E1": ["hospital_agent"],
        "E2": ["cyber_network_agent"],
        "E3": ["cyber_network_agent"],
    }

    for event in scenario["events"]:
        recipients = route_event(event)

        routing_rows.append({
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "recipients": ",".join(recipients),
        })

        checks.append(check(
            f"{event['event_id']}_correct_route",
            recipients == expected_routes[event["event_id"]],
            recipients,
            expected_routes[event["event_id"]],
        ))

        deliveries = deliver_event(event)

        for obs in deliveries.values():
            observation_rows.append(flatten_observation(obs))

    # --------------------------------------------------
    # Explicit asymmetry / non-leakage checks
    # --------------------------------------------------
    e1 = scenario["events"][0]
    e2 = scenario["events"][1]
    e3 = scenario["events"][2]

    hospital_e1 = build_observation("hospital_agent", e1)
    cyber_e2 = build_observation("cyber_network_agent", e2)
    cyber_e3 = build_observation("cyber_network_agent", e3)

    checks.append(check(
        "hospital_E1_contains_clinical_only",
        set(hospital_e1["payload"].keys()) == {"SpO2", "heart_rate"},
        sorted(hospital_e1["payload"].keys()),
        ["SpO2", "heart_rate"],
    ))

    checks.append(check(
        "cyber_E2_contains_network_only",
        set(cyber_e2["payload"].keys()) == {"packet_loss", "rtt_ms", "jitter_ms"},
        sorted(cyber_e2["payload"].keys()),
        ["jitter_ms", "packet_loss", "rtt_ms"],
    ))

    checks.append(check(
        "cyber_E3_contains_security_only",
        set(cyber_e3["payload"].keys()) == {"certificate_status", "session_origin"},
        sorted(cyber_e3["payload"].keys()),
        ["certificate_status", "session_origin"],
    ))

    # Unauthorized access must be rejected
    denied_hospital_network = False
    try:
        build_observation("hospital_agent", e2)
    except PermissionError:
        denied_hospital_network = True

    checks.append(check(
        "hospital_cannot_observe_network_event",
        denied_hospital_network,
        denied_hospital_network,
        True,
    ))

    denied_hospital_security = False
    try:
        build_observation("hospital_agent", e3)
    except PermissionError:
        denied_hospital_security = True

    checks.append(check(
        "hospital_cannot_observe_security_event",
        denied_hospital_security,
        denied_hospital_security,
        True,
    ))

    denied_cyber_clinical = False
    try:
        build_observation("cyber_network_agent", e1)
    except PermissionError:
        denied_cyber_clinical = True

    checks.append(check(
        "cyber_cannot_observe_clinical_event",
        denied_cyber_clinical,
        denied_cyber_clinical,
        True,
    ))

    # No hidden full-state payload fields
    forbidden_for_hospital = {
        "packet_loss", "rtt_ms", "jitter_ms",
        "certificate_status", "session_origin",
    }
    forbidden_for_cyber = {
        "SpO2", "heart_rate",
    }

    hospital_leaks = sorted(
        forbidden_for_hospital.intersection(hospital_e1["payload"].keys())
    )
    cyber_e2_leaks = sorted(
        forbidden_for_cyber.intersection(cyber_e2["payload"].keys())
    )
    cyber_e3_leaks = sorted(
        forbidden_for_cyber.intersection(cyber_e3["payload"].keys())
    )

    checks.append(check(
        "hospital_observation_no_cross_domain_leakage",
        len(hospital_leaks) == 0,
        hospital_leaks,
        [],
    ))

    checks.append(check(
        "cyber_network_observation_no_clinical_leakage",
        len(cyber_e2_leaks) == 0 and len(cyber_e3_leaks) == 0,
        {"E2": cyber_e2_leaks, "E3": cyber_e3_leaks},
        {"E2": [], "E3": []},
    ))

    # Scenario-declared visibility and router policy must stay synchronized
    sync_ok = True
    sync_details = []
    for event in scenario["events"]:
        declared = sorted(event["visible_to"])
        routed = sorted(route_event(event))
        if declared != routed:
            sync_ok = False
        sync_details.append({
            "event_id": event["event_id"],
            "declared": declared,
            "routed": routed,
        })

    checks.append(check(
        "scenario_visibility_matches_router_policy",
        sync_ok,
        sync_details,
        "all declared visibility == routed recipients",
    ))

    # --------------------------------------------------
    # Save diagnostics
    # --------------------------------------------------
    with (OUT / "gate3_routing_trace.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["event_id", "event_type", "recipients"],
        )
        writer.writeheader()
        writer.writerows(routing_rows)

    with (OUT / "gate3_observation_trace.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "agent_id",
                "event_id",
                "t",
                "event_type",
                "payload_json",
            ],
        )
        writer.writeheader()
        writer.writerows(observation_rows)

    with (OUT / "gate3_checks.csv").open(
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
        "gate": "GATE_3_ROUTING_AND_ASYMMETRIC_OBSERVATIONS",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "routing": {
            row["event_id"]: row["recipients"]
            for row in routing_rows
        },
        "observation_counts": {
            "hospital_agent": sum(
                r["agent_id"] == "hospital_agent"
                for r in observation_rows
            ),
            "cyber_network_agent": sum(
                r["agent_id"] == "cyber_network_agent"
                for r in observation_rows
            ),
        },
    }

    (OUT / "gate3_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 3 FAILED. Diagnose the failed routing/visibility invariant "
            "before changing agent logic."
        )

    print(
        "\nFULL GATE 3 PASS — eligible to proceed to Gate 4."
    )

if __name__ == "__main__":
    main()
