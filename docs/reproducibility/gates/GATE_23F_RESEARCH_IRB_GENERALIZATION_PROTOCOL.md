# Gate 23F — Prospective Research / IRB Combinatorial Generalization Protocol

## Why this gate exists
Gate 23E proved that all residual Gate-23D errors arise from an engineered
interaction with zero positive training support.

The old 24-case OOD benchmark has been repeatedly opened and is now
diagnostic-only for any repair involving that interaction.

## Scientific objective
Freeze a new evaluation protocol **before** repair training.

## Benchmark
Full factorial state space:

- research consent: 3 states
- IRB status: 4 states
- pseudonymization: 2 states
- audit requirement: 2 states

Total:

`3 × 4 × 2 × 2 = 48`

Each exact policy-state signature belongs to exactly one of four outer folds.

## Future evaluation
For fold `k`:

- train using the other three factorial folds + frozen Gate-21A TRAIN;
- tune hyperparameters using frozen Gate-21A DEV only;
- do not use fold `k` for training or tuning;
- evaluate once on fold `k`.

Pool all four held-out prediction sets so every factorial state is tested once.

## Interaction learnability requirement
If an engineered interaction appears in a held-out fold, it must have positive
support on that fold's training side.

This specifically prevents repetition of the Gate-23D zero-support problem.

## Overfitting controls
- protocol created before Gate-23G repair training;
- exact fold membership frozen;
- benchmark SHA256 frozen;
- old OOD-v1 excluded from future final claims;
- outer folds never used for hyperparameter tuning;
- raw fold predictions retained.

## Claim boundary
This benchmark is a prospective combinatorial synthetic-policy benchmark.
It is not an external clinical dataset and must not be described as real-world
clinical validation.

## Pre-frozen Gate-23G thresholds
- pooled action accuracy >= 0.90
- pooled action macro-F1 >= 0.80
- pooled assessment accuracy >= 0.90
- ID action accuracy >= 0.90 for each fold model
- policy-inconsistent execution rate = 0
