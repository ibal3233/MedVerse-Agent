from __future__ import annotations

from medverse.agents.base import InstitutionalAgent, Assessment

class CyberNetworkAgent(InstitutionalAgent):
    agent_id = "cyber_network_agent"

    def assess(self, observation):
        self.validate_observation(observation)

        event_type = observation["event_type"]
        p = observation["payload"]

        if event_type == "NETWORK_DEGRADATION":
            packet_loss = float(p["packet_loss"])
            rtt_ms = float(p["rtt_ms"])
            jitter_ms = float(p["jitter_ms"])

            severe = (
                packet_loss >= 0.20
                or rtt_ms >= 500.0
                or jitter_ms >= 100.0
            )

            if severe:
                assessment_code = "TELEMETRY_RELIABILITY_DEGRADED"
                risk = "HIGH"
                actions = [
                    "MARK_TELEMETRY_UNVERIFIED",
                    "REQUEST_ALTERNATIVE_CHANNEL",
                    "PRESERVE_TECHNICAL_LOGS",
                ]
                confidence = 0.96
                basis_codes = ["G4_NETWORK_DEGRADATION_RULE"]
            else:
                assessment_code = "NETWORK_CONDITIONS_ACCEPTABLE"
                risk = "LOW"
                actions = ["PRESERVE_TECHNICAL_LOGS"]
                confidence = 0.90
                basis_codes = ["G4_NETWORK_ACCEPTABLE_RULE"]

            human_review = False

        elif event_type == "DEVICE_AUTH_ANOMALY":
            certificate_status = str(p["certificate_status"])
            session_origin = str(p["session_origin"])

            anomaly = (
                certificate_status in {"mismatch", "expired", "revoked"}
                or session_origin == "abnormal"
            )

            if anomaly:
                assessment_code = "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN"
                risk = "HIGH"
                actions = [
                    "VERIFY_DEVICE_IDENTITY",
                    "ISOLATE_SUSPECT_SESSION",
                    "MARK_TELEMETRY_UNVERIFIED",
                    "PRESERVE_TECHNICAL_LOGS",
                ]
                confidence = 0.98
                basis_codes = ["G4_DEVICE_INTEGRITY_RULE"]
            else:
                assessment_code = "NO_DEVICE_AUTH_ANOMALY_DETECTED"
                risk = "LOW"
                actions = ["PRESERVE_TECHNICAL_LOGS"]
                confidence = 0.90
                basis_codes = ["G4_DEVICE_AUTH_NORMAL_RULE"]

            human_review = False

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
