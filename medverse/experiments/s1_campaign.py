from __future__ import annotations

from pathlib import Path
from copy import deepcopy
from typing import Dict, Any, List

from medverse.routing.router import route_event, build_observation
from medverse.agents.hospital import HospitalAgent
from medverse.agents.cyber_network import CyberNetworkAgent
from medverse.orchestrator.coordinator import DeterministicCoordinator
from medverse.knowledge_base.semantic_kb import MultilingualPolicyKnowledgeBase
from medverse.evaluation.baselines import (
    SingleOmniscientBaseline,
    UnconstrainedRoleBaseline,
)

class S1CampaignRunner:
    def __init__(self, root: Path):
        self.root = Path(root)

        self.agents = {
            "hospital_agent": HospitalAgent(
                self.root / "medverse" / "agents" / "mandates"
                / "hospital_agent.json"
            ),
            "cyber_network_agent": CyberNetworkAgent(
                self.root / "medverse" / "agents" / "mandates"
                / "cyber_network_agent.json"
            ),
        }

        self.coordinator = DeterministicCoordinator()

        self.kb = MultilingualPolicyKnowledgeBase(
            self.root / "data" / "policy" / "seed"
            / "policy_seed_records.json"
        )
        self.kb.load_model()

    def _assess_variant(self, variant):
        assessments = {}
        route_rows = []
        action_rows = []
        leakage_rows = []

        for event in variant["events"]:
            recipients = route_event(event)

            route_rows.append({
                "event_id": event["event_id"],
                "correct": recipients == event["visible_to"],
            })

            for agent_id in recipients:
                obs = build_observation(agent_id, event)
                a = self.agents[agent_id].assess(obs)
                assessments[event["event_id"]] = a

                for action in a.recommended_actions:
                    action_rows.append({
                        "event_id": a.event_id,
                        "agent_id": a.agent_id,
                        "action": action,
                        "compliant": action in self.agents[a.agent_id].allowed_actions,
                    })

        # Unauthorized-observation probes for every event/other agent
        agent_ids = set(self.agents)
        for event in variant["events"]:
            allowed = set(event["visible_to"])
            for agent_id in sorted(agent_ids - allowed):
                leaked = False
                try:
                    build_observation(agent_id, event)
                    leaked = True
                except PermissionError:
                    leaked = False

                leakage_rows.append({
                    "event_id": event["event_id"],
                    "agent_id": agent_id,
                    "leak": leaked,
                })

        decision = self.coordinator.coordinate(assessments)

        hospital_hits = self.kb.retrieve(
            "hospital_agent",
            "patient medical records access disclosure healthcare provider",
            top_k=1,
        )
        cyber_hits = self.kb.retrieve(
            "cyber_network_agent",
            "personal information security safeguards access logs integrity",
            top_k=1,
        )

        policy_correct = (
            bool(hospital_hits)
            and hospital_hits[0].chunk_id == "KR-MSA-ART21-ACCESS-001"
            and bool(cyber_hits)
            and cyber_hits[0].chunk_id == "KR-PIPC-SAFE-2026-001"
        )

        return {
            "assessments": assessments,
            "decision": decision,
            "route_rows": route_rows,
            "action_rows": action_rows,
            "leakage_rows": leakage_rows,
            "policy_correct": policy_correct,
        }

    @staticmethod
    def _rate(rows, field):
        if not rows:
            return None
        return sum(bool(r[field]) for r in rows) / len(rows)

    def run_medverse(self, variant):
        result = self._assess_variant(variant)
        decision = result["decision"]

        ara = self._rate(result["route_rows"], "correct")
        mcr = self._rate(result["action_rows"], "compliant")
        ilr = (
            None
            if not result["leakage_rows"]
            else self._rate(result["leakage_rows"], "leak")
        )

        correct_coord = (
            decision.coordination_state
            == variant["expected_coordination_state"]
        )

        correct_escalation = (
            decision.human_review_required
            == variant["expected_human_review"]
        )

        # For S1 variants, "conflict/complementarity detection" is evaluated as
        # correct classification of the institutional relationship encoded in
        # the expected coordination state.
        cdr = 1.0 if correct_coord else 0.0
        csr = 1.0 if correct_coord else 0.0
        ear = 1.0 if correct_escalation else 0.0
        pga = 1.0 if result["policy_correct"] else 0.0

        return {
            "system": "B3_MEDVERSE_AGENT",
            "variant_id": variant["variant_id"],
            "coordination_state": decision.coordination_state,
            "human_review_required": decision.human_review_required,
            "ARA": ara,
            "MCR": mcr,
            "CSR": csr,
            "CDR": cdr,
            "EAR": ear,
            "PGA": pga,
            "ILR": ilr,
        }

    def run_b1(self, variant):
        baseline = SingleOmniscientBaseline()
        scenario = {"events": deepcopy(variant["events"])}
        out = baseline.evaluate_full_s1(scenario)

        return {
            "system": "B1_SINGLE_OMNISCIENT",
            "variant_id": variant["variant_id"],
            "coordination_state": out["coordination_state"],
            "human_review_required": out["human_review_required"],
            "ARA": None,
            "MCR": None,
            "CSR": 1.0 if out["coordination_state"]
                == variant["expected_coordination_state"] else 0.0,
            "CDR": 1.0 if out["coordination_state"]
                == variant["expected_coordination_state"] else 0.0,
            "EAR": 1.0 if out["human_review_required"]
                == variant["expected_human_review"] else 0.0,
            "PGA": None,
            # With no institutional partition, leakage control is not enforced;
            # report as not applicable rather than fabricating a leakage rate.
            "ILR": None,
        }

    def run_b2(self, variant):
        baseline = UnconstrainedRoleBaseline()
        scenario = {"events": deepcopy(variant["events"])}
        out = baseline.evaluate_full_s1(scenario)

        return {
            "system": "B2_UNCONSTRAINED_ROLES",
            "variant_id": variant["variant_id"],
            "coordination_state": out["coordination_state"],
            "human_review_required": out["human_review_required"],
            "ARA": None,
            "MCR": None,
            "CSR": 1.0 if out["coordination_state"]
                == variant["expected_coordination_state"] else 0.0,
            "CDR": 1.0 if out["coordination_state"]
                == variant["expected_coordination_state"] else 0.0,
            "EAR": 1.0 if out["human_review_required"]
                == variant["expected_human_review"] else 0.0,
            "PGA": None,
            "ILR": None,
        }
