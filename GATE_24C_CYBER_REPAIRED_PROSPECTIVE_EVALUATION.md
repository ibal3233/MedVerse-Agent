# Gate 24C — Cyber / Network Repaired Prospective Evaluation

## Purpose
Close the Cyber/Network learning branch using the prospective benchmark frozen
in Gate 24B before repair training.

## Frozen intervention
From Gate 24A diagnosis:
- standardize `packet_loss`, `rtt_ms`, and `jitter_ms`;
- fit means/standard deviations on TRAIN only;
- encode absent `session_origin` explicitly as `__MISSING__`;
- keep multinomial logistic regression;
- keep thresholds unchanged.

## Data discipline
- TRAIN = Gate-21A g0-g2
- DEV = Gate-21A g3
- Gate-21A g4 = opened diagnostic-only; excluded
- confirmation = frozen Gate-24B g5-g8, 72 records

## Hyperparameter selection
C ∈ {0.01, 0.03, 0.1, 0.3, 1, 3, 10}

Selection is DEV-only. Prospective g5-g8 results are not used in selection.

## Reporting
- hyperparameter table (Markdown + CSV)
- hyperparameter plot
- group-wise training-history plot + CSV
- solver convergence plot
- prospective metrics table
- per-class precision/recall/F1
- confusion matrix
- g5-g8 stability plot
- raw prospective predictions

## Model persistence
The model is freshly trained from source data in the current runtime. This
avoids depending on a scikit-learn model serialized under a different version.

## Claim boundary
Synthetic prospective generator-shift benchmark using frozen Cyber scenario
semantics. It is not external network telemetry or clinical validation.

## Stop rule
If PASS, agent-learning experiments stop for the hackathon and the project
moves to final system consolidation and demo/video production.
