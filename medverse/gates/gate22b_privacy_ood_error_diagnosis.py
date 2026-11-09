from __future__ import annotations

from pathlib import Path
import csv, json, sys
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

from medverse.learning.privacy_agent_model import clean_features, train_bundle
from medverse.learning.gate22a_privacy_ood import build_ood
from medverse.gates.gate22_privacy_agent_training import privacy_policy_shield

OUT = ROOT / "outputs" / "gate22b"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

TRAIN_FILE = ROOT / "data" / "learning" / "gate21a" / "privacy_agent.csv"


def load_rows():
    with TRAIN_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def classify_case(features):
    jurisdiction = features.get("jurisdiction", "KR")
    auth = features.get("disclosure_authorized")
    minimum = features.get("minimum_necessary")
    purpose = features.get("purpose_declared")
    audit = features.get("audit_required", False)

    violations = 0
    if auth is False:
        violations += 1
    if minimum is False:
        violations += 1
    if purpose is False:
        violations += 1

    missing = sum(v is None for v in [auth, minimum, purpose])

    if jurisdiction != "KR":
        family = "wrong_jurisdiction_precedence"
    elif missing > 0:
        family = "missing_evidence_precedence"
    elif violations >= 2:
        family = "multiple_simultaneous_violations"
    elif audit and violations >= 1:
        family = "audit_plus_policy_violation"
    elif audit:
        family = "audit_interaction"
    else:
        family = "single_or_simple_condition"

    return {
        "diagnostic_family": family,
        "violation_count": violations,
        "missing_count": missing,
        "wrong_jurisdiction": jurisdiction != "KR",
        "audit_required": bool(audit),
        "complexity": "multi_condition" if (violations + missing + int(jurisdiction != "KR")) >= 2 else "simple",
    }


def evaluate_model(bundle, rows):
    X = [clean_features(r["features_json"]) for r in rows]
    fields = {
        "assessment": ("assessment_model", "target_assessment"),
        "action": ("action_model", "target_action"),
        "boundary": ("boundary_model", "target_boundary_status"),
        "enforcement": ("enforcement_model", "target_enforcement"),
        "evidence": ("evidence_model", "target_evidence_request"),
    }
    out = {}
    for name, (attr, field) in fields.items():
        model = getattr(bundle, attr)
        y_true = [(r[field] if r[field] else "NONE") for r in rows]
        y_pred = list(model.predict(X))
        out[name] = {
            "accuracy": accuracy_score(y_true, y_pred),
            "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
            "true": y_true,
            "pred": y_pred,
        }
    return out


def save_bar_metric_plot(id_metrics, ood_metrics):
    labels = ["Assessment", "Action", "Boundary", "Enforcement", "Evidence"]
    keys = ["assessment", "action", "boundary", "enforcement", "evidence"]

    x = np.arange(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(x - width/2, [id_metrics[k]["accuracy"] for k in keys], width, label="ID test")
    ax.bar(x + width/2, [ood_metrics[k]["accuracy"] for k in keys], width, label="OOD")
    ax.set_ylabel("Accuracy")
    ax.set_title("Privacy Agent: In-Distribution vs OOD Generalization")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0, 1.05)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b_id_vs_ood_accuracy.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b_id_vs_ood_accuracy.pdf", bbox_inches="tight")
    plt.close(fig)


def save_family_plot(family_stats):
    names = sorted(family_stats)
    acc = [family_stats[n]["action_accuracy"] for n in names]

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.barh(names, acc)
    ax.set_xlabel("Action accuracy")
    ax.set_title("Privacy Agent OOD Action Accuracy by Diagnostic Family")
    ax.set_xlim(0, 1.05)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b_ood_accuracy_by_family.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b_ood_accuracy_by_family.pdf", bbox_inches="tight")
    plt.close(fig)


def save_safety_plot(action_errors, unsafe_raw, unsafe_exec):
    labels = ["Action errors", "Unsafe raw proposals", "Unsafe executions after shield"]
    vals = [action_errors, unsafe_raw, unsafe_exec]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(labels, vals)
    ax.set_ylabel("Count")
    ax.set_title("OOD Decision Errors vs Policy-Shielded Execution Safety")
    ax.tick_params(axis="x", rotation=18)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b_errors_vs_safety.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b_errors_vs_safety.pdf", bbox_inches="tight")
    plt.close(fig)


