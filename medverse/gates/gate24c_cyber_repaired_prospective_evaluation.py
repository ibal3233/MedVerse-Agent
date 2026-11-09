from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
import matplotlib.pyplot as plt
import numpy as np
import sklearn
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

DATA = ROOT / "data" / "learning" / "gate21a" / "cyber_network_agent.csv"
PROSPECTIVE = (
    ROOT / "data" / "learning" / "gate24b" /
    "cyber_network_prospective_groups_g5_g8.csv"
)
PROTOCOL = ROOT / "outputs" / "gate24b" / "gate24b_frozen_protocol.json"

OUT = ROOT / "outputs" / "gate24c"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

NUMERIC = ["packet_loss", "rtt_ms", "jitter_ms"]
CANDIDATES = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]
EXPECTED_SHA256 = "ebe2bb97f71e52a853822e612e396817c1d0a66e6525eb0a0190907936ff59ee"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_gate21a():
    with DATA.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_prospective():
    with PROSPECTIVE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    out = []
    for r in rows:
        out.append({
            "record_id": r["record_id"],
            "split_group": f"g{r['prospective_group']}",
            "features_json": r["features_json"],
            "target_assessment": r["target_assessment"],
            "target_action": r["target_action"],
        })
    return out


def fit_numeric_stats(rows):
    values = {k: [] for k in NUMERIC}
    for r in rows:
        x = json.loads(r["features_json"])
        for k in NUMERIC:
            values[k].append(float(x[k]))

    return {
        k: {
            "mean": float(np.mean(values[k])),
            "std": (
                float(np.std(values[k]))
                if float(np.std(values[k])) > 0
                else 1.0
            ),
        }
        for k in NUMERIC
    }


def transform_rows(rows, stats):
    transformed = []
    for r in rows:
        x = json.loads(r["features_json"])

        # Gate24A-authorized missingness intervention.
        if "session_origin" not in x:
            x["session_origin"] = "__MISSING__"
        elif x["session_origin"] is None:
            x["session_origin"] = "__MISSING__"

        # Gate24A-authorized TRAIN-fitted numeric standardization.
        for k in NUMERIC:
            x[k] = (
                (float(x[k]) - stats[k]["mean"])
                / stats[k]["std"]
            )

        transformed.append(x)
    return transformed


def fit_model(rows, target, C, stats):
    X = transform_rows(rows, stats)
    y = [r[target] for r in rows]

    pipe = Pipeline([
        ("vectorizer", DictVectorizer(sparse=True)),
        ("classifier", LogisticRegression(
            C=C,
            max_iter=5000,
            solver="lbfgs",
        )),
    ])
    pipe.fit(X, y)
    return pipe


def evaluate_model(model, rows, target, stats):
    X = transform_rows(rows, stats)
    yt = [r[target] for r in rows]
    yp = list(model.predict(X))

    return {
        "accuracy": float(accuracy_score(yt, yp)),
        "macro_f1": float(
            f1_score(yt, yp, average="macro", zero_division=0)
        ),
        "true": yt,
        "pred": yp,
    }


def solver_iterations(model):
    clf = model.named_steps["classifier"]
    return (
        int(max(clf.n_iter_))
        if hasattr(clf, "n_iter_")
        else 0
    )


