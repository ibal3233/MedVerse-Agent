from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional

@dataclass
class EvidenceBundle:
    agent_id: str
    digital_twin_view: Dict[str, Any]
    epidemiological_context: Optional[Dict[str, Any]]
    policy_records: List[Dict[str, Any]]
    provenance: Dict[str, Any]

    def to_dict(self):
        return asdict(self)

class EvidenceBundleBuilder:
    """
    Builds bounded evidence views for institutional agents.

    Population epidemiological context is restricted to agents whose
    mandate can make legitimate use of descriptive clinical/research context.
    It is never exposed as patient-level disease probability.
    """

    DT_DOMAIN_ACCESS = {
        "hospital_agent": {
            "clinical", "patient_context", "quality", "validity"
        },
        "cyber_network_agent": {
            "network", "security", "quality", "validity"
        },
        "privacy_agent": {
            "consent", "quality", "validity"
        },
        "research_irb_agent": {
            "consent", "research", "patient_context", "quality", "validity"
        },
        "regulator_agent": {
            "ai_state", "quality", "validity"
        },
    }

    EPIDEMIOLOGY_ACCESS = {
        "hospital_agent",
        "research_irb_agent",
    }

    def __init__(self, policy_records_by_agent=None):
        self.policy_records_by_agent = policy_records_by_agent or {}

    def build(
        self,
        agent_id: str,
        dt,
        epidemiological_context=None,
    ):
        if agent_id not in self.DT_DOMAIN_ACCESS:
            raise ValueError(f"Unknown agent: {agent_id}")

        raw = dt.to_dict()
        allowed = self.DT_DOMAIN_ACCESS[agent_id]

        view = {}
        for key in allowed:
            view[key] = deepcopy(raw[key])

        epi = None
        if agent_id in self.EPIDEMIOLOGY_ACCESS:
            epi = deepcopy(epidemiological_context)

        if epi is not None:
            if epi.get("patient_level_probability") is not None:
                raise ValueError(
                    "Population context must not contain patient-level probability."
                )
            if epi.get("clinical_inference_permitted") is not False:
                raise ValueError(
                    "Population context must explicitly prohibit clinical inference."
                )

        policy = deepcopy(
            self.policy_records_by_agent.get(agent_id, [])
        )

        return EvidenceBundle(
            agent_id=agent_id,
            digital_twin_view=view,
            epidemiological_context=epi,
            policy_records=policy,
            provenance={
                "dt_fields": sorted(view.keys()),
                "policy_record_count": len(policy),
                "epidemiology_attached": epi is not None,
            },
        )
