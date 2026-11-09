"""Gate 28: run the frozen experiment, save PNG/PDF figures, then display them.

Default Spyder usage is unchanged: run this file normally. No second launcher
is required. The scientific evaluator, schedulers, data, and scoring are unchanged.

Optional arguments:
    --no-show              Save figures but do not open/display them.
    --no-plots             Run the experiment only (no matplotlib required).
    --plot-only            Plot an existing full run without rerunning Gate 28.
    --plot-only --run ID   Plot the specified saved run rather than the newest.
    --stage audit          Run the audit only; no comparison plots are expected.

The supplied manifest records this presentation-only amendment and preserves the
original manifest/entry-point bytes under data/coordination28/presentation_history.
Do not regenerate the scientific freeze to fix a hash mismatch.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RUNNER_PRESENTATION_VERSION = "1.1.0"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["all", "audit", "freeze"], default="all")
    parser.add_argument("--no-show", action="store_true", help="Save PNG/PDF without displaying.")
    parser.add_argument("--no-plots", action="store_true", help="Run evaluation only; no plotting dependency.")
    parser.add_argument("--plot-only", action="store_true", help="Plot saved evidence; do not rerun evaluation.")
    parser.add_argument("--run", help="Saved run ID, folder, or status.json; requires --plot-only.")
    parser.add_argument("--dpi", type=int, default=300, help="PNG resolution (default: 300 dpi).")
    return parser


def main(argv: Sequence[str] | None = None):
    """Return (scientific status, exact run directory, figure directory or None)."""
    parser = _parser()
    args = parser.parse_args(argv)
    if args.dpi <= 0:
        parser.error("--dpi must be positive")
    if args.run is not None and not args.plot_only:
        parser.error("--run requires --plot-only; new experiments always create a new run directory")
    if args.plot_only and (args.stage != "all" or args.no_plots):
        parser.error("--plot-only cannot be combined with --no-plots or --stage audit/freeze")
    if args.stage == "freeze":
        parser.error(
            "Gate 28 is already frozen. Use the supplied versioned manifest amendment; "
            "do not re-freeze the scientific experiment after viewing results."
        )

    from coordination28.evaluate import execute, verify_freeze
    verify_freeze()  # Includes the amended runner/helper and unchanged scientific files.
    print(f"Gate 28 | presentation v{RUNNER_PRESENTATION_VERSION} | same experiment, automatic figures")

    plotting = args.stage == "all" and not args.no_plots
    if plotting:
        # Fail before a new experiment if matplotlib is missing. Backend is never forced.
        from coordination28.interactive_figures import make_figures, require_matplotlib
        require_matplotlib()

    if args.plot_only:
        figure_dir = make_figures(ROOT, run=args.run, show=not args.no_show, dpi=args.dpi)
        run_dir = figure_dir.parent.parent
        status = json.loads((run_dir / "status.json").read_text(encoding="utf-8-sig"))
        return status, run_dir, figure_dir

    status, run_dir = execute(args.stage)
    if not plotting:
        reason = "Audit-only: no comparative results to plot." if args.stage == "audit" else "Figures disabled explicitly by --no-plots."
        print(reason)
        return status, run_dir, None

    # Pass the exact directory returned by this execution, never 'latest'.
    presentation = {
        "runner_presentation_version": RUNNER_PRESENTATION_VERSION,
        "source_run_id": status["run_id"],
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scientific_status_unchanged": True,
        "display_requested": not args.no_show,
        "status": "PENDING",
    }
    try:
        figure_dir = make_figures(ROOT, run=run_dir, show=not args.no_show, dpi=args.dpi)
    except Exception as exc:
        presentation.update(status="PLOTTING_FAILED", error=f"{type(exc).__name__}: {exc}")
        (run_dir / "presentation_status.json").write_text(
            json.dumps(presentation, indent=2), encoding="utf-8")
        print(
            f"\nScientific results remain saved at {run_dir}.\n"
            "Plotting failed separately; the experiment status was not altered.\n"
            f"After fixing plotting, rerun this same file with --plot-only --run {run_dir.name}.",
            file=sys.stderr,
        )
        raise
    presentation.update(status="FIGURES_EXPORTED", figures_relative_path=str(figure_dir.relative_to(run_dir)))
    (run_dir / "presentation_status.json").write_text(
        json.dumps(presentation, indent=2), encoding="utf-8")
    print("\nGate 28 complete: raw results, PNG/PDF figures, and plotting provenance saved together.")
    return status, run_dir, figure_dir


if __name__ == "__main__":
    main()