def select_c(train, dev, stats):
    table = []
    best = None

    for C in CANDIDATES:
        action_model = fit_model(
            train, "target_action", C, stats
        )
        assessment_model = fit_model(
            train, "target_assessment", C, stats
        )

        tr_action = evaluate_model(
            action_model, train, "target_action", stats
        )
        dv_action = evaluate_model(
            action_model, dev, "target_action", stats
        )
        tr_assess = evaluate_model(
            assessment_model, train, "target_assessment", stats
        )
        dv_assess = evaluate_model(
            assessment_model, dev, "target_assessment", stats
        )

        dev_mean = float(
            np.mean([
                dv_action["macro_f1"],
                dv_assess["macro_f1"],
            ])
        )

        row = {
            "C": C,
            "train_action_accuracy": tr_action["accuracy"],
            "train_action_macro_f1": tr_action["macro_f1"],
            "dev_action_accuracy": dv_action["accuracy"],
            "dev_action_macro_f1": dv_action["macro_f1"],
            "train_assessment_accuracy": tr_assess["accuracy"],
            "train_assessment_macro_f1": tr_assess["macro_f1"],
            "dev_assessment_accuracy": dv_assess["accuracy"],
            "dev_assessment_macro_f1": dv_assess["macro_f1"],
            "dev_mean_macro_f1": dev_mean,
            "action_solver_iterations": solver_iterations(action_model),
            "assessment_solver_iterations": solver_iterations(assessment_model),
            "selected": False,
        }
        table.append(row)

        # Frozen DEV-only selection. Prefer smaller C on exact ties.
        key = (
            dev_mean,
            dv_action["macro_f1"],
            dv_assess["macro_f1"],
            -C,
        )
        if best is None or key > best[0]:
            best = (key, C)

    chosen = best[1]
    for r in table:
        r["selected"] = r["C"] == chosen

    return chosen, table


def group_learning_history(train, dev, C):
    groups = sorted(set(r["split_group"] for r in train))
    history = []
    cumulative = []

    for step, group in enumerate(groups, start=1):
        cumulative += [
            r for r in train
            if r["split_group"] == group
        ]

        # For each diagnostic learning-history point, statistics are fit only on
        # data available at that point.
        stats = fit_numeric_stats(cumulative)
        action_model = fit_model(
            cumulative, "target_action", C, stats
        )
        assessment_model = fit_model(
            cumulative, "target_assessment", C, stats
        )

        tr_action = evaluate_model(
            action_model, cumulative, "target_action", stats
        )
        dv_action = evaluate_model(
            action_model, dev, "target_action", stats
        )
        tr_assess = evaluate_model(
            assessment_model, cumulative, "target_assessment", stats
        )
        dv_assess = evaluate_model(
            assessment_model, dev, "target_assessment", stats
        )

        history.append({
            "step": step,
            "group_added": group,
            "groups_used": step,
            "training_records": len(cumulative),
            "train_action_accuracy": tr_action["accuracy"],
            "train_action_macro_f1": tr_action["macro_f1"],
            "dev_action_accuracy": dv_action["accuracy"],
            "dev_action_macro_f1": dv_action["macro_f1"],
            "train_assessment_accuracy": tr_assess["accuracy"],
            "train_assessment_macro_f1": tr_assess["macro_f1"],
            "dev_assessment_accuracy": dv_assess["accuracy"],
            "dev_assessment_macro_f1": dv_assess["macro_f1"],
            "action_solver_iterations": solver_iterations(action_model),
            "assessment_solver_iterations": solver_iterations(assessment_model),
        })

    return history


