from __future__ import annotations

from medverse.agents.base import InstitutionalAgent, Assessment

class PrivacyAgent(InstitutionalAgent):
    agent_id = "privacy_agent"

    def assess(self, observation):
        self.validate_observation(observation)

        event_type = observation["event_type"]
        p = observation["payload"]

        if event_type == "CONSENT_SCOPE_UPDATE":
            care_allowed = bool(p["care_use_allowed"])
            research_allowed = bool(p["research_use_allowed"])
            consent_status = str(p["consent_status"])

            if care_allowed and not research_allowed:
                assessment_code = "CARE_ALLOWED_RESEARCH_WITHDRAWN"
                risk = "HIGH"
                actions = [
                    "ALLOW_TREATMENT_USE",
                    "BLOCK_RESEARCH_USE",
                    "REQUEST_PRIVACY_REVIEW",
                    "PRESERVE_PRIVACY_AUDIT_LOG",
                ]
                human_review = True
                confidence = 0.98
                basis_codes = ["G11B_CONSENT_SCOPE_SEPARATION"]
            else:
                assessment_code = "CONSENT_SCOPE_NOT_RESTRICTIVE"
                risk = "LOW"
                actions = ["PRESERVE_PRIVACY_AUDIT_LOG"]
                human_review = False
                confidence = 0.90
                basis_codes = ["G11B_CONSENT_SCOPE_NO_RESTRICTION"]

        elif event_type == "DISCLOSURE_REQUEST":
            minimum_necessary = bool(p["minimum_necessary"])
            purpose = str(p["declared_purpose"])

            if not minimum_necessary or purpose == "unspecified":
                assessment_code = "UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST"
                risk = "HIGH"
                actions = [
                    "DENY_UNAUTHORIZED_DISCLOSURE",
                    "LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY",
                    "PRESERVE_PRIVACY_AUDIT_LOG",
                ]
                human_review = False
                confidence = 0.99
                basis_codes = ["G11B_MINIMUM_NECESSARY_DISCLOSURE_RULE"]
            else:
                assessment_code = "DISCLOSURE_WITHIN_DECLARED_SCOPE"
                risk = "LOW"
                actions = [
                    "PRESERVE_PRIVACY_AUDIT_LOG",
                ]
                human_review = False
                confidence = 0.90
                basis_codes = ["G11B_DISCLOSURE_SCOPE_ACCEPTABLE"]

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
