# Gate 8 — End-to-End Integration and Demo Readiness

## (1) Question this gate answers
Can all frozen components from Gates 1-7B operate together end-to-end without changing their validated semantics?

The integrated pipeline must preserve:
- environment transitions
- institutional routing
- asymmetric observations
- independent assessments
- coordination semantics
- policy retrieval/provenance
- bounded explanation
- audit trace

## (2) Frozen
Gates 0-7B in full.

## (3) Changed
Only integration glue and a Streamlit visualization layer.

No institutional rule, threshold, mandate, routing rule, coordination rule,
embedding model, or reasoning contract is changed.

## (4) PASS/FAIL criteria
All checks must pass:
- exactly three S1 events processed in order
- Gate 2 DT trajectory preserved
- Gate 3 routing preserved
- Gate 4 assessment codes preserved
- Gate 5 coordination preserved
- Gate 7B grounded reasoning preserved
- complete event-level audit trace
- end-to-end replay exact

One regression means Gate 8 FAIL.

## (5) Outputs
outputs/gate8/
- gate8_full_audit.json
- gate8_checks.csv
- gate8_status.json

## Demo
The package includes:
demo/app.py

Install:
pip install streamlit

Run from project root:
streamlit run demo/app.py

The UI exposes:
- Medical Metaverse state
- progressive event release
- institutional agent cards
- coordination state
- joint actions
- policy-grounded explanation
- audit/provenance trace

## (6) Next action

### PASS
Freeze the integrated deterministic demonstrator.
Then proceed to:
- Gate 9: evaluation harness and baselines
- optional Gate 7C/live LLM adapter as a non-critical enhancement

### FAIL
Identify which frozen gate regressed and repair only the integration boundary.
Do not retune the underlying model.
