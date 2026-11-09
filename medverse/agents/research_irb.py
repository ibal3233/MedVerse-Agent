from __future__ import annotations

from medverse.agents.base import InstitutionalAgent, Assessment

class ResearchIRBAgent(InstitutionalAgent):
    agent_id = "research_irb_agent"

    def assess(self, observation):
        self.validate_observation(observation)

        p = observation["payload"]
        consent = str(p["participant_consent_status"])

        if consent in {"withdrawn", "not_active"}:
            assessment_code = "RESEARCH_PROCESSING_NOT_AUTHORIZED"
            risk = "HIGH"
            actions = [
                "BLOCK_RESEARCH_PROCESSING",
                "REQUEST_IRB_REVIEW",
                "PRESERVE_RESEARCH_AUDIT_LOG",
            ]
            human_review = True
            confidence = 0.99
            basis_codes = ["G11B_RESEARCH_CONSENT_REQUIRED"]
        else:
            assessment_code = "RESEARCH_PROCESSING_WITHIN_ACTIVE_CONSENT"
            risk = "LOW"
            actions = ["PRESERVE_RESEARCH_AUDIT_LOG"]
            human_review = False
            confidence = 0.90
            basis_codes = ["G11B_RESEARCH_CONSENT_ACTIVE"]

        self.validate_actions(actions)

        return Assessment(
            agent_id=self.agent_id,
            event_id=observation["event_id"],
            assessment_code=assessment_code,
            risk=risk,
            recommended_actions=actions,
            human_review_required=human_review,
            confidence=confidence,
            basis_codes=basis_codes,
            observed_fields=sorted(p.keys()),
        )
