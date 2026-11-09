# Gate 4 — Deterministic Institutional Assessments

## (1) Question this gate answers
Given only an authorized institutional observation, can each agent produce the expected independent assessment and remain inside its mandate?

This is the first gate where agents make decisions.

It still contains:
- no coordinator
- no policy RAG
- no LLM
- no learning

## (2) Frozen
- Gate 0 system model and metrics
- Gate 1 data semantics
- Gate 2 deterministic environment
- Gate 3 event routing and observation boundaries
- S1 events and visibility rules

## (3) Changed
Only:
- machine-readable agent mandates
- deterministic agent assessment functions
- action-space validation
- assessment diagnostics

## Hospital Agent
Input:
- SpO2
- heart_rate

Expected S1 assessment:
POSSIBLE_CRITICAL_CLINICAL_DETERIORATION

Allowed response:
- VERIFY_MEASUREMENT
- CONTACT_PATIENT
- REQUEST_HUMAN_CLINICAL_REVIEW

## Cyber/Network Agent
E2 expected assessment:
TELEMETRY_RELIABILITY_DEGRADED

E3 expected assessment:
DEVICE_IDENTITY_INTEGRITY_UNCERTAIN

## (4) PASS/FAIL criteria
All checks must pass:
- expected assessment code for E1/E2/E3
- expected risk level
- expected institutional actions
- hospital human-review flag for E1
- all actions within mandate
- unauthorized cross-domain actions explicitly rejected
- reasoning uses only authorized observation fields
- exact deterministic replay

One failure means Gate 4 FAIL.

The Gate-4 threshold rules are sandbox engineering rules for controlled experimentation.
They are not asserted as clinical, legal, or regulatory thresholds.

## (5) Outputs
outputs/gate4/
- gate4_assessments.csv
- gate4_checks.csv
- gate4_status.json

## (6) Next action by outcome

### PASS
Freeze independent agent assessment semantics.
Proceed to Gate 5: deterministic multi-agent coordinator.

### FAIL: wrong assessment with correct observation
Diagnose the local agent decision rule. Do not change routing or environment.

### FAIL: unauthorized action
Treat as mandate-enforcement failure. Do not proceed to coordination.

### FAIL: wrong observed fields
Gate 3 regression has broken. Restore observation-boundary correctness before touching agent logic.

### FAIL: replay mismatch
Treat as nondeterministic implementation defect. No LLM or learning may be introduced.
