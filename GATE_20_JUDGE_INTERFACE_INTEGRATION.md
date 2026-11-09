# Gate 20 — Judge-Facing Interface Integration

## 1. Objective

Validate that the competition interface exposes the frozen Gate-19 reasoning
chain clearly without changing any scientific decision.

## 2. Dataset

No new scientific dataset is introduced.

Gate 20 reuses:
`data/evaluation/gate19_end_to_end_cases.json`

A presentation-only contract is added:
`data/evaluation/gate20_ui_expectations.json`

It defines which five layers must be visible:
1. Digital Twin state
2. institutional assessments
3. Korean-policy evidence
4. policy-boundary status
5. MedVerse-Agent coordination

## 3. Agents

All five institutional agents remain unchanged:
- Healthcare Provider / Hospital
- Cyber / Network
- Privacy
- Research / IRB
- Health / AI Regulator

Only the agents participating in a selected S1-S4 scenario are rendered.

## 4. Files introduced

### `demo/judge_view_model.py`
Pure presentation adapter. Humanizes codes and constructs judge-facing policy,
agent, outcome, and coordination cards. It is prohibited from changing decisions.

### `demo/competition_app.py`
Streamlit competition interface using the validated Gate-19 pipeline directly.

### `medverse/gates/gate20_judge_interface_integration.py`
Regression gate that checks preservation of scientific outputs and completeness
of UI provenance.

### `data/evaluation/gate20_ui_expectations.json`
Presentation contract only; not scientific ground truth.

## 5. Scientific logic

No change to:
- Digital Twin semantics
- evidence partitions
- grounded-agent reasoning
- Korean policy corpus
- MiniLM embeddings
- jurisdiction filter
- agent-access filter
- policy-boundary validator
- MedVerse-Agent harmonization
- S1-S4 outcomes

## 6. Judge-facing flow

Digital Twin
-> Institutional Agent
-> Retrieved Korean Policy
-> Policy Boundary
-> MedVerse-Agent Harmonization
-> Final Outcome

## 7. Policy cards expose

- policy chunk ID
- authority
- source type
- article/section locator
- similarity score
- official source URL

## 8. Safety/evidence panel

The interface exposes:
- whether NCC population data were used
- whether patient-level inference was made from population data
- whether unauthorized evidence was used

The expected latter two remain `false`.

## 9. PASS criteria

- all four Gate-19 final outcomes preserved
- all four coordination states preserved
- participating agents visible
- each participating agent has policy evidence + boundary state
- source provenance visible
- evidence-boundary safety preserved
- all five UI layers implemented
- deterministic view transformation
- no scientific logic changed

## 10. Run commands

Gate:
`python medverse/gates/gate20_judge_interface_integration.py`

Interface:
`python -m streamlit run demo/competition_app.py`

## 11. Next step after PASS

After Gate 20 passes, the scientific and judge-facing integrated system is
functionally closed. The next work should be competition hardening:
- visual polish;
- demo timing;
- source-link validation;
- final screenshots;
- submission report/deck synchronization;
- packaging and demo-day rehearsal.

Those should be treated as release validation, not new research gates unless
they uncover an actual implementation defect.
