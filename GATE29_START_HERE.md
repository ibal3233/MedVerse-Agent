# Team MedVerse — Gate 29 workflow-choice experiment

## Scope

The current release is an additive deterministic research study. It does not replace
the live sandbox, Gates 26–28, saved models, policies, or prior outputs. All actual
permissions and records used in the new scenarios are modeled; clinical and Korean
legal interpretation review remains pending.

## One command: evaluate, save, plot, and display

In Spyder, after extracting the cumulative ZIP:

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate29/MedVerse-Agent/medverse/gates/gate29_institutional_workflow_choice.py --wdir
```

Adjust only the extraction path. No second plotting launcher is required.

Terminal alternative, from `MedVerse-Agent`:

```bash
python -B medverse/gates/gate29_institutional_workflow_choice.py
```

Python 3.10 or later; Matplotlib for figures. Evaluation itself uses the standard
library. No classifier or embedding download is required. PDF reports are created
using Matplotlib; a separate PDF-authoring dependency is unnecessary.

```bash
# Headless run: save PNG/PDF without opening windows
python -B medverse/gates/gate29_institutional_workflow_choice.py --no-show
# Deliberately run without plotting dependencies
python -B medverse/gates/gate29_institutional_workflow_choice.py --no-plots
# Replot an existing run; raw measurements are not changed
python -B medverse/gates/gate29_institutional_workflow_choice.py --plot-only --run RUN_ID
```

Outputs are run-specific under `outputs/gate29_workflow_choice/<RUN_ID>/`:
`status.json`, `case_metrics.csv`, `reference_outcomes.json`, `raw_traces.json`,
`paired_comparisons.csv`, `temporal_revalidation.csv`, `workspace_adapter_tests.csv`,
checks, split audit, environment, and `figures/display_<TIMESTAMP>/`.

The original projection's D-prefix is NOT a split label. The pre-execution grouping
moved D02 and D03 into confirmation. Always use the explicit `split` field.

## Terminology

Use **reference outcomes**, **reference decision specification**, and **independent
reference evaluator**. The latter is separately implemented, not independently
reviewed by an external clinical or legal expert. The runtime policy validator is
separate: expected outcomes never authorize action. Frozen historical filenames and
terminology remain untouched for reproducibility.

## Scientific interpretation

The original-request-only configuration is a limited control. The fair stateful
selector and independent constraint planner are capable comparisons and must not be
weakened. Ties are valid results. Fourteen developer-authored confirmation families
are not independent clinical patients. Temporal and adapter perturbations are not
additional semantic families. No metric changes or refreezing after confirmation.

Review `docs/coordination29/PROTOCOL.md` for all thirteen experimental elements.
The archived source snapshot preserves candidate evidence, not newly verified legal
applicability. The next dependency is qualified review and a separately evaluated UI
integration. This release does not automatically install a new live coordinator.
