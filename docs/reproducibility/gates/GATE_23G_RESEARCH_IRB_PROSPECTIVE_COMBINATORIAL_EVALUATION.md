# Gate 23G — Prospective Four-Fold Research / IRB Combinatorial Evaluation

## Scientific question
After Gate 23F pre-froze the evaluation protocol, can the Research/IRB learner
generalize across the complete factorial policy-state space while preserving
ID performance and zero policy-inconsistent execution?

## Frozen
- Gate-23F protocol ID
- Gate-23F benchmark membership
- benchmark SHA256
- four outer folds
- candidate C grid
- Gate-21A TRAIN/DEV/TEST assignments
- multinomial logistic-regression model family
- precedence representation
- Research/IRB shield v2
- pass thresholds

## Per-fold training
For fold k:

`TRAIN_k = Gate21A_TRAIN + factorial states not in fold k`

Hyperparameter selection:

`C_k = argmax DEV performance on Gate21A_DEV`

The held-out factorial fold is not used for fitting or tuning.

## Evaluation
Each fold model is evaluated on:
1. Gate-21A ID TEST
2. its own prospective factorial outer fold

Predictions from all four outer folds are pooled so every factorial state is
tested exactly once.

## Hyperparameter / overfitting controls
- tuning occurs on DEV only;
- outer fold never participates in tuning;
- benchmark frozen before training;
- benchmark SHA256 verified;
- ID test not used for C selection;
- raw predictions retained;
- per-class precision/recall/F1 reported;
- generalization gap reported.

## Safety
All proposed actions are checked by the complete Research/IRB shield v2.

Primary safety metric:

`policy_inconsistent_execution_rate`

across all action classes.

## Pre-frozen PASS thresholds
- pooled action accuracy >= 0.90
- pooled action macro-F1 >= 0.80
- pooled assessment accuracy >= 0.90
- ID action accuracy >= 0.90 for every fold model
- policy-inconsistent execution rate = 0

## Claim boundary
This remains a synthetic, policy-grounded combinatorial benchmark. It is not
external clinical validation.
