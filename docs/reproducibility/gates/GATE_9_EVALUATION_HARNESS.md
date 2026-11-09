# Gate 9 — Evaluation Harness and Baseline Validation

## (1) Question this gate answers
Are the MedVerse-Agent evaluation metrics, baseline interfaces, logging,
and deterministic result calculations implemented correctly before any
final campaign is run?

This gate validates the evaluator itself.

It does NOT establish final system performance.

## (2) Frozen
Gates 0-8 in full.

## (3) Changed
Only:
- evaluation-case fixtures
- metric functions
- baseline interfaces
- result serialization

No routing, assessment, coordination, retrieval, or reasoning semantics are changed.

## Metrics
- ARA: Agent Routing Accuracy
- MCR: Mandate Compliance Rate
- CSR: Coordination Success Rate
- CDR: Conflict/Complementarity Detection Rate
- EAR: Escalation Accuracy Rate
- PGA: Policy Grounding Accuracy
- ILR: Information Leakage Rate

## Baselines

### B1 — Single Omniscient Agent
Centralized access to all event information.
No institutional information partition is enforced.

### B2 — Unconstrained Role-Based Multi-Agent
Role labels exist, but observation, mandate, and communication boundaries
are not enforced.

### B3 — MedVerse-Agent
The validated gated system from Gates 0-8.

## Important interpretation boundary
The values produced in Gate 9 are evaluator-validation fixtures only.
They MUST NOT be reported as final experimental performance.

The current S1 fixture is intentionally deterministic and small.

## (4) PASS / FAIL
PASS requires:
- metric functions return expected values on known fixtures
- all rates lie in [0,1]
- ILR returns 0 when unauthorized observations are rejected
- baseline interfaces produce expected structural properties
- evaluator replay is exact

One failed check means Gate 9 FAIL.

## (5) Outputs
outputs/gate9/
- gate9_harness_metrics.csv
- gate9_medverse_details.json
- gate9_baseline_sanity.json
- gate9_checks.csv
- gate9_status.json

## (6) Next action

### PASS
Freeze the evaluation harness.
Proceed to Gate 10: final experiment-matrix freeze and controlled benchmark
generation with multiple scenario variants / repetitions.

### FAIL
Repair only the metric, fixture, or baseline-interface component that failed.
Do not modify the validated MedVerse-Agent pipeline.
