# Gate 24A — Cyber / Network Preprocessing Diagnosis

## Why this gate exists
Gate 24 reached perfect train and DEV performance but failed on the disjoint
held-out generation group.

## No intervention
Gate 24A does not change the production learner, frozen thresholds, or dataset.

## Diagnostic hypotheses
1. numeric feature-scale sensitivity;
2. implicit missingness encoding for `session_origin`;
3. DEV-performance plateau causing unstable regularization tie-breaking.

## Counterfactuals
At the frozen Gate-24 C=0.3:
- baseline;
- numeric standardization only;
- explicit missing-category encoding only;
- both.

These are diagnostic counterfactuals only.

## Training-history interpretation
The Gate-24 data-growth curve remains valid evidence:
- 18 records: DEV action macro-F1 = 0.71
- 36 records: DEV action macro-F1 = 0.76
- 54 records: DEV action macro-F1 = 1.0

But convergence on TRAIN/DEV did not guarantee held-out group generalization.

## Evaluation discipline
The current Gate-24 TEST group is now opened diagnostically. Any preprocessing
repair selected using these findings requires a fresh prospectively frozen
confirmation benchmark before performance claims.

## Next step
Pre-freeze Gate 24B prospective Cyber/Network evaluation before training the
minimal preprocessing repair.
