# MedVerse-Agent Diagnostic-Gated Workflow

This is a single cumulative project.

## Important rule
Gates are validation stages, not separate software projects.

You should keep working in this same folder:

MedVerse-Agent/

and add each new gate incrementally.

## Current status

Gate 0 — System/experimental contract: FROZEN
Gate 1 — Data loading/validation: implemented
Gate 2 — Deterministic Medical Metaverse environment: implemented

## Shared data

The NCC dataset lives only once:

data/external/ncc_cancer_incidence.csv

Do not copy it into gate-specific folders.

## Running Gate 1

In Spyder:

%runfile <PROJECT_ROOT>/medverse/gates/gate1_data_loading.py --wdir

## Running Gate 2

In Spyder:

%runfile <PROJECT_ROOT>/medverse/gates/gate2_environment.py --wdir

Both scripts calculate PROJECT_ROOT automatically, so the same repository
layout is used by every gate.

## Outputs

outputs/gate1/
outputs/gate2/

Future gates will add:

outputs/gate3/
outputs/gate4/
...

## Regression principle

After Gate 2 passes, future gates should not change:
- Gate 1 data semantics
- Gate 1 dataset fingerprint
- Gate 2 deterministic environment semantics

unless a targeted diagnostic proves that a frozen component is wrong.


## Gate 3
Routing and asymmetric observations.

Run:

%runfile <PROJECT_ROOT>/medverse/gates/gate3_routing_observations.py --wdir

PASS freezes event routing and observation boundaries before any institutional reasoning is added.


## Gate 4
Deterministic institutional assessments.

Run:

%runfile <PROJECT_ROOT>/medverse/gates/gate4_deterministic_assessments.py --wdir

PASS freezes independent Hospital and Cyber/Network assessments and mandate enforcement before the coordinator is introduced.


## Gate 5
Deterministic multi-agent coordination.

Run:

%runfile <PROJECT_ROOT>/medverse/gates/gate5_deterministic_coordination.py --wdir

PASS freezes:
- coordination-state semantics
- joint action logic
- action delegation
- minimum-necessary inter-agent communication

Only after Gate 5 passes do we begin authentic policy KB ingestion/retrieval.


## Gate 6
Policy knowledge-base ingestion and deterministic retrieval.

Run:

%runfile <PROJECT_ROOT>/medverse/gates/gate6_policy_kb_retrieval.py --wdir

PASS freezes source provenance, policy access partitions and retrieval semantics before multilingual embeddings or LLM reasoning are introduced.


## Gate 7A
Multilingual semantic retrieval and translation-provenance diagnostics.

Dependency:
pip install sentence-transformers

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate7a_multilingual_semantic_retrieval.py --wdir

PASS is required before any LLM policy-grounded reasoning adapter is introduced.


## Gate 7B
Bounded policy-grounded reasoning contract.

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate7b_bounded_reasoning.py --wdir

This gate does NOT execute an external LLM.
It validates the constraints that any future LLM must satisfy.


## Gate 8
End-to-end integration and demo readiness.

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate8_end_to_end_integration.py --wdir

Optional demo:
pip install streamlit
streamlit run demo/app.py

PASS freezes the deterministic end-to-end demonstrator before final evaluation.


## Gate 9
Evaluation harness and baseline validation.

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate9_evaluation_harness.py --wdir

Gate 9 validates the evaluator only.
Do not interpret its fixture metrics as final scientific performance.


## Post-Gate-9 regression
Run first:
%runfile <PROJECT_ROOT>/medverse/gates/regression_post_gate9_patch.py --wdir

Required before Gate 10 because Gate 9 exposed and corrected a frozen Gate 5
coordinator-domain defect.

## Gate 10
After regression PASS:
%runfile <PROJECT_ROOT>/medverse/gates/gate10_experiment_matrix_freeze.py --wdir

Gate 10 freezes the final experiment matrix but generates no final scientific results.


## Gate 11A
Final benchmark campaign for the implemented S1 family.

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate11a_s1_final_campaign.py --wdir

A PASS generates final S1 evidence only.
S2-S4 remain required for complete Gate 10 claim coverage.


## Gate 11B
Deterministic institutional extension for S2-S4.

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate11b_s2_s4_deterministic_extension.py --wdir

PASS is required before final S2-S4 benchmarking.


## Gate 11C
Final operational benchmark campaign for S2-S4.

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate11c_s2_s4_final_campaign.py --wdir

PASS completes operational benchmark coverage for S1-S4.
PGA for S2-S4 remains deferred until authoritative policy KB expansion.


## Gate 12
Authoritative policy-KB expansion for Privacy, Research/IRB and Regulator agents.

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate12_policy_kb_expansion.py --wdir

PASS is required before S2-S4 PGA can be scored as final evidence.


## Gate 13
Final policy-grounding campaign across S1-S4.

Run:
%runfile <PROJECT_ROOT>/medverse/gates/gate13_final_policy_grounding_campaign.py --wdir

PASS closes the full Gate 10 experimental matrix.


## Gate 14 — Data-Grounded Digital-Twin Foundation

Run:

```python
%runfile <PROJECT_ROOT>/medverse/gates/gate14_data_grounded_dt_foundation.py --wdir
```

The Korean NCC cancer-incidence CSV remains a shared external dataset:

`data/external/ncc_cancer_incidence.csv`

Missing external data causes HOLD rather than scientific FAIL.


## Gate 15 — Data/Policy-Grounded Agent Reasoning

Run:

```python
%runfile <PROJECT_ROOT>/medverse/gates/gate15_data_policy_grounded_agent_reasoning.py --wdir
```

PASS requires grounded S1-S4 agent assessments, policy attribution, DT provenance
attribution, bounded open-data use, and zero patient-level inference from the
population NCC dataset.
