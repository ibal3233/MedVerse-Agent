# Gate 23F Support-Validation Patch

Classification: implementation/protocol-checker correction, not scientific FAIL.

The original Gate-23F checker evaluated interaction support using only the
three non-held-out factorial folds. However, the frozen protocol explicitly
defines the future training set as:

`other factorial folds + frozen Gate-21A TRAIN`.

The patched checker therefore reports:
- factorial train-side support;
- Gate-21A base-train support;
- total valid training support.

Unchanged:
- 48-state benchmark;
- exact outer-fold assignment;
- benchmark SHA256;
- frozen thresholds;
- hyperparameter policy;
- OOD-v1 diagnostic-only status;
- no training in Gate 23F.
