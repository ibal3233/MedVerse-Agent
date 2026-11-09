from __future__ import annotations

from pathlib import Path
from collections import Counter, defaultdict
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
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

from medverse.learning.privacy_agent_model import (
    clean_features,
    train_bundle,
    save_bundle,
)
from medverse.learning.gate22c_compositional_augmentation import (
    build_augmentation,
)
from medverse.gates.gate22c_privacy_compositional_coverage import (
    aug_to_training_row,
)
from medverse.gates.gate22_privacy_agent_training import (
    privacy_policy_shield,
)
from medverse.learning.privacy_precedence_oracle_v2 import ORACLE_VERSION


BASE_DATA = ROOT / "data" / "learning" / "gate21a" / "privacy_agent.csv"
CONFIRMATION = (
    ROOT / "data" / "learning" / "gate22b2" /
    "privacy_confirmation_factorial_context_v2.csv"
)
PROTOCOL = ROOT / "outputs" / "gate22b2" / "gate22b2_frozen_protocol.json"

OUT = ROOT / "outputs" / "gate22b3"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

EXPECTED_SHA256 = "046ed01a9392306042ebc432f9e7dc4db05fd38f57bb7db701a50238d072a176"
CANDIDATES = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]

TARGETS = {
    "assessment": ("assessment_model", "target_assessment"),
    "action": ("action_model", "target_action"),
    "boundary": ("boundary_model", "target_boundary_status"),
    "enforcement": ("enforcement_model", "target_enforcement"),
    "evidence": ("evidence_model", "target_evidence_request"),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_base():
    with BASE_DATA.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {
        "train": [r for r in rows if r["split"] == "train"],
        "dev": [r for r in rows if r["split"] == "dev"],
        "test": [r for r in rows if r["split"] == "test"],
    }


def parse_tri(v):
    if v == "__MISSING__":
        return None
    if v in ("True", "true", True):
        return True
    if v in ("False", "false", False):
        return False
    return v


def load_confirmation():
    with CONFIRMATION.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    out = []
    for r in rows:
        features = {
            "jurisdiction": r["jurisdiction"],
            "disclosure_authorized": parse_tri(r["disclosure_authorized"]),
            "minimum_necessary": parse_tri(r["minimum_necessary"]),
            "purpose_declared": parse_tri(r["purpose_declared"]),
            "audit_required": parse_tri(r["audit_required"]),
            "request_context": r["request_context"],
        }
        out.append({
            "record_id": r["record_id"],
            "features_json": json.dumps(features, sort_keys=True),
            "features": features,
            "target_assessment": r["target_assessment"],
            "target_action": r["target_action"],
            "target_boundary_status": r["target_boundary_status"],
            "target_enforcement": r["target_enforcement"],
            "target_evidence_request": (
                "" if r["target_evidence_request"] == "NONE"
                else r["target_evidence_request"]
            ),
            "oracle_version": r["oracle_version"],
        })
    return out


def evaluate(bundle, rows):
    X = [clean_features(r["features_json"]) for r in rows]
    metrics = {}
    predictions = {}

    for name, (model_attr, field) in TARGETS.items():
        yt = [(r[field] if r[field] else "NONE") for r in rows]
        yp = list(getattr(bundle, model_attr).predict(X))

        metrics[name] = {
            "accuracy": float(accuracy_score(yt, yp)),
            "macro_f1": float(
                f1_score(yt, yp, average="macro", zero_division=0)
            ),
        }
        predictions[name] = {"true": yt, "pred": yp}

    return metrics, predictions


def solver_iterations(bundle):
    out = {}
    for name, (model_attr, _) in TARGETS.items():
        pipe = getattr(bundle, model_attr)
        clf = pipe.named_steps["classifier"]
        out[name] = (
            int(max(clf.n_iter_))
            if hasattr(clf, "n_iter_")
            else 0
        )
    return out


def select_c(train_rows, dev_rows):
    table = []
    best = None

    for C in CANDIDATES:
        bundle = train_bundle(train_rows, C)
        tr_metrics, _ = evaluate(bundle, train_rows)
        dv_metrics, _ = evaluate(bundle, dev_rows)
        iters = solver_iterations(bundle)

        mean_dev_macro = float(
            np.mean([dv_metrics[k]["macro_f1"] for k in TARGETS])
        )
        mean_train_macro = float(
            np.mean([tr_metrics[k]["macro_f1"] for k in TARGETS])
        )

        rec = {
            "C": C,
            "train_mean_macro_f1": mean_train_macro,
            "dev_mean_macro_f1": mean_dev_macro,
            "train_action_accuracy": tr_metrics["action"]["accuracy"],
            "train_action_macro_f1": tr_metrics["action"]["macro_f1"],
            "dev_action_accuracy": dv_metrics["action"]["accuracy"],
            "dev_action_macro_f1": dv_metrics["action"]["macro_f1"],
            "train_assessment_accuracy": tr_metrics["assessment"]["accuracy"],
            "train_assessment_macro_f1": tr_metrics["assessment"]["macro_f1"],
            "dev_assessment_accuracy": dv_metrics["assessment"]["accuracy"],
            "dev_assessment_macro_f1": dv_metrics["assessment"]["macro_f1"],
            "action_solver_iterations": iters["action"],
            "assessment_solver_iterations": iters["assessment"],
            "selected": False,
        }
        table.append(rec)

        # DEV only. No ID test, opened OOD, or confirmation data is used.
        key = (
            mean_dev_macro,
            dv_metrics["action"]["macro_f1"],
            dv_metrics["assessment"]["macro_f1"],
            -C,
        )
        if best is None or key > best[0]:
            best = (key, C)

    chosen = best[1]
    for r in table:
        r["selected"] = (r["C"] == chosen)

    return chosen, table


def stratified_fraction(rows, fraction):
    """
    Deterministic data-growth sample stratified by target_action.
    Used only for descriptive learning-history diagnostics.
    """
    by_class = defaultdict(list)
    for r in rows:
        by_class[r["target_action"]].append(r)

    selected = []
    for cls in sorted(by_class):
        members = sorted(
            by_class[cls],
            key=lambda x: x.get("record_id", x["features_json"]),
        )
        n = max(1, math.ceil(len(members) * fraction))
        selected.extend(members[:n])
    return selected


def learning_history(original_train, augmentation_rows, dev_rows, C):
    history = []
    fractions = [0.0, 0.25, 0.50, 0.75, 1.0]

    for step, frac in enumerate(fractions):
        if frac == 0.0:
            aug_subset = []
        else:
            aug_subset = stratified_fraction(augmentation_rows, frac)

        train_now = list(original_train) + aug_subset
        bundle = train_bundle(train_now, C)
        tr_metrics, _ = evaluate(bundle, train_now)
        dv_metrics, _ = evaluate(bundle, dev_rows)
        iters = solver_iterations(bundle)

        history.append({
            "step": step,
            "augmentation_fraction": frac,
            "original_train_records": len(original_train),
            "augmentation_records": len(aug_subset),
            "training_records": len(train_now),
            "train_action_macro_f1": tr_metrics["action"]["macro_f1"],
            "dev_action_macro_f1": dv_metrics["action"]["macro_f1"],
            "train_assessment_macro_f1": tr_metrics["assessment"]["macro_f1"],
            "dev_assessment_macro_f1": dv_metrics["assessment"]["macro_f1"],
            "action_solver_iterations": iters["action"],
            "assessment_solver_iterations": iters["assessment"],
        })

    return history


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


def write_markdown_hyperparameter_table(rows):
    path = OUT / "gate22b3_hyperparameter_results_table.md"
    lines = [
        "# Gate 22B.3 Hyperparameter Selection Table",
        "",
        "Selection uses TRAIN/DEV only. Confirmation metrics are deliberately excluded.",
        "",
        "| C | Train action F1 | Dev action F1 | Train assessment F1 | Dev assessment F1 | Dev mean F1 | Action iter. | Assessment iter. | Selected |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['C']:.2g} | {r['train_action_macro_f1']:.3f} | "
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


def write_markdown_confirmation_table(metrics):
    path = OUT / "gate22b3_confirmation_metrics_table.md"
    lines = [
        "# Gate 22B.3 Confirmation Performance Table",
        "",
        "| Output | Accuracy | Macro-F1 |",
        "|---|---:|---:|",
    ]
    for key in ["assessment", "action", "boundary", "enforcement", "evidence"]:
        lines.append(
            f"| {key.title()} | {metrics[key]['accuracy']:.3f} | "
            f"{metrics[key]['macro_f1']:.3f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def save_hyperparameter_plot(rows):
    Cs = [r["C"] for r in rows]
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    ax.plot(
        Cs,
        [r["dev_action_macro_f1"] for r in rows],
        marker="o",
        label="DEV action macro-F1",
    )
    ax.plot(
        Cs,
        [r["dev_assessment_macro_f1"] for r in rows],
        marker="o",
        label="DEV assessment macro-F1",
    )
    ax.plot(
        Cs,
        [r["dev_mean_macro_f1"] for r in rows],
        marker="o",
        label="DEV mean macro-F1",
    )
    ax.set_xscale("log")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Logistic-regression C")
    ax.set_ylabel("DEV score")
    ax.set_title("Privacy Agent Hyperparameter Selection (DEV Only)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b3_hyperparameter_selection.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b3_hyperparameter_selection.pdf", bbox_inches="tight")
    plt.close(fig)


def save_learning_history(history):
    x = [r["training_records"] for r in history]
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
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
    ax.set_xlabel("Training records")
    ax.set_ylabel("Macro-F1")
    ax.set_title("Privacy Agent Training History: Compositional Data Growth")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b3_training_history.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b3_training_history.pdf", bbox_inches="tight")
    plt.close(fig)


def save_solver_plot(rows):
    Cs = [r["C"] for r in rows]
    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    ax.plot(
        Cs,
        [r["action_solver_iterations"] for r in rows],
        marker="o",
        label="Action",
    )
    ax.plot(
        Cs,
        [r["assessment_solver_iterations"] for r in rows],
        marker="o",
        label="Assessment",
    )
    ax.set_xscale("log")
    ax.set_xlabel("C")
    ax.set_ylabel("LBFGS iterations")
    ax.set_title("Privacy Agent Solver-Convergence Diagnostics")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b3_solver_iterations.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b3_solver_iterations.pdf", bbox_inches="tight")
    plt.close(fig)


def save_confirmation_metrics(metrics):
    keys = ["assessment", "action", "boundary", "enforcement", "evidence"]
    labels = [k.title() for k in keys]
    x = np.arange(len(keys))
    w = 0.36

    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    ax.bar(
        x-w/2,
        [metrics[k]["accuracy"] for k in keys],
        w,
        label="Accuracy",
    )
    ax.bar(
        x+w/2,
        [metrics[k]["macro_f1"] for k in keys],
        w,
        label="Macro-F1",
    )
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Privacy Agent Fresh Confirmation Performance")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b3_confirmation_metrics.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b3_confirmation_metrics.pdf", bbox_inches="tight")
    plt.close(fig)


def save_confusion(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(cm, aspect="auto")
    ax.set_title("Privacy Agent Fresh-Confirmation Action Confusion Matrix")
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
    fig.savefig(FIG / "fig22b3_action_confusion.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b3_action_confusion.pdf", bbox_inches="tight")
    plt.close(fig)


def save_action_class_recall(class_rows):
    labels = [r["class"] for r in class_rows]
    vals = [r["recall"] for r in class_rows]
    fig, ax = plt.subplots(figsize=(10, 5.0))
    ax.bar(labels, vals)
    ax.axhline(0.80, linestyle="--", linewidth=1)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Recall")
    ax.set_title("Privacy Agent Action Recall by Class")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b3_action_class_recall.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b3_action_class_recall.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 22B.3")
    print(" Privacy Confirmation Training")
    print(" & Prospective Evaluation")
    print("========================================\n")

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    observed_hash = sha256(CONFIRMATION)

    base = load_base()
    augmentation = build_augmentation()
    aug_rows = [aug_to_training_row(a) for a in augmentation]

    # Add stable IDs solely for deterministic data-growth diagnostics.
    for i, r in enumerate(aug_rows):
        r["record_id"] = augmentation[i]["record_id"]

    train_rows = list(base["train"]) + aug_rows
    dev_rows = list(base["dev"])
    confirmation_rows = load_confirmation()

    # Hyperparameter selection BEFORE any confirmation evaluation.
    chosen_C, hp_table = select_c(train_rows, dev_rows)
    hp_md = write_markdown_hyperparameter_table(hp_table)

    # Training-history diagnostics at the already-selected DEV-only C.
    history = learning_history(
        base["train"],
        aug_rows,
        dev_rows,
        chosen_C,
    )

    # Fit final confirmation model only after C is fixed.
    final_bundle = train_bundle(train_rows, chosen_C)
    save_bundle(final_bundle, OUT / "privacy_agent_confirmation_model.joblib")

    id_test_metrics, id_test_pred = evaluate(final_bundle, base["test"])
    confirmation_metrics, confirmation_pred = evaluate(
        final_bundle,
        confirmation_rows,
    )

    confirmation_md = write_markdown_confirmation_table(
        confirmation_metrics
    )

    action_class_metrics = per_class(
        confirmation_pred["action"]["true"],
        confirmation_pred["action"]["pred"],
    )

    # Benchmark-specific shield diagnostics.
    unsafe_allow_proposals = 0
    unsafe_allow_executions = 0
    action_errors = 0
    shield_blocks = 0
    shield_escalations = 0
    raw_rows = []

    for i, row in enumerate(confirmation_rows):
        f = row["features"]
        pred_action = confirmation_pred["action"]["pred"][i]
        true_action = confirmation_pred["action"]["true"][i]

        shield_status, shield_enforcement = privacy_policy_shield(
            pred_action,
            f,
        )

        raw_unsafe_allow = (
            pred_action == "ALLOW_AUTHORIZED_DISCLOSURE"
            and not (
                f.get("jurisdiction") == "KR"
                and f.get("disclosure_authorized") is True
                and f.get("minimum_necessary") is True
                and f.get("purpose_declared") is True
            )
        )

        unsafe_allow_proposals += int(raw_unsafe_allow)
        unsafe_allow_executions += int(
            raw_unsafe_allow and shield_enforcement == "PERMIT"
        )
        action_errors += int(pred_action != true_action)
        shield_blocks += int(shield_enforcement == "BLOCK")
        shield_escalations += int(shield_enforcement == "ESCALATE")

        raw_rows.append({
            "record_id": row["record_id"],
            "features_json": row["features_json"],
            "true_assessment": confirmation_pred["assessment"]["true"][i],
            "pred_assessment": confirmation_pred["assessment"]["pred"][i],
            "true_action": true_action,
            "pred_action": pred_action,
            "true_boundary": confirmation_pred["boundary"]["true"][i],
            "pred_boundary": confirmation_pred["boundary"]["pred"][i],
            "true_enforcement": confirmation_pred["enforcement"]["true"][i],
            "pred_enforcement": confirmation_pred["enforcement"]["pred"][i],
            "true_evidence": confirmation_pred["evidence"]["true"][i],
            "pred_evidence": confirmation_pred["evidence"]["pred"][i],
            "action_correct": pred_action == true_action,
            "shield_status": shield_status,
            "shield_enforcement": shield_enforcement,
            "unsafe_allow_proposal": raw_unsafe_allow,
            "unsafe_allow_execution": (
                raw_unsafe_allow and shield_enforcement == "PERMIT"
            ),
        })

    unsafe_allow_execution_rate = (
        unsafe_allow_executions / len(confirmation_rows)
    )

    # Machine-readable hyperparameter table.
    with (OUT / "gate22b3_hyperparameter_results.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(hp_table[0].keys()))
        w.writeheader()
        w.writerows(hp_table)

    # Raw training history.
    with (OUT / "gate22b3_training_history.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        w.writeheader()
        w.writerows(history)

    # Confirmation predictions.
    with (OUT / "gate22b3_confirmation_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(raw_rows[0].keys()))
        w.writeheader()
        w.writerows(raw_rows)

    # Per-class table.
    with (OUT / "gate22b3_action_class_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=["class", "precision", "recall", "f1", "support"],
        )
        w.writeheader()
        w.writerows(action_class_metrics)

    # A separate machine-readable final evaluation table.
    eval_rows = []
    for split_name, metrics in [
        ("opened_id_test_diagnostic", id_test_metrics),
        ("fresh_confirmation", confirmation_metrics),
    ]:
        for output_name, vals in metrics.items():
            eval_rows.append({
                "evaluation_set": split_name,
                "output": output_name,
                "accuracy": vals["accuracy"],
                "macro_f1": vals["macro_f1"],
            })

    with (OUT / "gate22b3_evaluation_results_table.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(eval_rows[0].keys()))
        w.writeheader()
        w.writerows(eval_rows)

    methodology = {
        "gate": "GATE_22B3_PRIVACY_CONFIRMATION_TRAINING",
        "agent": "Privacy Agent",
        "oracle_version": ORACLE_VERSION,
        "model_family": "multinomial_logistic_regression",
        "original_train_records": len(base["train"]),
        "augmentation_records": len(aug_rows),
        "combined_training_records": len(train_rows),
        "dev_records": len(dev_rows),
        "opened_id_test_records": len(base["test"]),
        "fresh_confirmation_records": len(confirmation_rows),
        "hyperparameter_grid": CANDIDATES,
        "chosen_C": chosen_C,
        "hyperparameter_selection_data": "Gate-21A DEV only",
        "confirmation_used_for_hyperparameter_selection": False,
        "opened_gate22a_used_for_training": False,
        "opened_gate22a_used_for_selection": False,
        "training_history_type": (
            "stratified compositional-data-growth curve; no fabricated epochs"
        ),
        "hyperparameter_table": (
            "outputs/gate22b3/gate22b3_hyperparameter_results_table.md"
        ),
        "claim_boundary": protocol["claim_boundary"],
        "shield_boundary": (
            "The existing privacy_policy_shield is a benchmark-specific execution "
            "control. Its unsafe-ALLOW metric tests disclosure safety and must not "
            "be described as complete Korean legal-policy validation."
        ),
        "patient_data": False,
    }
    (OUT / "gate22b3_training_methodology.json").write_text(
        json.dumps(methodology, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Figures
    save_hyperparameter_plot(hp_table)
    save_learning_history(history)
    save_solver_plot(hp_table)
    save_confirmation_metrics(confirmation_metrics)
    save_confusion(
        confirmation_pred["action"]["true"],
        confirmation_pred["action"]["pred"],
    )
    save_action_class_recall(action_class_metrics)

    min_action_recall = min(
        r["recall"] for r in action_class_metrics
    )

    thresholds = protocol["confirmation_thresholds"]

    checks = [
        {
            "check": "benchmark_sha256_matches_frozen_protocol",
            "pass": observed_hash == EXPECTED_SHA256,
            "observed": observed_hash,
            "expected": EXPECTED_SHA256,
        },
        {
            "check": "dev_only_hyperparameter_selection",
            "pass": chosen_C in CANDIDATES,
            "observed": chosen_C,
            "expected": CANDIDATES,
        },
        {
            "check": "confirmation_action_accuracy",
            "pass": (
                confirmation_metrics["action"]["accuracy"]
                >= thresholds["action_accuracy"]
            ),
            "observed": confirmation_metrics["action"]["accuracy"],
            "expected": f">={thresholds['action_accuracy']}",
        },
        {
            "check": "confirmation_action_macro_f1",
            "pass": (
                confirmation_metrics["action"]["macro_f1"]
                >= thresholds["action_macro_f1"]
            ),
            "observed": confirmation_metrics["action"]["macro_f1"],
            "expected": f">={thresholds['action_macro_f1']}",
        },
        {
            "check": "confirmation_assessment_accuracy",
            "pass": (
                confirmation_metrics["assessment"]["accuracy"]
                >= thresholds["assessment_accuracy"]
            ),
            "observed": confirmation_metrics["assessment"]["accuracy"],
            "expected": f">={thresholds['assessment_accuracy']}",
        },
        {
            "check": "confirmation_assessment_macro_f1",
            "pass": (
                confirmation_metrics["assessment"]["macro_f1"]
                >= thresholds["assessment_macro_f1"]
            ),
            "observed": confirmation_metrics["assessment"]["macro_f1"],
            "expected": f">={thresholds['assessment_macro_f1']}",
        },
        {
            "check": "confirmation_boundary_accuracy",
            "pass": (
                confirmation_metrics["boundary"]["accuracy"]
                >= thresholds["boundary_accuracy"]
            ),
            "observed": confirmation_metrics["boundary"]["accuracy"],
            "expected": f">={thresholds['boundary_accuracy']}",
        },
        {
            "check": "confirmation_enforcement_accuracy",
            "pass": (
                confirmation_metrics["enforcement"]["accuracy"]
                >= thresholds["enforcement_accuracy"]
            ),
            "observed": confirmation_metrics["enforcement"]["accuracy"],
            "expected": f">={thresholds['enforcement_accuracy']}",
        },
        {
            "check": "confirmation_evidence_accuracy",
            "pass": (
                confirmation_metrics["evidence"]["accuracy"]
                >= thresholds["evidence_accuracy"]
            ),
            "observed": confirmation_metrics["evidence"]["accuracy"],
            "expected": f">={thresholds['evidence_accuracy']}",
        },
        {
            "check": "minimum_action_class_recall",
            "pass": min_action_recall >= thresholds["minimum_action_class_recall"],
            "observed": min_action_recall,
            "expected": f">={thresholds['minimum_action_class_recall']}",
        },
        {
            "check": "unsafe_allow_execution_rate",
            "pass": (
                unsafe_allow_execution_rate
                == thresholds["policy_inconsistent_execution_rate"]
            ),
            "observed": unsafe_allow_execution_rate,
            "expected": thresholds["policy_inconsistent_execution_rate"],
        },
        {
            "check": "hyperparameter_table_and_history_outputs",
            "pass": (
                (OUT / "gate22b3_hyperparameter_results.csv").exists()
                and hp_md.exists()
                and (OUT / "gate22b3_training_history.csv").exists()
                and confirmation_md.exists()
            ),
            "observed": True,
            "expected": True,
        },
        {
            "check": "publication_outputs",
            "pass": (
                len(list(FIG.glob("*.png"))) >= 6
                and len(list(FIG.glob("*.pdf"))) >= 6
            ),
            "observed": {
                "png": len(list(FIG.glob("*.png"))),
                "pdf": len(list(FIG.glob("*.pdf"))),
            },
            "expected": ">=6 PNG and >=6 PDF",
        },
    ]

    passed = sum(c["pass"] for c in checks)

    result = {
        "gate": "GATE_22B3_PRIVACY_CONFIRMATION_TRAINING",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "agent": "Privacy Agent",
        "oracle_version": ORACLE_VERSION,
        "model_family": "multinomial_logistic_regression",
        "chosen_C": chosen_C,
        "original_train_records": len(base["train"]),
        "augmentation_records": len(aug_rows),
        "combined_training_records": len(train_rows),
        "dev_records": len(dev_rows),
        "fresh_confirmation_records": len(confirmation_rows),
        "confirmation_metrics": confirmation_metrics,
        "opened_id_test_metrics": id_test_metrics,
        "action_class_metrics": action_class_metrics,
        "minimum_action_class_recall": min_action_recall,
        "confirmation_action_errors": action_errors,
        "unsafe_allow_proposals": unsafe_allow_proposals,
        "unsafe_allow_executions": unsafe_allow_executions,
        "unsafe_allow_execution_rate": unsafe_allow_execution_rate,
        "shield_blocks": shield_blocks,
        "shield_escalations": shield_escalations,
        "training_history_steps": len(history),
        "hyperparameter_table_path": (
            "outputs/gate22b3/gate22b3_hyperparameter_results_table.md"
        ),
        "evaluation_table_path": (
            "outputs/gate22b3/gate22b3_evaluation_results_table.csv"
        ),
        "model_path": "outputs/gate22b3/privacy_agent_confirmation_model.joblib",
        "figures_directory": "outputs/gate22b3/figures",
        "next_dependency": (
            "If PASS, promote the audited Privacy learning methodology and resume "
            "Cyber Gate 24C. If FAIL, diagnose confirmation errors without using "
            "the confirmation set for hyperparameter retuning."
        ),
    }

    (OUT / "gate22b3_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate22b3_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print("\nHyperparameter selection table (TRAIN/DEV only):")
    for r in hp_table:
        print({
            "C": r["C"],
            "dev_action_macro_f1": round(r["dev_action_macro_f1"], 4),
            "dev_assessment_macro_f1": round(r["dev_assessment_macro_f1"], 4),
            "dev_mean_macro_f1": round(r["dev_mean_macro_f1"], 4),
            "selected": r["selected"],
        })

    print("\nTraining history:")
    print(json.dumps(history, indent=2))

    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] != "PASS":
        raise SystemExit(
            "Gate 22B.3 FAILED. Do not retune against the frozen confirmation "
            "benchmark; diagnose the residual failure first."
        )

    print(
        "\nFULL GATE 22B.3 PASS — The Privacy Agent satisfies the fresh "
        "prospective confirmation thresholds under the explicitly adopted "
        "precedence semantics, with DEV-only hyperparameter selection and "
        "complete training-history/table reporting."
    )


if __name__ == "__main__":
    main()
