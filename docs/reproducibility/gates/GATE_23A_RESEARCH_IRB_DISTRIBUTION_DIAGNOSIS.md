# Gate 23A — Research / IRB Distribution-Shift & Model-Selection Diagnosis

## Purpose
Diagnose why Gate 23 achieved perfect OOD action performance but degraded the
original ID action test.

## Frozen
- Gate-21A Research/IRB train/dev/test data
- Gate-23 OOD benchmark
- Gate-23 compositional augmentation
- multinomial logistic-regression family
- candidate C grid
- hard policy shield
- all PASS thresholds

## No intervention
Gate 23A does not tune, rebalance, augment, or change the model.

## Questions
1. Did augmentation skew the action-class distribution?
2. Was C=0.1 only appropriate before augmentation?
3. Can the same model family recover ID performance at other C values?
4. Is there an ID/OOD regularization tradeoff?

## Required plots
- original vs augmentation action-class distribution
- C sensitivity before/after augmentation
- post-augmentation ID/OOD tradeoff
- OOD confusion matrix at C=1

## Next step
Only if the diagnosis passes:
Gate 23B may rebalance compositional coverage and perform dev-only hyperparameter
selection after augmentation, while preserving the OOD benchmark untouched.
