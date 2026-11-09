# Gate 11A HOLD Diagnostic Patch

## Observed condition
Gate 11A returned HOLD:
`Gate 10 status file not found.`

## Classification
Packaging/provenance artifact issue.

Gate 10 had already passed 10/10 in the user's validated run, but its runtime-generated
`outputs/gate10/gate10_status.json` was not present inside the newly packaged Gate 11A
snapshot.

This is not:
- a campaign failure,
- a model failure,
- a baseline failure,
- a metric failure.

## Controlled change
Introduced `FREEZE_REGISTRY.json`, a persistent machine-readable promotion registry.

Gate 11A now checks the registry entry for Gate 10 rather than depending on a transient
outputs directory from a previous extracted package.

## Scientific components unchanged
- Gate 10 matrix version 1.0
- B1/B2/B3
- S1 variants
- metrics
- 10 deterministic repetitions
- campaign logic
- agent/coordinator/policy/reasoning semantics

## Required outcome
Rerun Gate 11A.
Promotion requires all Gate 11A campaign checks to PASS.
