from __future__ import annotations
from typing import Dict, Any, Tuple

from medverse.learning.gate23_research_irb_benchmark import oracle


def validate_research_irb_action(
    action: str,
    features: Dict[str, Any],
) -> Tuple[str, str]:
    """
    Complete Research/IRB execution validator.

    The validator is derived from the same frozen institutional semantics used
    to define the deterministic Research/IRB oracle.

    PERMIT is granted only when the proposed action is feasible for the current
    institutional state. Incorrect proposals in insufficient-evidence states
    escalate; other policy-inconsistent proposals are blocked.
    """
    expected = oracle(features)
    expected_action = expected["action"]

    if action == expected_action:
        return expected["boundary"], expected["enforcement"]

    if expected["boundary"] == "INSUFFICIENT_EVIDENCE":
        return "INSUFFICIENT_EVIDENCE", "ESCALATE"

    return "OUT_OF_POLICY", "BLOCK"
