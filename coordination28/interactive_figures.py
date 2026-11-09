"""Additive Gate 28 plotting: read saved evidence, export PNG/PDF, then display.

No frozen experiment module, input, result, or manifest is modified. Matplotlib
is optional for the experiment itself, but required by this presentation helper.
The selected Matplotlib backend is respected (including Spyder's inline backend).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

PATCH_VERSION = "1.1.0"
GATE = "GATE_28_COORDINATION_MECHANISM"
STRATEGY_ORDER = (
    "SNAPSHOT_ONCE", "SEQUENTIAL_ONCE", "STATEFUL_FIXED_POINT",
    "DEPENDENCY_ORDERED", "DEPENDENCY_EDGES_REMOVED",
)
LABELS = {
    "SNAPSHOT_ONCE": "Snapshot\nonce",
    "SEQUENTIAL_ONCE": "Sequential\nonce",
    "STATEFUL_FIXED_POINT": "Fair stateful\nretry",
    "DEPENDENCY_ORDERED": "Dependency\nordered",
    "DEPENDENCY_EDGES_REMOVED": "Dependency\nedges removed",
}
NONINTERACTIVE_BACKENDS = {"agg", "pdf", "pgf", "ps", "svg", "template", "cairo"}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read saved evidence {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_matplotlib():
    """Import lazily without forcing a backend or modifying rc settings."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "Plotting requires matplotlib in the same environment as Spyder. "
            "Install it there with `python -m pip install matplotlib`. "
            "The existing experiment results do not need to be rerun."
        ) from exc
    return matplotlib, plt


def select_run(root: Path, run: str | Path | None = None) -> Path:
    """Resolve an explicit run, or the newest full run (not a later audit-only run).

    The newest full run is validated by load_results; a failed full run is never
    silently replaced by an older successful run.
    """
    root = Path(root).expanduser().resolve()
    evidence = root / "outputs" / "gate28_coordination"
    if run is not None:
        requested = Path(run).expanduser()
        if requested.is_absolute():
            candidates = [requested]
        else:
            candidates = [evidence / requested, root / requested]
        for path in candidates:
            if path.is_file() and path.name == "status.json":
                return path.parent.resolve()
            if path.is_dir() and (path / "status.json").is_file():
                return path.resolve()
        raise FileNotFoundError(
            f"No Gate 28 status.json at {run!s}. Supply a run ID, run folder, "
            "or status.json path. No experiment was rerun."
        )
    if not evidence.is_dir():
        raise FileNotFoundError(f"No Gate 28 results directory: {evidence}")
    full_runs = []
    for path in sorted(evidence.glob("*/status.json")):
        status = _read_json(path)
        if status.get("gate") == GATE and status.get("stage") == "all":
            full_runs.append(path.parent)
    if not full_runs:
        raise FileNotFoundError(
            "No full Gate 28 run is available. An audit-only run has no "
            "strategy comparison to plot."
        )
    return max(full_runs, key=lambda path: path.name).resolve()


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}; received {value!r}.")
    return value


def _fraction(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} is not numeric: {value!r}.")
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} is not a finite fraction in [0, 1]: {value!r}.")
    return value


