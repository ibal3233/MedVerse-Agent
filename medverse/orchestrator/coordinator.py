from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

@dataclass
class CoordinationDecision:
    coordination_state: str
    rationale_code: str
    joint_actions: List[str]
    delegated_actions: Dict[str, List[str]]
    human_review_required: bool
    required_information_exchange: List[dict]

    def to_dict(self):
        return asdict(self)

class DeterministicCoordinator:
    '''
    Gate 5 deterministic coordination layer.

    No LLM.
    No RAG.
    No learned policy.
    No majority voting.

    The coordinator combines already-validated institutional assessments.
    '''

    HOSPITAL_AGENT = "hospital_agent"
    CYBER_AGENT = "cyber_network_agent"

    def coordinate(self, assessments_by_event):
        e1 = assessments_by_event.get("E1")
        e2 = assessments_by_event.get("E2")
        e3 = assessments_by_event.get("E3")

        # E1 is not mandatory for all coordination cases.
        # Gate 9 exercises technical-only and no-risk counterfactuals.
        # Preserve full-S1 behavior while allowing the already-defined
        # TECHNICAL_VERIFICATION and MONITOR branches to be reachable.
        clinical_high = (
            e1 is not None
            and e1.agent_id == self.HOSPITAL_AGENT
            and e1.assessment_code == "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION"
            and e1.risk == "HIGH"
        )

        telemetry_degraded = (
            e2 is not None
            and e2.agent_id == self.CYBER_AGENT
            and e2.assessment_code == "TELEMETRY_RELIABILITY_DEGRADED"
            and e2.risk == "HIGH"
        )

        device_uncertain = (
            e3 is not None
            and e3.agent_id == self.CYBER_AGENT
            and e3.assessment_code == "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN"
            and e3.risk == "HIGH"
        )

        if clinical_high and (telemetry_degraded or device_uncertain):
            delegated = {
                self.HOSPITAL_AGENT: [
                    "CONTACT_PATIENT",
                    "VERIFY_MEASUREMENT",
                    "REQUEST_HUMAN_CLINICAL_REVIEW",
                ],
                self.CYBER_AGENT: [
                    "MARK_TELEMETRY_UNVERIFIED",
                    "VERIFY_DEVICE_IDENTITY",
                    "PRESERVE_TECHNICAL_LOGS",
                ],
            }

            if device_uncertain:
                delegated[self.CYBER_AGENT].append(
                    "ISOLATE_SUSPECT_SESSION"
                )

            if telemetry_degraded:
                delegated[self.CYBER_AGENT].append(
                    "REQUEST_ALTERNATIVE_CHANNEL"
                )

            required_exchange = [
                {
                    "from": self.CYBER_AGENT,
                    "to": self.HOSPITAL_AGENT,
                    "message_type": "TELEMETRY_TRUST_STATUS",
                    "payload": {
                        "telemetry_trust": "UNVERIFIED"
                        if device_uncertain
                        else "DEGRADED"
                    },
                },
                {
                    "from": self.HOSPITAL_AGENT,
                    "to": self.CYBER_AGENT,
                    "message_type": "CLINICAL_PRIORITY",
                    "payload": {
                        "priority": "URGENT"
                    },
                },
            ]

            joint_actions = sorted({
                action
                for actions in delegated.values()
                for action in actions
            } | {"USE_INDEPENDENT_MEASUREMENT_CHANNEL"})

            return CoordinationDecision(
                coordination_state="COMPLEMENTARY_RISK",
                rationale_code="HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST",
                joint_actions=joint_actions,
                delegated_actions=delegated,
                human_review_required=True,
                required_information_exchange=required_exchange,
            )

        if clinical_high:
            delegated = {
                self.HOSPITAL_AGENT: [
                    "CONTACT_PATIENT",
                    "VERIFY_MEASUREMENT",
                    "REQUEST_HUMAN_CLINICAL_REVIEW",
                ]
            }
            return CoordinationDecision(
                coordination_state="SINGLE_DOMAIN_ESCALATION",
                rationale_code="HIGH_CLINICAL_RISK_ONLY",
                joint_actions=sorted(delegated[self.HOSPITAL_AGENT]),
                delegated_actions=delegated,
                human_review_required=True,
                required_information_exchange=[],
            )

        if telemetry_degraded or device_uncertain:
            delegated = {
                self.CYBER_AGENT: [
                    "MARK_TELEMETRY_UNVERIFIED",
                    "PRESERVE_TECHNICAL_LOGS",
                ]
            }
            if telemetry_degraded:
                delegated[self.CYBER_AGENT].append(
                    "REQUEST_ALTERNATIVE_CHANNEL"
                )
            if device_uncertain:
                delegated[self.CYBER_AGENT] += [
                    "VERIFY_DEVICE_IDENTITY",
                    "ISOLATE_SUSPECT_SESSION",
                ]

            return CoordinationDecision(
                coordination_state="TECHNICAL_VERIFICATION",
                rationale_code="LOW_TELEMETRY_TRUST_ONLY",
                joint_actions=sorted(set(delegated[self.CYBER_AGENT])),
                delegated_actions=delegated,
                human_review_required=False,
                required_information_exchange=[],
            )

        return CoordinationDecision(
            coordination_state="MONITOR",
            rationale_code="NO_COORDINATION_ESCALATION",
            joint_actions=[],
            delegated_actions={},
            human_review_required=False,
            required_information_exchange=[],
        )
