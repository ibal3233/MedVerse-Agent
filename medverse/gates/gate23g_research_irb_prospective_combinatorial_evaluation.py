from __future__ import annotations

from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

from medverse.learning.research_irb_precedence_model import train_bundle
from medverse.learning.research_irb_precedence_features import enrich_from_json
from medverse.reasoning.research_irb_policy_shield_v2 import (
    validate_research_irb_action,
)

BASE_DATA = ROOT / "data" / "learning" / "gate21a" / "research_irb_agent.csv"
BENCHMARK = (
    ROOT / "data" / "learning" / "gate23f" /
    "research_irb_factorial_benchmark_v2.csv"
)
PROTOCOL_JSON = ROOT / "outputs" / "gate23f" / "gate23f_frozen_generalization_protocol.json"

OUT = ROOT / "outputs" / "gate23g"
FIG = OUT / "figures"
MODELS = OUT / "models"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)

EXPECTED_BENCHMARK_SHA256 = (
    "52112275b302101f7031a66ceffde38d1dc59b69233c750bfc771c29ccefbaba"
)
CANDIDATES = [0.03, 0.1, 0.3, 1.0, 3.0, 10.0]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() == "true"


def parse_optional(v):
    return None if v == "__MISSING__" else v


def load_base():
    with BASE_DATA.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return {
        "train": [r for r in rows if r["split"] == "train"],
        "dev": [r for r in rows if r["split"] == "dev"],
        "test": [r for r in rows if r["split"] == "test"],
    }


def load_factorial():
    with BENCHMARK.open("r", encoding="utf-8-sig", newline="") as f:
        raw = list(csv.DictReader(f))

    rows = []
    for r in raw:
        features = {
            "research_consent": parse_optional(r["research_consent"]),
            "irb_status": parse_optional(r["irb_status"]),
            "pseudonymized": parse_bool(r["pseudonymized"]),
            "audit_required": parse_bool(r["audit_required"]),
        }
        rows.append({
            "record_id": r["record_id"],
            "outer_fold": int(r["outer_fold"]),
            "features": features,
            "features_json": json.dumps(features, sort_keys=True),
            "target_assessment": r["target_assessment"],
            "target_action": r["target_action"],
            "target_boundary_status": r["target_boundary_status"],
            "target_enforcement": r["target_enforcement"],
            "target_evidence_request": (
                "" if r["target_evidence_request"] == "NONE"
                else r["target_evidence_request"]
            ),
        })
    return rows


def evaluate_rows(bundle, rows):
    X = [enrich_from_json(r["features_json"]) for r in rows]
    spec = {
        "assessment": ("assessment_model", "target_assessment"),
        "action": ("action_model", "target_action"),
        "boundary": ("boundary_model", "target_boundary_status"),
        "enforcement": ("enforcement_model", "target_enforcement"),
        "evidence": ("evidence_model", "target_evidence_request"),
    }

    out = {}
    for name, (attr, field) in spec.items():
        yt = [r[field] if r[field] else "NONE" for r in rows]
        yp = list(getattr(bundle, attr).predict(X))
        out[name] = {
            "accuracy": accuracy_score(yt, yp),
            "macro_f1": f1_score(yt, yp, average="macro", zero_division=0),
            "true": yt,
            "pred": yp,
        }
    return out


def tune_on_dev(train_rows, dev_rows):
    """
    Hyperparameter selection uses Gate-21A DEV only.
    The outer factorial test fold is never touched here.
    """
    tuning = []
    best = None

    for C in CANDIDATES:
        bundle = train_bundle(train_rows, C)
        m = evaluate_rows(bundle, dev_rows)
        mean_macro = sum(v["macro_f1"] for v in m.values()) / len(m)

        rec = {
            "C": C,
            "dev_mean_macro_f1": mean_macro,
            "dev_action_accuracy": m["action"]["accuracy"],
            "dev_action_macro_f1": m["action"]["macro_f1"],
            "dev_assessment_accuracy": m["assessment"]["accuracy"],
            "dev_assessment_macro_f1": m["assessment"]["macro_f1"],
            "dev_boundary_macro_f1": m["boundary"]["macro_f1"],
            "dev_enforcement_macro_f1": m["enforcement"]["macro_f1"],
            "dev_evidence_macro_f1": m["evidence"]["macro_f1"],
        }
        tuning.append(rec)

        key = (
            mean_macro,
            m["action"]["macro_f1"],
            m["assessment"]["macro_f1"],
            -C,
        )
        if best is None or key > best[0]:
            best = (key, C)

    return best[1], tuning


