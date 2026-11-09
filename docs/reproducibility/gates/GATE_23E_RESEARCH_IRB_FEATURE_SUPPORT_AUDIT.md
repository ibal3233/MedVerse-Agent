# Gate 23E — Research / IRB Feature-Support & OOD Learnability Audit

## Scientific question
Are the four residual Gate-23D OOD errors evidence of insufficient model
capacity, or does the failed policy interaction simply have no positive
training support?

## Frozen
- Gate-23D learner
- Gate-23D C selection
- representation
- shield v2
- original train/dev/test
- compositional augmentation
- replay
- current 24-case OOD benchmark
- all Gate-23D thresholds

## No intervention
No retraining, rebalancing, feature modification or hyperparameter tuning.

## Primary audit
Count positive activation of the critical interaction:

`active consent AND approved IRB AND pseudonymization deficient`

across:
- original train
- dev
- ID test
- compositional augmentation
- replay
- combined training
- OOD

## Evaluation discipline
If the interaction is later added to training, the current OOD set cannot be
used as a fresh post-repair test. It becomes diagnostic-only.

## Dataset-design rule
A learnable OOD benchmark should ensure that policy-relevant primitives and
engineered interactions have some training support while still withholding
novel combinations for generalization evaluation.

## Outputs
- feature-support matrix CSV
- error-support trace CSV
- diagnosis JSON
- future evaluation contract
- four publication-ready figures in PNG/PDF
