# Gate 10 — Final Experiment-Matrix Freeze

## (1) Question this gate answers
Before generating final hackathon/paper evidence, is every intended claim mapped
to a controlled experiment, baseline, scenario family, perturbation, metric, and
report artifact?

Gate 10 does not generate final results.

## (2) Frozen
All validated components from Gates 0-9, contingent on the post-Gate-9
regression PASS.

## (3) Changed
Only the final experimental design specification.

No system behavior is changed.

## (4) PASS/HOLD/FAIL

### HOLD
Gate 10 remains on HOLD until:
`regression_post_gate9_patch.py`
returns PASS.

### PASS
All matrix-integrity checks pass:
- B1/B2/B3 defined
- seven metrics defined
- S1-S4 scenario families defined
- perturbation axes defined
- every claim maps to valid metrics, baselines and scenarios
- raw-result preservation is required
- fixture results are prohibited as final claims
- uncertainty is required for stochastic components
- live-LLM results are separated from deterministic-core results

### FAIL
Any inconsistent claim mapping or missing experimental component.

## (5) Required outputs
outputs/gate10/
- gate10_claim_experiment_map.csv
- gate10_checks.csv
- gate10_status.json

Frozen matrix source:
data/experiments/gate10_experiment_matrix.json

## (6) Exact next action

1. Run the post-Gate-9 regression suite.
2. If PASS, run Gate 10.
3. If Gate 10 PASS, freeze the matrix.
4. Only then implement/generate the final benchmark campaign.
