from __future__ import annotations

from medverse.agents.base import InstitutionalAgent, Assessment

class RegulatorAgent(InstitutionalAgent):
    agent_id = "regulator_agent"

    def assess(self, observation):
        self.validate_observation(observation)

        event_type = observation["event_type"]
        p = observation["payload"]

        if event_type == "DT_VALIDITY_ALERT":
            validity = str(p["dt_validity"])
            age = float(p["dt_age_seconds"])
            integrity = str(p["integrity_status"])

            unsafe = (
                validity in {"STALE", "UNVERIFIED"}
                or integrity != "verified"
                or age > 300.0
            )

            if unsafe:
                assessment_code = "DT_EVIDENCE_NOT_TRUSTWORTHY_FOR_HIGH_IMPACT_USE"
                risk = "HIGH"
                actions = [
                    "REQUIRE_FRESH_DT_VERIFICATION",
                    "REQUEST_HUMAN_OVERSIGHT",
                    "PRESERVE_REGULATORY_AUDIT_LOG",
                ]
                human_review = True
                confidence = 0.98
                basis_codes = ["G11B_DT_VALIDITY_RULE"]
            else:
                assessment_code = "DT_EVIDENCE_ACCEPTABLE_FOR_REVIEW"
                risk = "LOW"
                actions = ["PRESERVE_REGULATORY_AUDIT_LOG"]
                human_review = False
                confidence = 0.90
                basis_codes = ["G11B_DT_VALIDITY_ACCEPTABLE"]

        elif event_type == "HIGH_IMPACT_AI_REQUEST":
            impact = str(p["decision_impact"])

            if impact == "high":
                assessment_code = "HIGH_IMPACT_AI_REQUIRES_VALIDATED_EVIDENCE_AND_OVERSIGHT"
                risk = "HIGH"
                actions = [
                    "BLOCK_AUTOMATED_HIGH_IMPACT_ACTION",
                    "REQUEST_HUMAN_OVERSIGHT",
                    "PRESERVE_REGULATORY_AUDIT_LOG",
                ]
                human_review = True
                confidence = 0.97
                basis_codes = ["G11B_HIGH_IMPACT_AI_OVERSIGHT_RULE"]
            else:
                assessment_code = "AI_REQUEST_NOT_HIGH_IMPACT"
                risk = "LOW"
                actions = ["PRESERVE_REGULATORY_AUDIT_LOG"]
                human_review = False
                confidence = 0.90
                basis_codes = ["G11B_AI_IMPACT_LOW"]

        else:
            raise ValueError(
                f"Unsupported event type for {self.agent_id}: {event_type}"
            )

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
