from __future__ import annotations

LLM_OUTPUT_CONTRACT = {
    "required_fields": [
        "coordination_state",
        "rationale_code",
        "summary",
        "cited_policy_chunks",
        "allowed_joint_actions",
        "human_review_required",
        "grounding_complete",
    ],
    "hard_constraints": [
        "coordination_state must equal deterministic coordinator output",
        "rationale_code must equal deterministic coordinator output",
        "allowed_joint_actions must exactly equal deterministic joint action set",
        "cited_policy_chunks must be a subset of supplied retrieval hits",
        "human_review_required may not be downgraded",
        "no raw hidden chain-of-thought is stored or requested",
    ],
}

def build_llm_prompt(
    coordination_decision,
    policy_hits,
):
    return {
        "system_instruction": (
            "Explain the provided validated coordination decision using only "
            "the supplied policy evidence. Do not invent actions, legal rules, "
            "or institutional permissions. Do not change the coordination result."
        ),
        "coordination_decision": coordination_decision,
        "policy_hits": policy_hits,
        "output_contract": LLM_OUTPUT_CONTRACT,
    }
