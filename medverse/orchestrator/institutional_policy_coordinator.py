from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List

@dataclass
class InstitutionalPolicyDecision:
    coordination_state: str
    rationale_code: str
    joint_actions: List[str]
    delegated_actions: Dict[str, List[str]]
    human_review_required: bool
    required_information_exchange: List[dict]

    def to_dict(self):
        return asdict(self)

class InstitutionalPolicyCoordinator:
    PRIVACY = "privacy_agent"
    RESEARCH = "research_irb_agent"
    REGULATOR = "regulator_agent"

    def coordinate(self, assessments_by_event):
        codes = {
            e: a.assessment_code
            for e, a in assessments_by_event.items()
        }

        # S2: clinical care allowed, research consent withdrawn.
        s2_privacy = (
            "S2E1" in assessments_by_event
            and codes["S2E1"] == "CARE_ALLOWED_RESEARCH_WITHDRAWN"
        )
        s2_research = (
            "S2E2" in assessments_by_event
            and codes["S2E2"] == "RESEARCH_PROCESSING_NOT_AUTHORIZED"
        )

        if s2_privacy and s2_research:
            delegated = {
                self.PRIVACY: [
                    "ALLOW_TREATMENT_USE",
                    "BLOCK_RESEARCH_USE",
                    "REQUEST_PRIVACY_REVIEW",
                    "PRESERVE_PRIVACY_AUDIT_LOG",
                ],
                self.RESEARCH: [
                    "BLOCK_RESEARCH_PROCESSING",
                    "REQUEST_IRB_REVIEW",
                    "PRESERVE_RESEARCH_AUDIT_LOG",
                ],
            }
            joint = sorted({
                a for actions in delegated.values() for a in actions
            })
            return InstitutionalPolicyDecision(
                coordination_state="CARE_CONTINUES_RESEARCH_RESTRICTED",
                rationale_code="CARE_SCOPE_VALID_RESEARCH_CONSENT_WITHDRAWN",
                joint_actions=joint,
                delegated_actions=delegated,
                human_review_required=True,
                required_information_exchange=[
                    {
                        "from": self.PRIVACY,
                        "to": self.RESEARCH,
                        "message_type": "RESEARCH_CONSENT_SCOPE",
                        "payload": {"research_use": "NOT_AUTHORIZED"},
                    }
                ],
            )

        # S3: stale/unverified DT + high-impact AI action request.
        s3_dt = (
            "S3E1" in assessments_by_event
            and codes["S3E1"] == "DT_EVIDENCE_NOT_TRUSTWORTHY_FOR_HIGH_IMPACT_USE"
        )
        s3_ai = (
            "S3E2" in assessments_by_event
            and codes["S3E2"] == "HIGH_IMPACT_AI_REQUIRES_VALIDATED_EVIDENCE_AND_OVERSIGHT"
        )

        if s3_dt and s3_ai:
            delegated = {
                self.REGULATOR: [
                    "BLOCK_AUTOMATED_HIGH_IMPACT_ACTION",
                    "REQUIRE_FRESH_DT_VERIFICATION",
                    "REQUEST_HUMAN_OVERSIGHT",
                    "PRESERVE_REGULATORY_AUDIT_LOG",
                ]
            }
            return InstitutionalPolicyDecision(
                coordination_state="EVIDENCE_INSUFFICIENT_HIGH_IMPACT_AI_BLOCKED",
                rationale_code="HIGH_IMPACT_AI_ON_STALE_OR_UNVERIFIED_DT",
                joint_actions=sorted(set(delegated[self.REGULATOR])),
                delegated_actions=delegated,
                human_review_required=True,
                required_information_exchange=[],
            )

        # S4: excessive / unauthorized disclosure request.
        s4 = (
            "S4E1" in assessments_by_event
            and codes["S4E1"] == "UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST"
        )

        if s4:
            delegated = {
                self.PRIVACY: [
                    "DENY_UNAUTHORIZED_DISCLOSURE",
                    "LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY",
                    "PRESERVE_PRIVACY_AUDIT_LOG",
                ]
            }
            return InstitutionalPolicyDecision(
                coordination_state="DISCLOSURE_BLOCKED",
                rationale_code="AUTHORITY_OR_MINIMUM_NECESSARY_VIOLATION",
                joint_actions=sorted(set(delegated[self.PRIVACY])),
                delegated_actions=delegated,
                human_review_required=False,
                required_information_exchange=[],
            )

        return InstitutionalPolicyDecision(
            coordination_state="NO_POLICY_ESCALATION",
            rationale_code="NO_INSTITUTIONAL_POLICY_TRIGGER",
            joint_actions=[],
            delegated_actions={},
            human_review_required=False,
            required_information_exchange=[],
        )