def load_results(run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    status = _read_json(Path(run_dir) / "status.json")
    if status.get("gate") != GATE:
        raise ValueError("The selected status file is not a Gate 28 result.")
    if status.get("stage") != "all":
        raise ValueError("The selected run is audit-only; it has no complete comparison.")
    if status.get("engineering_integrity") != "PASS":
        raise ValueError(
            "The selected full run did not pass engineering integrity. "
            "No older successful result will be substituted."
        )
    records = status.get("strategy_summary")
    if not isinstance(records, list) or len(records) != len(STRATEGY_ORDER):
        raise ValueError("Expected the five saved strategy summaries.")
    by_strategy = {}
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("Invalid strategy summary row.")
        key = row.get("strategy")
        if key in by_strategy:
            raise ValueError(f"Duplicate strategy: {key}")
        by_strategy[key] = row
    if set(by_strategy) != set(STRATEGY_ORDER):
        raise ValueError("The saved strategies do not match the frozen Gate 28 comparison.")
    families = _integer(status.get("unique_semantic_families"), "unique_semantic_families", 1)
    pairs = _integer(status.get("effective_family_schedule_pairs"), "effective_family_schedule_pairs", 1)
    ordered = [by_strategy[name] for name in STRATEGY_ORDER]
    for row in ordered:
        key = row["strategy"]
        _fraction(row.get("macro_family_completion_fraction"), key + ".macro_completion")
        _fraction(row.get("pooled_completion_fraction"), key + ".pooled_completion")
        _integer(row.get("total_validation_calls"), key + ".total_validation_calls")
        completed = _integer(row.get("completed_runs"), key + ".completed_runs")
        n = _integer(row.get("effective_family_schedule_runs"), key + ".runs", 1)
        if n != pairs or completed > n or row.get("semantic_families") != families:
            raise ValueError(f"Inconsistent denominators in {key}.")
        if not math.isclose(completed / n, row["pooled_completion_fraction"], abs_tol=1e-10):
            raise ValueError(f"Saved pooled completion disagrees with saved counts in {key}.")
    return status, ordered


def _decorate(ax, title: str, ylabel: str) -> None:
    ax.set_title(title, pad=14)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)


def _annotations(ax, bars, texts: Sequence[str]) -> None:
    for bar, text in zip(bars, texts):
        ax.annotate(text, (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 5), textcoords="offset points", ha="center", va="bottom")


