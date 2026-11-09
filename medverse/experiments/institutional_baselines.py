from __future__ import annotations

class InstitutionalSingleOmniscientBaseline:
    name = "B1_SINGLE_OMNISCIENT"

    def evaluate(self, scenario):
        sid = scenario["scenario_id"]

        if sid == "S2_CARE_VS_RESEARCH":
            return {
                "coordination_state": "CARE_CONTINUES_RESEARCH_RESTRICTED",
                "human_review_required": True,
                "institutional_partition_enforced": False,
                "mandate_validation_enforced": False,
                "minimum_necessary_exchange_enforced": False,
            }

        if sid == "S3_STALE_DT_AI_RECOMMENDATION":
            return {
                "coordination_state": "EVIDENCE_INSUFFICIENT_HIGH_IMPACT_AI_BLOCKED",
                "human_review_required": True,
                "institutional_partition_enforced": False,
                "mandate_validation_enforced": False,
                "minimum_necessary_exchange_enforced": False,
            }

        if sid == "S4_UNAUTHORIZED_DISCLOSURE":
            return {
                "coordination_state": "DISCLOSURE_BLOCKED",
                "human_review_required": False,
                "institutional_partition_enforced": False,
                "mandate_validation_enforced": False,
                "minimum_necessary_exchange_enforced": False,
            }

        raise ValueError(f"Unsupported institutional scenario: {sid}")


class InstitutionalUnconstrainedRoleBaseline:
    name = "B2_UNCONSTRAINED_ROLES"

    def evaluate(self, scenario):
        # Role labels are retained, but observation, action and exchange
        # boundaries are not enforced.
        base = InstitutionalSingleOmniscientBaseline().evaluate(scenario)
        return dict(base)
