# Gate 11A — Final Benchmark Campaign for Implemented S1 Family

## (1) Question this gate answers
Under the frozen Gate 10 experiment design, does the implemented S1
Complementary-Risk family produce stable, reproducible benchmark evidence
for B1, B2, and B3?

## (2) Frozen
- Gates 0-10
- B1/B2/B3 definitions
- seven metrics
- deterministic repetition count = 10
- S1 family semantics

## (3) Changed
Only final campaign execution and raw-result serialization.

No system behavior is changed.

## S1 variants
- S1a canonical clinical + network + security
- S1b clinical + security
- S1c clinical + network
- S1d technical only
- S1e clinical only

## (4) PASS/FAIL
PASS requires:
- 5 variants
- 10 exact deterministic repetitions
- 3 systems
- 150 raw rows
- exact repeated signatures for every system/variant
- B3 correct S1 coordination/escalation across all variants
- B3 ARA = 1 on every variant
- B3 MCR = 1 on every variant
- B3 PGA = 1 on every variant
- B3 ILR = 0 on every variant

## Critical scope boundary
A Gate 11A PASS is final evidence only for S1.

It does NOT authorize final claims spanning the complete Gate 10 matrix because:
- S2 Care vs Research is not implemented
- S3 stale-DT AI recommendation is not implemented
- S4 unauthorized disclosure is not implemented

Those families must be implemented and benchmarked before the full three claims
in Gate 10 can be reported as experimentally supported.

## (5) Outputs
outputs/gate11a/
- gate11a_raw_results.csv
- gate11a_per_variant_results.csv
- gate11a_aggregate_results.csv
- gate11a_checks.csv
- gate11a_coverage.json
- gate11a_status.json

## (6) Next action

### PASS
Inspect S1 raw and aggregate evidence.
Then implement Gate 11B: S2-S4 institutional scenarios before claiming complete
hackathon evaluation coverage.

### FAIL
Diagnose only the failing variant/system/metric. Do not alter the frozen
experiment matrix or underlying system unless the failure establishes a genuine
model defect.
