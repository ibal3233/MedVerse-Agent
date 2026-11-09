from __future__ import annotations

from copy import deepcopy

KNOWN_AGENTS = {
    "privacy_agent",
    "research_irb_agent",
    "regulator_agent",
}

ROUTE_POLICY = {
    "CONSENT_SCOPE_UPDATE": ["privacy_agent"],
    "RESEARCH_USE_REQUEST": ["research_irb_agent"],
    "DT_VALIDITY_ALERT": ["regulator_agent"],
    "HIGH_IMPACT_AI_REQUEST": ["regulator_agent"],
    "DISCLOSURE_REQUEST": ["privacy_agent"],
}

def route_event(event):
    event_type = event["event_type"]
    if event_type not in ROUTE_POLICY:
        raise ValueError(f"No institutional routing rule for event type: {event_type}")

    recipients = list(ROUTE_POLICY[event_type])
    declared = list(event.get("visible_to", []))

    if sorted(recipients) != sorted(declared):
        raise ValueError(
            f"Scenario visibility mismatch for {event['event_id']}: "
            f"routing policy={recipients}, scenario visible_to={declared}"
        )
    return recipients

def build_observation(agent_id, event):
    if agent_id not in KNOWN_AGENTS:
        raise ValueError(f"Unknown institutional agent_id: {agent_id}")

    recipients = route_event(event)
    if agent_id not in recipients:
        raise PermissionError(
            f"{agent_id} is not authorized to observe event {event['event_id']}"
        )

    return {
        "agent_id": agent_id,
        "event_id": event["event_id"],
        "t": event["t"],
        "event_type": event["event_type"],
        "payload": deepcopy(event["payload"]),
    }

def deliver_event(event):
    return {
        agent_id: build_observation(agent_id, event)
        for agent_id in route_event(event)
    }
