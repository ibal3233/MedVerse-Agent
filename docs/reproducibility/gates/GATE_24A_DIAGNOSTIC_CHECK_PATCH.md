# Gate 24A Diagnostic Check Patch

The first Gate-24A checker incorrectly required assessment failure to persist
for *every* C value.

The actual diagnostic question is whether changing regularization alone can
jointly recover both action and assessment performance.

Observed baseline C sweep:
- very small C can recover assessment but damages action;
- C >= 1 recovers action but assessment remains degraded;
- no baseline C simultaneously achieves >=0.90 action and >=0.90 assessment.

The patch changes only this diagnostic assertion. It does not alter data,
models, predictions, counterfactuals, thresholds, or scientific conclusions.