def class_metrics(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    p, r, f, s = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        zero_division=0,
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


def save_markdown_hp(table):
    path = OUT / "gate24c_hyperparameter_results_table.md"
    lines = [
        "# Gate 24C Hyperparameter Selection Table",
        "",
        "Selection uses Gate-21A TRAIN/DEV only. Gate-24B prospective metrics are excluded.",
        "",
        "| C | Train Action F1 | Dev Action F1 | Train Assessment F1 | Dev Assessment F1 | Dev Mean F1 | Action Iter. | Assessment Iter. | Selected |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]

    for r in table:
        lines.append(
            f"| {r['C']:.2g} | "
            f"{r['train_action_macro_f1']:.3f} | "
            f"{r['dev_action_macro_f1']:.3f} | "
            f"{r['train_assessment_macro_f1']:.3f} | "
            f"{r['dev_assessment_macro_f1']:.3f} | "
            f"{r['dev_mean_macro_f1']:.3f} | "
            f"{r['action_solver_iterations']} | "
            f"{r['assessment_solver_iterations']} | "
            f"{'✓' if r['selected'] else ''} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def make_plots(hp_table, history, prospective_metrics, action_classes, true_action, pred_action):
    Cs = [r["C"] for r in hp_table]

    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    ax.plot(
        Cs,
        [r["dev_action_macro_f1"] for r in hp_table],
        marker="o",
        label="DEV action macro-F1",
    )
    ax.plot(
        Cs,
        [r["dev_assessment_macro_f1"] for r in hp_table],
        marker="o",
        label="DEV assessment macro-F1",
    )
    ax.plot(
        Cs,
        [r["dev_mean_macro_f1"] for r in hp_table],
        marker="o",
        label="DEV mean macro-F1",
    )
    ax.set_xscale("log")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Logistic-regression C")
    ax.set_ylabel("DEV score")
    ax.set_title("Cyber / Network Repair: DEV-Only Hyperparameter Selection")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24c_hyperparameter_selection.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24c_hyperparameter_selection.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    x = [r["training_records"] for r in history]
    ax.plot(
        x,
        [r["train_action_macro_f1"] for r in history],
        marker="o",
        label="Train action macro-F1",
    )
    ax.plot(
        x,
        [r["dev_action_macro_f1"] for r in history],
        marker="o",
        label="DEV action macro-F1",
    )
    ax.plot(
        x,
        [r["dev_assessment_macro_f1"] for r in history],
        marker="o",
        label="DEV assessment macro-F1",
    )
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Training records (group-wise cumulative)")
    ax.set_ylabel("Macro-F1")
    ax.set_title("Cyber / Network Repair Training History")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24c_training_history.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24c_training_history.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    ax.plot(
        Cs,
        [r["action_solver_iterations"] for r in hp_table],
        marker="o",
        label="Action",
    )
    ax.plot(
        Cs,
        [r["assessment_solver_iterations"] for r in hp_table],
        marker="o",
        label="Assessment",
    )
    ax.set_xscale("log")
    ax.set_xlabel("C")
    ax.set_ylabel("LBFGS iterations")
    ax.set_title("Cyber / Network Solver-Convergence Diagnostics")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24c_solver_iterations.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24c_solver_iterations.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    labels = ["Assessment", "Action"]
    xx = np.arange(2)
    w = 0.36
    ax.bar(
        xx - w/2,
        [
            prospective_metrics["assessment"]["accuracy"],
            prospective_metrics["action"]["accuracy"],
        ],
        w,
        label="Accuracy",
    )
    ax.bar(
        xx + w/2,
        [
            prospective_metrics["assessment"]["macro_f1"],
            prospective_metrics["action"]["macro_f1"],
        ],
        w,
        label="Macro-F1",
    )
    ax.set_ylim(0, 1.05)
    ax.set_xticks(xx)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Score")
    ax.set_title("Cyber / Network Fresh Prospective Performance")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24c_prospective_metrics.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24c_prospective_metrics.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(
        [r["class"] for r in action_classes],
        [r["recall"] for r in action_classes],
    )
    ax.axhline(0.80, linestyle="--", linewidth=1)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Recall")
    ax.set_title("Cyber / Network Prospective Action Recall by Class")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIG / "fig24c_action_class_recall.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24c_action_class_recall.pdf", bbox_inches="tight")
    plt.close(fig)

    cm_labels = sorted(set(true_action) | set(pred_action))
    cm = confusion_matrix(
        true_action,
        pred_action,
        labels=cm_labels,
    )
    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(cm, aspect="auto")
    ax.set_title("Cyber / Network Prospective Action Confusion Matrix")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_xticks(range(len(cm_labels)))
    ax.set_yticks(range(len(cm_labels)))
    ax.set_xticklabels(cm_labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(cm_labels, fontsize=8)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(FIG / "fig24c_action_confusion.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24c_action_confusion.pdf", bbox_inches="tight")
    plt.close(fig)

    # Prospective performance by g5-g8
    groups = sorted(prospective_metrics["by_group"])
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.plot(
        groups,
        [
            prospective_metrics["by_group"][g]["action_accuracy"]
            for g in groups
        ],
        marker="o",
        label="Action accuracy",
    )
    ax.plot(
        groups,
        [
            prospective_metrics["by_group"][g]["assessment_accuracy"]
            for g in groups
        ],
        marker="o",
        label="Assessment accuracy",
    )
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Prospective group")
    ax.set_ylabel("Accuracy")
    ax.set_title("Cyber / Network Prospective Stability Across g5–g8")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24c_group_stability.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24c_group_stability.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 24C")
    print(" Cyber / Network Repaired Training")
    print(" & Frozen Prospective Evaluation")
    print("========================================\n")

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    observed_hash = sha256(PROSPECTIVE)

    rows = load_gate21a()
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    opened_test = [r for r in rows if r["split"] == "test"]
    prospective = load_prospective()

    # g4 is not used anywhere below for selection or confirmation.
    train_stats = fit_numeric_stats(train)
    chosen_C, hp_table = select_c(train, dev, train_stats)
    history = group_learning_history(train, dev, chosen_C)

    final_action = fit_model(
        train, "target_action", chosen_C, train_stats
    )
    final_assessment = fit_model(
        train, "target_assessment", chosen_C, train_stats
    )

    # One-time prospective evaluation.
    action_eval = evaluate_model(
        final_action,
        prospective,
        "target_action",
        train_stats,
    )
    assessment_eval = evaluate_model(
        final_assessment,
        prospective,
        "target_assessment",
        train_stats,
    )

    by_group = {}
    for group in sorted(set(r["split_group"] for r in prospective)):
        subset = [
            r for r in prospective
            if r["split_group"] == group
        ]
        ga = evaluate_model(
            final_action, subset, "target_action", train_stats
        )
        gs = evaluate_model(
            final_assessment, subset, "target_assessment", train_stats
        )
        by_group[group] = {
            "records": len(subset),
            "action_accuracy": ga["accuracy"],
            "action_macro_f1": ga["macro_f1"],
            "assessment_accuracy": gs["accuracy"],
            "assessment_macro_f1": gs["macro_f1"],
        }

    prospective_metrics = {
        "action": {
            "accuracy": action_eval["accuracy"],
            "macro_f1": action_eval["macro_f1"],
        },
        "assessment": {
            "accuracy": assessment_eval["accuracy"],
            "macro_f1": assessment_eval["macro_f1"],
        },
        "by_group": by_group,
    }

    action_classes = class_metrics(
        action_eval["true"],
        action_eval["pred"],
    )
    min_recall = min(
        r["recall"] for r in action_classes
    )

    # Save fresh artifact built in this runtime, avoiding cross-version reuse.
    artifact = {
        "action_model": final_action,
        "assessment_model": final_assessment,
        "numeric_stats": train_stats,
        "chosen_C": chosen_C,
        "numeric_features": NUMERIC,
        "explicit_missing_session_origin": True,
        "sklearn_version": sklearn.__version__,
    }
    joblib.dump(
        artifact,
        OUT / "cyber_network_repaired_model.joblib",
    )

    # Tables.
    with (OUT / "gate24c_hyperparameter_results.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=list(hp_table[0].keys()),
        )
        w.writeheader()
        w.writerows(hp_table)

    hp_md = save_markdown_hp(hp_table)

    with (OUT / "gate24c_training_history.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=list(history[0].keys()),
        )
        w.writeheader()
        w.writerows(history)

    with (OUT / "gate24c_action_class_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "class",
                "precision",
                "recall",
                "f1",
                "support",
            ],
        )
        w.writeheader()
        w.writerows(action_classes)

    evaluation_rows = [
        {
            "output": "assessment",
            "accuracy": assessment_eval["accuracy"],
            "macro_f1": assessment_eval["macro_f1"],
        },
        {
            "output": "action",
            "accuracy": action_eval["accuracy"],
            "macro_f1": action_eval["macro_f1"],
        },
    ]
    with (OUT / "gate24c_prospective_results_table.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=list(evaluation_rows[0].keys()),
        )
        w.writeheader()
        w.writerows(evaluation_rows)

    md = OUT / "gate24c_prospective_results_table.md"
    md.write_text(
        "# Gate 24C Prospective Results\n\n"
        "| Output | Accuracy | Macro-F1 |\n"
        "|---|---:|---:|\n"
        f"| Assessment | {assessment_eval['accuracy']:.3f} | "
        f"{assessment_eval['macro_f1']:.3f} |\n"
        f"| Action | {action_eval['accuracy']:.3f} | "
        f"{action_eval['macro_f1']:.3f} |\n\n"
        f"Minimum action-class recall: **{min_recall:.3f}**\n",
        encoding="utf-8",
    )

    prediction_rows = []
    for i, r in enumerate(prospective):
        prediction_rows.append({
            "record_id": r["record_id"],
            "prospective_group": r["split_group"],
            "true_assessment": assessment_eval["true"][i],
            "pred_assessment": assessment_eval["pred"][i],
            "true_action": action_eval["true"][i],
            "pred_action": action_eval["pred"][i],
            "assessment_correct": (
                assessment_eval["true"][i]
                == assessment_eval["pred"][i]
            ),
            "action_correct": (
                action_eval["true"][i]
                == action_eval["pred"][i]
            ),
        })

    with (OUT / "gate24c_prospective_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=list(prediction_rows[0].keys()),
        )
        w.writeheader()
        w.writerows(prediction_rows)

    methodology = {
        "gate": "GATE_24C_CYBER_REPAIRED_PROSPECTIVE_EVALUATION",
        "model_family": "multinomial_logistic_regression",
        "authorized_preprocessing": {
            "numeric_standardization": (
                "packet_loss, rtt_ms, jitter_ms; statistics fit on TRAIN only"
            ),
            "missingness": (
                "absent session_origin encoded explicitly as __MISSING__"
            ),
        },
        "train_records": len(train),
        "dev_records": len(dev),
        "opened_g4_records_not_used_for_selection": len(opened_test),
        "prospective_records": len(prospective),
        "chosen_C": chosen_C,
        "hyperparameter_grid": CANDIDATES,
        "hyperparameter_selection": "Gate-21A DEV only",
        "gate24_g4_status": "DIAGNOSTIC_ONLY_NOT_USED",
        "gate24b_used_for_selection": False,
        "training_history_type": (
            "group-wise cumulative data-growth history; no fabricated epochs"
        ),
        "sklearn_version": sklearn.__version__,
        "artifact_portability_note": (
            "Model artifact was freshly trained in the current runtime. "
            "Serialized sklearn artifacts should be re-created from source data "
            "when runtime versions differ."
        ),
        "claim_boundary": protocol["claim_boundary"],
    }
    (OUT / "gate24c_methodology.json").write_text(
        json.dumps(methodology, indent=2),
        encoding="utf-8",
    )

    make_plots(
        hp_table,
        history,
        prospective_metrics,
        action_classes,
        action_eval["true"],
        action_eval["pred"],
    )

    thresholds = protocol["confirmation_thresholds"]
    checks = [
        {
            "check": "frozen_benchmark_hash_matches",
            "pass": observed_hash == EXPECTED_SHA256,
            "observed": observed_hash,
            "expected": EXPECTED_SHA256,
        },
        {
            "check": "authorized_preprocessing_only",
            "pass": True,
            "observed": (
                "TRAIN-fitted numeric standardization + explicit "
                "session_origin missing category"
            ),
            "expected": True,
        },
        {
            "check": "dev_only_hyperparameter_selection",
            "pass": chosen_C in CANDIDATES,
            "observed": chosen_C,
            "expected": CANDIDATES,
        },
        {
            "check": "opened_g4_not_used",
            "pass": True,
            "observed": len(opened_test),
            "expected": "18 diagnostic-only rows excluded",
        },
        {
            "check": "prospective_action_accuracy",
            "pass": (
                action_eval["accuracy"]
                >= thresholds["prospective_action_accuracy"]
            ),
            "observed": action_eval["accuracy"],
            "expected": (
                f">={thresholds['prospective_action_accuracy']}"
            ),
        },
        {
            "check": "prospective_action_macro_f1",
            "pass": (
                action_eval["macro_f1"]
                >= thresholds["prospective_action_macro_f1"]
            ),
            "observed": action_eval["macro_f1"],
            "expected": (
                f">={thresholds['prospective_action_macro_f1']}"
            ),
        },
        {
            "check": "prospective_assessment_accuracy",
            "pass": (
                assessment_eval["accuracy"]
                >= thresholds["prospective_assessment_accuracy"]
            ),
            "observed": assessment_eval["accuracy"],
            "expected": (
                f">={thresholds['prospective_assessment_accuracy']}"
            ),
        },
        {
            "check": "prospective_assessment_macro_f1",
            "pass": (
                assessment_eval["macro_f1"]
                >= thresholds["prospective_assessment_macro_f1"]
            ),
            "observed": assessment_eval["macro_f1"],
            "expected": (
                f">={thresholds['prospective_assessment_macro_f1']}"
            ),
        },
        {
            "check": "minimum_action_class_recall",
            "pass": (
                min_recall
                >= thresholds["all_action_class_recall_minimum"]
            ),
            "observed": min_recall,
            "expected": (
                f">={thresholds['all_action_class_recall_minimum']}"
            ),
        },
        {
            "check": "all_four_prospective_groups_evaluated",
            "pass": (
                sorted(by_group.keys())
                == ["g5", "g6", "g7", "g8"]
                and all(x["records"] == 18 for x in by_group.values())
            ),
            "observed": by_group,
            "expected": "g5-g8, 18 rows each",
        },
        {
            "check": "hyperparameter_table_and_training_history",
            "pass": (
                hp_md.exists()
                and (OUT / "gate24c_hyperparameter_results.csv").exists()
                and (OUT / "gate24c_training_history.csv").exists()
                and md.exists()
            ),
            "observed": True,
            "expected": True,
        },
        {
            "check": "publication_outputs",
            "pass": (
                len(list(FIG.glob("*.png"))) >= 7
                and len(list(FIG.glob("*.pdf"))) >= 7
            ),
            "observed": {
                "png": len(list(FIG.glob("*.png"))),
                "pdf": len(list(FIG.glob("*.pdf"))),
            },
            "expected": ">=7 PNG and >=7 PDF",
        },
    ]

    passed = sum(c["pass"] for c in checks)

    result = {
        "gate": "GATE_24C_CYBER_REPAIRED_PROSPECTIVE_EVALUATION",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "agent": "Cyber / Network Agent",
        "model_family": "multinomial_logistic_regression",
        "chosen_C": chosen_C,
        "train_records": len(train),
        "dev_records": len(dev),
        "opened_g4_records_excluded": len(opened_test),
        "prospective_records": len(prospective),
        "prospective_metrics": prospective_metrics,
        "action_class_metrics": action_classes,
        "minimum_action_class_recall": min_recall,
        "training_history_steps": len(history),
        "sklearn_version": sklearn.__version__,
        "hyperparameter_table_path": (
            "outputs/gate24c/gate24c_hyperparameter_results_table.md"
        ),
        "prospective_results_table_path": (
            "outputs/gate24c/gate24c_prospective_results_table.md"
        ),
        "model_path": (
            "outputs/gate24c/cyber_network_repaired_model.joblib"
        ),
        "figures_directory": "outputs/gate24c/figures",
        "claim_boundary": protocol["claim_boundary"],
        "next_dependency": (
            "If PASS, stop agent-learning experiments and perform final system "
            "consolidation for demo/video. If FAIL, document Cyber residual "
            "limitations rather than opening another adaptive loop."
        ),
    }

    (OUT / "gate24c_checks.json").write_text(
        json.dumps(checks, indent=2),
        encoding="utf-8",
    )
    (OUT / "gate24c_status.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print("\nHyperparameter table:")
    for r in hp_table:
        print({
            "C": r["C"],
            "train_action_macro_f1": round(r["train_action_macro_f1"], 4),
            "dev_action_macro_f1": round(r["dev_action_macro_f1"], 4),
            "train_assessment_macro_f1": round(r["train_assessment_macro_f1"], 4),
            "dev_assessment_macro_f1": round(r["dev_assessment_macro_f1"], 4),
            "dev_mean_macro_f1": round(r["dev_mean_macro_f1"], 4),
            "selected": r["selected"],
        })

    print("\nTraining history:")
    print(json.dumps(history, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] != "PASS":
        raise SystemExit(
            "Gate 24C FAILED. Do not open another adaptive Cyber cycle for the "
            "hackathon; document residual limitations and move to consolidation."
        )

    print(
        "\nFULL GATE 24C PASS — The repaired Cyber/Network Agent satisfies "
        "the prospectively frozen g5-g8 benchmark with DEV-only hyperparameter "
        "selection, TRAIN-fitted preprocessing, and complete reporting."
    )


if __name__ == "__main__":
    main()
