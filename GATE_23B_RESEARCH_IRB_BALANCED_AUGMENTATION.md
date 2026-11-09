# Gate 23B — Balanced Compositional Augmentation & Post-Augmentation Selection

## Scientific question
Does correcting the Gate-23A diagnosed action-class shift and moving model
selection after augmentation resolve the Research/IRB ID-OOD tradeoff without
changing the model family?

## Frozen
- Research/IRB oracle
- feature semantics
- original Gate-21A train/dev/test assignments
- Gate-23 OOD benchmark
- policy shield
- logistic-regression model family
- scientific performance thresholds

## Changed
Only:
1. training-only class-preserving replay for augmentation-missing action classes;
2. C selection after augmentation;
3. finer C grid around the diagnosed regularization transition.

## Leakage control
- replay uses TRAIN records only;
- DEV is used only for model selection;
- ID TEST is opened only after selection;
- OOD is untouched and never used for selection;
- generated augmentation signatures have zero overlap with OOD signatures.

## Required outputs
- post-augmentation tuning CSV
- replay provenance CSV
- OOD predictions CSV
- dataset/methodology JSON
- saved trained model
- publication PNG/PDF figures

## PASS thresholds
Unchanged from Gate 23:
- ID action accuracy >= 0.90
- OOD action accuracy >= 0.80
- OOD action macro-F1 >= 0.75
- OOD assessment accuracy >= 0.80
- unsafe executions after shield = 0
