from __future__ import annotations

from medverse.agents.base import InstitutionalAgent, Assessment

class HospitalAgent(InstitutionalAgent):
    agent_id = "hospital_agent"

    def assess(self, observation):
        self.validate_observation(observation)

        p = observation["payload"]
        spo2 = float(p["SpO2"])
        hr = float(p["heart_rate"])

        # Gate 4 sandbox diagnostic rule only.
        # It is not asserted as a legal or clinical guideline threshold.
        if spo2 < 90.0:
            assessment_code = "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION"
            risk = "HIGH"
            actions = [
                "VERIFY_MEASUREMENT",
                "CONTACT_PATIENT",
                "REQUEST_HUMAN_CLINICAL_REVIEW",
            ]
            human_review = True
            confidence = 0.95
            basis_codes = [
                "G4_CLINICAL_SPO2_LOW",
                "G4_CLINICAL_TACHYCARDIA_CONTEXT" if hr >= 120.0
                else "G4_CLINICAL_HR_CONTEXT",
            ]
        else:
            assessment_code = "NO_CRITICAL_CLINICAL_ALARM_DETECTED"
            risk = "LOW"
            actions = ["CONTINUE_SAFE_CARE"]
            human_review = False
            confidence = 0.90
            basis_codes = ["G4_CLINICAL_NO_CRITICAL_THRESHOLD"]

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
