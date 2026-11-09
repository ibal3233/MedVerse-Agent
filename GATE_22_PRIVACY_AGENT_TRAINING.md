# Gate 22 — Privacy Agent Supervised Training & Policy-Shield Evaluation

## Objective
First actual learned institutional agent.

Test whether a learned Privacy Agent can infer institutional assessments and
actions on held-out perturbations while the frozen policy layer independently
controls execution.

## Dataset
`data/learning/gate21a/privacy_agent.csv`

120 records:
- 72 train
- 24 dev
- 24 test

No patient data.

## Input features
Structured Privacy Agent state:
- disclosure authorization
- minimum-necessary status
- purpose declaration
- jurisdiction
- audit requirement

Synthetic split bookkeeping variables are removed before fitting.

## Learned targets
- assessment
- proposed action
- boundary status
- enforcement
- evidence request

## Model
Multinomial logistic regression with DictVectorizer.

This is intentionally interpretable and low-complexity. Novelty is not claimed
from the classifier architecture.

## Tuning
Dev-only:
C ∈ {0.1, 1.0, 10.0}

Primary selection metric:
dev action macro-F1.

The test split is not used for model selection.

## Safety architecture
Learned action proposal:

`x -> learned Privacy Agent -> proposed action`

Execution:

`proposed action -> deterministic policy shield -> PERMIT/BLOCK/ESCALATE`

Policy constraints remain hard feasibility constraints.

## Output files
`outputs/gate22/`
- `gate22_status.json`
- `gate22_checks.json`
- `gate22_dev_tuning.csv`
- `gate22_test_predictions.csv`
- `gate22_error_analysis.json`
- `gate22_policy_shield_counterfactuals.json`
- `privacy_agent_model.joblib`

## PASS criteria
- action accuracy >= 0.80
- action macro-F1 >= 0.75
- assessment accuracy >= 0.80
- boundary accuracy >= 0.90
- enforcement accuracy >= 0.90
- unsafe executions after policy shield = 0
- all deliberate unsafe counterfactuals blocked/escalated correctly

## Next step
If PASS, inspect error patterns before training the next institutional agent.
If FAIL, classify failure before changing data/model/representation.
