# Gate 21A — Learning Dataset Adequacy & Split Strengthening

## Why this gate exists
Gate 21 passed its structural contract, but the observed split (40 train / 2 dev / 2 test)
is insufficient for meaningful learned-agent evaluation.

## Dataset
`data/learning/gate21a/`

Approximately 480 deterministic policy/safety benchmark records.

## Agents
- Healthcare Provider / Hospital Agent
- Cyber / Network Agent
- Privacy Agent
- Research / IRB Agent
- Health / AI Regulator Agent

## Split
Agent-aware grouped perturbation split:
- 60% groups train
- 20% groups dev
- 20% groups test

Each agent must have substantial representation in every split.

## Important files
- `medverse/learning/gate21a_dataset_builder.py`
- `medverse/gates/gate21a_learning_dataset_adequacy.py`
- `data/learning/gate21a/*.csv`
- `data/learning/gate21a/splits.json`

## PASS requirements
- >=400 total records
- every agent has train/dev/test coverage
- train >=40, dev >=12, test >=12 per agent
- no split-group leakage
- no exact feature duplicates
- every held-out action and assessment class appears in training
- no patient data
- deterministic regeneration

## Next gate
Gate 22 — first actual model training, beginning with the Privacy Agent.