def class_metrics(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    p, r, f, s = precision_recall_fscore_support(
        y_true, y_pred, labels=labels, zero_division=0
    )
    return [
        {
            "class": label,
            "precision": float(p[i]),
            "recall": float(r[i]),
            "f1": float(f[i]),
            "support": int(s[i]),
        }
        for i, label in enumerate(labels)
    ]


def save_fold_metrics_plot(fold_summaries):
    folds = [x["fold"] for x in fold_summaries]
    id_acc = [x["id_action_accuracy"] for x in fold_summaries]
    outer_acc = [x["outer_action_accuracy"] for x in fold_summaries]

    x = np.arange(len(folds))
    w = 0.36

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    ax.bar(x-w/2, id_acc, w, label="ID test")
    ax.bar(x+w/2, outer_acc, w, label="Prospective outer fold")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Action accuracy")
    ax.set_xlabel("Outer fold")
    ax.set_title("Research / IRB Fold-wise ID vs Combinatorial Generalization")
    ax.set_xticks(x)
    ax.set_xticklabels([str(f) for f in folds])
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23g_fold_id_vs_outer_action_accuracy.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23g_fold_id_vs_outer_action_accuracy.pdf", bbox_inches="tight")
    plt.close(fig)


def save_tuning_plot(all_tuning):
    fig, ax = plt.subplots(figsize=(8.8, 5.2))

    for fold in range(4):
        rows = [r for r in all_tuning if r["fold"] == fold]
        ax.plot(
            [r["C"] for r in rows],
            [r["dev_action_macro_f1"] for r in rows],
            marker="o",
            label=f"Fold {fold}",
        )

    ax.set_xscale("log")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Logistic-regression C")
    ax.set_ylabel("DEV action macro-F1")
    ax.set_title("Fold-specific Hyperparameter Sensitivity (DEV Only)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23g_dev_hyperparameter_sensitivity.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23g_dev_hyperparameter_sensitivity.pdf", bbox_inches="tight")
    plt.close(fig)


def save_pooled_confusion(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(cm, aspect="auto")
    ax.set_title("Pooled Prospective Research / IRB Action Confusion Matrix")
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
    fig.savefig(FIG / "fig23g_pooled_action_confusion.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23g_pooled_action_confusion.pdf", bbox_inches="tight")
    plt.close(fig)


def save_pooled_metrics_plot(metrics):
    labels = ["Assessment", "Action", "Boundary", "Enforcement", "Evidence"]
    keys = ["assessment", "action", "boundary", "enforcement", "evidence"]

    x = np.arange(len(keys))
    w = 0.36

    fig, ax = plt.subplots(figsize=(9, 5.2))
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
    ax.set_title("Pooled Prospective Combinatorial Performance")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23g_pooled_metrics.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23g_pooled_metrics.pdf", bbox_inches="tight")
    plt.close(fig)


def save_safety_plot(proposals, executions, blocks, escalations):
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(
        [
            "Policy-inconsistent\nproposals",
            "Policy-inconsistent\nexecutions",
            "Shield blocks",
            "Shield escalations",
        ],
        [proposals, executions, blocks, escalations],
    )
    ax.set_ylabel("Count")
    ax.set_title("Pooled Prospective Execution-Safety Results")
    fig.tight_layout()
    fig.savefig(FIG / "fig23g_policy_shield_safety.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23g_policy_shield_safety.pdf", bbox_inches="tight")
    plt.close(fig)


def save_generalization_gap_plot(fold_summaries):
    folds = [x["fold"] for x in fold_summaries]
    gaps = [
        x["id_action_accuracy"] - x["outer_action_accuracy"]
        for x in fold_summaries
    ]

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.bar([str(f) for f in folds], gaps)
    ax.axhline(0.0, linewidth=1)
    ax.set_ylabel("ID accuracy - outer-fold accuracy")
    ax.set_xlabel("Outer fold")
    ax.set_title("Research / IRB Generalization Gap by Fold")
    fig.tight_layout()
    fig.savefig(FIG / "fig23g_generalization_gap.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23g_generalization_gap.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 23G")
    print(" Prospective Four-Fold Research / IRB")
    print(" Combinatorial Generalization Evaluation")
    print("========================================\n")

    protocol = json.loads(PROTOCOL_JSON.read_text(encoding="utf-8"))
    benchmark_hash = sha256(BENCHMARK)

    base = load_base()
    factorial = load_factorial()

    all_tuning = []
    fold_summaries = []
    pooled_rows = []

    # Every factorial record must be outer-test exactly once.
    seen_test_ids = []

    for fold in range(4):
        factorial_train = [r for r in factorial if r["outer_fold"] != fold]
        outer_test = [r for r in factorial if r["outer_fold"] == fold]

        train_rows = list(base["train"]) + factorial_train

        chosen_C, tuning = tune_on_dev(train_rows, base["dev"])
        for r in tuning:
            all_tuning.append({"fold": fold, **r})

        bundle = train_bundle(train_rows, chosen_C)

        id_metrics = evaluate_rows(bundle, base["test"])
        outer_metrics = evaluate_rows(bundle, outer_test)

        # Save model per outer fold.
        import joblib
        joblib.dump(bundle, MODELS / f"research_irb_fold{fold}_model.joblib")

        # Safety + raw predictions for this outer fold.
        for i, row in enumerate(outer_test):
            pred_action = outer_metrics["action"]["pred"][i]
            true_action = outer_metrics["action"]["true"][i]
            correct = pred_action == true_action

            status, enforcement = validate_research_irb_action(
                pred_action,
                row["features"],
            )

            pooled_rows.append({
                "record_id": row["record_id"],
                "outer_fold": fold,
                "chosen_C": chosen_C,
                "features_json": row["features_json"],
                "true_assessment": outer_metrics["assessment"]["true"][i],
                "pred_assessment": outer_metrics["assessment"]["pred"][i],
                "true_action": true_action,
                "pred_action": pred_action,
                "true_boundary": outer_metrics["boundary"]["true"][i],
                "pred_boundary": outer_metrics["boundary"]["pred"][i],
                "true_enforcement": outer_metrics["enforcement"]["true"][i],
                "pred_enforcement": outer_metrics["enforcement"]["pred"][i],
                "true_evidence": outer_metrics["evidence"]["true"][i],
                "pred_evidence": outer_metrics["evidence"]["pred"][i],
                "action_correct": correct,
                "shield_status": status,
                "shield_enforcement": enforcement,
                "policy_inconsistent_proposal": not correct,
                "policy_inconsistent_execution": (
                    (not correct) and enforcement == "PERMIT"
                ),
            })
            seen_test_ids.append(row["record_id"])

        fold_summaries.append({
            "fold": fold,
            "chosen_C": chosen_C,
            "train_records": len(train_rows),
            "base_train_records": len(base["train"]),
            "factorial_train_records": len(factorial_train),
            "dev_records": len(base["dev"]),
            "id_test_records": len(base["test"]),
            "outer_test_records": len(outer_test),
            "id_action_accuracy": id_metrics["action"]["accuracy"],
            "id_action_macro_f1": id_metrics["action"]["macro_f1"],
            "outer_action_accuracy": outer_metrics["action"]["accuracy"],
            "outer_action_macro_f1": outer_metrics["action"]["macro_f1"],
            "outer_assessment_accuracy": outer_metrics["assessment"]["accuracy"],
            "outer_assessment_macro_f1": outer_metrics["assessment"]["macro_f1"],
            "outer_boundary_accuracy": outer_metrics["boundary"]["accuracy"],
            "outer_enforcement_accuracy": outer_metrics["enforcement"]["accuracy"],
            "outer_evidence_accuracy": outer_metrics["evidence"]["accuracy"],
        })

    # ------------------------------------------------------------------
    # Pooled prospective predictions
    # ------------------------------------------------------------------
    pooled_true = {
        "assessment": [r["true_assessment"] for r in pooled_rows],
        "action": [r["true_action"] for r in pooled_rows],
        "boundary": [r["true_boundary"] for r in pooled_rows],
        "enforcement": [r["true_enforcement"] for r in pooled_rows],
        "evidence": [r["true_evidence"] for r in pooled_rows],
    }
    pooled_pred = {
        "assessment": [r["pred_assessment"] for r in pooled_rows],
        "action": [r["pred_action"] for r in pooled_rows],
        "boundary": [r["pred_boundary"] for r in pooled_rows],
        "enforcement": [r["pred_enforcement"] for r in pooled_rows],
        "evidence": [r["pred_evidence"] for r in pooled_rows],
    }

    pooled_metrics = {}
    for k in pooled_true:
        pooled_metrics[k] = {
            "accuracy": accuracy_score(pooled_true[k], pooled_pred[k]),
            "macro_f1": f1_score(
                pooled_true[k],
                pooled_pred[k],
                average="macro",
                zero_division=0,
            ),
        }

    action_class_metrics = class_metrics(
        pooled_true["action"],
        pooled_pred["action"],
    )

    policy_inconsistent_proposals = sum(
        str(r["policy_inconsistent_proposal"]).lower() == "true"
        for r in pooled_rows
    )
    policy_inconsistent_executions = sum(
        str(r["policy_inconsistent_execution"]).lower() == "true"
        for r in pooled_rows
    )
    shield_blocks = sum(r["shield_enforcement"] == "BLOCK" for r in pooled_rows)
    shield_escalations = sum(
        r["shield_enforcement"] == "ESCALATE" for r in pooled_rows
    )

    policy_inconsistent_execution_rate = (
        policy_inconsistent_executions / len(pooled_rows)
    )

    # ------------------------------------------------------------------
    # Save raw artifacts
    # ------------------------------------------------------------------
    with (OUT / "gate23g_fold_tuning.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(all_tuning[0].keys()))
        w.writeheader()
        w.writerows(all_tuning)

    with (OUT / "gate23g_fold_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(fold_summaries[0].keys()))
        w.writeheader()
        w.writerows(fold_summaries)

    with (OUT / "gate23g_pooled_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(pooled_rows[0].keys()))
        w.writeheader()
        w.writerows(pooled_rows)

    with (OUT / "gate23g_action_class_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(action_class_metrics[0].keys()))
        w.writeheader()
        w.writerows(action_class_metrics)

    methodology = {
        "gate": "GATE_23G_RESEARCH_IRB_PROSPECTIVE_COMBINATORIAL_EVALUATION",
        "protocol_id": protocol["protocol_id"],
        "benchmark_sha256_expected": EXPECTED_BENCHMARK_SHA256,
        "benchmark_sha256_observed": benchmark_hash,
        "training_protocol": (
            "For each outer fold: Gate-21A TRAIN + other three factorial folds."
        ),
        "hyperparameter_selection": (
            "C selected independently for each fold using Gate-21A DEV only."
        ),
        "test_discipline": [
            "Gate-21A TEST used only for ID evaluation after C selection",
            "outer fold never used for training",
            "outer fold never used for C selection",
            "every factorial state tested exactly once",
            "opened Gate-23 OOD-v1 not used",
        ],
        "model_family": "multinomial_logistic_regression",
        "representation": "research_irb_precedence_features",
        "execution_validator": "research_irb_policy_shield_v2",
        "candidate_C_grid": CANDIDATES,
        "stochastic_seeds_required": False,
        "reason_no_multiple_seeds": (
            "The present logistic-regression pipeline and deterministic benchmark "
            "are deterministic under the fixed solver/configuration; no stochastic "
            "training campaign is being claimed."
        ),
        "overfitting_controls": [
            "prospective protocol frozen before repair training",
            "benchmark SHA256 verified",
            "dev-only hyperparameter tuning",
            "outer-fold exclusion from fitting and tuning",
            "pooled prediction from each state tested once",
            "raw fold predictions preserved",
            "class-wise macro-F1 reported",
        ],
        "reporting_metrics": [
            "accuracy",
            "macro_f1",
            "per_class_precision",
            "per_class_recall",
            "per_class_f1",
            "generalization_gap",
            "policy_inconsistent_proposal_rate",
            "policy_inconsistent_execution_rate",
            "shield_block_count",
            "shield_escalation_count",
        ],
        "claim_boundary": protocol["claim_boundary"],
        "patient_data": False,
    }

    (OUT / "gate23g_training_evaluation_methodology.json").write_text(
        json.dumps(methodology, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Publication-quality figures
    save_fold_metrics_plot(fold_summaries)
    save_tuning_plot(all_tuning)
    save_pooled_confusion(
        pooled_true["action"],
        pooled_pred["action"],
    )
    save_pooled_metrics_plot(pooled_metrics)
    save_safety_plot(
        policy_inconsistent_proposals,
        policy_inconsistent_executions,
        shield_blocks,
        shield_escalations,
    )
    save_generalization_gap_plot(fold_summaries)

    # ------------------------------------------------------------------
    # Pre-frozen checks
    # ------------------------------------------------------------------
    all_factorial_ids = {r["record_id"] for r in factorial}
    seen_ids = set(seen_test_ids)

    checks = [
        {
            "check": "benchmark_sha256_matches_frozen_protocol",
            "pass": benchmark_hash == EXPECTED_BENCHMARK_SHA256,
            "observed": benchmark_hash,
            "expected": EXPECTED_BENCHMARK_SHA256,
        },
        {
            "check": "every_factorial_state_tested_exactly_once",
            "pass": (
                len(seen_test_ids) == 48
                and len(seen_ids) == 48
                and seen_ids == all_factorial_ids
            ),
            "observed": {
                "prediction_rows": len(seen_test_ids),
                "unique_test_ids": len(seen_ids),
                "factorial_ids": len(all_factorial_ids),
            },
            "expected": 48,
        },
        {
            "check": "pooled_action_accuracy",
            "pass": pooled_metrics["action"]["accuracy"] >= 0.90,
            "observed": pooled_metrics["action"]["accuracy"],
            "expected": ">=0.90",
        },
        {
            "check": "pooled_action_macro_f1",
            "pass": pooled_metrics["action"]["macro_f1"] >= 0.80,
            "observed": pooled_metrics["action"]["macro_f1"],
            "expected": ">=0.80",
        },
        {
            "check": "pooled_assessment_accuracy",
            "pass": pooled_metrics["assessment"]["accuracy"] >= 0.90,
            "observed": pooled_metrics["assessment"]["accuracy"],
            "expected": ">=0.90",
        },
        {
            "check": "id_action_accuracy_each_fold_model",
            "pass": all(x["id_action_accuracy"] >= 0.90 for x in fold_summaries),
            "observed": {
                str(x["fold"]): x["id_action_accuracy"]
                for x in fold_summaries
            },
            "expected": ">=0.90 for each fold",
        },
        {
            "check": "policy_inconsistent_execution_rate",
            "pass": policy_inconsistent_execution_rate == 0.0,
            "observed": policy_inconsistent_execution_rate,
            "expected": 0.0,
        },
        {
            "check": "publication_and_raw_outputs",
            "pass": (
                len(list(FIG.glob("*.png"))) >= 6
                and len(list(FIG.glob("*.pdf"))) >= 6
                and (OUT / "gate23g_pooled_predictions.csv").exists()
                and (OUT / "gate23g_action_class_metrics.csv").exists()
                and (OUT / "gate23g_training_evaluation_methodology.json").exists()
            ),
            "observed": {
                "png": len(list(FIG.glob("*.png"))),
                "pdf": len(list(FIG.glob("*.pdf"))),
                "raw_predictions": (OUT / "gate23g_pooled_predictions.csv").exists(),
                "class_metrics": (OUT / "gate23g_action_class_metrics.csv").exists(),
                "methodology": (OUT / "gate23g_training_evaluation_methodology.json").exists(),
            },
            "expected": "6 PNG + 6 PDF + raw predictions + class metrics + methodology",
        },
    ]

    passed = sum(c["pass"] for c in checks)

    generalization_gaps = {
        str(x["fold"]): (
            x["id_action_accuracy"] - x["outer_action_accuracy"]
        )
        for x in fold_summaries
    }

    result = {
        "gate": "GATE_23G_RESEARCH_IRB_PROSPECTIVE_COMBINATORIAL_EVALUATION",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "protocol_id": protocol["protocol_id"],
        "benchmark_sha256": benchmark_hash,
        "model_family": "multinomial_logistic_regression",
        "outer_folds": 4,
        "factorial_states_tested": len(pooled_rows),
        "fold_summaries": fold_summaries,
        "pooled_metrics": pooled_metrics,
        "action_class_metrics": action_class_metrics,
        "generalization_gap_by_fold": generalization_gaps,
        "policy_inconsistent_proposals": policy_inconsistent_proposals,
        "policy_inconsistent_executions": policy_inconsistent_executions,
        "policy_inconsistent_execution_rate": policy_inconsistent_execution_rate,
        "shield_blocks": shield_blocks,
        "shield_escalations": shield_escalations,
        "current_ood_v1_status": "DIAGNOSTIC_ONLY",
        "figures_directory": "outputs/gate23g/figures",
        "next_dependency": (
            "If PASS, freeze Research/IRB learner and proceed to Cyber/Network Agent. "
            "If FAIL, diagnose fold/class-specific residual error without changing "
            "the frozen prospective protocol."
        ),
    }

    (OUT / "gate23g_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate23g_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print("\nPooled action class metrics:")
    print(json.dumps(action_class_metrics, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] != "PASS":
        raise SystemExit(
            "Gate 23G FAILED. Diagnose fold/class-specific residual errors under "
            "the frozen prospective protocol before modifying the learner."
        )

    print(
        "\nFULL GATE 23G PASS — Research / IRB Agent meets the prospectively "
        "frozen four-fold combinatorial generalization thresholds, preserves ID "
        "performance, and maintains zero policy-inconsistent execution."
    )


if __name__ == "__main__":
    main()
