from __future__ import annotations

ALLOWED_MESSAGE_TYPES = {
    ("cyber_network_agent", "hospital_agent"): {
        "TELEMETRY_TRUST_STATUS"
    },
    ("hospital_agent", "cyber_network_agent"): {
        "CLINICAL_PRIORITY"
    },
}

ALLOWED_PAYLOAD_FIELDS = {
    "TELEMETRY_TRUST_STATUS": {"telemetry_trust"},
    "CLINICAL_PRIORITY": {"priority"},
}

def validate_coordination_message(message):
    sender = message["from"]
    receiver = message["to"]
    message_type = message["message_type"]
    payload = message["payload"]

    allowed_types = ALLOWED_MESSAGE_TYPES.get(
        (sender, receiver),
        set(),
    )

    if message_type not in allowed_types:
        raise PermissionError(
            f"Message type {message_type} not allowed from "
            f"{sender} to {receiver}"
        )

    allowed_fields = ALLOWED_PAYLOAD_FIELDS[message_type]
    extra = set(payload.keys()) - allowed_fields

    if extra:
        raise PermissionError(
            f"Unauthorized payload fields for {message_type}: "
            f"{sorted(extra)}"
        )

    return True
