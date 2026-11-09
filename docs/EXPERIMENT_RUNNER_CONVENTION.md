# Default convention for the remaining MedVerse experiment runners

The **main gate script itself** is the ordinary entry point. A normal execution must:

`validate inputs -> execute -> save raw evidence -> calculate/report metrics -> save PNG/PDF -> display`

No second launcher or manual plotting import should be required.

## Rules

- Use the exact run directory returned by the evaluator, never a stale global latest
  pointer when plotting a newly executed experiment.
- Save raw JSON/CSV before presentation. Preserve new timestamped runs rather than
  overwriting earlier evidence.
- Export each required figure as a 300-dpi PNG and vector PDF, then call the display
  mechanism. Respect the user's plotting backend; do not close figures before show.
- Record input/result hashes, metric definitions, denominators, and the source run ID.
- Plot actual measured values only. Do not change hypotheses, thresholds, labels,
  or baselines to make a chart look favorable.
- Keep scientific integrity and plotting status separate. A hypothesis can be
  unsupported even when engineering integrity passes. A plotting failure must not
  alter an experiment's result or trigger substitution of older data.
- Check plotting dependencies before starting a long default run. Keep `--no-show`
  and `--no-plots` as explicit opt-outs, not the default.
- Provide optional `--plot-only --run <ID>` on the same entry point for re-exporting
  saved evidence without retraining or re-executing the experiment.
- An audit-only stage must not fabricate comparative result figures.
- When a frozen entry point changes for presentation reasons, record a versioned
  amendment and preserve the original manifest and file. Never silently re-freeze
  the scientific design after observing results.

This convention is implemented for Gate 28 in presentation revision 1.1.0. It is a
requirement for subsequent gate runners; it does not retroactively modify all older
experimental scripts.
