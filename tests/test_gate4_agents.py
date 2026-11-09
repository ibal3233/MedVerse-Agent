from pathlib import Path
import json
import pytest

from medverse.routing.router import build_observation
from medverse.agents.hospital import HospitalAgent
from medverse.agents.cyber_network import CyberNetworkAgent

ROOT = Path(__file__).resolve().parents[1]

def scenario():
    return json.loads(
        (ROOT / "data" / "reference" / "MVKR-S01.json")
        .read_text(encoding="utf-8")
    )

def hospital():
    return HospitalAgent(
        ROOT / "medverse" / "agents" / "mandates"
        / "hospital_agent.json"
    )

def cyber():
    return CyberNetworkAgent(
        ROOT / "medverse" / "agents" / "mandates"
        / "cyber_network_agent.json"
    )

def test_hospital_assessment():
    e1 = scenario()["events"][0]
    obs = build_observation("hospital_agent", e1)
    a = hospital().assess(obs)
    assert a.assessment_code == "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION"
    assert a.risk == "HIGH"
    assert a.human_review_required is True

def test_cyber_network_assessment():
    e2 = scenario()["events"][1]
    obs = build_observation("cyber_network_agent", e2)
    a = cyber().assess(obs)
    assert a.assessment_code == "TELEMETRY_RELIABILITY_DEGRADED"
    assert a.risk == "HIGH"

def test_hospital_rejects_network_action():
    with pytest.raises(PermissionError):
        hospital().validate_actions(["ISOLATE_SUSPECT_SESSION"])

def test_cyber_rejects_clinical_action():
    with pytest.raises(PermissionError):
        cyber().validate_actions(["CONTACT_PATIENT"])
