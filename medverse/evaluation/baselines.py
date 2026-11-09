from __future__ import annotations

from typing import Dict, Any

class SingleOmniscientBaseline:
    '''
    Baseline B1.

    Reads all event payloads as one global context and produces a single
    centralized response. It intentionally has no institutional observation
    partition and therefore cannot satisfy information-asymmetry metrics.
    '''

    name = "B1_SINGLE_OMNISCIENT"

    def evaluate_full_s1(self, scenario):
        event_types = {e["event_type"] for e in scenario["events"]}

        clinical = "CLINICAL_ALARM" in event_types
        technical = (
            "NETWORK_DEGRADATION" in event_types
            or "DEVICE_AUTH_ANOMALY" in event_types
        )

        if clinical and technical:
            state = "COMPLEMENTARY_RISK"
            human = True
        elif clinical:
            state = "SINGLE_DOMAIN_ESCALATION"
            human = True
        elif technical:
            state = "TECHNICAL_VERIFICATION"
            human = False
        else:
            state = "MONITOR"
            human = False

        return {
            "coordination_state": state,
            "human_review_required": human,
            "institutional_partition_enforced": False,
            "mandate_validation_enforced": False,
            "minimum_necessary_exchange_enforced": False,
        }


class UnconstrainedRoleBaseline:
    '''
    Baseline B2.

    Preserves role labels but assumes every role may read every event and does
    not enforce action/communication boundaries.
    '''

    name = "B2_UNCONSTRAINED_ROLES"

    def evaluate_full_s1(self, scenario):
        event_types = {e["event_type"] for e in scenario["events"]}

        clinical = "CLINICAL_ALARM" in event_types
        technical = (
            "NETWORK_DEGRADATION" in event_types
            or "DEVICE_AUTH_ANOMALY" in event_types
        )

        if clinical and technical:
            state = "COMPLEMENTARY_RISK"
            human = True
        elif clinical:
            state = "SINGLE_DOMAIN_ESCALATION"
            human = True
        elif technical:
            state = "TECHNICAL_VERIFICATION"
            human = False
        else:
            state = "MONITOR"
            human = False

        return {
            "coordination_state": state,
            "human_review_required": human,
            "institutional_partition_enforced": False,
            "mandate_validation_enforced": False,
            "minimum_necessary_exchange_enforced": False,
        }
