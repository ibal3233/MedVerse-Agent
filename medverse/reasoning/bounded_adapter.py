from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class GroundedExplanation:
    explanation_id: str
    coordination_state: str
    rationale_code: str
    summary: str
    cited_policy_chunks: List[str]
    allowed_joint_actions: List[str]
    human_review_required: bool
    grounding_complete: bool

    def to_dict(self):
        return asdict(self)

class BoundedReasoningAdapter:
    '''
    Gate 7B reference adapter.

    This is intentionally deterministic. It defines the contract that any
    future LLM adapter must satisfy.

    The adapter may:
    - explain an existing frozen coordination decision
    - cite retrieved policy chunks
    - restate already-authorized actions

    The adapter may NOT:
    - create new actions
    - change coordination state
    - relax mandates
    - suppress required human review
    - cite policy chunks not supplied to it
    '''

    def explain(
        self,
        coordination_decision: Dict[str, Any],
        policy_hits: List[Dict[str, Any]],
    ) -> GroundedExplanation:

        if not policy_hits:
            raise ValueError("At least one policy retrieval hit is required.")

        chunk_ids = [p["chunk_id"] for p in policy_hits]

        for p in policy_hits:
            required = {
                "chunk_id",
                "document_id",
                "title",
                "article",
                "official_url",
                "effective_date",
                "authority",
                "translation_status",
            }
            missing = required - set(p.keys())
            if missing:
                raise ValueError(
                    f"Policy hit {p.get('chunk_id')} missing fields: "
                    f"{sorted(missing)}"
                )

        state = coordination_decision["coordination_state"]
        rationale = coordination_decision["rationale_code"]
        actions = list(coordination_decision["joint_actions"])
        human_review = bool(
            coordination_decision["human_review_required"]
        )

        if state == "COMPLEMENTARY_RISK":
            summary = (
                "The clinical assessment indicates urgent patient risk while "
                "the cyber/network assessments indicate reduced trust in the "
                "telemetry and device/session integrity. The assessments are "
                "complementary rather than mutually exclusive. The response "
                "therefore preserves urgent clinical verification and human "
                "review while independently validating the telemetry pathway "
                "and device identity. Policy evidence is attached for provenance; "
                "it does not replace institutional mandates."
            )
        else:
            summary = (
                "The explanation reflects the previously validated deterministic "
                "coordination decision and does not introduce additional actions."
            )

        return GroundedExplanation(
            explanation_id="G7B-S1-EXPLANATION",
            coordination_state=state,
            rationale_code=rationale,
            summary=summary,
            cited_policy_chunks=chunk_ids,
            allowed_joint_actions=actions,
            human_review_required=human_review,
            grounding_complete=True,
        )

def validate_bounded_output(
    explanation: GroundedExplanation,
    coordination_decision: Dict[str, Any],
    supplied_policy_hits: List[Dict[str, Any]],
):
    errors = []

    if explanation.coordination_state != coordination_decision["coordination_state"]:
        errors.append("coordination_state_changed")

    if explanation.rationale_code != coordination_decision["rationale_code"]:
        errors.append("rationale_code_changed")

    if set(explanation.allowed_joint_actions) != set(
        coordination_decision["joint_actions"]
    ):
        errors.append("action_set_changed")

    if explanation.human_review_required != bool(
        coordination_decision["human_review_required"]
    ):
        errors.append("human_review_flag_changed")

    supplied = {p["chunk_id"] for p in supplied_policy_hits}
    cited = set(explanation.cited_policy_chunks)

    if not cited:
        errors.append("no_policy_citation")

    if not cited.issubset(supplied):
        errors.append("unsupported_policy_citation")

    if not explanation.grounding_complete:
        errors.append("grounding_incomplete")

    return errors
