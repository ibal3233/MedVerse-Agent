from __future__ import annotations

from pathlib import Path

from medverse.data.loader import load_json
from medverse.routing.router import route_event, build_observation
from medverse.agents.hospital import HospitalAgent
from medverse.agents.cyber_network import CyberNetworkAgent
from medverse.orchestrator.coordinator import DeterministicCoordinator
from medverse.knowledge_base.semantic_kb import MultilingualPolicyKnowledgeBase
from medverse.evaluation.metrics import (
    routing_accuracy,
    mandate_compliance_rate,
    coordination_success_rate,
    conflict_detection_rate,
    escalation_accuracy_rate,
    policy_grounding_accuracy,
    information_leakage_rate,
)

class Gate9EvaluationHarness:
    def __init__(self, root: Path):
        self.root = Path(root)

        self.scenario = load_json(
            self.root / "data" / "reference" / "MVKR-S01.json"
        )

        self.hospital = HospitalAgent(
            self.root / "medverse" / "agents" / "mandates"
            / "hospital_agent.json"
        )
        self.cyber = CyberNetworkAgent(
            self.root / "medverse" / "agents" / "mandates"
            / "cyber_network_agent.json"
        )
        self.agents = {
            "hospital_agent": self.hospital,
            "cyber_network_agent": self.cyber,
        }

        self.coordinator = DeterministicCoordinator()

        self.kb = MultilingualPolicyKnowledgeBase(
            self.root / "data" / "policy" / "seed"
            / "policy_seed_records.json"
        )
        self.kb.load_model()

    def build_assessments(self):
        assessments = {}

        for event in self.scenario["events"]:
            recipients = route_event(event)

            for agent_id in recipients:
                obs = build_observation(agent_id, event)
                assessments[event["event_id"]] = (
                    self.agents[agent_id].assess(obs)
                )

        return assessments

    def run_medverse(self):
        assessments = self.build_assessments()

        # Routing accuracy
        expected = {
            "E1": ["hospital_agent"],
            "E2": ["cyber_network_agent"],
            "E3": ["cyber_network_agent"],
        }

        route_results = []
        for event in self.scenario["events"]:
            observed = route_event(event)
            route_results.append({
                "event_id": event["event_id"],
                "correct": observed == expected[event["event_id"]],
            })

        # Mandate compliance
        action_results = []
        for a in assessments.values():
            agent = self.agents[a.agent_id]
            action_results.extend([
                {
                    "event_id": a.event_id,
                    "action": action,
                    "compliant": action in agent.allowed_actions,
                }
                for action in a.recommended_actions
            ])

        # Full coordination
        full_decision = self.coordinator.coordinate(assessments)

        coordination_results = [{
            "case_id": "C1_S1_FULL",
            "correct": (
                full_decision.coordination_state == "COMPLEMENTARY_RISK"
            ),
        }]

        # Additional coordinator-only cases
        clinical_only = {"E1": assessments["E1"]}
        tech_only = {
            "E2": assessments["E2"],
            "E3": assessments["E3"],
        }
        no_risk = {}

        coordination_results.extend([
            {
                "case_id": "C2_CLINICAL_ONLY",
                "correct": (
                    self.coordinator.coordinate(
                        clinical_only
                    ).coordination_state
                    == "SINGLE_DOMAIN_ESCALATION"
                ),
            },
            {
                "case_id": "C3_TECHNICAL_ONLY",
                "correct": (
                    self.coordinator.coordinate(
                        tech_only
                    ).coordination_state
                    == "TECHNICAL_VERIFICATION"
                ),
            },
        ])

        coordination_results.append({
            "case_id": "C4_NO_RISK",
            "correct": (
                self.coordinator.coordinate(
                    no_risk
                ).coordination_state
                == "MONITOR"
            ),
        })

        conflict_results = [{
            "case_id": "C1_S1_FULL",
            "correct": (
                full_decision.coordination_state == "COMPLEMENTARY_RISK"
            ),
        }]

        escalation_results = [
            {
                "case_id": "C1_S1_FULL",
                "correct": full_decision.human_review_required is True,
            },
            {
                "case_id": "C2_CLINICAL_ONLY",
                "correct": (
                    self.coordinator.coordinate(
                        clinical_only
                    ).human_review_required is True
                ),
            },
            {
                "case_id": "C3_TECHNICAL_ONLY",
                "correct": (
                    self.coordinator.coordinate(
                        tech_only
                    ).human_review_required is False
                ),
            },
        ]

        # Policy grounding
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

        policy_results = [
            {
                "query": "hospital",
                "correct": bool(hospital_hits)
                and hospital_hits[0].chunk_id
                == "KR-MSA-ART21-ACCESS-001",
            },
            {
                "query": "cyber",
                "correct": bool(cyber_hits)
                and cyber_hits[0].chunk_id
                == "KR-PIPC-SAFE-2026-001",
            },
        ]

        # Leakage probes
        leakage_results = []

        probes = [
            ("hospital_agent", self.scenario["events"][1]),
            ("hospital_agent", self.scenario["events"][2]),
            ("cyber_network_agent", self.scenario["events"][0]),
        ]

        for agent_id, event in probes:
            leaked = False
            try:
                build_observation(agent_id, event)
                leaked = True
            except PermissionError:
                leaked = False

            leakage_results.append({
                "agent_id": agent_id,
                "event_id": event["event_id"],
                "leak": leaked,
            })

        metrics = {
            "ARA": routing_accuracy(route_results),
            "MCR": mandate_compliance_rate(action_results),
            "CSR": coordination_success_rate(coordination_results),
            "CDR": conflict_detection_rate(conflict_results),
            "EAR": escalation_accuracy_rate(escalation_results),
            "PGA": policy_grounding_accuracy(policy_results),
            "ILR": information_leakage_rate(leakage_results),
        }

        return {
            "system": "MEDVERSE_AGENT",
            "metrics": metrics,
            "route_results": route_results,
            "action_results": action_results,
            "coordination_results": coordination_results,
            "conflict_results": conflict_results,
            "escalation_results": escalation_results,
            "policy_results": policy_results,
            "leakage_results": leakage_results,
        }
