from __future__ import annotations

from pathlib import Path

from medverse.data.loader import load_json
from medverse.agents.privacy import PrivacyAgent
from medverse.agents.research_irb import ResearchIRBAgent
from medverse.agents.regulator import RegulatorAgent
from medverse.routing.institutional_router import (
    route_event,
    build_observation,
)
from medverse.orchestrator.institutional_policy_coordinator import (
    InstitutionalPolicyCoordinator,
)
from medverse.experiments.institutional_baselines import (
    InstitutionalSingleOmniscientBaseline,
    InstitutionalUnconstrainedRoleBaseline,
)

class InstitutionalCampaignRunner:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.agents = {
            "privacy_agent": PrivacyAgent(
                self.root / "medverse" / "agents" / "mandates" / "privacy_agent.json"
            ),
            "research_irb_agent": ResearchIRBAgent(
                self.root / "medverse" / "agents" / "mandates" / "research_irb_agent.json"
            ),
            "regulator_agent": RegulatorAgent(
                self.root / "medverse" / "agents" / "mandates" / "regulator_agent.json"
            ),
        }
        self.coordinator = InstitutionalPolicyCoordinator()

    def load_scenario(self, filename):
        return load_json(self.root / "data" / "reference" / filename)

    @staticmethod
    def _rate(rows, field):
        if not rows:
            return None
        return sum(bool(r[field]) for r in rows) / len(rows)

    def run_medverse(self, scenario, variant):
        assessments = {}
        route_rows = []
        action_rows = []
        leakage_rows = []

        for event in scenario["events"]:
            recipients = route_event(event)
            route_rows.append({
                "event_id": event["event_id"],
                "correct": recipients == event["visible_to"],
            })

            for agent_id in recipients:
                obs = build_observation(agent_id, event)
                assessment = self.agents[agent_id].assess(obs)
                assessments[event["event_id"]] = assessment

                allowed = self.agents[agent_id].allowed_actions
                for action in assessment.recommended_actions:
                    action_rows.append({
                        "event_id": event["event_id"],
                        "agent_id": agent_id,
                        "action": action,
                        "compliant": action in allowed,
                    })

            authorized = set(event["visible_to"])
            for agent_id in sorted(set(self.agents) - authorized):
                leaked = False
                try:
                    build_observation(agent_id, event)
                    leaked = True
                except (PermissionError, ValueError):
                    leaked = False

                leakage_rows.append({
                    "event_id": event["event_id"],
                    "agent_id": agent_id,
                    "leak": leaked,
                })

        decision = self.coordinator.coordinate(assessments)

        return {
            "system": "B3_MEDVERSE_AGENT",
            "variant_id": variant["variant_id"],
            "scenario_id": scenario["scenario_id"],
            "coordination_state": decision.coordination_state,
            "human_review_required": decision.human_review_required,
            "ARA": self._rate(route_rows, "correct"),
            "MCR": self._rate(action_rows, "compliant"),
            "CSR": 1.0 if decision.coordination_state
                == variant["expected_coordination_state"] else 0.0,
            "CDR": 1.0 if decision.coordination_state
                == variant["expected_coordination_state"] else 0.0,
            "EAR": 1.0 if decision.human_review_required
                == variant["expected_human_review"] else 0.0,
            "PGA": None,
            "ILR": self._rate(leakage_rows, "leak"),
        }

    def run_b1(self, scenario, variant):
        out = InstitutionalSingleOmniscientBaseline().evaluate(scenario)
        return {
            "system": "B1_SINGLE_OMNISCIENT",
            "variant_id": variant["variant_id"],
            "scenario_id": scenario["scenario_id"],
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

    def run_b2(self, scenario, variant):
        out = InstitutionalUnconstrainedRoleBaseline().evaluate(scenario)
        return {
            "system": "B2_UNCONSTRAINED_ROLES",
            "variant_id": variant["variant_id"],
            "scenario_id": scenario["scenario_id"],
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
