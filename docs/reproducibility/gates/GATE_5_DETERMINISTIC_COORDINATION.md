# Gate 5 — Deterministic Multi-Agent Coordination

## (1) Question this gate answers
Can independently correct but incomplete institutional assessments be combined into the expected safe joint response without violating agent mandates or leaking unnecessary cross-domain information?

This is the first true multi-agent coordination gate.

## (2) Frozen
- Gate 0 system formulation.
- Gate 1 data semantics.
- Gate 2 deterministic environment.
- Gate 3 routing and observation boundaries.
- Gate 4 deterministic independent assessments and mandate enforcement.

## (3) Changed
Only:
- coordination-state classification
- deterministic joint-action logic
- delegation of actions back to authorized institutions
- minimum-necessary inter-agent message policy
- coordination diagnostics

No RAG, LLM, dashboard, or learning is introduced.

## Expected coordination relation
Hospital:
POSSIBLE_CRITICAL_CLINICAL_DETERIORATION

Cyber/Network:
TELEMETRY_RELIABILITY_DEGRADED
and
DEVICE_IDENTITY_INTEGRITY_UNCERTAIN

Therefore:
coordination_state = COMPLEMENTARY_RISK

The two assessments do not cancel one another.

Expected rationale:
HIGH_CLINICAL_RISK_PLUS_LOW_TELEMETRY_TRUST

## Expected safe joint response
Hospital:
- CONTACT_PATIENT
- VERIFY_MEASUREMENT
- REQUEST_HUMAN_CLINICAL_REVIEW

Cyber/Network:
- MARK_TELEMETRY_UNVERIFIED
- VERIFY_DEVICE_IDENTITY
- ISOLATE_SUSPECT_SESSION
- REQUEST_ALTERNATIVE_CHANNEL
- PRESERVE_TECHNICAL_LOGS

Coordinator-level joint requirement:
- USE_INDEPENDENT_MEASUREMENT_CHANNEL

## Minimum-necessary communication
Cyber -> Hospital:
TELEMETRY_TRUST_STATUS = UNVERIFIED

Hospital -> Cyber:
CLINICAL_PRIORITY = URGENT

The coordinator must reject raw unnecessary fields such as:
- SpO2 sent to Cyber/Network
- certificate_status sent to Hospital

## (4) PASS/FAIL criteria
All checks must pass:
- coordination state = COMPLEMENTARY_RISK
- rationale is correct
- human review required
- exact expected joint action set
- delegated actions remain within each institutional mandate
- no cross-institution action delegation
- all required coordination messages satisfy message policy
- excessive clinical/security detail is rejected
- exact deterministic replay

One failed check means Gate 5 FAIL.

## (5) Outputs
outputs/gate5/
- gate5_decision.json
- gate5_coordination_messages.csv
- gate5_checks.csv
- gate5_status.json

## (6) Next action by outcome

### PASS
Freeze the deterministic coordination semantics.
Proceed to Gate 6: policy knowledge-base ingestion/retrieval.

### FAIL: wrong coordination state
Do not change agent rules first.
Inspect the already-frozen Gate 4 assessments and the coordinator relation logic.

### FAIL: unauthorized delegation
Treat as coordinator authority-boundary failure.
Do not weaken agent mandates.

### FAIL: message leakage
Treat as inter-agent disclosure-control failure.
Tighten the message schema only after identifying the leaking field/path.

### FAIL: missing safe action
Determine whether the missing action belongs to:
- an institutional agent mandate, or
- coordinator-level joint action.
Do not add it arbitrarily to both.

### FAIL: replay mismatch
Treat as implementation nondeterminism.
No policy retrieval or LLM may be added until exact replay is restored.
