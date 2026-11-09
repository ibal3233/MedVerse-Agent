# Gate 22B.3 Failure Record

Status: FAIL
Checks: 12/13

Passed:
- benchmark hash integrity
- DEV-only hyperparameter selection
- action accuracy
- action macro-F1
- assessment metrics
- boundary/enforcement/evidence metrics
- unsafe-ALLOW execution rate
- reporting outputs

Failed:
- minimum action-class recall

Observed:
- LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY recall = 0.50
- confirmation action errors = 21

The confirmation benchmark is now opened diagnostically. It must not be used
for hyperparameter retuning.
