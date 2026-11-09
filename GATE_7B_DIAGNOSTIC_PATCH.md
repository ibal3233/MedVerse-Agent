# Gate 7B Diagnostic Patch

## Failure classification
Implementation error in the diagnostic assertion only.

## Observed result
11/12 checks passed.

## Root cause
The test `llm_contract_contains_no_chain_of_thought_request` required the literal
string `chain-of-thought` to be absent from the serialized contract. However,
the frozen LLM contract intentionally contains the sentence:

`no raw hidden chain-of-thought is stored or requested`

Therefore the test falsely failed on the presence of an explicit prohibition.

## Controlled change
Only the diagnostic assertion was changed.

The revised test verifies:
1. the hard-constraint section explicitly prohibits hidden chain-of-thought;
2. the system instruction does not request chain-of-thought, step-by-step
   reasoning, or hidden reasoning.

## Not changed
- Gate 5 coordination semantics
- Gate 6 policy records/provenance/access partitions
- Gate 7A embedding model/retrieval
- bounded reasoning adapter
- grounded explanation
- joint actions
- human-review requirement
- LLM prompt content
- policy citations

## Promotion rule
Rerun Gate 7B. PASS requires 12/12 checks.
