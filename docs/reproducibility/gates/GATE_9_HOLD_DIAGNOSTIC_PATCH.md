# Gate 9 HOLD Diagnostic Patch

## Observed condition
Gate 9 returned HOLD:
`Missing E1 hospital assessment.`

## Classification
Implementation/model-domain defect in the deterministic coordinator interface,
revealed by Gate 9 counterfactual evaluation.

This is not:
- a semantic-retrieval failure,
- an embedding failure,
- a learning failure,
- a metric failure.

## Root cause
`DeterministicCoordinator.coordinate()` raised immediately when E1 was absent.

That made two already-defined coordinator branches unreachable:
- TECHNICAL_VERIFICATION
- MONITOR

The full S1 case did not expose this defect because S1 always contains E1.

## Controlled change
Only the coordinator's unconditional E1 guard was removed.

`clinical_high` is now false when E1 is absent.

No full-S1 rule, threshold, action set, mandate, routing rule, policy record,
embedding model, or bounded reasoning rule was changed.

Gate 9 was also changed so C4_NO_RISK now invokes the real coordinator rather
than being hard-coded as correct.

## Required regression sequence
Because a frozen Gate 5 component was touched, rerun:
1. Gate 5
2. Gate 7B
3. Gate 8
4. Gate 9

Promotion requires all affected regression gates to pass.

## Expected coordinator domain
- Full S1 -> COMPLEMENTARY_RISK
- Clinical only -> SINGLE_DOMAIN_ESCALATION
- Technical only -> TECHNICAL_VERIFICATION
- Empty/no-risk -> MONITOR
