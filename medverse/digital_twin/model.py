from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Literal, Optional
import math

DTValidity = Literal["VALID", "DEGRADED", "UNVERIFIED"]

@dataclass
class ProvenanceRecord:
    field_name: str
    source_type: str
    source_id: str
    observed_at: float
    ingestion_method: str = "controlled_event"
    authority: Optional[str] = None

@dataclass
class DigitalTwinQuality:
    freshness: float = 1.0
    integrity: float = 1.0
    completeness: float = 1.0
    provenance: float = 1.0
    uncertainty: float = 0.0

    def validate(self):
        for name in [
            "freshness", "integrity", "completeness",
            "provenance", "uncertainty"
        ]:
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0,1], got {value}")

@dataclass
class PatientDigitalTwin:
    t: float = 0.0

    clinical: Dict[str, Any] = field(default_factory=lambda: {
        "SpO2": 97.0,
        "heart_rate": 81.0,
    })

    patient_context: Dict[str, Any] = field(default_factory=dict)

    network: Dict[str, Any] = field(default_factory=lambda: {
        "packet_loss": 0.01,
        "rtt_ms": 24.0,
        "jitter_ms": 4.0,
    })

    security: Dict[str, Any] = field(default_factory=lambda: {
        "certificate_status": "valid",
        "session_origin": "normal",
    })

    consent: Dict[str, Any] = field(default_factory=dict)
    research: Dict[str, Any] = field(default_factory=dict)
    ai_state: Dict[str, Any] = field(default_factory=dict)

    quality: DigitalTwinQuality = field(default_factory=DigitalTwinQuality)
    provenance_records: List[ProvenanceRecord] = field(default_factory=list)

    # Diagnostic display category derived from quality/infrastructure state.
    validity: DTValidity = "VALID"

    def update_domain(
        self,
        domain: str,
        payload: Dict[str, Any],
        *,
        t: float,
        source_type: str,
        source_id: str,
        authority: Optional[str] = None,
    ):
        if t < self.t:
            raise ValueError(
                f"Digital twin time cannot move backwards: {t} < {self.t}"
            )

        target = getattr(self, domain)
        if not isinstance(target, dict):
            raise ValueError(f"Unsupported DT domain: {domain}")

        for key, value in payload.items():
            target[key] = value
            self.provenance_records.append(
                ProvenanceRecord(
                    field_name=f"{domain}.{key}",
                    source_type=source_type,
                    source_id=source_id,
                    observed_at=float(t),
                    authority=authority,
                )
            )

        self.t = float(t)
        self.recompute_quality()

    def recompute_quality(self, current_t: Optional[float] = None):
        now = self.t if current_t is None else float(current_t)

        # Freshness is an explicit, monotone age function for the sandbox.
        # Half-life parameter is a modeling choice, not a clinical standard.
        latest_obs = max(
            [p.observed_at for p in self.provenance_records],
            default=self.t,
        )
        age = max(0.0, now - latest_obs)
        freshness = math.exp(-age / 300.0)

        network_bad = (
            float(self.network.get("packet_loss", 0.0)) >= 0.20
            or float(self.network.get("rtt_ms", 0.0)) >= 500.0
            or float(self.network.get("jitter_ms", 0.0)) >= 100.0
        )

        security_bad = (
            str(self.security.get("certificate_status", "valid"))
            in {"mismatch", "expired", "revoked"}
            or str(self.security.get("session_origin", "normal")) == "abnormal"
        )

        integrity = 0.0 if security_bad else 1.0

        # Completeness is evaluated only against fields required by the
        # implemented S1 digital-twin core, not all possible healthcare fields.
        required = {
            "clinical.SpO2": self.clinical.get("SpO2"),
            "clinical.heart_rate": self.clinical.get("heart_rate"),
            "network.packet_loss": self.network.get("packet_loss"),
            "network.rtt_ms": self.network.get("rtt_ms"),
            "network.jitter_ms": self.network.get("jitter_ms"),
            "security.certificate_status": self.security.get("certificate_status"),
            "security.session_origin": self.security.get("session_origin"),
        }
        completeness = (
            sum(v is not None for v in required.values()) / len(required)
        )

        provenance = 1.0 if self.provenance_records else 0.5

        # Uncertainty is metadata-quality uncertainty, not disease probability.
        uncertainty = max(
            1.0 - freshness,
            1.0 - integrity,
            1.0 - completeness,
            0.5 if network_bad else 0.0,
        )

        self.quality = DigitalTwinQuality(
            freshness=float(freshness),
            integrity=float(integrity),
            completeness=float(completeness),
            provenance=float(provenance),
            uncertainty=float(min(1.0, uncertainty)),
        )
        self.quality.validate()

        if security_bad:
            self.validity = "UNVERIFIED"
        elif network_bad or freshness < 0.5 or completeness < 1.0:
            self.validity = "DEGRADED"
        else:
            self.validity = "VALID"

    def provenance_for(self, field_name: str):
        return [
            asdict(p)
            for p in self.provenance_records
            if p.field_name == field_name
        ]

    def to_dict(self):
        return asdict(self)
