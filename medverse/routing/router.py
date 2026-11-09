from __future__ import annotations

from copy import deepcopy
from typing import Dict, Any, List

KNOWN_AGENTS = {
    "hospital_agent",
    "cyber_network_agent",
}

ROUTE_POLICY = {
    "CLINICAL_ALARM": ["hospital_agent"],
    "NETWORK_DEGRADATION": ["cyber_network_agent"],
    "DEVICE_AUTH_ANOMALY": ["cyber_network_agent"],
}

def route_event(event: Dict[str, Any]) -> List[str]:
    event_type = event["event_type"]

    if event_type not in ROUTE_POLICY:
        raise ValueError(f"No routing rule for event type: {event_type}")

    recipients = list(ROUTE_POLICY[event_type])

    declared = list(event.get("visible_to", []))
    if sorted(recipients) != sorted(declared):
        raise ValueError(
            f"Scenario visibility mismatch for {event['event_id']}: "
            f"routing policy={recipients}, scenario visible_to={declared}"
        )

    return recipients

def build_observation(agent_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    if agent_id not in KNOWN_AGENTS:
        raise ValueError(f"Unknown agent_id: {agent_id}")

    recipients = route_event(event)

    if agent_id not in recipients:
        raise PermissionError(
            f"{agent_id} is not authorized to observe event {event['event_id']}"
        )

    # Minimal event-scoped observation. The full world state is intentionally
    # NOT copied into the observation.
    return {
        "agent_id": agent_id,
        "event_id": event["event_id"],
        "t": event["t"],
        "event_type": event["event_type"],
        "payload": deepcopy(event["payload"]),
    }

def deliver_event(event: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    deliveries = {}

    for agent_id in route_event(event):
        deliveries[agent_id] = build_observation(agent_id, event)

    return deliveries
