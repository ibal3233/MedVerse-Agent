from pathlib import Path
import json
import pytest

from medverse.routing.router import deliver_event
from medverse.agents.hospital import HospitalAgent
from medverse.agents.cyber_network import CyberNetworkAgent
from medverse.orchestrator.coordinator import DeterministicCoordinator
from medverse.orchestrator.message_policy import validate_coordination_message

ROOT = Path(__file__).resolve().parents[1]

def build_assessments():
    scenario = json.loads(
        (ROOT / "data" / "reference" / "MVKR-S01.json")
        .read_text(encoding="utf-8")
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

    out = {}
    for event in scenario["events"]:
        for agent_id, observation in deliver_event(event).items():
            out[event["event_id"]] = agents[agent_id].assess(observation)
    return out

def test_coordination_state():
    d = DeterministicCoordinator().coordinate(build_assessments())
    assert d.coordination_state == "COMPLEMENTARY_RISK"
    assert d.human_review_required is True

def test_minimum_necessary_messages():
    d = DeterministicCoordinator().coordinate(build_assessments())
    for message in d.required_information_exchange:
        assert validate_coordination_message(message) is True

def test_rejects_excess_clinical_payload():
    with pytest.raises(PermissionError):
        validate_coordination_message({
            "from":"hospital_agent",
            "to":"cyber_network_agent",
            "message_type":"CLINICAL_PRIORITY",
            "payload":{"priority":"URGENT","SpO2":78},
        })
