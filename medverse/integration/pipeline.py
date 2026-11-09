from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from medverse.data.loader import load_json
from medverse.environment.env import MedVerseEnvironment
from medverse.routing.router import deliver_event
from medverse.agents.hospital import HospitalAgent
from medverse.agents.cyber_network import CyberNetworkAgent
from medverse.orchestrator.coordinator import DeterministicCoordinator
from medverse.knowledge_base.semantic_kb import MultilingualPolicyKnowledgeBase
from medverse.reasoning.bounded_adapter import BoundedReasoningAdapter

class MedVerseIntegratedPipeline:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.scenario = load_json(
            self.root / "data" / "reference" / "MVKR-S01.json"
        )
        self.env = MedVerseEnvironment()

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

        self.reasoner = BoundedReasoningAdapter()

        self.reset()

    def reset(self):
        self.env.reset()
        self.event_index = 0
        self.assessments = {}
        self.audit_log = []
        self.last_coordination = None
        self.last_explanation = None

    @property
    def done(self):
        return self.event_index >= len(self.scenario["events"])

    def release_next_event(self) -> Dict[str, Any]:
        if self.done:
            raise StopIteration("All scenario events have already been released.")

        event = self.scenario["events"][self.event_index]
        self.event_index += 1

        state = self.env.step(event)
        deliveries = deliver_event(event)

        event_assessments = {}

        for agent_id, observation in deliveries.items():
            assessment = self.agents[agent_id].assess(observation)
            self.assessments[event["event_id"]] = assessment
            event_assessments[agent_id] = assessment.to_dict()

        coordination = None
        explanation = None

        # Only coordinate once the clinical event exists and at least one
        # technical-risk assessment exists.
        if "E1" in self.assessments and (
            "E2" in self.assessments or "E3" in self.assessments
        ):
            coordination_obj = self.coordinator.coordinate(self.assessments)
            coordination = coordination_obj.to_dict()
            self.last_coordination = coordination

            policy_hits = []

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

            policy_hits.extend([h.to_dict() for h in hospital_hits])
            policy_hits.extend([h.to_dict() for h in cyber_hits])

            explanation_obj = self.reasoner.explain(
                coordination,
                policy_hits,
            )
            explanation = explanation_obj.to_dict()
            self.last_explanation = explanation

        audit_entry = {
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "visible_to": list(event["visible_to"]),
            "state": state.to_dict(),
            "assessments": event_assessments,
            "coordination": coordination,
            "explanation": explanation,
        }

        self.audit_log.append(audit_entry)

        return audit_entry

    def run_all(self) -> List[Dict[str, Any]]:
        outputs = []
        while not self.done:
            outputs.append(self.release_next_event())
        return outputs
