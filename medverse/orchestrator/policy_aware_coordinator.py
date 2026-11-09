from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional


BLOCKING_BOUNDARY_STATES = {
    "OUT_OF_POLICY",
    "WRONG_JURISDICTION",
    "OUTSIDE_MANDATE",
}

EVIDENCE_BOUNDARY_STATES = {
    "INSUFFICIENT_EVIDENCE",
}

ALLOWED_COORDINATION_STATES = {
    "AGREEMENT",
    "COMPLEMENTARY",
    "CONDITIONAL_HARMONIZATION",
    "INSTITUTIONAL_CONFLICT",
    "POLICY_CONFLICT",
    "INSUFFICIENT_EVIDENCE",
    "HUMAN_AUTHORITY_REQUIRED",
}


@dataclass
class InstitutionalPosition:
    agent_id: str
    assessment_code: str
    proposed_actions: List[str]
    boundary_status: str
    enforcement: str
    policy_ids: List[str]
    requested_evidence: List[str]
    human_review_required: bool = False
    priority: str = "NORMAL"
    notes: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class HarmonizationResult:
    coordination_state: str
    accepted_actions: List[Dict[str, str]]
    blocked_actions: List[Dict[str, str]]
    conditional_steps: List[Dict[str, Any]]
    evidence_requests: List[Dict[str, str]]
    minimum_necessary_messages: List[Dict[str, str]]
    escalation_required: bool
    escalation_targets: List[str]
    rationale_code: str

    def to_dict(self):
        return asdict(self)


