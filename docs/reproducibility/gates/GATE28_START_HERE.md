# Team MedVerse — Gate 28 coordination mechanism study

This additive package investigates why the existing MEDVERSE and STATEFUL_FILTER controls tie, then tests only the scheduling mechanism. It does not retrain models, revise Korean policy interpretations, overwrite historical results, or update the live v1 web interface.

## Start here

Use the cumulative ZIP for a complete project. Alternatively, merge the **contents** of the add-on ZIP's `MedVerse-Agent` directory into your existing `MedVerse-Agent` directory. Do not create `MedVerse-Agent/MedVerse-Agent`.

From the project root:

```bash
python -B medverse/gates/gate28_coordination_mechanism.py
```

Spyder (adjust only the installation path):

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate28/MedVerse-Agent/medverse/gates/gate28_coordination_mechanism.py --wdir
```

Audit-only command:

```bash
python -B medverse/gates/gate28_coordination_mechanism.py --stage audit
```

The gate uses Python 3.10+ and the standard library. It does not load pickle files or require scikit-learn, a sentence-transformer, network access or an API key. Linux/Python 3.13.5 execution and isolated `-I -S` audit were tested here. Windows/Spyder were not independently exercised in this run.

The supplied code/data manifest is frozen. Do not rerun `--stage freeze` over it or edit source data to improve a result. Every evaluation creates a new timestamped output folder. A hash mismatch correctly stops execution; it must not be bypassed.

## What actually ran

- Native comparison: 12/12 workflow families had identical normalized MEDVERSE and STATEFUL_FILTER behavior. Only LOCAL_FILTER and DENY_ALL are distinguished in the original cycle strategy branches.
- 16/16 deterministic instrumentation and boundary checks passed.
- Scheduling study: eight **previously seen** WF05–WF12 families, 318 distinct family-schedule pairs, five configurations, 1,590 executions.
- Macro-family completion: snapshot once 75%; sequential once 87.5%; fair stateful retry 100%; dependency ordering 100%; dependency edges removed 87.5%.
- Every method preserved the tested execution invariants. This is not a clinical safety guarantee.
- Dependency ordering and fair retry produced identical paired effect sets in 318/318 comparisons.
- Dependency ordering used 12,060 validator calls versus 12,186 for fair retry: **1.03% fewer**, not a demonstrated latency speedup.
- All 903 original files are preserved byte-for-byte.

The graph scheduler is an experimental add-on, not a new hidden default in the web interface. Its strict completion-superiority hypothesis over fair retry is **NOT SUPPORTED**. The native controls were not made artificially weaker after seeing their tie.

## Files

- `docs/coordination28/PROTOCOL.md`: frozen 13-item protocol.
- `data/coordination28/freeze_manifest.json`: code/data hashes.
- `data/coordination28/schedule_bank.json`: input-only schedules, deduplicated before outcomes.
- `outputs/gate28_coordination/LATEST_FULL.json`: identifies the measured full run.
- Each timestamped run: summary JSON, environment, instrumentation checks, per-family/per-schedule CSVs, paired comparisons, compressed per-proposal attempt ledger, native and representative traces.
- `outputs/gate28_coordination/Team_MedVerse_Gate28_Coordination_Report.pdf`: six-page report.
- `outputs/gate28_coordination/figures/`: two measured-result charts as PNG/PDF.
- `outputs/gate28_coordination/report_pages/`: report pages as PNG.
- `docs/coordination28/original_artifact_preservation.json`: original file hashes.
- `docs/coordination28/NEXT_WORKFLOW_SELECTION_PROTOCOL_DRAFT.md`: next scientific dependency, **not implemented or executed**.

Optional plotting (requires matplotlib/numpy) and report generation (requires reportlab/Pillow and the fonts named in the script):

```bash
python -B -m coordination28.figures
python -B -m coordination28.report
```

## Your model-version warning

Your supplied console loaded estimators saved with scikit-learn 1.8.0 under 1.9.0. Cross-version loading is unsupported according to the official scikit-learn documentation. Do not suppress the warning, overwrite the artifacts, or retrain frozen models merely to eliminate it. Use an isolated environment matching 1.8.0 and the original recorded dependencies for model replay. Gate 28 does not need that repair because it does not load those classifiers.

## Next scientific question

Scheduling a single predefined release path is not the same as selecting a feasible workflow among institution-owned alternatives. The next experiment should define those alternatives and an independent feasibility oracle, then compare against a capable stateful selector and a separate constraint planner with equal inputs and budgets. The provided draft specifies the required evidence and fairness conditions. No general coordination or multi-agent superiority claim follows from increasing the number of schedule variants.
