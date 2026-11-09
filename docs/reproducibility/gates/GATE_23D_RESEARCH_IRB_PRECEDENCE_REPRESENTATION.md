# Gate 23D — Research / IRB Precedence Representation & Complete Policy Shield

## Scientific question
Can the remaining Research/IRB OOD failures be resolved by exposing
policy-relevant interactions explicitly while retaining the same interpretable
logistic-regression model family?

## Frozen
- Research/IRB institutional oracle
- original Gate-21A train/dev/test assignments
- Gate-23 OOD benchmark
- compositional augmentation
- class-preserving train replay
- performance thresholds
- logistic-regression model family

## Changed
Only the two Gate-23C diagnosed components:

1. **Representation**
   Explicit governance interaction features derived from:
   - research consent,
   - IRB status,
   - pseudonymization status,
   - audit requirement.

   No target labels are used as features.

2. **Execution validation**
   Versioned complete Research/IRB policy shield:
   `medverse/reasoning/research_irb_policy_shield_v2.py`

   All action classes are checked against frozen institutional semantics.

## Hyperparameter tuning
Performed after the representation change using DEV only.

Grid:
`C ∈ {0.03, 0.1, 0.3, 1, 3, 10}`

ID test and OOD are never used for selection.

## Overfitting controls
- original split assignments frozen;
- zero generated augmentation/OOD signature overlap;
- dev-only selection;
- ID and OOD opened only after selection;
- raw predictions preserved.

## Safety
Primary safety metric:
`policy_inconsistent_execution_rate`

This covers every action class.

## Publication outputs
- hyperparameter-selection plot;
- ID vs OOD metrics;
- Gate-23B vs Gate-23D OOD error reduction;
- complete-shield safety plot;
- OOD confusion matrix;
- methodology JSON;
- raw OOD prediction/safety CSV.
