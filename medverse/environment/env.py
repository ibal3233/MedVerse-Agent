from __future__ import annotations

from copy import deepcopy

from medverse.environment.state import (
    MedVerseState,
    ClinicalState,
    NetworkState,
    SecurityState,
    DigitalTwinState,
)

class MedVerseEnvironment:
    def __init__(self):
        self._initial_state = MedVerseState(
            clinical=ClinicalState(),
            network=NetworkState(),
            security=SecurityState(),
            dt=DigitalTwinState(),
        )
        self.state = deepcopy(self._initial_state)

    def reset(self):
        self.state = deepcopy(self._initial_state)
        return deepcopy(self.state)

    def step(self, event):
        self._validate_event_time(event)

        event_type = event["event_type"]
        payload = event["payload"]

        if event_type == "CLINICAL_ALARM":
            self._apply_clinical_event(payload)
        elif event_type == "NETWORK_DEGRADATION":
            self._apply_network_event(payload)
        elif event_type == "DEVICE_AUTH_ANOMALY":
            self._apply_security_event(payload)
        else:
            raise ValueError(f"Unknown event type: {event_type}")

        self.state.dt.last_event_t = float(event["t"])
        self._recompute_dt_validity()
        self._validate_state()

        return deepcopy(self.state)

    def _apply_clinical_event(self, payload):
        if "SpO2" in payload:
            self.state.clinical.spo2 = float(payload["SpO2"])
        if "heart_rate" in payload:
            self.state.clinical.heart_rate = float(payload["heart_rate"])

    def _apply_network_event(self, payload):
        if "packet_loss" in payload:
            self.state.network.packet_loss = float(payload["packet_loss"])
        if "rtt_ms" in payload:
            self.state.network.rtt_ms = float(payload["rtt_ms"])
        if "jitter_ms" in payload:
            self.state.network.jitter_ms = float(payload["jitter_ms"])

    def _apply_security_event(self, payload):
        if "certificate_status" in payload:
            self.state.security.certificate_status = str(payload["certificate_status"])
        if "session_origin" in payload:
            self.state.security.session_origin = str(payload["session_origin"])

    def _recompute_dt_validity(self):
        network_bad = (
            self.state.network.packet_loss >= 0.20
            or self.state.network.rtt_ms >= 500.0
            or self.state.network.jitter_ms >= 100.0
        )

        security_bad = (
            self.state.security.certificate_status in {"mismatch", "expired", "revoked"}
            or self.state.security.session_origin == "abnormal"
        )

        if security_bad:
            self.state.dt.validity = "UNVERIFIED"
            self.state.dt.trust_score = 0.0
        elif network_bad:
            self.state.dt.validity = "DEGRADED"
            self.state.dt.trust_score = 0.5
        else:
            self.state.dt.validity = "VALID"
            self.state.dt.trust_score = 1.0

    def _validate_event_time(self, event):
        t = float(event["t"])
        if t <= self.state.dt.last_event_t:
            raise ValueError(
                f"Event times must be strictly increasing. "
                f"last={self.state.dt.last_event_t}, received={t}"
            )

    def _validate_state(self):
        s = self.state

        if not (0.0 <= s.clinical.spo2 <= 100.0):
            raise ValueError(f"Invalid SpO2: {s.clinical.spo2}")

        if s.clinical.heart_rate <= 0.0:
            raise ValueError(f"Invalid heart rate: {s.clinical.heart_rate}")

        if not (0.0 <= s.network.packet_loss <= 1.0):
            raise ValueError(f"Invalid packet loss: {s.network.packet_loss}")

        if s.network.rtt_ms < 0.0:
            raise ValueError(f"Invalid RTT: {s.network.rtt_ms}")

        if s.network.jitter_ms < 0.0:
            raise ValueError(f"Invalid jitter: {s.network.jitter_ms}")

        if s.dt.validity not in {"VALID", "DEGRADED", "UNVERIFIED"}:
            raise ValueError(f"Invalid DT validity: {s.dt.validity}")

        if not (0.0 <= s.dt.trust_score <= 1.0):
            raise ValueError(f"Invalid DT trust score: {s.dt.trust_score}")
