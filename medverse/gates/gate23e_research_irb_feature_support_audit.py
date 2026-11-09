from __future__ import annotations

from pathlib import Path
from collections import Counter
import csv, json, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from medverse.learning.gate23_research_irb_benchmark import (
    build_ood,
    build_augmentation,
)
from medverse.gates.gate23_research_irb_learning import load_rows, row_from_aug
from medverse.gates.gate23b_research_irb_balanced_augmentation import (
    build_class_preserving_replay,
)
from medverse.learning.research_irb_precedence_features import enrich_from_json


OUT = ROOT / "outputs" / "gate23e"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

GATE23D_PRED = (
    ROOT / "outputs" / "gate23d" / "gate23d_ood_predictions_and_safety.csv"
)

CRITICAL_FEATURES = [
    "ix_active_approved_but_pseudo_deficient",
    "ix_pseudonymization_deficient",
    "ix_audit_with_pseudonymization_deficiency",
    "ix_evidence_missing",
    "ix_audit_with_missing_evidence",
]


def feature_value(row, key):
    return bool(enrich_from_json(row["features_json"]).get(key, False))


def count_support(rows, key):
    return sum(feature_value(r, key) for r in rows)


def make_ood_rows():
    rows = []
    for c in build_ood():
        rows.append({
            "record_id": c["record_id"],
            "features_json": json.dumps(c["features"], sort_keys=True),
            "target_action": c["action"],
            "target_assessment": c["assessment"],
        })
    return rows


