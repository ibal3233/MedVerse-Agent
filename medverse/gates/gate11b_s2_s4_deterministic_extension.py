from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.agents.privacy import PrivacyAgent
from medverse.agents.research_irb import ResearchIRBAgent
from medverse.agents.regulator import RegulatorAgent
from medverse.routing.institutional_router import (
    deliver_event,
    build_observation,
)
from medverse.orchestrator.institutional_policy_coordinator import (
    InstitutionalPolicyCoordinator,
)
from medverse.orchestrator.coordinator import DeterministicCoordinator
from medverse.data.loader import load_json
from medverse.routing.router import deliver_event as deliver_s1
from medverse.agents.hospital import HospitalAgent
from medverse.agents.cyber_network import CyberNetworkAgent

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate11b"
OUT.mkdir(parents=True, exist_ok=True)

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def load_scenario(name):
    return load_json(ROOT / "data" / "reference" / name)

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 11B")
    print(" Deterministic S2-S4 Institutional Extension")
    print("========================================\n")

    registry = json.loads(
        (ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8")
    )
    gate11a = registry.get("promoted_gates", {}).get("GATE_11A")
    # Gate11A may not yet be in registry because this package is created
    # immediately after its validated run. We validate the documented freeze
    # record instead of depending on transient outputs.
    freeze_doc = ROOT / "GATE_11A_FREEZE_RECORD.md"

    if not freeze_doc.exists():
        status = {
            "gate": "GATE_11B_S2_S4_DETERMINISTIC_EXTENSION",
            "status": "HOLD",
            "reason": "Gate 11A freeze record not found.",
        }
        (OUT / "gate11b_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    agents = {
        "privacy_agent": PrivacyAgent(
            ROOT / "medverse" / "agents" / "mandates" / "privacy_agent.json"
        ),
        "research_irb_agent": ResearchIRBAgent(
            ROOT / "medverse" / "agents" / "mandates" / "research_irb_agent.json"
        ),
        "regulator_agent": RegulatorAgent(
            ROOT / "medverse" / "agents" / "mandates" / "regulator_agent.json"
        ),
    }

    coordinator = InstitutionalPolicyCoordinator()
    checks = []
    trace = {}

    scenario_files = [
        "S2_CARE_VS_RESEARCH.json",
        "S3_STALE_DT_AI.json",
        "S4_UNAUTHORIZED_DISCLOSURE.json",
    ]

    for filename in scenario_files:
        scenario = load_scenario(filename)
        assessments = {}

        for event in scenario["events"]:
            deliveries = deliver_event(event)
            for agent_id, obs in deliveries.items():
                assessments[event["event_id"]] = agents[agent_id].assess(obs)

        decision = coordinator.coordinate(assessments)

        checks.append(check(
            f"{scenario['scenario_id']}_coordination_state",
            decision.coordination_state
            == scenario["expected_coordination_state"],
            decision.coordination_state,
            scenario["expected_coordination_state"],
        ))

        checks.append(check(
            f"{scenario['scenario_id']}_human_review",
            decision.human_review_required
            == scenario["expected_human_review"],
            decision.human_review_required,
            scenario["expected_human_review"],
        ))

        # Every recommended action must remain within the producing agent mandate.
        mandate_ok = True
        mandate_detail = []
        for assessment in assessments.values():
            allowed = agents[assessment.agent_id].allowed_actions
            bad = sorted(
                set(assessment.recommended_actions) - set(allowed)
            )
            if bad:
                mandate_ok = False
            mandate_detail.append({
                "agent_id": assessment.agent_id,
                "event_id": assessment.event_id,
                "unauthorized_actions": bad,
            })

        checks.append(check(
            f"{scenario['scenario_id']}_mandate_compliance",
            mandate_ok,
            mandate_detail,
            "no unauthorized action",
        ))

        # Unauthorized observation probes.
        known = set(agents)
        leakage = []
        for event in scenario["events"]:
            authorized = set(event["visible_to"])
            for agent_id in sorted(known - authorized):
                leaked = False
                try:
                    build_observation(agent_id, event)
                    leaked = True
                except (PermissionError, ValueError):
                    leaked = False
                leakage.append({
                    "event_id": event["event_id"],
                    "agent_id": agent_id,
                    "leak": leaked,
                })

        checks.append(check(
            f"{scenario['scenario_id']}_no_observation_leakage",
            all(not row["leak"] for row in leakage),
            leakage,
            "all unauthorized probes rejected",
        ))

        trace[scenario["scenario_id"]] = {
            "assessments": {
                k: v.to_dict()
                for k, v in assessments.items()
            },
            "decision": decision.to_dict(),
            "leakage_probes": leakage,
        }

    # Explicit S2 action semantics
    s2_actions = set(
        trace["S2_CARE_VS_RESEARCH"]["decision"]["joint_actions"]
    )
    checks.append(check(
        "S2_preserves_care_and_blocks_research",
        {
            "ALLOW_TREATMENT_USE",
            "BLOCK_RESEARCH_USE",
            "BLOCK_RESEARCH_PROCESSING",
        }.issubset(s2_actions),
        sorted(s2_actions),
        "care allowed while research processing is blocked",
    ))

    # Explicit S3 action semantics
    s3_actions = set(
        trace["S3_STALE_DT_AI_RECOMMENDATION"]["decision"]["joint_actions"]
    )
    checks.append(check(
        "S3_blocks_high_impact_automation_until_fresh_DT",
        {
            "BLOCK_AUTOMATED_HIGH_IMPACT_ACTION",
            "REQUIRE_FRESH_DT_VERIFICATION",
            "REQUEST_HUMAN_OVERSIGHT",
        }.issubset(s3_actions),
        sorted(s3_actions),
        "automation blocked + fresh DT + human oversight",
    ))

    # Explicit S4 action semantics
    s4_actions = set(
        trace["S4_UNAUTHORIZED_DISCLOSURE"]["decision"]["joint_actions"]
    )
    checks.append(check(
        "S4_blocks_excessive_disclosure",
        {
            "DENY_UNAUTHORIZED_DISCLOSURE",
            "LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY",
        }.issubset(s4_actions),
        sorted(s4_actions),
        "deny excessive disclosure and enforce minimum necessary",
    ))

    # Regression: frozen S1 remains unchanged.
    s1 = load_json(ROOT / "data" / "reference" / "MVKR-S01.json")
    s1_agents = {
        "hospital_agent": HospitalAgent(
            ROOT / "medverse" / "agents" / "mandates" / "hospital_agent.json"
        ),
        "cyber_network_agent": CyberNetworkAgent(
            ROOT / "medverse" / "agents" / "mandates" / "cyber_network_agent.json"
        ),
    }
    s1_assessments = {}
    for event in s1["events"]:
        for agent_id, obs in deliver_s1(event).items():
            s1_assessments[event["event_id"]] = s1_agents[agent_id].assess(obs)

    s1_decision = DeterministicCoordinator().coordinate(s1_assessments)
    checks.append(check(
        "S1_regression_unchanged",
        s1_decision.coordination_state == "COMPLEMENTARY_RISK"
        and s1_decision.rationale_code
        == "HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST"
        and s1_decision.human_review_required is True,
        s1_decision.to_dict(),
        "frozen Gate 5 S1 behavior",
    ))

    with (OUT / "gate11b_checks.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "observed", "expected"],
        )
        writer.writeheader()
        writer.writerows(checks)

    (OUT / "gate11b_trace.json").write_text(
        json.dumps(trace, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)
    gate_pass = passed == total

    status = {
        "gate": "GATE_11B_S2_S4_DETERMINISTIC_EXTENSION",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "scenario_families_validated": [
            "S2_CARE_VS_RESEARCH",
            "S3_STALE_DT_AI_RECOMMENDATION",
            "S4_UNAUTHORIZED_DISCLOSURE",
        ],
        "new_agents": [
            "privacy_agent",
            "research_irb_agent",
            "regulator_agent",
        ],
        "final_benchmark_results_generated": False,
    }

    (OUT / "gate11b_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 11B FAILED. Diagnose the deterministic institutional "
            "extension before benchmarking S2-S4."
        )

    print(
        "\nFULL GATE 11B PASS — S2-S4 deterministic institutional "
        "semantics validated. Eligible for Gate 11C final benchmarking."
    )

if __name__ == "__main__":
    main()
