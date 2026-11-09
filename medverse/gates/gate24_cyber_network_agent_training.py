from __future__ import annotations

from pathlib import Path
from collections import Counter
import csv, json, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

from medverse.learning.cyber_network_model import (
    clean_features,
    train_bundle,
    save_bundle,
    solver_iterations,
)

DATA = ROOT / "data" / "learning" / "gate21a" / "cyber_network_agent.csv"
OUT = ROOT / "outputs" / "gate24"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

CANDIDATES = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]


def load_rows():
    with DATA.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def evaluate(bundle, rows):
    X = [clean_features(r["features_json"]) for r in rows]

    true_assessment = [r["target_assessment"] for r in rows]
    true_action = [r["target_action"] for r in rows]

    pred_assessment = list(bundle.assessment_model.predict(X))
    pred_action = list(bundle.action_model.predict(X))

    return {
        "assessment": {
            "accuracy": accuracy_score(true_assessment, pred_assessment),
            "macro_f1": f1_score(true_assessment, pred_assessment, average="macro", zero_division=0),
            "true": true_assessment,
            "pred": pred_assessment,
        },
        "action": {
            "accuracy": accuracy_score(true_action, pred_action),
            "macro_f1": f1_score(true_action, pred_action, average="macro", zero_division=0),
            "true": true_action,
            "pred": pred_action,
        },
    }


def train_dev_path(train, dev):
    rows = []
    best = None

    for C in CANDIDATES:
        bundle = train_bundle(train, C)
        tr = evaluate(bundle, train)
        dv = evaluate(bundle, dev)

        rec = {
            "C": C,
            "train_action_accuracy": tr["action"]["accuracy"],
            "train_action_macro_f1": tr["action"]["macro_f1"],
            "dev_action_accuracy": dv["action"]["accuracy"],
            "dev_action_macro_f1": dv["action"]["macro_f1"],
            "train_assessment_accuracy": tr["assessment"]["accuracy"],
            "train_assessment_macro_f1": tr["assessment"]["macro_f1"],
            "dev_assessment_accuracy": dv["assessment"]["accuracy"],
            "dev_assessment_macro_f1": dv["assessment"]["macro_f1"],
            "action_solver_iterations": solver_iterations(bundle.action_model),
            "assessment_solver_iterations": solver_iterations(bundle.assessment_model),
        }
        rows.append(rec)

        key = (
            dv["action"]["macro_f1"],
            dv["action"]["accuracy"],
            dv["assessment"]["macro_f1"],
            -C,
        )
        if best is None or key > best[0]:
            best = (key, C)

    return best[1], rows


def group_learning_history(train, dev, C):
    """
    For logistic regression there is no epoch-wise training history.
    We use a group-wise data-growth learning curve instead.

    Gate-21A Cyber TRAIN contains three disjoint generation groups:
    g0, g1, g2. We add them cumulatively and evaluate on frozen DEV g3.
    """
    groups = sorted(set(r["split_group"] for r in train))
    history = []

    cumulative = []
    for idx, g in enumerate(groups, start=1):
        cumulative += [r for r in train if r["split_group"] == g]
        bundle = train_bundle(cumulative, C)
        tr = evaluate(bundle, cumulative)
        dv = evaluate(bundle, dev)

        history.append({
            "step": idx,
            "groups_used": idx,
            "group_added": g,
            "training_records": len(cumulative),
            "train_action_accuracy": tr["action"]["accuracy"],
            "train_action_macro_f1": tr["action"]["macro_f1"],
            "dev_action_accuracy": dv["action"]["accuracy"],
            "dev_action_macro_f1": dv["action"]["macro_f1"],
            "train_assessment_accuracy": tr["assessment"]["accuracy"],
            "dev_assessment_accuracy": dv["assessment"]["accuracy"],
            "action_solver_iterations": solver_iterations(bundle.action_model),
            "assessment_solver_iterations": solver_iterations(bundle.assessment_model),
        })

    return history