def make_figures(root: str | Path | None = None, *, run: str | Path | None = None,
                 show: bool = True, dpi: int = 300) -> Path:
    """Render the two Gate 28 figures from saved values only.

    Each call writes a new presentation-only folder under the selected run.
    Both files are saved before plt.show(); figures are not closed before show.
    No model, benchmark, scheduler, or frozen evaluator is imported here.
    """
    root = Path(root).expanduser().resolve() if root is not None else Path(__file__).resolve().parents[1]
    run_dir = select_run(root, run)
    status, rows = load_results(run_dir)
    if not isinstance(dpi, int) or dpi <= 0:
        raise ValueError("dpi must be a positive integer.")
    source = run_dir / "status.json"
    source_hash = _sha256(source)
    matplotlib, plt = require_matplotlib()
    run_id = str(status.get("run_id", run_dir.name))
    families = status["unique_semantic_families"]
    pairs = status["effective_family_schedule_pairs"]
    figures = []
    try:
        fig, ax = plt.subplots(figsize=(10.0, 5.4))
        figures.append(("Gate28_Order_Robustness", fig))
        labels = [LABELS[row["strategy"]] for row in rows]
        values = [100 * row["macro_family_completion_fraction"] for row in rows]
        bars = ax.bar(labels, values, width=0.60)
        _annotations(ax, bars, [f"{value:.1f}%" for value in values])
        ax.set_ylim(0, 114)
        _decorate(ax, "Gate 28: proposal-order robustness",
                  "Completion averaged equally across workflow families (%)")
        fig.text(0.5, 0.060,
                 f"{families} previously seen modeled families; {pairs:,} distinct family-schedule pairs per configuration.\n"
                 "Macro-family completion is not pooled completion; order variants are not independent clinical cases.",
                 ha="center", fontsize=9)
        fig.text(0.5, 0.015, f"Source run: {run_id}", ha="center", fontsize=8)
        fig.tight_layout(rect=(0, 0.15, 1, 1))

        by_strategy = {row["strategy"]: row for row in rows}
        fixed = by_strategy["STATEFUL_FIXED_POINT"]
        graph = by_strategy["DEPENDENCY_ORDERED"]
        counts = [fixed["total_validation_calls"], graph["total_validation_calls"]]
        saved = counts[0] - counts[1]
        relative = (100 * saved / counts[0]) if counts[0] else None
        reduction = (f"Call reduction: {saved:,} ({relative:.2f}%)." if relative is not None
                     else f"Call difference: {saved:,}; percentage undefined for a zero baseline.")
        equal = (fixed["completed_runs"] == graph["completed_runs"] and
                 fixed["macro_family_completion_fraction"] == graph["macro_family_completion_fraction"])
        fig, ax = plt.subplots(figsize=(9.0, 5.3))
        figures.append(("Gate28_Validation_Effort", fig))
        bars = ax.bar(["Fair stateful retry", "Dependency ordering"], counts, width=0.50)
        _annotations(ax, bars, [f"{count:,}" for count in counts])
        ax.set_ylim(0, max(1, max(counts)) * 1.18)
        title = ("Equal completion; validator-call comparison" if equal else
                 "Validator-call comparison; completion differs")
        _decorate(ax, title, "Total validator calls (preflight + final revalidation)")
        completion = (f"Both complete {fixed['completed_runs']:,}/{pairs:,} schedules. " if equal else
                      f"Completed schedules: retry {fixed['completed_runs']:,}/{pairs:,}; "
                      f"ordered {graph['completed_runs']:,}/{pairs:,}. ")
        fig.text(0.5, 0.060, completion + reduction + "\n"
                 "Operation counts only; this figure does not establish an end-to-end latency advantage.",
                 ha="center", fontsize=9)
        fig.text(0.5, 0.015, f"Source run: {run_id}", ha="center", fontsize=8)
        fig.tight_layout(rect=(0, 0.15, 1, 1))

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        dest = run_dir / "figures" / ("display_" + stamp)
        dest.mkdir(parents=True, exist_ok=False)
        paths = []
        for name, fig in figures:
            for suffix in ("png", "pdf"):
                path = dest / f"{name}.{suffix}"
                fig.savefig(path, dpi=dpi, bbox_inches="tight")
                paths.append(path)
        if _sha256(source) != source_hash:
            raise RuntimeError("The input status.json changed during rendering; discard this export.")
        backend = str(matplotlib.get_backend())
        display_possible = backend.lower() not in NONINTERACTIVE_BACKENDS
        manifest = {
            "presentation_patch_version": PATCH_VERSION,
            "source_run_id": run_id,
            "source_status_sha256": source_hash,
            "source_status_path_relative_to_export": "../../status.json",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "matplotlib_version": matplotlib.__version__,
            "backend": backend, "display_requested": show,
            "display_attempted": bool(show and display_possible),
            "experiment_rerun_by_plotter": False,
            "raw_evidence_modified": False,
            "completion_metric": "macro_family_completion_fraction",
            "effort_metric": "total_validation_calls",
            "dpi": dpi,
            "exports": {path.name: _sha256(path) for path in paths},
        }
        (dest / "plotting_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nGate 28 plotting | source run: {run_id}")
        print(f"Saved two figures, each as PNG ({dpi} dpi) and PDF:\n{dest}")
        print(f"Backend: {backend}. Raw evidence and scientific evaluation files were not changed by plotting.")
        print("Completion plotted: equal-weight macro-family fraction, not the pooled fraction.")
        if show and display_possible:
            print("Displaying figures using the current Matplotlib backend.")
            plt.show()
        else:
            for _, fig in figures:
                plt.close(fig)
            if show:
                print("The current backend is non-interactive: files were saved, but no display is available.\n"
                      "In Spyder's IPython console enter `%matplotlib inline`, then run gate28_coordination_mechanism.py with --plot-only.\n"
                      "Use `%matplotlib qt` for separate windows when a Qt backend is available.")
        return dest
    except Exception:
        for _, fig in figures:
            plt.close(fig)
        raise


def plot_main(root: str | Path | None = None, argv: Sequence[str] | None = None) -> Path:
    parser = argparse.ArgumentParser(description="Display/export saved Gate 28 results; no experiment rerun.")
    parser.add_argument("--run", help="Run ID, run directory, or status.json; defaults to newest full run.")
    parser.add_argument("--no-show", action="store_true", help="Export PNG/PDF without displaying figures.")
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args(argv)
    return make_figures(root, run=args.run, show=not args.no_show, dpi=args.dpi)


if __name__ == "__main__":
    plot_main()
