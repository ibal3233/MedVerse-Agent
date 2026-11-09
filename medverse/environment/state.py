from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

DTValidity = Literal["VALID", "DEGRADED", "UNVERIFIED"]

@dataclass
class ClinicalState:
    spo2: float = 97.0
    heart_rate: float = 81.0

@dataclass
class NetworkState:
    packet_loss: float = 0.01
    rtt_ms: float = 24.0
    jitter_ms: float = 4.0

@dataclass
class SecurityState:
    certificate_status: str = "valid"
    session_origin: str = "normal"

@dataclass
class DigitalTwinState:
    validity: DTValidity = "VALID"
    last_event_t: float = 0.0
    trust_score: float = 1.0

@dataclass
class MedVerseState:
    clinical: ClinicalState
    network: NetworkState
    security: SecurityState
    dt: DigitalTwinState

    def to_dict(self):
        return asdict(self)
