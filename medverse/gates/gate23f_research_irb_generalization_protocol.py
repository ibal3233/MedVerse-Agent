from __future__ import annotations

from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from medverse.learning.gate23f_research_irb_factorial_protocol import (
    build_factorial_benchmark,
    INTERACTION_FEATURES,
)

OUT = ROOT / "outputs" / "gate23f"
FIG = OUT / "figures"
DATA_OUT = ROOT / "data" / "learning" / "gate23f"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
DATA_OUT.mkdir(parents=True, exist_ok=True)

BASE_CSV = ROOT / "data" / "learning" / "gate21a" / "research_irb_agent.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_base_train():
    with BASE_CSV.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["split"] == "train"]


def feature_support(rows, feature):
    return sum(feature in r["active_interactions"] for r in rows)


def base_train_feature_support(base_train_rows, feature):
    from medverse.learning.research_irb_precedence_features import enrich_from_json
    return sum(
        bool(enrich_from_json(r["features_json"]).get(feature, False))
        for r in base_train_rows
    )


def save_fold_size_plot(rows):
    counts = Counter(r["outer_fold"] for r in rows)
    labels = [f"Fold {i}" for i in range(4)]
    vals = [counts[i] for i in range(4)]

    fig, ax = plt.subplots(figsize=(7.2, 4.7))
    ax.bar(labels, vals)
    ax.set_ylabel("Held-out factorial states")
    ax.set_title("Gate 23F Prospective Outer-Fold Sizes")
    fig.tight_layout()
    fig.savefig(FIG / "fig23f_outer_fold_sizes.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23f_outer_fold_sizes.pdf", bbox_inches="tight")
    plt.close(fig)


def save_action_distribution_plot(rows):
    labels = sorted({r["action"] for r in rows})
    x = np.arange(len(labels))
    width = 0.18

    fig, ax = plt.subplots(figsize=(10, 5.3))
    for fold in range(4):
        subset = [r for r in rows if r["outer_fold"] == fold]
        c = Counter(r["action"] for r in subset)
        ax.bar(
            x + (fold - 1.5) * width,
            [c.get(k, 0) for k in labels],
            width,
            label=f"Fold {fold}",
        )

    ax.set_ylabel("Held-out records")
    ax.set_title("Action-Class Composition of Prospective Outer Folds")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23f_outer_fold_action_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23f_outer_fold_action_support.pdf", bbox_inches="tight")
    plt.close(fig)


def save_critical_support_plot(rows):
    feature = "ix_active_approved_but_pseudo_deficient"
    train_support = []
    test_support = []

    for fold in range(4):
        test = [r for r in rows if r["outer_fold"] == fold]
        train = [r for r in rows if r["outer_fold"] != fold]
        train_support.append(feature_support(train, feature))
        test_support.append(feature_support(test, feature))

    x = np.arange(4)
    w = 0.36

    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.bar(x-w/2, train_support, w, label="Prospective train-side support")
    ax.bar(x+w/2, test_support, w, label="Held-out fold support")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Fold {i}" for i in range(4)])
    ax.set_ylabel("Positive activations")
    ax.set_title("Critical Interaction Support by Outer Fold")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23f_critical_interaction_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23f_critical_interaction_support.pdf", bbox_inches="tight")
    plt.close(fig)


