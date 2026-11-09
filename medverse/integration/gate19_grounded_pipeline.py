from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import json

from medverse.digital_twin.model import PatientDigitalTwin
from medverse.data_grounding.evidence_bundle import EvidenceBundleBuilder
from medverse.data_grounding.ncc_context import NCCCancerContext
from medverse.reasoning.grounded_agent import DataPolicyGroundedAgent
from medverse.knowledge_base.jurisdictional_semantic_kb import JurisdictionAwarePolicyKB
from medverse.reasoning.policy_boundary import PolicyBoundaryValidator
from medverse.orchestrator.policy_aware_coordinator import (
    InstitutionalPosition,
    MedVersePolicyAwareCoordinator,
)


FINAL_OUTCOME_MAP = {
    ("S1", "COMPLEMENTARY"): "COMPLEMENTARY_RISK",
    ("S2", "AGREEMENT"): "CARE_CONTINUES_RESEARCH_RESTRICTED",
    ("S3", "HUMAN_AUTHORITY_REQUIRED"): "EVIDENCE_INSUFFICIENT_HIGH_IMPACT_AI_BLOCKED",
    ("S4", "INSTITUTIONAL_CONFLICT"): "DISCLOSURE_BLOCKED",
}


class Gate19GroundedPipeline:
    """
    End-to-end deterministic integration of the frozen MedVerse components.

    This adapter connects:
      DT -> bounded evidence -> grounded agent -> KR semantic retrieval ->
      deterministic policy boundary -> MedVerse harmonization -> final outcome.

    It does not introduce a learned decision policy or clinical inference model.
    """

    def __init__(self, root: Path):
        self.root = Path(root)
        self.corpus_path = (
            self.root
            / "data/policy/candidate_v0.4/policy_records_v0.4_candidate.json"
        )

        self.kb = JurisdictionAwarePolicyKB(
            self.corpus_path,
            deployment_jurisdiction="KR",
        )
        self.kb.load_model()

        self.boundary = PolicyBoundaryValidator()
        self.coordinator = MedVersePolicyAwareCoordinator()

        self.ncc = None
        ncc_path = self.root / "data/external/ncc_cancer_incidence.csv"
        if ncc_path.exists():
            self.ncc = NCCCancerContext(ncc_path)

    def _build_dt(self, case: Dict[str, Any]) -> PatientDigitalTwin:
        dt = PatientDigitalTwin()
        for update in case["dt_updates"]:
            dt.update_domain(
                update["domain"],
                update["payload"],
                t=update["t"],
                source_type=update["source_type"],
                source_id=update["source_id"],
                authority=update.get("authority"),
            )
        return dt

    def _population_context(self):
        if self.ncc is None:
            return None
        # Descriptive context only. No patient-level filtering or probability.
        return self.ncc.query(year=2023)

    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        dt = self._build_dt(case)

        policy_hits_by_agent = {}
        policy_records_by_agent = {}

        for agent_id in case["agents"]:
            hits = self.kb.retrieve(
                agent_id,
                case["policy_queries"][agent_id],
                top_k=3,
            )
            policy_hits_by_agent[agent_id] = hits
            policy_records_by_agent[agent_id] = [
                h.to_dict() for h in hits
            ]

        builder = EvidenceBundleBuilder(
            policy_records_by_agent=policy_records_by_agent
        )

        epi = self._population_context()

        assessments = {}
        positions = []
        boundary_decisions = {}
        bundles = {}

        for agent_id in case["agents"]:
            bundle = builder.build(
                agent_id,
                dt,
                epidemiological_context=epi,
            )
            bundles[agent_id] = bundle

            assessment = DataPolicyGroundedAgent(agent_id).assess(bundle)
            assessments[agent_id] = assessment

            action = case["boundary_action"][agent_id]
            decision = self.boundary.validate(
                agent_id=agent_id,
                proposed_action=action,
                jurisdiction="KR",
                policy_hits=policy_hits_by_agent[agent_id],
                facts=case["boundary_facts"].get(agent_id, {}),
            )
            boundary_decisions[agent_id] = decision

            positions.append(
                InstitutionalPosition(
                    agent_id=agent_id,
                    assessment_code=assessment.assessment_code,
                    proposed_actions=[action],
                    boundary_status=decision.status,
                    enforcement=decision.enforcement,
                    policy_ids=decision.supporting_policy_ids,
                    requested_evidence=[],
                    human_review_required=assessment.human_review_required,
                    priority="URGENT" if assessment.risk == "HIGH" else "NORMAL",
                    notes=assessment.rationale,
                )
            )

        coordination = self.coordinator.harmonize(
            positions,
            context=case.get("coordinator_context", {}),
        )

        final_outcome = FINAL_OUTCOME_MAP.get(
            (case["scenario_id"], coordination.coordination_state),
            "UNMAPPED_OUTCOME",
        )

        # Judge-facing policy trace contains only explicit auditable attribution.
        judge_trace = {
            "scenario_id": case["scenario_id"],
            "deployment_jurisdiction": "KR",
            "dt_validity": dt.validity,
            "agents": {
                agent_id: {
                    "assessment_code": assessments[agent_id].assessment_code,
                    "risk": assessments[agent_id].risk,
                    "recommended_actions": assessments[agent_id].recommended_actions,
                    "selected_boundary_action": case["boundary_action"][agent_id],
                    "policy_boundary_status": boundary_decisions[agent_id].status,
                    "enforcement": boundary_decisions[agent_id].enforcement,
                    "policy_ids": boundary_decisions[agent_id].supporting_policy_ids,
                    "retrieved_policy": [
                        {
                            "chunk_id": h.chunk_id,
                            "authority": h.authority,
                            "source_type": h.source_type,
                            "official_url": h.official_url,
                            "locator": h.locator,
                            "score": h.score,
                        }
                        for h in policy_hits_by_agent[agent_id]
                    ],
                    "dt_evidence_used": assessments[agent_id].dt_evidence_used,
                    "open_data_evidence_used": assessments[agent_id].open_data_evidence_used,
                    "patient_level_inference_from_population_data":
                        assessments[agent_id].patient_level_inference_from_population_data,
                    "unauthorized_evidence_used":
                        assessments[agent_id].unauthorized_evidence_used,
                }
                for agent_id in case["agents"]
            },
            "coordination_state": coordination.coordination_state,
            "accepted_actions": coordination.accepted_actions,
            "blocked_actions": coordination.blocked_actions,
            "conditional_steps": coordination.conditional_steps,
            "evidence_requests": coordination.evidence_requests,
            "minimum_necessary_messages": coordination.minimum_necessary_messages,
            "escalation_required": coordination.escalation_required,
            "escalation_targets": coordination.escalation_targets,
            "rationale_code": coordination.rationale_code,
            "final_outcome": final_outcome,
        }

        return {
            "digital_twin": dt.to_dict(),
            "bundles": {k: v.to_dict() for k, v in bundles.items()},
            "assessments": {k: v.to_dict() for k, v in assessments.items()},
            "boundary_decisions": {
                k: v.to_dict() for k, v in boundary_decisions.items()
            },
            "coordination": coordination.to_dict(),
            "judge_trace": judge_trace,
        }