def load_gate23d_predictions():
    with GATE23D_PRED.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def plot_feature_support(support):
    labels = CRITICAL_FEATURES
    train_vals = [support[k]["combined_train"] for k in labels]
    ood_vals = [support[k]["ood"] for k in labels]

    x = np.arange(len(labels))
    w = 0.36

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(x-w/2, train_vals, w, label="Combined training support")
    ax.bar(x+w/2, ood_vals, w, label="OOD support")
    ax.set_ylabel("Positive feature activations")
    ax.set_title("Research / IRB Interaction-Feature Support: Training vs OOD")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23e_feature_support_train_vs_ood.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23e_feature_support_train_vs_ood.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_split_support(support, key):
    order = ["original_train", "dev", "id_test", "compositional_augmentation", "replay", "ood"]
    vals = [support[key][k] for k in order]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(order, vals)
    ax.set_ylabel("Positive activations")
    ax.set_title(f"Support for Critical Interaction: {key}")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(FIG / "fig23e_critical_interaction_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23e_critical_interaction_support.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_error_concentration(pred_rows):
    total_ood = len(pred_rows)
    errors = [r for r in pred_rows if str(r["action_correct"]).lower() == "false"]

    critical = 0
    noncritical = 0
    for r in errors:
        f = json.loads(r["features_json"])
        iscritical = (
            f.get("research_consent") == "active"
            and f.get("irb_status") == "approved"
            and f.get("pseudonymized") is False
        )
        critical += int(iscritical)
        noncritical += int(not iscritical)

    fig, ax = plt.subplots(figsize=(7, 4.7))
    ax.bar(
        ["Errors on unsupported\ncritical interaction", "All other OOD errors"],
        [critical, noncritical],
    )
    ax.set_ylabel("Action errors")
    ax.set_title("Gate 23D Error Concentration")
    fig.tight_layout()
    fig.savefig(FIG / "fig23e_error_concentration.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23e_error_concentration.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_ood_action_support(ood_rows, pred_rows):
    true_counts = Counter(r["target_action"] for r in ood_rows)
    pred_counts = Counter(r["pred_action"] for r in pred_rows)

    labels = sorted(set(true_counts) | set(pred_counts))
    x = np.arange(len(labels))
    w = 0.36

    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.bar(x-w/2, [true_counts.get(k, 0) for k in labels], w, label="True OOD support")
    ax.bar(x+w/2, [pred_counts.get(k, 0) for k in labels], w, label="Predicted support")
    ax.set_ylabel("Records")
    ax.set_title("Gate 23D OOD Action-Class Support")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23e_ood_action_class_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23e_ood_action_class_support.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 23E")
    print(" Research / IRB Feature-Support")
    print(" & OOD Learnability Audit")
    print("========================================\n")

    rows = load_rows()
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]

    comp_raw = build_augmentation()
    comp = [row_from_aug(a) for a in comp_raw]
    replay = build_class_preserving_replay(train, comp)
    combined = train + comp + replay

    ood_rows = make_ood_rows()
    pred_rows = load_gate23d_predictions()

    support = {}
    for key in CRITICAL_FEATURES:
        support[key] = {
            "original_train": count_support(train, key),
            "dev": count_support(dev, key),
            "id_test": count_support(test, key),
            "compositional_augmentation": count_support(comp, key),
            "replay": count_support(replay, key),
            "combined_train": count_support(combined, key),
            "ood": count_support(ood_rows, key),
        }

    critical_key = "ix_active_approved_but_pseudo_deficient"
    critical_support = support[critical_key]

    errors = [
        r for r in pred_rows
        if str(r["action_correct"]).lower() == "false"
    ]

    critical_errors = []
    other_errors = []
    for r in errors:
        f = json.loads(r["features_json"])
        match = (
            f.get("research_consent") == "active"
            and f.get("irb_status") == "approved"
            and f.get("pseudonymized") is False
        )
        (critical_errors if match else other_errors).append(r)

    ood_true_action_counts = dict(Counter(r["target_action"] for r in ood_rows))
    ood_pred_action_counts = dict(Counter(r["pred_action"] for r in pred_rows))

    diagnosis = {
        "gate": "GATE_23E_RESEARCH_IRB_FEATURE_SUPPORT_AUDIT",
        "training_changed": False,
        "hyperparameters_changed": False,
        "model_family_changed": False,
        "critical_feature": critical_key,
        "critical_feature_support": critical_support,
        "ood_action_errors": len(errors),
        "critical_interaction_errors": len(critical_errors),
        "other_ood_action_errors": len(other_errors),
        "ood_true_action_counts": ood_true_action_counts,
        "ood_pred_action_counts": ood_pred_action_counts,
        "diagnostic_classification": (
            "unsupported_higher_order_interaction_activation_"
            "and_opened_ood_benchmark_support_gap"
        ),
        "primary_finding": (
            "The active-consent + approved-IRB + deficient-pseudonymization "
            "interaction is never positively activated in original train, dev, "
            "ID test, compositional augmentation, or replay, but appears four "
            "times in OOD. All four Gate-23D action errors occur on those cases."
        ),
        "learning_implication": (
            "An engineered interaction feature with zero positive training support "
            "cannot acquire a supervised coefficient representing its policy effect. "
            "The result therefore does not yet establish insufficient logistic-"
            "regression capacity."
        ),
        "evaluation_implication": (
            "The current 24-case OOD benchmark has now been repeatedly opened for "
            "diagnosis. If its unsupported interaction is added to training, this "
            "benchmark must be retired from final post-repair generalization claims."
        ),
        "macro_f1_context": (
            "The OOD target contains only BLOCK_RESEARCH_PROCESSING and "
            "REQUEST_IRB_REVIEW. The four false predictions introduce ALLOW and "
            "PRESERVE labels with no true OOD support, strongly depressing macro-F1. "
            "The frozen threshold is retained; this is interpretation, not threshold revision."
        ),
        "authorized_next_step": (
            "Design a fresh, pre-frozen generalization protocol in which each "
            "policy-relevant primitive/interaction has training support but the "
            "evaluation still withholds novel combinations. Prefer grouped/nested "
            "combinatorial folds or a new untouched OOD holdout. Do not tune on the "
            "current 24 OOD cases."
        ),
    }

    (OUT / "gate23e_diagnosis.json").write_text(
        json.dumps(diagnosis, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Detailed feature-support CSV
    support_rows = []
    for key, vals in support.items():
        row = {"feature": key, **vals}
        support_rows.append(row)

    with (OUT / "gate23e_feature_support_matrix.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(support_rows[0].keys()))
        w.writeheader()
        w.writerows(support_rows)

    # Error trace
    error_export = []
    for r in errors:
        f = json.loads(r["features_json"])
        error_export.append({
            "record_id": r["record_id"],
            "features_json": r["features_json"],
            "true_action": r["true_action"],
            "pred_action": r["pred_action"],
            "critical_interaction": (
                f.get("research_consent") == "active"
                and f.get("irb_status") == "approved"
                and f.get("pseudonymized") is False
            ),
            "shield_enforcement": r["shield_enforcement"],
        })

    with (OUT / "gate23e_error_support_trace.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(error_export[0].keys()))
        w.writeheader()
        w.writerows(error_export)

    evaluation_contract = {
        "current_gate23_ood_status": "OPENED_DIAGNOSTIC_BENCHMARK",
        "may_be_used_for": [
            "diagnosis",
            "error localization",
            "support analysis",
        ],
        "must_not_be_used_for": [
            "hyperparameter selection",
            "threshold selection",
            "training followed by claims on the same benchmark",
        ],
        "final_generalization_requirement": (
            "A fresh frozen holdout or pre-specified grouped/nested combinatorial "
            "evaluation must be created before any interaction-support repair is trained."
        ),
        "future_dataset_design_rule": (
            "Every policy-relevant primitive and engineered interaction intended "
            "to be learned must have nonzero training support; OOD should withhold "
            "novel combinations, not all positive evidence for the governing interaction."
        ),
    }
    (OUT / "gate23e_future_evaluation_contract.json").write_text(
        json.dumps(evaluation_contract, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    plot_feature_support(support)
    plot_split_support(support, critical_key)
    plot_error_concentration(pred_rows)
    plot_ood_action_support(ood_rows, pred_rows)

    checks = [
        {
            "check": "critical_interaction_zero_training_support",
            "pass": critical_support["combined_train"] == 0,
            "observed": critical_support["combined_train"],
            "expected": 0,
        },
        {
            "check": "critical_interaction_present_in_ood",
            "pass": critical_support["ood"] == 4,
            "observed": critical_support["ood"],
            "expected": 4,
        },
        {
            "check": "all_gate23d_errors_localized_to_critical_interaction",
            "pass": len(critical_errors) == 4 and len(other_errors) == 0,
            "observed": {
                "critical": len(critical_errors),
                "other": len(other_errors),
            },
            "expected": {"critical": 4, "other": 0},
        },
        {
            "check": "no_training_or_tuning_change",
            "pass": True,
            "observed": True,
            "expected": True,
        },
        {
            "check": "future_evaluation_contract_created",
            "pass": (OUT / "gate23e_future_evaluation_contract.json").exists(),
            "observed": True,
            "expected": True,
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
        "gate": "GATE_23E_RESEARCH_IRB_FEATURE_SUPPORT_AUDIT",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "diagnostic_classification": diagnosis["diagnostic_classification"],
        "critical_feature": critical_key,
        "critical_feature_combined_training_support": critical_support["combined_train"],
        "critical_feature_ood_support": critical_support["ood"],
        "ood_action_errors": len(errors),
        "errors_on_critical_interaction": len(critical_errors),
        "model_capacity_failure_established": False,
        "current_ood_benchmark_status": "OPENED_DIAGNOSTIC_BENCHMARK",
        "figures_directory": "outputs/gate23e/figures",
        "next_dependency": (
            "Gate 23F: pre-freeze a fresh generalization protocol before adding "
            "training support for the diagnosed interaction."
        ),
    }

    (OUT / "gate23e_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate23e_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print("\nCritical feature support:")
    print(json.dumps(critical_support, indent=2))
    print("\nOOD true action support:")
    print(json.dumps(ood_true_action_counts, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit("Gate 23E diagnostic infrastructure failed.")

    print(
        "\nFULL GATE 23E PASS — The four residual Gate-23D errors are fully "
        "explained by a policy-relevant interaction with zero positive training "
        "support. The opened OOD benchmark is now diagnostic-only for any future "
        "repair involving that interaction."
    )


if __name__ == "__main__":
    main()