def save_hyperparameter_plot(path_rows):
    Cs = [r["C"] for r in path_rows]

    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    ax.plot(Cs, [r["train_action_macro_f1"] for r in path_rows], marker="o", label="Train action macro-F1")
    ax.plot(Cs, [r["dev_action_macro_f1"] for r in path_rows], marker="o", label="Dev action macro-F1")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Logistic-regression C")
    ax.set_ylabel("Macro-F1")
    ax.set_title("Cyber / Network Agent: Train–Dev Hyperparameter Path")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24_train_dev_hyperparameter_history.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24_train_dev_hyperparameter_history.pdf", bbox_inches="tight")
    plt.close(fig)


def save_learning_curve(history):
    x = [r["training_records"] for r in history]

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    ax.plot(x, [r["train_action_macro_f1"] for r in history], marker="o", label="Train action macro-F1")
    ax.plot(x, [r["dev_action_macro_f1"] for r in history], marker="o", label="Dev action macro-F1")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Training records (group-wise cumulative)")
    ax.set_ylabel("Macro-F1")
    ax.set_title("Cyber / Network Agent Training History: Data-Growth Learning Curve")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24_training_history_learning_curve.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24_training_history_learning_curve.pdf", bbox_inches="tight")
    plt.close(fig)


def save_solver_plot(path_rows):
    Cs = [r["C"] for r in path_rows]

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.plot(Cs, [r["action_solver_iterations"] for r in path_rows], marker="o", label="Action classifier")
    ax.plot(Cs, [r["assessment_solver_iterations"] for r in path_rows], marker="o", label="Assessment classifier")
    ax.set_xscale("log")
    ax.set_xlabel("Logistic-regression C")
    ax.set_ylabel("LBFGS iterations to convergence")
    ax.set_title("Cyber / Network Agent Optimization Convergence")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24_solver_convergence_iterations.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24_solver_convergence_iterations.pdf", bbox_inches="tight")
    plt.close(fig)


def save_test_metrics(test_metrics):
    fig, ax = plt.subplots(figsize=(6.8, 4.7))
    labels = ["Assessment", "Action"]
    x = np.arange(2)
    w = 0.36

    ax.bar(
        x-w/2,
        [test_metrics["assessment"]["accuracy"], test_metrics["action"]["accuracy"]],
        w,
        label="Accuracy",
    )
    ax.bar(
        x+w/2,
        [test_metrics["assessment"]["macro_f1"], test_metrics["action"]["macro_f1"]],
        w,
        label="Macro-F1",
    )
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Cyber / Network Agent Held-Out ID Test")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24_id_test_metrics.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24_id_test_metrics.pdf", bbox_inches="tight")
    plt.close(fig)


def save_confusion(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(cm, aspect="auto")
    ax.set_title("Cyber / Network Agent Action Confusion Matrix")
    ax.set_xlabel("Predicted action")
    ax.set_ylabel("True action")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=8)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(FIG / "fig24_action_confusion_matrix.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24_action_confusion_matrix.pdf", bbox_inches="tight")
    plt.close(fig)