def save_interaction_coverage_plot(coverage):
    labels = list(coverage.keys())
    mins = [coverage[k]["minimum_train_side_support"] for k in labels]

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    ax.barh(labels, mins)
    ax.set_xlabel("Minimum train-side positive support across folds")
    ax.set_title("Prospective Interaction Learnability Coverage")
    fig.tight_layout()
    fig.savefig(FIG / "fig23f_interaction_min_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23f_interaction_min_support.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 23F")
    print(" Prospective Research / IRB")
    print(" Combinatorial Generalization Protocol")
    print("========================================\n")

    rows = build_factorial_benchmark()
    base_train = load_base_train()

    # Materialize the benchmark BEFORE any future repair training.
    benchmark_path = DATA_OUT / "research_irb_factorial_benchmark_v2.csv"
    fieldnames = [
        "record_id",
        "outer_fold",
        "research_consent",
        "irb_status",
        "pseudonymized",
        "audit_required",
        "target_assessment",
        "target_action",
        "target_boundary_status",
        "target_enforcement",
        "target_evidence_request",
        "active_interactions_json",
    ]

    with benchmark_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            feat = r["features"]
            w.writerow({
                "record_id": r["record_id"],
                "outer_fold": r["outer_fold"],
                "research_consent": (
                    "__MISSING__" if feat["research_consent"] is None
                    else feat["research_consent"]
                ),
                "irb_status": (
                    "__MISSING__" if feat["irb_status"] is None
                    else feat["irb_status"]
                ),
                "pseudonymized": feat["pseudonymized"],
                "audit_required": feat["audit_required"],
                "target_assessment": r["assessment"],
                "target_action": r["action"],
                "target_boundary_status": r["boundary"],
                "target_enforcement": r["enforcement"],
                "target_evidence_request": r["evidence"],
                "active_interactions_json": json.dumps(
                    r["active_interactions"], sort_keys=True
                ),
            })

    # Fold integrity
    fold_sizes = Counter(r["outer_fold"] for r in rows)
    record_ids = [r["record_id"] for r in rows]
    signatures = [r["signature"] for r in rows]

    # Every interaction present in a held-out fold must remain represented on
    # that fold's train side.
    coverage = {}
    coverage_violations = []

    for feature in INTERACTION_FEATURES:
        per_fold = {}
        base_train_n = base_train_feature_support(base_train, feature)

        for fold in range(4):
            test = [r for r in rows if r["outer_fold"] == fold]
            factorial_train = [r for r in rows if r["outer_fold"] != fold]

            test_n = feature_support(test, feature)
            factorial_train_n = feature_support(factorial_train, feature)
            total_train_n = factorial_train_n + base_train_n

            per_fold[str(fold)] = {
                "factorial_train_side": factorial_train_n,
                "base_gate21a_train": base_train_n,
                "total_train_side": total_train_n,
                "held_out": test_n,
            }

            if test_n > 0 and total_train_n == 0:
                coverage_violations.append({
                    "feature": feature,
                    "fold": fold,
                    "held_out_support": test_n,
                    "factorial_train_support": factorial_train_n,
                    "base_gate21a_train_support": base_train_n,
                    "total_train_support": total_train_n,
                })

        coverage[feature] = {
            "per_fold": per_fold,
            "minimum_train_side_support": min(
                v["total_train_side"] for v in per_fold.values()
            ),
            "total_support": sum(
                1 for r in rows if feature in r["active_interactions"]
            ),
        }

    # Future protocol is pre-registered now; no training in Gate 23F.
    protocol = {
        "protocol_id": "MEDVERSE-G23F-RESEARCH-IRB-COMBINATORIAL-v2",
        "status": "PRE_FROZEN_BEFORE_REPAIR_TRAINING",
        "benchmark_semantics": (
            "Full 3x4x2x2 factorial Research/IRB state space under the already "
            "frozen deterministic institutional oracle."
        ),
        "total_factorial_states": len(rows),
        "outer_folds": 4,
        "states_per_outer_fold": dict(sorted(fold_sizes.items())),
        "future_training_protocol": (
            "For outer fold k, fit only on states whose outer_fold != k plus "
            "the frozen original Gate-21A TRAIN partition. Hyperparameters are "
            "selected using the frozen Gate-21A DEV partition only. Evaluate "
            "once on outer fold k."
        ),
        "aggregate_evaluation": (
            "Pool predictions from all four held-out folds after each record has "
            "served as test exactly once. Report pooled accuracy, macro-F1, "
            "per-class metrics, confusion matrix and policy-inconsistent execution."
        ),
        "hyperparameter_policy": {
            "selection_data": "Gate-21A DEV only",
            "outer_test_used_for_selection": False,
            "candidate_grid": [0.03, 0.1, 0.3, 1.0, 3.0, 10.0],
        },
        "overfitting_controls": [
            "protocol frozen before Gate-23G repair training",
            "each factorial signature belongs to exactly one outer test fold",
            "outer test fold excluded from fitting and hyperparameter selection",
            "current Gate-23 OOD-v1 remains diagnostic-only",
            "raw fold predictions retained",
            "same frozen oracle and feature semantics used across folds",
        ],
        "interaction_learnability_rule": (
            "Any engineered interaction activated in an outer test fold must "
            "have nonzero positive support on that fold's training side."
        ),
        "current_ood_v1_status": "DIAGNOSTIC_ONLY",
        "claim_boundary": (
            "This is a prospective combinatorial generalization benchmark over a "
            "synthetic policy state space. It is not an external clinical dataset "
            "and must not be described as externally unseen real-world data."
        ),
        "future_pass_thresholds": {
            "pooled_action_accuracy": 0.90,
            "pooled_action_macro_f1": 0.80,
            "pooled_assessment_accuracy": 0.90,
            "id_action_accuracy_each_fold_model": 0.90,
            "policy_inconsistent_execution_rate": 0.0,
        },
    }

    benchmark_hash = sha256(benchmark_path)
    protocol["benchmark_sha256"] = benchmark_hash

    protocol_path = OUT / "gate23f_frozen_generalization_protocol.json"
    protocol_path.write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    coverage_path = OUT / "gate23f_interaction_coverage.json"
    coverage_path.write_text(
        json.dumps({
            "coverage": coverage,
            "violations": coverage_violations,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    manifest = {
        "protocol_id": protocol["protocol_id"],
        "benchmark_file": str(
            benchmark_path.relative_to(ROOT)
        ).replace("\\", "/"),
        "benchmark_sha256": benchmark_hash,
        "protocol_file": str(
            protocol_path.relative_to(ROOT)
        ).replace("\\", "/"),
        "created_before_repair_training": True,
        "training_performed_in_gate23f": False,
        "benchmark_rows": len(rows),
        "unique_record_ids": len(set(record_ids)),
        "unique_signatures": len(set(signatures)),
    }
    (OUT / "gate23f_freeze_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    save_fold_size_plot(rows)
    save_action_distribution_plot(rows)
    save_critical_support_plot(rows)
    save_interaction_coverage_plot(coverage)

    checks = [
        {
            "check": "complete_factorial_state_space",
            "pass": len(rows) == 48 and len(set(signatures)) == 48,
            "observed": {
                "rows": len(rows),
                "unique_signatures": len(set(signatures)),
            },
            "expected": 48,
        },
        {
            "check": "outer_fold_partition",
            "pass": all(fold_sizes[i] == 12 for i in range(4)),
            "observed": dict(sorted(fold_sizes.items())),
            "expected": {0: 12, 1: 12, 2: 12, 3: 12},
        },
        {
            "check": "unique_record_ids",
            "pass": len(record_ids) == len(set(record_ids)),
            "observed": len(set(record_ids)),
            "expected": 48,
        },
        {
            "check": "interaction_learnability",
            "pass": len(coverage_violations) == 0,
            "observed": coverage_violations,
            "expected": [],
        },
        {
            "check": "critical_interaction_supported_each_relevant_fold",
            "pass": all(
                (
                    coverage["ix_active_approved_but_pseudo_deficient"]
                    ["per_fold"][str(i)]["held_out"] == 0
                )
                or (
                    coverage["ix_active_approved_but_pseudo_deficient"]
                    ["per_fold"][str(i)]["total_train_side"] > 0
                )
                for i in range(4)
            ),
            "observed": (
                coverage["ix_active_approved_but_pseudo_deficient"]["per_fold"]
            ),
            "expected": "nonzero train-side support whenever held-out support > 0",
        },
        {
            "check": "protocol_frozen_without_training",
            "pass": protocol["status"] == "PRE_FROZEN_BEFORE_REPAIR_TRAINING",
            "observed": {
                "status": protocol["status"],
                "training_performed": False,
            },
            "expected": "pre-frozen, no training",
        },
        {
            "check": "benchmark_hash_recorded",
            "pass": (
                len(benchmark_hash) == 64
                and manifest["benchmark_sha256"] == benchmark_hash
            ),
            "observed": benchmark_hash,
            "expected": "SHA256 recorded",
        },
        {
            "check": "publication_outputs_created",
            "pass": (
                len(list(FIG.glob("*.png"))) >= 4
                and len(list(FIG.glob("*.pdf"))) >= 4
            ),
            "observed": {
                "png": len(list(FIG.glob("*.png"))),
                "pdf": len(list(FIG.glob("*.pdf"))),
            },
            "expected": ">=4 PNG and >=4 PDF",
        },
    ]

    passed = sum(c["pass"] for c in checks)
    status = {
        "gate": "GATE_23F_RESEARCH_IRB_GENERALIZATION_PROTOCOL",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "training_performed": False,
        "protocol_id": protocol["protocol_id"],
        "factorial_states": len(rows),
        "outer_folds": 4,
        "states_per_fold": dict(sorted(fold_sizes.items())),
        "interaction_coverage_violations": len(coverage_violations),
        "benchmark_sha256": benchmark_hash,
        "current_ood_v1_status": "DIAGNOSTIC_ONLY",
        "new_protocol_status": "PRE_FROZEN_BEFORE_REPAIR_TRAINING",
        "figures_directory": "outputs/gate23f/figures",
        "next_dependency": (
            "Gate 23G: retrain/evaluate Research/IRB under the frozen four-fold "
            "combinatorial protocol, with model family and shield v2 unchanged."
        ),
    }

    (OUT / "gate23f_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate23f_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print("\nCritical interaction coverage:")
    print(json.dumps(
        coverage["ix_active_approved_but_pseudo_deficient"]["per_fold"],
        indent=2
    ))
    print(f"\nBenchmark saved to:\n{benchmark_path}")
    print(f"SHA256:\n{benchmark_hash}")
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit(
            "Gate 23F FAILED. Do not train the repair until the prospective "
            "generalization protocol is valid."
        )

    print(
        "\nFULL GATE 23F PASS — A four-fold prospective combinatorial "
        "generalization benchmark has been frozen before repair training, with "
        "complete interaction learnability coverage and a recorded SHA256."
    )


if __name__ == "__main__":
    main()
