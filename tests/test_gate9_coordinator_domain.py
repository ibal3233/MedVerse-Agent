from pathlib import Path
import json

from medverse.routing.router import deliver_event
from medverse.agents.hospital import HospitalAgent
from medverse.agents.cyber_network import CyberNetworkAgent
from medverse.orchestrator.coordinator import DeterministicCoordinator

ROOT = Path(__file__).resolve().parents[1]

def _assessments():
    scenario = json.loads(
        (ROOT / "data" / "reference" / "MVKR-S01.json")
        .read_text(encoding="utf-8")
    )
    agents = {
        "hospital_agent": HospitalAgent(
            ROOT / "medverse" / "agents" / "mandates" / "hospital_agent.json"
        ),
        "cyber_network_agent": CyberNetworkAgent(
            ROOT / "medverse" / "agents" / "mandates" / "cyber_network_agent.json"
        ),
    }
    out = {}
    for event in scenario["events"]:
        for agent_id, obs in deliver_event(event).items():
            out[event["event_id"]] = agents[agent_id].assess(obs)
    return out

def test_full_s1_behavior_unchanged():
    a = _assessments()
    d = DeterministicCoordinator().coordinate(a)
    assert d.coordination_state == "COMPLEMENTARY_RISK"
    assert d.rationale_code == "HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST"
    assert d.human_review_required is True

def test_clinical_only_reachable():
    a = _assessments()
    d = DeterministicCoordinator().coordinate({"E1": a["E1"]})
    assert d.coordination_state == "SINGLE_DOMAIN_ESCALATION"
    assert d.human_review_required is True

def test_technical_only_reachable():
    a = _assessments()
    d = DeterministicCoordinator().coordinate({
        "E2": a["E2"],
        "E3": a["E3"],
    })
    assert d.coordination_state == "TECHNICAL_VERIFICATION"
    assert d.human_review_required is False

def test_no_risk_reachable():
    d = DeterministicCoordinator().coordinate({})
    assert d.coordination_state == "MONITOR"
    assert d.human_review_required is False
