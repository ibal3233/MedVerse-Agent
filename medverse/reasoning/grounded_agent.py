from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

@dataclass
class GroundedInstitutionalAssessment:
    agent_id: str
    assessment_code: str
    risk: str
    recommended_actions: List[str]
    human_review_required: bool

    # Attribution layer
    dt_evidence_used: List[str]
    policy_evidence_used: List[str]
    open_data_evidence_used: List[str]
    provenance_evidence_used: List[str]

    # Explicit safety declarations
    patient_level_inference_from_population_data: bool
    unauthorized_evidence_used: bool

    rationale: str

    def to_dict(self):
        return asdict(self)


class DataPolicyGroundedAgent:
    """
    Deterministic reference reasoner over an EvidenceBundle.

    This layer is intentionally not an LLM and does not replace the frozen
    institutional mandate logic. Its purpose is to make evidence attribution
    explicit and machine-checkable.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    def _policy_ids(self, bundle) -> List[str]:
        ids = []
        for r in bundle.policy_records:
            rid = r.get("chunk_id") or r.get("document_id")
            if rid:
                ids.append(str(rid))
        return ids

    def _provenance_refs(self, bundle) -> List[str]:
        fields = bundle.provenance.get("dt_fields", [])
        return [f"dt_domain:{x}" for x in fields]

    def assess(self, bundle) -> GroundedInstitutionalAssessment:
        if bundle.agent_id != self.agent_id:
            raise PermissionError(
                f"Bundle for {bundle.agent_id} cannot be assessed by {self.agent_id}"
            )

        if self.agent_id == "hospital_agent":
            return self._assess_hospital(bundle)
        if self.agent_id == "cyber_network_agent":
            return self._assess_cyber(bundle)
        if self.agent_id == "privacy_agent":
            return self._assess_privacy(bundle)
        if self.agent_id == "research_irb_agent":
            return self._assess_research(bundle)
        if self.agent_id == "regulator_agent":
            return self._assess_regulator(bundle)

        raise ValueError(f"Unsupported agent_id: {self.agent_id}")

    def _assess_hospital(self, b):
        clinical = b.digital_twin_view.get("clinical", {})
        spo2 = clinical.get("SpO2")
        hr = clinical.get("heart_rate")

        high = (
            spo2 is not None and float(spo2) <= 85.0
        ) or (
            hr is not None and float(hr) >= 120.0
        )

        epi_used = []
        if b.epidemiological_context is not None:
            # Population context may be acknowledged as background context,
            # but never converted into patient-level disease inference.
            epi_used = ["NCC_population_epidemiological_context"]

        return GroundedInstitutionalAssessment(
            agent_id=self.agent_id,
            assessment_code=(
                "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION"
                if high else "NO_CRITICAL_CLINICAL_TRIGGER"
            ),
            risk="HIGH" if high else "LOW",
            recommended_actions=(
                [
                    "VERIFY_MEASUREMENT",
                    "CONTACT_PATIENT",
                    "REQUEST_HUMAN_CLINICAL_REVIEW",
                ]
                if high else []
            ),
            human_review_required=bool(high),
            dt_evidence_used=[
                x for x in ["clinical.SpO2", "clinical.heart_rate"]
                if clinical.get(x.split(".")[-1]) is not None
            ],
            policy_evidence_used=self._policy_ids(b),
            open_data_evidence_used=epi_used,
            provenance_evidence_used=self._provenance_refs(b),
            patient_level_inference_from_population_data=False,
            unauthorized_evidence_used=False,
            rationale=(
                "Clinical deterioration is derived from authorized patient-state "
                "measurements. NCC data, when present, remains descriptive population context."
            ),
        )

    def _assess_cyber(self, b):
        net = b.digital_twin_view.get("network", {})
        sec = b.digital_twin_view.get("security", {})

        degraded = (
            float(net.get("packet_loss", 0.0)) >= 0.20
            or float(net.get("rtt_ms", 0.0)) >= 500.0
            or float(net.get("jitter_ms", 0.0)) >= 100.0
        )
        integrity_bad = (
            str(sec.get("certificate_status", "valid"))
            in {"mismatch", "expired", "revoked"}
            or str(sec.get("session_origin", "normal")) == "abnormal"
        )

        if integrity_bad:
            code = "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN"
            actions = [
                "VERIFY_DEVICE_IDENTITY",
                "ISOLATE_SUSPECT_SESSION",
                "MARK_TELEMETRY_UNVERIFIED",
                "PRESERVE_TECHNICAL_LOGS",
            ]
            risk = "HIGH"
        elif degraded:
            code = "TELEMETRY_RELIABILITY_DEGRADED"
            actions = [
                "MARK_TELEMETRY_UNVERIFIED",
                "REQUEST_ALTERNATIVE_CHANNEL",
                "PRESERVE_TECHNICAL_LOGS",
            ]
            risk = "HIGH"
        else:
            code = "TECHNICAL_STATE_ACCEPTABLE"
            actions = []
            risk = "LOW"

        return GroundedInstitutionalAssessment(
            agent_id=self.agent_id,
            assessment_code=code,
            risk=risk,
            recommended_actions=actions,
            human_review_required=False,
            dt_evidence_used=[
                "network.packet_loss",
                "network.rtt_ms",
                "network.jitter_ms",
                "security.certificate_status",
                "security.session_origin",
            ],
            policy_evidence_used=self._policy_ids(b),
            open_data_evidence_used=[],
            provenance_evidence_used=self._provenance_refs(b),
            patient_level_inference_from_population_data=False,
            unauthorized_evidence_used=False,
            rationale=(
                "Telemetry reliability and integrity are assessed only from the "
                "authorized network/security Digital-Twin view."
            ),
        )

    def _assess_privacy(self, b):
        consent = b.digital_twin_view.get("consent", {})

        research_allowed = consent.get("research_use_allowed")
        care_allowed = consent.get("care_use_allowed")
        disclosure_allowed = consent.get("disclosure_authorized")
        minimum_necessary = consent.get("minimum_necessary")

        if care_allowed is True and research_allowed is False:
            code = "CARE_ALLOWED_RESEARCH_WITHDRAWN"
            actions = [
                "ALLOW_TREATMENT_USE",
                "BLOCK_RESEARCH_USE",
                "REQUEST_PRIVACY_REVIEW",
                "PRESERVE_PRIVACY_AUDIT_LOG",
            ]
            high = True
        elif disclosure_allowed is False or minimum_necessary is False:
            code = "UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST"
            actions = [
                "DENY_UNAUTHORIZED_DISCLOSURE",
                "LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY",
                "PRESERVE_PRIVACY_AUDIT_LOG",
            ]
            high = True
        else:
            code = "PRIVACY_SCOPE_ACCEPTABLE"
            actions = []
            high = False

        return GroundedInstitutionalAssessment(
            agent_id=self.agent_id,
            assessment_code=code,
            risk="HIGH" if high else "LOW",
            recommended_actions=actions,
            human_review_required=(
                code == "CARE_ALLOWED_RESEARCH_WITHDRAWN"
            ),
            dt_evidence_used=[
                f"consent.{k}" for k in sorted(consent)
            ],
            policy_evidence_used=self._policy_ids(b),
            open_data_evidence_used=[],
            provenance_evidence_used=self._provenance_refs(b),
            patient_level_inference_from_population_data=False,
            unauthorized_evidence_used=False,
            rationale=(
                "Privacy assessment is grounded in consent/disclosure state "
                "and authorized privacy-policy evidence only."
            ),
        )

    def _assess_research(self, b):
        research = b.digital_twin_view.get("research", {})
        consent = b.digital_twin_view.get("consent", {})

        status = (
            research.get("participant_consent_status")
            or consent.get("research_consent_status")
        )

        blocked = status in {"withdrawn", "not_active"}

        epi_used = []
        if b.epidemiological_context is not None:
            epi_used = ["NCC_population_epidemiological_context"]

        return GroundedInstitutionalAssessment(
            agent_id=self.agent_id,
            assessment_code=(
                "RESEARCH_PROCESSING_NOT_AUTHORIZED"
                if blocked else "RESEARCH_SCOPE_ACCEPTABLE"
            ),
            risk="HIGH" if blocked else "LOW",
            recommended_actions=(
                [
                    "BLOCK_RESEARCH_PROCESSING",
                    "REQUEST_IRB_REVIEW",
                    "PRESERVE_RESEARCH_AUDIT_LOG",
                ]
                if blocked else []
            ),
            human_review_required=bool(blocked),
            dt_evidence_used=[
                *[f"research.{k}" for k in sorted(research)],
                *[f"consent.{k}" for k in sorted(consent)],
            ],
            policy_evidence_used=self._policy_ids(b),
            open_data_evidence_used=epi_used,
            provenance_evidence_used=self._provenance_refs(b),
            patient_level_inference_from_population_data=False,
            unauthorized_evidence_used=False,
            rationale=(
                "Research authorization is determined from consent/research state. "
                "NCC data may provide population context but not participant-level inference."
            ),
        )

    def _assess_regulator(self, b):
        ai = b.digital_twin_view.get("ai_state", {})
        validity = b.digital_twin_view.get("validity")
        quality = b.digital_twin_view.get("quality", {})

        high_impact = ai.get("decision_impact") == "high"
        untrusted = (
            validity in {"DEGRADED", "UNVERIFIED"}
            or float(quality.get("integrity", 1.0)) < 1.0
            or float(quality.get("freshness", 1.0)) < 0.5
        )

        block = high_impact and untrusted

        return GroundedInstitutionalAssessment(
            agent_id=self.agent_id,
            assessment_code=(
                "HIGH_IMPACT_AI_REQUIRES_VALIDATED_EVIDENCE_AND_OVERSIGHT"
                if block else "AI_USE_WITHIN_CURRENT_EVIDENCE_BOUND"
            ),
            risk="HIGH" if block else "LOW",
            recommended_actions=(
                [
                    "BLOCK_AUTOMATED_HIGH_IMPACT_ACTION",
                    "REQUIRE_FRESH_DT_VERIFICATION",
                    "REQUEST_HUMAN_OVERSIGHT",
                    "PRESERVE_REGULATORY_AUDIT_LOG",
                ]
                if block else []
            ),
            human_review_required=bool(block),
            dt_evidence_used=[
                *[f"ai_state.{k}" for k in sorted(ai)],
                "validity",
                "quality.freshness",
                "quality.integrity",
            ],
            policy_evidence_used=self._policy_ids(b),
            open_data_evidence_used=[],
            provenance_evidence_used=self._provenance_refs(b),
            patient_level_inference_from_population_data=False,
            unauthorized_evidence_used=False,
            rationale=(
                "High-impact AI use is bounded by authorized AI state, DT quality, "
                "and regulator policy evidence."
            ),
        )
