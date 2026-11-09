from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import Any, Dict, List

@dataclass
class Assessment:
    agent_id: str
    event_id: str
    assessment_code: str
    risk: str
    recommended_actions: List[str]
    human_review_required: bool
    confidence: float
    basis_codes: List[str]
    observed_fields: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class InstitutionalAgent:
    agent_id = ""

    def __init__(self, mandate_path):
        self.mandate = json.loads(
            Path(mandate_path).read_text(encoding="utf-8")
        )

        if self.mandate["agent_id"] != self.agent_id:
            raise ValueError(
                f"Mandate agent_id mismatch: "
                f"{self.mandate['agent_id']} != {self.agent_id}"
            )

    @property
    def allowed_actions(self):
        return set(self.mandate["allowed_actions"])

    @property
    def allowed_event_types(self):
        return set(self.mandate["allowed_event_types"])

    @property
    def allowed_observation_fields(self):
        return set(self.mandate["allowed_observation_fields"])

    def validate_observation(self, observation):
        if observation["agent_id"] != self.agent_id:
            raise PermissionError(
                f"{self.agent_id} cannot assess an observation for "
                f"{observation['agent_id']}"
            )

        if observation["event_type"] not in self.allowed_event_types:
            raise PermissionError(
                f"{self.agent_id} is not authorized for event type "
                f"{observation['event_type']}"
            )

        observed_fields = set(observation["payload"].keys())
        extra = observed_fields - self.allowed_observation_fields
        if extra:
            raise PermissionError(
                f"{self.agent_id} observation contains unauthorized fields: "
                f"{sorted(extra)}"
            )

    def validate_actions(self, actions):
        unauthorized = sorted(set(actions) - self.allowed_actions)
        if unauthorized:
            raise PermissionError(
                f"{self.agent_id} proposed unauthorized actions: "
                f"{unauthorized}"
            )

    def assess(self, observation):
        raise NotImplementedError
