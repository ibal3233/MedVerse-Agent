# Gate 24 — Cyber / Network Agent Training + Training-History Diagnostics

## Question
Can the Cyber/Network Agent learn its institution-specific telemetry/security
assessment and action policy from the frozen Gate-21A dataset while maintaining
clean split discipline and interpretable training diagnostics?

## Dataset
`data/learning/gate21a/cyber_network_agent.csv`

Actual records:
- 54 train
- 18 dev
- 18 test

Actual split groups:
- TRAIN: g0, g1, g2
- DEV: g3
- TEST: g4

No split group crosses partitions.

## Features
- certificate status
- packet loss
- RTT
- jitter
- session origin when present

Split identifiers and perturbation identifiers are not model features.

## Targets
Learning evidence:
- assessment
- action

The current dataset's boundary/enforcement/evidence outputs are constants and
are not presented as meaningful learned discrimination.

## Hyperparameter tuning
C grid:
`{0.01, 0.03, 0.1, 0.3, 1, 3, 10}`

Selection uses DEV only.

## Training history
Logistic regression with LBFGS does not provide an epoch-wise loss history.
Therefore we report three valid training diagnostics instead:

1. cumulative group-wise data-growth learning curve;
2. train-vs-dev macro-F1 over C;
3. LBFGS iteration counts over C.

Raw values are saved in CSV.

## Overfitting controls
- disjoint generation groups;
- DEV-only hyperparameter selection;
- TEST opened only after selection;
- train and DEV trajectories shown together;
- raw prediction and training-history files retained.

## Required figures
- training-history learning curve
- train/dev hyperparameter path
- solver convergence iterations
- ID test metrics
- action confusion matrix
