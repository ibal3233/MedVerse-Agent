from pathlib import Path
import json
import pytest

from medverse.routing.router import (
    route_event,
    build_observation,
)

ROOT = Path(__file__).resolve().parents[1]

def load_scenario():
    return json.loads(
        (ROOT / "data" / "reference" / "MVKR-S01.json")
        .read_text(encoding="utf-8")
    )

def test_routes_match_reference_visibility():
    s = load_scenario()
    for event in s["events"]:
        assert sorted(route_event(event)) == sorted(event["visible_to"])

def test_hospital_denied_network_event():
    s = load_scenario()
    with pytest.raises(PermissionError):
        build_observation("hospital_agent", s["events"][1])

def test_cyber_denied_clinical_event():
    s = load_scenario()
    with pytest.raises(PermissionError):
        build_observation("cyber_network_agent", s["events"][0])

def test_observation_payloads_are_minimal():
    s = load_scenario()
    h = build_observation("hospital_agent", s["events"][0])
    c = build_observation("cyber_network_agent", s["events"][1])

    assert set(h["payload"]) == {"SpO2", "heart_rate"}
    assert set(c["payload"]) == {"packet_loss", "rtt_ms", "jitter_ms"}