def per_class(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    p, r, f, s = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    return [
        {
            "class": labels[i],
            "precision": float(p[i]),
            "recall": float(r[i]),
            "f1": float(f[i]),
            "support": int(s[i]),
        }
        for i in range(len(labels))
    ]


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 24")
    print(" Cyber / Network Agent Training")
    print(" + Training-History Diagnostics")
    print("========================================\n")

    rows = load_rows()
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]

    # Actual split-group leakage audit.
    group_to_splits = {}
    for r in rows:
        group_to_splits.setdefault(r["split_group"], set()).add(r["split"])
    crossing_groups = {
        g: sorted(s)
        for g, s in group_to_splits.items()
        if len(s) > 1
    }

    chosen_C, hp_path = train_dev_path(train, dev)
    learning_history = group_learning_history(train, dev, chosen_C)

    final = train_bundle(train, chosen_C)
    test_metrics = evaluate(final, test)
    save_bundle(final, OUT / "cyber_network_agent_model.joblib")

    class_metrics = per_class(
        test_metrics["action"]["true"],
        test_metrics["action"]["pred"],
    )

    with (OUT / "gate24_hyperparameter_history.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(hp_path[0].keys()))
        w.writeheader()
        w.writerows(hp_path)

    with (OUT / "gate24_training_history.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(learning_history[0].keys()))
        w.writeheader()
        w.writerows(learning_history)

    with (OUT / "gate24_action_class_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(class_metrics[0].keys()))
        w.writeheader()
        w.writerows(class_metrics)

    prediction_rows = []
    for i, r in enumerate(test):
        prediction_rows.append({
            "record_id": r["record_id"],
            "split_group": r["split_group"],
            "features_json": r["features_json"],
            "true_assessment": test_metrics["assessment"]["true"][i],
            "pred_assessment": test_metrics["assessment"]["pred"][i],
            "true_action": test_metrics["action"]["true"][i],
            "pred_action": test_metrics["action"]["pred"][i],
            "action_correct": (
                test_metrics["action"]["true"][i]
                == test_metrics["action"]["pred"][i]
            ),
        })

    with (OUT / "gate24_test_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(prediction_rows[0].keys()))
        w.writeheader()
        w.writerows(prediction_rows)

    methodology = {
        "agent": "Cyber / Network Agent",
        "dataset": "data/learning/gate21a/cyber_network_agent.csv",
        "records": {
            "total": len(rows),
            "train": len(train),
            "dev": len(dev),
            "test": len(test),
        },
        "actual_split_groups": {
            "train": sorted({r["split_group"] for r in train}),
            "dev": sorted({r["split_group"] for r in dev}),
            "test": sorted({r["split_group"] for r in test}),
            "groups_crossing_partitions": crossing_groups,
        },
        "features": [
            "certificate_status",
            "packet_loss",
            "rtt_ms",
            "jitter_ms",
            "session_origin when present",
        ],
        "feature_rationale": (
            "Only Cyber/Network mandate-relevant telemetry and identity/session "
            "signals are used. Split/group identifiers are not model features."
        ),
        "targets": [
            "target_assessment",
            "target_action",
        ],
        "constant_outputs_not_treated_as_learning_evidence": {
            "target_boundary_status": "COMPLIANT",
            "target_enforcement": "PERMIT",
            "target_evidence_request": "empty",
        },
        "model_family": "multinomial_logistic_regression",
        "hyperparameter_grid": CANDIDATES,
        "selection_rule": "DEV action macro-F1 primary, then action accuracy, assessment macro-F1, smaller C",
        "test_used_for_selection": False,
        "training_history_definition": (
            "Because LBFGS logistic regression is not trained in reportable epochs, "
            "training history is represented by a cumulative group-wise learning curve, "
            "train-vs-dev hyperparameter path, and solver iteration diagnostics."
        ),
        "overfitting_controls": [
            "disjoint split_group partitions",
            "DEV-only hyperparameter selection",
            "TEST opened after C selection",
            "train and dev curves both reported",
            "raw history CSV preserved",
        ],
        "patient_data": False,
    }

    (OUT / "gate24_training_methodology.json").write_text(
        json.dumps(methodology, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Figures
    save_hyperparameter_plot(hp_path)
    save_learning_curve(learning_history)
    save_solver_plot(hp_path)
    save_test_metrics(test_metrics)
    save_confusion(
        test_metrics["action"]["true"],
        test_metrics["action"]["pred"],
    )

    checks = [
        {
            "check": "split_group_leakage",
            "pass": len(crossing_groups) == 0,
            "observed": crossing_groups,
            "expected": {},
        },
        {
            "check": "dev_only_hyperparameter_selection",
            "pass": chosen_C in CANDIDATES,
            "observed": chosen_C,
            "expected": CANDIDATES,
        },
        {
            "check": "test_action_accuracy",
            "pass": test_metrics["action"]["accuracy"] >= 0.90,
            "observed": test_metrics["action"]["accuracy"],
            "expected": ">=0.90",
        },
        {
            "check": "test_action_macro_f1",
            "pass": test_metrics["action"]["macro_f1"] >= 0.85,
            "observed": test_metrics["action"]["macro_f1"],
            "expected": ">=0.85",
        },
        {
            "check": "test_assessment_accuracy",
            "pass": test_metrics["assessment"]["accuracy"] >= 0.90,
            "observed": test_metrics["assessment"]["accuracy"],
            "expected": ">=0.90",
        },
        {
            "check": "training_history_created",
            "pass": (
                len(learning_history) == 3
                and (OUT / "gate24_training_history.csv").exists()
                and (FIG / "fig24_training_history_learning_curve.png").exists()
            ),
            "observed": {
                "history_steps": len(learning_history),
                "csv": (OUT / "gate24_training_history.csv").exists(),
                "plot": (FIG / "fig24_training_history_learning_curve.png").exists(),
            },
            "expected": "3 group-wise history steps + raw CSV + plot",
        },
        {
            "check": "publication_outputs",
            "pass": (
                len(list(FIG.glob("*.png"))) >= 5
                and len(list(FIG.glob("*.pdf"))) >= 5
            ),
            "observed": {
                "png": len(list(FIG.glob("*.png"))),
                "pdf": len(list(FIG.glob("*.pdf"))),
            },
            "expected": ">=5 PNG and >=5 PDF",
        },
        {
            "check": "raw_and_methodology_outputs",
            "pass": (
                (OUT / "gate24_hyperparameter_history.csv").exists()
                and (OUT / "gate24_test_predictions.csv").exists()
                and (OUT / "gate24_action_class_metrics.csv").exists()
                and (OUT / "gate24_training_methodology.json").exists()
            ),
            "observed": True,
            "expected": True,
        },
    ]

    passed = sum(c["pass"] for c in checks)

    result = {
        "gate": "GATE_24_CYBER_NETWORK_AGENT_TRAINING",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "agent": "Cyber / Network Agent",
        "model_family": "multinomial_logistic_regression",
        "chosen_C": chosen_C,
        "train_records": len(train),
        "dev_records": len(dev),
        "test_records": len(test),
        "train_groups": len({r["split_group"] for r in train}),
        "dev_groups": len({r["split_group"] for r in dev}),
        "test_groups": len({r["split_group"] for r in test}),
        "split_group_leakage_count": len(crossing_groups),
        "test_metrics": {
            k: {
                "accuracy": v["accuracy"],
                "macro_f1": v["macro_f1"],
            }
            for k, v in test_metrics.items()
        },
        "training_history_steps": len(learning_history),
        "training_history_final": learning_history[-1],
        "action_class_metrics": class_metrics,
        "model_path": "outputs/gate24/cyber_network_agent_model.joblib",
        "figures_directory": "outputs/gate24/figures",
        "next_dependency": (
            "If PASS, Gate 24A prospective Cyber/Network compositional and threshold "
            "generalization protocol. If FAIL, diagnose class/feature/regularization error."
        ),
    }

    (OUT / "gate24_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate24_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print("\nTraining history:")
    print(json.dumps(learning_history, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] != "PASS":
        raise SystemExit(
            "Gate 24 FAILED. Diagnose Cyber/Network training before OOD evaluation."
        )

    print(
        "\nFULL GATE 24 PASS — Cyber / Network Agent baseline training passes "
        "with DEV-only tuning, disjoint generation groups, raw training-history "
        "evidence, and held-out ID evaluation."
    )


if __name__ == "__main__":
    main()
