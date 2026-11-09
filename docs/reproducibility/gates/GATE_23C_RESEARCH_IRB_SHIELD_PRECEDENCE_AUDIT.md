# Gate 23C — Research / IRB Rule-Precedence & Shield Completeness Audit

## Why this gate exists
Gate 23B restored perfect ID performance but retained six OOD action errors.
A detailed audit also showed that the legacy unsafe-execution metric covered
erroneous ALLOW actions only.

## Frozen
- Gate-23B training path
- balanced/replay dataset
- selected C path
- model family
- OOD benchmark
- Research/IRB oracle
- all scientific performance thresholds

## No learning intervention
Gate 23C performs no retraining and no hyperparameter tuning.

## Questions
1. Which rule-precedence combinations explain the six OOD errors?
2. Does the current Research/IRB shield validate every action against the
   complete institutional semantics?
3. Is the existing unsafe-execution metric sufficiently broad?

## Important safety correction
Future safety reporting uses:
`policy_inconsistent_execution_rate`

It covers every action class, not only invalid ALLOW actions.

## Next authorized changes
Only after this audit:
1. complete the Research/IRB shield semantics;
2. introduce explicit rule-precedence interaction representation;
3. keep the model family unchanged for the next test.
