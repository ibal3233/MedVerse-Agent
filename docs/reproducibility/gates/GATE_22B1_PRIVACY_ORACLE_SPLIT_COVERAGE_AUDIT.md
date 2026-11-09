# Gate 22B.1 — Privacy Oracle / Split / Coverage Audit

## Why this gate is required
Gate 22C and later cross-agent learning work were executed before validating
three foundational assumptions:

1. whether Gate-21A and Gate-22A use the same Privacy target semantics;
2. whether the Gate-21A split actually prevents model-visible leakage;
3. whether Gate-22A failures are on combinations whose precedence is defined by
   the Gate-21A generator.

## Frozen
No model, label, threshold, feature, or benchmark is changed.

## Audit
- reconstruct the eight Gate-21A Privacy base templates directly from the data;
- compare Gate-22A oracle outputs on every observed base;
- inspect the actual g0–g4 split;
- quantify model-visible signature overlap across TRAIN/DEV/TEST;
- quantify exact core, pair and triple interaction coverage;
- classify every Gate-22A OOD row as:
  - oracle_compatible,
  - oracle_conflict,
  - undefined_by_train_oracle;
- partition the already-saved Gate-22A errors without retraining.

## Corrected methodological statement
The Gate-21A split is **group-disjoint**, but it is not semantic-signature-
disjoint for Privacy. The same eight model-visible semantic templates occur in
TRAIN, DEV and TEST; the changing `request_context_index` is removed before
modeling.

Therefore perfect Gate-22 ID accuracy is interpolation evidence, not evidence
of independent compositional generalization.

## Gate-22C interpretation
Gate-22C uses the Gate-22A oracle to label new combinations. If Gate-21A does
not explicitly define those precedence combinations, Gate-22C is an explicit
oracle-extension/adoption plus coverage intervention, not merely recovery of
a rule already supervised by Gate-21A.

## Required future step
The 40 Gate-22A cases are opened diagnostic cases. A fresh frozen Privacy
confirmation benchmark is required after the precedence oracle is explicitly
adopted.
