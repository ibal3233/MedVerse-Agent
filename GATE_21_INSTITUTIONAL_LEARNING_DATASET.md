# Gate 21 — Institutional Learning Dataset & Baseline Freeze

## Objective
Freeze the institutional learning problem before fitting any model.

## Dataset
`data/learning/gate21/`

Files:
- `all_agents.csv`
- `hospital_agent.csv`
- `cyber_network_agent.csv`
- `privacy_agent.csv`
- `research_irb_agent.csv`
- `regulator_agent.csv`
- `splits.json`
- `baseline_matrix.json`

The dataset is a deterministic synthetic policy/safety benchmark and contains no patient records.

## Agents
- Healthcare Provider / Hospital Agent
- Cyber / Network Agent
- Privacy Agent
- Research / IRB Agent
- Health / AI Regulator Agent

## Targets
- assessment
- action
- policy-boundary status
- enforcement
- evidence request
- escalation

## Split rule
Scenario-family group split; no family can appear in more than one of train/dev/test.

## Baselines
B1 Single Omniscient Agent
B2 Role-Prompted Unconstrained MAS
B3 Consensus / Debate MAS
B4 Policy-Filtered MAS without Harmonization
B5 MedVerse-Agent

## Important files
`medverse/learning/gate21_dataset_builder.py`
`medverse/gates/gate21_institutional_learning_dataset.py`

## Next gate
Gate 22 performs the first actual institutional-agent training. The learned proposal remains subordinate to the frozen Gate-17 hard validator.
