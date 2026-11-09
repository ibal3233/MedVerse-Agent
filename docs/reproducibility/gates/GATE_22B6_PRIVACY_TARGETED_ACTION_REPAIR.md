# Gate 22B.6 — Patched Privacy Targeted Action-Head Repair

## Why patched
The first local Gate-22B.6 implementation retrained every Privacy output head.
Although it fixed action prediction, evidence accuracy regressed.

That violates the one-component-intervention principle because Gate-22B.4
diagnosed an **action precedence support** defect.

## Correct intervention
- load the Gate-22B.3 multi-output Privacy model;
- keep assessment, boundary, enforcement and evidence models unchanged;
- retrain **only the action head**;
- raise the seven diagnosed policy cores to six action-training examples each;
- select the action-head C using DEV only;
- evaluate once on Gate-22B.5.

## Cumulative regression checks
The gate retains the earlier multi-output thresholds:
- action accuracy >= 0.95
- action macro-F1 >= 0.90
- minimum action recall >= 0.80
- protected diagnosed-core accuracy >= 0.90
- assessment accuracy >= 0.95 and macro-F1 >= 0.90
- boundary accuracy >= 0.95
- enforcement accuracy >= 0.95
- evidence accuracy >= 0.95
- unsafe-ALLOW execution rate = 0

## Reporting
Hyperparameter table and training history refer to the action head only, because
that is the only component retrained.