class MedVersePolicyAwareCoordinator:
    """
    Deterministic policy-aware institutional harmonizer.

    The coordinator does not make clinical diagnoses or legal determinations.
    It combines already-validated institutional positions under the frozen
    MedVerse benchmark rules.

    Order of reasoning:
      1. Reject invalid/blocked institutional actions.
      2. Detect evidence insufficiency.
      3. Detect authority-required conditions.
      4. Detect known institutional conflicts.
      5. Detect conditional dependencies.
      6. Otherwise classify agreement vs complementarity.
    """

    def harmonize(self, positions: List[InstitutionalPosition],
                  context: Optional[Dict[str, Any]] = None) -> HarmonizationResult:
        context = context or {}

        accepted_actions = []
        blocked_actions = []
        evidence_requests = []
        messages = []
        conditional_steps = []
        escalation_targets = []

        # ----------------------------------------------------------
        # 1. Hard policy/mandate boundary
        # ----------------------------------------------------------
        blocking = []
        insufficient = []

        for p in positions:
            if p.boundary_status in BLOCKING_BOUNDARY_STATES or p.enforcement == "BLOCK":
                blocking.append(p)
                for a in p.proposed_actions:
                    blocked_actions.append({
                        "agent_id": p.agent_id,
                        "action": a,
                        "reason": p.boundary_status,
                    })
            elif p.boundary_status in EVIDENCE_BOUNDARY_STATES or p.enforcement == "ESCALATE":
                insufficient.append(p)
            else:
                for a in p.proposed_actions:
                    accepted_actions.append({
                        "agent_id": p.agent_id,
                        "action": a,
                    })

        # If a peer action itself violates law/mandate, do not harmonize it into a plan.
        if blocking:
            return HarmonizationResult(
                coordination_state="POLICY_CONFLICT",
                accepted_actions=accepted_actions,
                blocked_actions=blocked_actions,
                conditional_steps=[],
                evidence_requests=[],
                minimum_necessary_messages=[],
                escalation_required=False,
                escalation_targets=[],
                rationale_code="INVALID_INSTITUTIONAL_ACTION_REMOVED",
            )

        # ----------------------------------------------------------
        # 2. Evidence insufficiency
        # ----------------------------------------------------------
        if insufficient:
            for p in insufficient:
                for e in p.requested_evidence or ["AUTHORIZED_EVIDENCE"]:
                    evidence_requests.append({
                        "requesting_agent": p.agent_id,
                        "evidence": e,
                    })

            return HarmonizationResult(
                coordination_state="INSUFFICIENT_EVIDENCE",
                accepted_actions=accepted_actions,
                blocked_actions=[],
                conditional_steps=[],
                evidence_requests=evidence_requests,
                minimum_necessary_messages=[],
                escalation_required=False,
                escalation_targets=[],
                rationale_code="MORE_EVIDENCE_REQUIRED_BEFORE_ACTION",
            )

        # ----------------------------------------------------------
        # 3. Explicit human authority requirement
        # ----------------------------------------------------------
        requiring_human = [p for p in positions if p.human_review_required]
        if context.get("human_authority_required") is True:
            requiring_human = requiring_human or positions[:1]

        if requiring_human and context.get("machine_resolvable") is False:
            escalation_targets = context.get(
                "escalation_targets",
                ["AUTHORIZED_HUMAN_REVIEWER"]
            )
            return HarmonizationResult(
                coordination_state="HUMAN_AUTHORITY_REQUIRED",
                accepted_actions=accepted_actions,
                blocked_actions=[],
                conditional_steps=[],
                evidence_requests=[],
                minimum_necessary_messages=[],
                escalation_required=True,
                escalation_targets=escalation_targets,
                rationale_code="NO_MACHINE_AUTHORITY_FOR_FINAL_RESOLUTION",
            )

        # ----------------------------------------------------------
        # 4. Known institutional objective conflict:
        #    care objective vs privacy/research disclosure constraint
        # ----------------------------------------------------------
        codes = {p.agent_id: p.assessment_code for p in positions}

        if context.get("institutional_conflict") == "CARE_VS_DISCLOSURE":
            # Search for policy-compliant alternative rather than immediately escalating.
            alternative = context.get(
                "compliant_alternative",
                "LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY"
            )

            conditional_steps = [{
                "step": 1,
                "owner": "privacy_agent",
                "action": "CHECK_AUTHORIZED_MINIMUM_NECESSARY_SCOPE",
            }, {
                "step": 2,
                "owner": "hospital_agent",
                "action": alternative,
                "condition": "IF_POLICY_AUTHORIZED",
            }]

            if context.get("alternative_available", True):
                return HarmonizationResult(
                    coordination_state="INSTITUTIONAL_CONFLICT",
                    accepted_actions=accepted_actions,
                    blocked_actions=[],
                    conditional_steps=conditional_steps,
                    evidence_requests=[],
                    minimum_necessary_messages=[
                        {
                            "from": "privacy_agent",
                            "to": "hospital_agent",
                            "message": "FULL_DISCLOSURE_NOT_AUTHORIZED_USE_MINIMUM_NECESSARY",
                        }
                    ],
                    escalation_required=False,
                    escalation_targets=[],
                    rationale_code="CONFLICT_RECONCILED_WITH_COMPLIANT_ALTERNATIVE",
                )

            return HarmonizationResult(
                coordination_state="HUMAN_AUTHORITY_REQUIRED",
                accepted_actions=accepted_actions,
                blocked_actions=[],
                conditional_steps=[],
                evidence_requests=[],
                minimum_necessary_messages=[],
                escalation_required=True,
                escalation_targets=[
                    "AUTHORIZED_CLINICIAN",
                    "PRIVACY_OFFICER",
                ],
                rationale_code="NO_COMPLIANT_JOINT_ACTION_FOUND",
            )

        # ----------------------------------------------------------
        # 5. Conditional dependency:
        #    clinical action depends on telemetry trust verification
        # ----------------------------------------------------------
        hospital = next((p for p in positions if p.agent_id == "hospital_agent"), None)
        cyber = next((p for p in positions if p.agent_id == "cyber_network_agent"), None)

        if (
            hospital is not None
            and cyber is not None
            and context.get("telemetry_trust") == "UNVERIFIED"
            and context.get("clinical_priority") == "URGENT"
            and context.get("requires_trusted_measurement_before_dt_use") is True
        ):
            conditional_steps = [
                {
                    "step": 1,
                    "owner": "cyber_network_agent",
                    "action": "VERIFY_DEVICE_IDENTITY_OR_TRUSTED_CHANNEL",
                },
                {
                    "step": 2,
                    "owner": "hospital_agent",
                    "action": "USE_VERIFIED_DT_MEASUREMENT",
                    "condition": "IF_TRUST_RESTORED",
                },
                {
                    "step": 2,
                    "owner": "hospital_agent",
                    "action": "USE_INDEPENDENT_PHYSICAL_MEASUREMENT",
                    "condition": "IF_TRUST_NOT_RESTORED",
                },
            ]
            messages = [
                {
                    "from": "cyber_network_agent",
                    "to": "hospital_agent",
                    "message": "TELEMETRY_TRUST=UNVERIFIED",
                },
                {
                    "from": "hospital_agent",
                    "to": "cyber_network_agent",
                    "message": "CLINICAL_PRIORITY=URGENT",
                },
            ]
            return HarmonizationResult(
                coordination_state="CONDITIONAL_HARMONIZATION",
                accepted_actions=accepted_actions,
                blocked_actions=[],
                conditional_steps=conditional_steps,
                evidence_requests=[],
                minimum_necessary_messages=messages,
                escalation_required=False,
                escalation_targets=[],
                rationale_code="URGENT_CLINICAL_ACTION_DEPENDS_ON_TELEMETRY_TRUST",
            )

        # ----------------------------------------------------------
        # 6. Complementary clinical + cyber risk
        # ----------------------------------------------------------
        if (
            hospital is not None
            and cyber is not None
            and hospital.assessment_code == "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION"
            and cyber.assessment_code in {
                "TELEMETRY_RELIABILITY_DEGRADED",
                "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN",
            }
        ):
            messages = [
                {
                    "from": "cyber_network_agent",
                    "to": "hospital_agent",
                    "message": "TELEMETRY_TRUST=UNVERIFIED",
                },
                {
                    "from": "hospital_agent",
                    "to": "cyber_network_agent",
                    "message": "CLINICAL_PRIORITY=URGENT",
                },
            ]
            return HarmonizationResult(
                coordination_state="COMPLEMENTARY",
                accepted_actions=accepted_actions,
                blocked_actions=[],
                conditional_steps=[],
                evidence_requests=[],
                minimum_necessary_messages=messages,
                escalation_required=False,
                escalation_targets=[],
                rationale_code="HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST",
            )

        # ----------------------------------------------------------
        # 7. Agreement: all valid positions are directionally aligned
        # ----------------------------------------------------------
        if context.get("all_agents_agree") is True:
            return HarmonizationResult(
                coordination_state="AGREEMENT",
                accepted_actions=accepted_actions,
                blocked_actions=[],
                conditional_steps=[],
                evidence_requests=[],
                minimum_necessary_messages=[],
                escalation_required=False,
                escalation_targets=[],
                rationale_code="ALL_VALID_INSTITUTIONAL_POSITIONS_ALIGNED",
            )

        # Conservative default:
        # valid positions without explicit conflict are complementary.
        return HarmonizationResult(
            coordination_state="COMPLEMENTARY",
            accepted_actions=accepted_actions,
            blocked_actions=[],
            conditional_steps=[],
            evidence_requests=[],
            minimum_necessary_messages=[],
            escalation_required=False,
            escalation_targets=[],
            rationale_code="MULTI_DOMAIN_VALID_ACTIONS_CAN_COEXIST",
        )
