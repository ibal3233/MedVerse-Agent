# Gate 11B — Deterministic Institutional Extension for S2-S4

## Purpose
Validate the new institutional roles and coordination semantics required by
the three Gate 10 scenario families that were not implemented in Gate 11A.

## New agents
- Privacy Agent
- Research/IRB Agent
- Regulator Agent

## Scenarios
### S2 — Care vs Research
Care use remains allowed while research consent is withdrawn.
Expected:
`CARE_CONTINUES_RESEARCH_RESTRICTED`

### S3 — Stale/Unverified DT + High-Impact AI
High-impact automation is requested using stale/unverified DT evidence.
Expected:
`EVIDENCE_INSUFFICIENT_HIGH_IMPACT_AI_BLOCKED`

### S4 — Unauthorized Disclosure
A cross-institution request exceeds minimum-necessary scope.
Expected:
`DISCLOSURE_BLOCKED`

## Scientific boundary
All new rules in Gate 11B are controlled sandbox governance semantics for the
hackathon demonstrator. They are not asserted as universal clinical or legal rules.

## Frozen
- Gates 0-11A
- S1 coordinator and benchmark behavior
- Gate 10 experiment matrix

## Changed
Only:
- three new institutional agents
- their mandates
- S2-S4 routing
- S2-S4 deterministic coordinator
- S2-S4 scenario fixtures

The frozen S1 router/coordinator are not modified.

## PASS criteria
Every S2-S4 scenario must:
- route only to authorized agents
- produce mandate-compliant actions
- reject unauthorized observation probes
- reach the expected coordination state
- match expected human-review semantics
- preserve frozen S1 behavior

## Next action
PASS -> Gate 11C final benchmark campaign for S2-S4.
FAIL -> diagnose only the failing scenario/agent/coordination rule.
