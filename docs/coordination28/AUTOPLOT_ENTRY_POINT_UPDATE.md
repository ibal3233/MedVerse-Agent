# Gate 28: automatic plots in the original entry point

Presentation revision 1.1.0. The existing entry point is now
`medverse/gates/gate28_coordination_mechanism.py` for both evaluation and plotting.
A second launcher or a separate plotting command is not needed.

## Install into your existing project

Close any running Gate 28 evaluation. Extract the update archive and merge its
`MedVerse-Agent` folder into your existing `MedVerse-Agent` folder. Allow replacement
of the original runner and `data/coordination28/freeze_manifest.json`.

**Copy the complete update, not just the Python file.** The original runner was
hash-checked. The supplied manifest documents a presentation-only amendment and
preserves every other inherited scientific hash. The original manifest and runner
bytes are archived under `data/coordination28/presentation_history/v1_0_0/`.
Do not regenerate the freeze manifest to make unrelated code modifications pass.

The earlier separate plotting-fix ZIP is not required. Existing separate plot/run
launchers may remain on disk, but they are no longer needed for normal execution.
No existing result directory is included in the small update or overwritten by it.

## Your original Spyder command stays unchanged

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate28/MedVerse-Agent/medverse/gates/gate28_coordination_mechanism.py --wdir
```

Default behavior:

1. Validate the versioned freeze manifest.
2. Check that Matplotlib is available in the running Python environment.
3. Execute the unchanged Gate 28 evaluator.
4. Save raw JSON/CSV evidence in the evaluator's new timestamped run directory.
5. Read that exact run, not an older or globally selected run.
6. Export two charts as 300-dpi PNGs and vector PDFs.
7. Display both charts using the currently configured Matplotlib backend.

Figures are written to:

```text
outputs/gate28_coordination/<RUN_ID>/figures/display_<TIMESTAMP>/
  Gate28_Order_Robustness.png
  Gate28_Order_Robustness.pdf
  Gate28_Validation_Effort.png
  Gate28_Validation_Effort.pdf
  plotting_manifest.json
```

The main completion figure uses **equal-weight macro-family completion**, not pooled
completion. The operation-count figure does not claim an end-to-end latency benefit.
Both retain the tie with the fair stateful comparator.

`presentation_status.json` records export success or failure separately from the
scientific `status.json`. Plotting errors do not rewrite scientific results. Missing
Matplotlib is reported before a new full evaluation starts. A non-interactive backend
can save files but cannot display a window; the runner reports that explicitly.

## Optional modes on this same file

```bash
# Save both PNG and PDF, but do not display:
python -B medverse/gates/gate28_coordination_mechanism.py --no-show

# Reuse your existing result without rerunning the experiment:
python -B medverse/gates/gate28_coordination_mechanism.py --plot-only --run 20261103T051949_321858Z

# Plot the newest full saved run:
python -B medverse/gates/gate28_coordination_mechanism.py --plot-only

# Explicit experiment-only mode (Matplotlib not required):
python -B medverse/gates/gate28_coordination_mechanism.py --no-plots

# Audit-only mode: no comparative results are available to plot:
python -B medverse/gates/gate28_coordination_mechanism.py --stage audit
```

Matplotlib must be installed in the same environment used by Spyder. No backend is
forced and no global plot styling is changed. If a headless backend was deliberately
selected, configure an interactive or inline backend in Spyder before requesting
visible plots. This update does not change scikit-learn or load saved classifiers.

## What changed and what did not

Updated: the original entry-point file and its active manifest hash.
Added: a presentation helper, archived parent manifest/runner, unit tests, verification
records, and a runner convention for subsequent experiments.
Unchanged: the scientific evaluator, schedulers, oracle, dataset, schedule bank,
protocol, scoring functions, thresholds, previous gates, and historical result files.

This is a retrospective presentation amendment, not a new scientific pre-registration.
The original scientific freeze timestamp remains recorded. Its lineage is explicit in
`presentation_amendment` in the active manifest.

## Verification actually performed

- 21/21 direct-runner and manifest-lineage unit tests passed.
- All 19 active file hashes passed; 15 non-runner inherited hashes were unchanged.
- A complete default run executed all 1,590 workflow evaluations.
- All 16/16 frozen experiment checks passed.
- Every per-schedule value except elapsed time matched the archived run.
- Both figures exported as PNG/PDF and displayed through the inline backend.
- Native Windows/Spyder execution was not available for independent testing.

See `AUTO_PLOT_VERIFICATION.json` and `autoplot_runner_tests.txt` in this directory.
