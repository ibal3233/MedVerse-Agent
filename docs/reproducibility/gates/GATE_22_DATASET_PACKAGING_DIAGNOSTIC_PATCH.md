# Gate 22 Dataset Packaging Diagnostic Patch

## Observed failure

Gate 22 raised:

`FileNotFoundError: data/learning/gate21a/privacy_agent.csv`

before model training began.

## Classification

Implementation / cumulative-packaging error.

This is not:
- a model-training failure;
- a representation failure;
- a data-adequacy failure;
- a policy-shield failure.

Gate 22 scientific status remains HOLD until rerun.

## Root cause

Gate 21A generates its expanded 480-record benchmark at runtime. The cumulative
Gate-22 ZIP inherited the Gate-21A source code but did not include the post-run
generated CSV files from the user's local execution.

## Patch

The cumulative package now materializes the deterministic Gate-21A dataset and
includes:

- `all_agents.csv`
- `hospital_agent.csv`
- `cyber_network_agent.csv`
- `privacy_agent.csv`
- `research_irb_agent.csv`
- `regulator_agent.csv`
- `splits.json`
- `dataset_integrity_manifest.json`

The integrity manifest records the expected dataset counts and SHA-256 hash of
each frozen file.

Gate 22 now verifies the presence and expected Privacy Agent row count before
training.

## Frozen scientific components

Unchanged:
- Gate-21A dataset-generation logic
- 480-record benchmark definition
- train/dev/test split
- Privacy Agent feature representation
- target labels
- model family
- C search set
- tuning metric
- PASS thresholds
- policy-shield logic