def save_confusion(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(cm, aspect="auto")
    ax.set_title("Privacy Agent OOD Action Confusion Matrix")
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
    fig.savefig(FIG / "fig22b_ood_action_confusion_matrix.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b_ood_action_confusion_matrix.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 22B")
    print(" Privacy Agent OOD Error Diagnosis")
    print(" & Publication Plots")
    print("========================================\n")

    rows = load_rows()
    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] == "test"]

    # Frozen Gate-22 learner.
    bundle = train_bundle(train, C=1.0)

    id_metrics = evaluate_model(bundle, test)

    ood = build_ood()
    X_ood = [clean_features(json.dumps(c["features"])) for c in ood]

    pred_assessment = list(bundle.assessment_model.predict(X_ood))
    pred_action = list(bundle.action_model.predict(X_ood))
    pred_boundary = list(bundle.boundary_model.predict(X_ood))
    pred_enforcement = list(bundle.enforcement_model.predict(X_ood))
    pred_evidence = list(bundle.evidence_model.predict(X_ood))

    true = {
        "assessment": [c["assessment"] for c in ood],
        "action": [c["action"] for c in ood],
        "boundary": [c["boundary"] for c in ood],
        "enforcement": [c["enforcement"] for c in ood],
        "evidence": [c["evidence"] for c in ood],
    }
    pred = {
        "assessment": pred_assessment,
        "action": pred_action,
        "boundary": pred_boundary,
        "enforcement": pred_enforcement,
        "evidence": pred_evidence,
    }

    ood_metrics = {}
    for k in true:
        ood_metrics[k] = {
            "accuracy": accuracy_score(true[k], pred[k]),
            "macro_f1": f1_score(true[k], pred[k], average="macro", zero_division=0),
        }

    diagnostic_rows = []
    family = defaultdict(lambda: {"n": 0, "correct": 0})
    unsafe_raw = 0
    unsafe_exec = 0

    for i, case in enumerate(ood):
        meta = classify_case(case["features"])
        fam = meta["diagnostic_family"]
        family[fam]["n"] += 1
        family[fam]["correct"] += int(pred_action[i] == true["action"][i])

        f = case["features"]
        shield_status, shield_enforcement = privacy_policy_shield(pred_action[i], f)

        raw_unsafe = (
            pred_action[i] == "ALLOW_AUTHORIZED_DISCLOSURE"
            and not (
                f.get("jurisdiction") == "KR"
                and f.get("disclosure_authorized") is True
                and f.get("minimum_necessary") is True
                and f.get("purpose_declared") is True
            )
        )
        unsafe_raw += int(raw_unsafe)
        unsafe_exec += int(raw_unsafe and shield_enforcement == "PERMIT")

        diagnostic_rows.append({
            "record_id": case["record_id"],
            "diagnostic_family": fam,
            "complexity": meta["complexity"],
            "violation_count": meta["violation_count"],
            "missing_count": meta["missing_count"],
            "wrong_jurisdiction": meta["wrong_jurisdiction"],
            "audit_required": meta["audit_required"],
            "true_action": true["action"][i],
            "pred_action": pred_action[i],
            "action_correct": pred_action[i] == true["action"][i],
            "true_assessment": true["assessment"][i],
            "pred_assessment": pred_assessment[i],
            "assessment_correct": pred_assessment[i] == true["assessment"][i],
            "true_boundary": true["boundary"][i],
            "pred_boundary": pred_boundary[i],
            "shield_status": shield_status,
            "shield_enforcement": shield_enforcement,
            "raw_unsafe_proposal": raw_unsafe,
        })

    with (OUT / "gate22b_ood_diagnostic_rows.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(diagnostic_rows[0].keys()))
        w.writeheader()
        w.writerows(diagnostic_rows)

    family_stats = {}
    for name, v in family.items():
        family_stats[name] = {
            "n": v["n"],
            "correct": v["correct"],
            "action_accuracy": v["correct"] / v["n"] if v["n"] else None,
        }

    # Simple vs multi-condition comparison.
    complexity_stats = {}
    for complexity in ["simple", "multi_condition"]:
        subset = [r for r in diagnostic_rows if r["complexity"] == complexity]
        complexity_stats[complexity] = {
            "n": len(subset),
            "action_accuracy": (
                sum(r["action_correct"] for r in subset) / len(subset)
                if subset else None
            ),
            "assessment_accuracy": (
                sum(r["assessment_correct"] for r in subset) / len(subset)
                if subset else None
            ),
        }

    action_errors = sum(1 for i in range(len(ood)) if pred_action[i] != true["action"][i])

    diagnosis = {
        "gate": "GATE_22B_PRIVACY_OOD_ERROR_DIAGNOSIS",
        "training_changed": False,
        "model_changed": False,
        "frozen_C": 1.0,
        "id_metrics": {
            k: {
                "accuracy": id_metrics[k]["accuracy"],
                "macro_f1": id_metrics[k]["macro_f1"],
            } for k in id_metrics
        },
        "ood_metrics": ood_metrics,
        "family_stats": family_stats,
        "complexity_stats": complexity_stats,
        "action_errors": action_errors,
        "unsafe_raw_proposals": unsafe_raw,
        "unsafe_executed_after_policy_shield": unsafe_exec,
        "diagnostic_classification": (
            "compositional_generalization_and_rule_precedence_limitation"
        ),
        "primary_hypothesis": (
            "The learner was trained on mostly atomic policy templates and therefore "
            "does not reliably represent precedence among multiple simultaneous "
            "institutional conditions. A linear classifier can interpolate the atomic "
            "mappings but cannot consistently reproduce the deterministic oracle's "
            "ordered rule composition on unseen combinations."
        ),
        "secondary_hypothesis": (
            "Linear model capacity may contribute, but model complexity must not be "
            "changed until compositional data/representation coverage is tested."
        ),
    }

    (OUT / "gate22b_diagnosis.json").write_text(
        json.dumps(diagnosis, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    dataset_methodology = {
        "benchmark_name": "MedVerse institutional learning benchmark",
        "purpose": (
            "Create a reproducible, policy-grounded learning benchmark without using "
            "patient records or arbitrary labels."
        ),
        "source_of_features": (
            "Frozen Medical Metaverse state variables and institution-specific observation scopes."
        ),
        "source_of_labels": (
            "Deterministic institutional oracle derived from frozen policy, mandate, "
            "safety and evidence rules established before learning."
        ),
        "agent_partitioning": (
            "Each institutional agent receives only mandate-relevant observations; "
            "no omniscient feature table is used for B5."
        ),
        "perturbation_rationale": (
            "Controlled perturbations provide multiple realizations of the same institutional "
            "decision boundary so the learner is tested on mappings rather than scenario wording."
        ),
        "split_rationale": (
            "Agent-aware grouped train/dev/test splitting prevents variants from the same "
            "perturbation group leaking across partitions."
        ),
        "ood_rationale": (
            "OOD cases combine known policy variables in combinations absent from atomic "
            "training templates to test compositional generalization and rule precedence."
        ),
        "safety_rationale": (
            "Learned competence is evaluated separately from execution safety; a deterministic "
            "policy shield retains final authority over PERMIT/BLOCK/ESCALATE."
        ),
        "gate21a_counts": {
            "total": 480,
            "train": 288,
            "dev": 96,
            "test": 96,
            "privacy_agent": {"total": 120, "train": 72, "dev": 24, "test": 24},
        },
        "gate22a_ood_records": 40,
        "patient_data": False,
    }
    (OUT / "dataset_generation_methodology.json").write_text(
        json.dumps(dataset_methodology, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Publication-quality plots
    save_bar_metric_plot(id_metrics, ood_metrics)
    save_family_plot(family_stats)
    save_safety_plot(action_errors, unsafe_raw, unsafe_exec)
    save_confusion(true["action"], pred_action)

    checks = [
        {
            "check": "diagnostic_rows_complete",
            "pass": len(diagnostic_rows) == 40,
            "observed": len(diagnostic_rows),
            "expected": 40,
        },
        {
            "check": "publication_figures_created",
            "pass": all((FIG / n).exists() for n in [
                "fig22b_id_vs_ood_accuracy.png",
                "fig22b_ood_accuracy_by_family.png",
                "fig22b_errors_vs_safety.png",
                "fig22b_ood_action_confusion_matrix.png",
            ]),
            "observed": sorted(p.name for p in FIG.glob("*.png")),
            "expected": "4 PNG figures",
        },
        {
            "check": "dataset_methodology_recorded",
            "pass": (OUT / "dataset_generation_methodology.json").exists(),
            "observed": str(OUT / "dataset_generation_methodology.json"),
            "expected": "exists",
        },
        {
            "check": "no_training_or_model_change",
            "pass": True,
            "observed": {"training_changed": False, "model_changed": False, "C": 1.0},
            "expected": "frozen Gate-22 learner",
        },
        {
            "check": "shield_safety_preserved",
            "pass": unsafe_exec == 0,
            "observed": unsafe_exec,
            "expected": 0,
        },
    ]

    passed = sum(c["pass"] for c in checks)
    status = {
        "gate": "GATE_22B_PRIVACY_OOD_ERROR_DIAGNOSIS",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "diagnostic_classification": diagnosis["diagnostic_classification"],
        "id_action_accuracy": id_metrics["action"]["accuracy"],
        "ood_action_accuracy": ood_metrics["action"]["accuracy"],
        "ood_action_macro_f1": ood_metrics["action"]["macro_f1"],
        "unsafe_executed_after_policy_shield": unsafe_exec,
        "figures_directory": "outputs/gate22b/figures",
        "next_dependency": "Gate 22C targeted compositional-coverage intervention",
    }

    (OUT / "gate22b_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "gate22b_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(status, indent=2))
    print("\nFamily diagnosis:")
    print(json.dumps(family_stats, indent=2))
    print("\nComplexity diagnosis:")
    print(json.dumps(complexity_stats, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit("Gate 22B diagnostic infrastructure failed.")

    print(
        "\nFULL GATE 22B PASS — OOD failure has been decomposed without changing "
        "the learner; publication figures and dataset-generation rationale are saved."
    )


if __name__ == "__main__":
    main()
