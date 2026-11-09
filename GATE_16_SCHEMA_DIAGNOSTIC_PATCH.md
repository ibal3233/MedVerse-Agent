# Gate 16 Schema Diagnostic Patch

## Classification
Implementation/schema integration issue — not a scientific failure.

## Observed failure
Gate 16 returned 7/8 checks PASS because two legacy KB v0.3 records lacked
the new candidate-corpus metadata field `source_type`.

## Patched records

- `KR-MSA-ART21-ACCESS-001`
  - source_type: `statute`

- `KR-PIPC-SAFE-2026-001`
  - source_type: `administrative_rule`

## Frozen content
No policy text, jurisdiction, agent access, effective date, source URL,
retrieval eligibility, or reasoning semantics were changed.

## Expected rerun result
All 8 corpus structure/provenance checks should pass.

Because the full official 2026.03 Pseudonymized Information Processing
Guideline is still absent, the overall Gate 16 status should then be:

`HOLD`

not `FAIL`.

The HOLD is an external-source dependency and should remain until the actual
full guideline PDF is obtained.
