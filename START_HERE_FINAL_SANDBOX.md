# Team MedVerse — Final validation sandbox v1.0

## Start the judge interface

Requires Python 3.10 or later. The new **local runtime uses only the standard library**.
From this project directory:

```bash
python -B run_final_sandbox.py --open
```

Open `http://127.0.0.1:8765` in your browser. Keep the terminal open. Stop with Ctrl+C.
A second port can be selected with `--port 8766`. The service deliberately binds to localhost.

Spyder:

```python
%runfile D:/experiments/hackathon/MedVerse-Agent/run_final_sandbox.py --wdir
```

The Windows path is illustrative; use the extracted location. Linux/Python 3.13.5 was tested;
Windows/Spyder execution was not performed in this environment.

## Seven-minute demonstration sequence

1. Keep `WF05 · Progressive oncology flagship` and `MedVerse-Agent` selected.
2. Release events one at a time. The first reports a clinical concern; the second marks
   telemetry UNVERIFIED; the third introduces the research request.
3. Inspect Hospital, Cyber and Research views. Clinical observations are not visible to
   Cyber/Research peers. The inspector is an operator view, not peer-to-peer data sharing.
4. Observe withheld research disclosure. Events four/five supply **modeled** institutional
   reviews. The minimum-necessary research view is released only after both attestations.
5. Open Decisions & receipts. Inspect the actual proposal ID, rule verdict, source IDs,
   source-record hashes and modeled side effect. Export the trace.
6. Open Korean policy evidence and search in Korean/English. Search an unknown exact ID
   to demonstrate refusal to substitute another article. The live backend is explicitly
   **lexical BM25**, not the unavailable original embedding model.
7. Open Experimental evidence and Readiness. Explain the stateful-control tie and remaining
   clinical/legal review obligations. Do not describe this as production-safe or clinically deployed.

## What changed

The extension adds progressive event intake, role-scoped views, actual institution-owned
proposals, exact source/date checks, scoped mock human-review tickets, final revalidation,
request revocation, idempotent/locked commits, explicit evidence abstention, and chained receipts.
No real hospital, regulator, device, patient or cloud service is connected.
The new institutional proposer is a deterministic scenario reference model. The saved Privacy
and Cyber classifiers were replayed separately; they are **not the live proposer in this UI**.
No fine-tuning, LLM reasoning, trained-model improvement, legal certification or physiological
Digital Twin validity is implied.

All original archive files are retained. Existing source code, thresholds, models, data,
Gate 1–26 outputs and benchmarks were not rewritten. Python refreshed three old bytecode
caches during inference replay; archived bytes were restored. Use `python -B` to avoid this.

## Reproduce final validation

```bash
python -B medverse/gates/gate27_final_validation.py --stage confirm
python -B -m final_validation.latency_benchmark
```

`--stage confirm` checks the frozen core manifest before executing. It writes new outputs
under `outputs/final_validation/confirm`. Archive those outputs before another run when preserving
an exact timing record. Timing varies with machine load; logical results must not be tuned.
Do **not** run `--stage freeze` over the supplied manifest. Create a new version for substantive
changes, preserve failures, diagnose them, and use a fresh confirmation protocol.

The modeled runtime and core checks need no third-party packages. Frozen-model inference replay
additionally needs numpy/scipy/scikit-learn/joblib; missing packages are reported as BLOCKED, not PASS.
The saved model environment uses scikit-learn 1.8.0. No retraining is performed.

Optional original multilingual embedding evaluation, on a machine with the original dependency/model:

```bash
python -B -m final_validation.dense_evaluation --local-only
```

The helper does not silently switch to lexical search. This optional branch could not run here
because the dependency is missing and package installation could not reach the network.

Plots and PDF regeneration (additional analysis dependencies required):

```bash
python -B -m final_validation.make_figures
python -B -m final_validation.make_report
```

## Evidence locations

- `data/final_validation/freeze_manifest.json`: frozen code/data identities before confirmation.
- `data/final_validation/workflow_families.json`: 12 input-only scenario sequence families.
- `data/final_validation/workflow_oracle.json`: separate developer-authored obligations.
- `data/final_validation/query_families.json`: 40 bilingual intent families, grouped splits.
- `outputs/final_validation/confirm/`: raw retrieval, workflow, boundary and 512-state outputs.
- `outputs/final_validation/legacy_reproduction/`: Gate 26 replay and saved model inference.
- `outputs/final_validation/interface/`: actual rendered UI PNGs and exported receipt trace.
- `outputs/final_validation/figures/`: four result charts in PNG and vector PDF.
- `outputs/final_validation/MedVerse_Validation_and_Interface_Report.pdf`: consolidated report.
- `docs/final_validation/`: protocols, caveats, source checks and artifact preservation record.

## Readiness decision

Engineering checks pass for the specified finite modeled tests. General deployment readiness
remains **HOLD**. Independent Korean legal interpretation, institutional SOP applicability,
clinical review, the original dense-backend replay and externally authenticated deployment
are not established. Local HMAC review tickets represent a trusted simulator operator, not
verified clinical identities. The hash chain has no independent external anchor.

The new confirmation families recombine known legal/operational primitives; they are not an
unseen-law benchmark. Developer-authored oracles are not independent clinical adjudication.
The stateful scheduling control intentionally shares the ordered execution kernel with MedVerse;
its equal task completion is an equivalence check, not evidence of general comparative superiority.
