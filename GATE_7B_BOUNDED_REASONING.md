# Gate 7B — Bounded Policy-Grounded Reasoning Contract

## (1) Question this gate answers
Can a reasoning/explanation layer sit on top of the validated MedVerse-Agent pipeline without changing the deterministic institutional decision, inventing actions, fabricating policy evidence, or suppressing required human review?

This gate validates the reasoning contract before any external LLM is executed.

## (2) Frozen
- Gates 0-7A.
- Gate 5 deterministic coordination decision.
- Gate 6 provenance/access semantics.
- Gate 7A multilingual semantic retrieval.

## (3) Changed
Only:
- bounded explanation schema
- grounding validation
- adversarial mutation tests
- future LLM prompt/output contract

No external LLM call is made in this gate.

## Reasoning boundary
The reasoning layer MAY:
- explain the frozen coordination decision
- cite supplied policy evidence
- restate allowed actions
- state why human review is required

It MAY NOT:
- change coordination state
- change rationale code
- create actions
- delete required actions
- weaken human review
- cite unsupplied policy evidence
- expand agent mandates
- expose or request raw hidden chain-of-thought

## (4) PASS/FAIL criteria
All checks must pass:
- output preserves coordination state
- rationale is unchanged
- joint action set exactly preserved
- human-review flag preserved
- citations are nonempty and subset of supplied retrieval hits
- grounding marked complete
- invented action is rejected
- unsupported citation is rejected
- human-review downgrade is rejected
- deterministic replay exact
- LLM contract does not request hidden chain-of-thought

## (5) Outputs
outputs/gate7b/
- gate7b_grounded_explanation.json
- gate7b_llm_prompt_contract.json
- gate7b_checks.csv
- gate7b_status.json

## (6) Next action

### PASS
Freeze the bounded reasoning contract.
Then decide between:
- Gate 7C: execute one external LLM under the frozen contract, or
- Gate 8: dashboard/demo integration using deterministic reasoning only.

For hackathon reliability, deterministic reasoning remains the fallback path even if an LLM is later connected.

### FAIL
Do not connect an LLM.
Diagnose the exact contract violation first.
