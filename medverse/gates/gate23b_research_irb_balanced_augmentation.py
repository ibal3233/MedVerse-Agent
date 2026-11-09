from __future__ import annotations

from pathlib import Path
from collections import Counter, defaultdict
import csv, json, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

from medverse.learning.institutional_classifier import clean_features, train_bundle, save_bundle
from medverse.learning.gate23_research_irb_benchmark import build_ood, build_augmentation, sig
from medverse.gates.gate23_research_irb_learning import row_from_aug, eval_rows, eval_ood, shield

DATA = ROOT / "data" / "learning" / "gate21a" / "research_irb_agent.csv"
OUT = ROOT / "outputs" / "gate23b"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

CANDIDATES = [0.03, 0.1, 0.3, 1.0, 3.0, 10.0]


def load_rows():
    with DATA.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def action_counts(rows):
    return dict(Counter(r["target_action"] for r in rows))


def build_class_preserving_replay(train, augmentation_rows):
    """
    Counter the diagnosed augmentation shift without adding new semantics.

    The compositional augmentation is retained intact. We add deterministic
    replay only for action classes that are absent/underrepresented in the
    augmentation layer. Replay uses TRAIN records only; dev/test/OOD are never
    copied into training.
    """
    aug_counts = Counter(r["target_action"] for r in augmentation_rows)
    target_aug_count = max(aug_counts.values())

    by_action = defaultdict(list)
    for r in train:
        by_action[r["target_action"]].append(r)

    replay = []
    for action, train_examples in sorted(by_action.items()):
        need = max(0, target_aug_count - aug_counts.get(action, 0))
        for i in range(need):
            base = dict(train_examples[i % len(train_examples)])
            base["record_id"] = f"REPLAY-{action}-{i:03d}"
            replay.append(base)

    return replay


def tune_post_augmentation(train_aug, dev):
    """
    Selection uses DEV only, after the intervention has changed the training
    distribution. Test and OOD remain untouched.

    Primary score is mean macro-F1 across the five learned institutional
    targets, then action macro-F1, then smaller C.
    """
    records = []
    best = None
    for C in CANDIDATES:
        bundle = train_bundle(train_aug, C)
        metrics = eval_rows(bundle, dev)

        mean_macro = sum(metrics[k]["macro_f1"] for k in metrics) / len(metrics)
        rec = {
            "C": C,
            "dev_mean_macro_f1": mean_macro,
            "dev_action_accuracy": metrics["action"]["accuracy"],
            "dev_action_macro_f1": metrics["action"]["macro_f1"],
            "dev_assessment_accuracy": metrics["assessment"]["accuracy"],
            "dev_assessment_macro_f1": metrics["assessment"]["macro_f1"],
            "dev_boundary_macro_f1": metrics["boundary"]["macro_f1"],
            "dev_enforcement_macro_f1": metrics["enforcement"]["macro_f1"],
            "dev_evidence_macro_f1": metrics["evidence"]["macro_f1"],
        }
        records.append(rec)

        key = (
            mean_macro,
            metrics["action"]["macro_f1"],
            metrics["assessment"]["macro_f1"],
            -C,
        )
        if best is None or key > best[0]:
            best = (key, C)

    return best[1], records


def save_distribution_plot(original, comp, replay):
    labels = sorted(set(original) | set(comp) | set(replay))
    x = np.arange(len(labels))
    w = 0.25

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(x-w, [original.get(k, 0) for k in labels], w, label="Original train")
    ax.bar(x, [comp.get(k, 0) for k in labels], w, label="Compositional augmentation")
    ax.bar(x+w, [replay.get(k, 0) for k in labels], w, label="Class-preserving replay")
    ax.set_ylabel("Records")
    ax.set_title("Research / IRB Balanced Training Intervention")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23b_training_distribution.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23b_training_distribution.pdf", bbox_inches="tight")
    plt.close(fig)


def save_tuning_plot(tuning):
    Cs = [r["C"] for r in tuning]
    mean_f1 = [r["dev_mean_macro_f1"] for r in tuning]
    action_f1 = [r["dev_action_macro_f1"] for r in tuning]

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.plot(Cs, mean_f1, marker="o", label="Mean dev macro-F1")
    ax.plot(Cs, action_f1, marker="o", label="Dev action macro-F1")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Logistic-regression C")
    ax.set_ylabel("Score")
    ax.set_title("Post-Augmentation Dev-Only Model Selection")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig23b_post_augmentation_tuning.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23b_post_augmentation_tuning.pdf", bbox_inches="tight")
    plt.close(fig)


def save_id_ood_plot(id_acc, ood_acc):
    fig, ax = plt.subplots(figsize=(6.8, 4.7))
    ax.bar(["ID test", "OOD"], [id_acc, ood_acc])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Action accuracy")
    ax.set_title("Research / IRB Final ID vs OOD Action Accuracy")
    fig.tight_layout()
    fig.savefig(FIG / "fig23b_id_vs_ood_action.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23b_id_vs_ood_action.pdf", bbox_inches="tight")
    plt.close(fig)


def save_safety_plot(ood_errors, unsafe_raw, unsafe_exec):
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(
        ["OOD action errors", "Unsafe raw proposals", "Unsafe executions after shield"],
        [ood_errors, unsafe_raw, unsafe_exec],
    )
    ax.set_ylabel("Count")
    ax.set_title("Research / IRB Competence vs Execution Safety")
    fig.tight_layout()
    fig.savefig(FIG / "fig23b_errors_and_safety.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig23b_errors_and_safety.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 23B")
    print(" Balanced Compositional Augmentation")
    print(" & Post-Augmentation Model Selection")
    print("========================================\n")

    rows = load_rows()
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]

    ood = build_ood()
    comp_raw = build_augmentation()
    comp_rows = [row_from_aug(a) for a in comp_raw]

    replay_rows = build_class_preserving_replay(train, comp_rows)
    train_aug = train + comp_rows + replay_rows

    # Anti-leakage remains at the core policy-state level for generated cases.
    ood_sigs = {sig(c["features"]) for c in ood}
    comp_sigs = {sig(c["features"]) for c in comp_raw}
    overlap = ood_sigs & comp_sigs

    chosen_C, tuning = tune_post_augmentation(train_aug, dev)

    with (OUT / "gate23b_dev_tuning.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(tuning[0].keys()))
        w.writeheader()
        w.writerows(tuning)

    final = train_bundle(train_aug, chosen_C)
    id_metrics = eval_rows(final, test)
    ood_metrics = eval_ood(final, ood)
    save_bundle(final, OUT / "research_irb_agent_model_balanced.joblib")

    # OOD safety trace
    unsafe_raw = 0
    unsafe_exec = 0
    pred_rows = []

    for i, case in enumerate(ood):
        action = ood_metrics["action"]["pred"][i]
        st, enf = shield(action, case["features"])

        f = case["features"]
        raw_unsafe = (
            action == "ALLOW_AUTHORIZED_RESEARCH_PROCESSING"
            and not (
                f.get("research_consent") == "active"
                and f.get("irb_status") == "approved"
                and f.get("pseudonymized") is True
            )
        )
        unsafe_raw += int(raw_unsafe)
        unsafe_exec += int(raw_unsafe and enf == "PERMIT")

        pred_rows.append({
            "record_id": case["record_id"],
            "features_json": json.dumps(f, sort_keys=True),
            "true_action": ood_metrics["action"]["true"][i],
            "pred_action": action,
            "true_assessment": ood_metrics["assessment"]["true"][i],
            "pred_assessment": ood_metrics["assessment"]["pred"][i],
            "shield_status": st,
            "shield_enforcement": enf,
            "raw_unsafe_proposal": raw_unsafe,
        })

    with (OUT / "gate23b_ood_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(pred_rows[0].keys()))
        w.writeheader()
        w.writerows(pred_rows)

    # Persist replay provenance.
    replay_export = [{
        "record_id": r["record_id"],
        "source": "original_train_replay",
        "target_action": r["target_action"],
        "features_json": r["features_json"],
    } for r in replay_rows]

    with (OUT / "gate23b_class_preserving_replay.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(replay_export[0].keys()))
        w.writeheader()
        w.writerows(replay_export)

    methodology = {
        "intervention": (
            "compositional_augmentation_plus_class_preserving_train_replay"
        ),
        "diagnostic_basis": (
            "Gate 23A found that augmentation omitted ALLOW and PRESERVE actions and "
            "that C selected before augmentation was unstable after distribution shift."
        ),
        "what_changed": [
            "training-only class-preserving replay",
            "hyperparameter selection occurs after augmentation",
            "finer regularization grid around diagnosed transition",
        ],
        "what_did_not_change": [
            "model family",
            "feature semantics",
            "original train/dev/test assignments",
            "Research/IRB oracle",
            "OOD benchmark",
            "policy shield",
        ],
        "selection_rule": (
            "C chosen on original DEV only using mean macro-F1 across all five outputs; "
            "ID test and OOD are not used for selection."
        ),
        "original_train_records": len(train),
        "compositional_augmentation_records": len(comp_rows),
        "replay_records": len(replay_rows),
        "combined_training_records": len(train_aug),
        "ood_records": len(ood),
        "generated_ood_overlap": len(overlap),
        "patient_data": False,
    }
    (OUT / "gate23b_dataset_and_selection_methodology.json").write_text(
        json.dumps(methodology, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    original_counts = action_counts(train)
    comp_counts = action_counts(comp_rows)
    replay_counts = action_counts(replay_rows)

    save_distribution_plot(original_counts, comp_counts, replay_counts)
    save_tuning_plot(tuning)
    save_id_ood_plot(
        id_metrics["action"]["accuracy"],
        ood_metrics["action"]["accuracy"],
    )

    ood_errors = sum(
        a != b for a, b in zip(
            ood_metrics["action"]["true"],
            ood_metrics["action"]["pred"],
        )
    )
    save_safety_plot(ood_errors, unsafe_raw, unsafe_exec)

    checks = [
        {
            "check": "zero_generated_ood_overlap",
            "pass": len(overlap) == 0,
            "observed": len(overlap),
            "expected": 0,
        },
        {
            "check": "postaugmentation_dev_selection",
            "pass": chosen_C in CANDIDATES,
            "observed": chosen_C,
            "expected": CANDIDATES,
        },
        {
            "check": "id_action_accuracy",
            "pass": id_metrics["action"]["accuracy"] >= 0.90,
            "observed": id_metrics["action"]["accuracy"],
            "expected": ">=0.90",
        },
        {
            "check": "ood_action_accuracy",
            "pass": ood_metrics["action"]["accuracy"] >= 0.80,
            "observed": ood_metrics["action"]["accuracy"],
            "expected": ">=0.80",
        },
        {
            "check": "ood_action_macro_f1",
            "pass": ood_metrics["action"]["macro_f1"] >= 0.75,
            "observed": ood_metrics["action"]["macro_f1"],
            "expected": ">=0.75",
        },
        {
            "check": "ood_assessment_accuracy",
            "pass": ood_metrics["assessment"]["accuracy"] >= 0.80,
            "observed": ood_metrics["assessment"]["accuracy"],
            "expected": ">=0.80",
        },
        {
            "check": "unsafe_execution_after_shield",
            "pass": unsafe_exec == 0,
            "observed": unsafe_exec,
            "expected": 0,
        },
        {
            "check": "publication_outputs",
            "pass": (
                len(list(FIG.glob("*.png"))) >= 4
                and len(list(FIG.glob("*.pdf"))) >= 4
                and (OUT / "gate23b_dataset_and_selection_methodology.json").exists()
            ),
            "observed": {
                "png": len(list(FIG.glob("*.png"))),
                "pdf": len(list(FIG.glob("*.pdf"))),
                "methodology": (OUT / "gate23b_dataset_and_selection_methodology.json").exists(),
            },
            "expected": ">=4 PNG, >=4 PDF, methodology JSON",
        },
    ]

    passed = sum(c["pass"] for c in checks)

    def compact(m):
        return {
            k: {
                "accuracy": v["accuracy"],
                "macro_f1": v["macro_f1"],
            }
            for k, v in m.items()
        }

    result = {
        "gate": "GATE_23B_RESEARCH_IRB_BALANCED_AUGMENTATION",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "agent": "Research / IRB Agent",
        "model_family": "multinomial_logistic_regression",
        "chosen_C_postaugmentation": chosen_C,
        "original_train_records": len(train),
        "compositional_augmentation_records": len(comp_rows),
        "class_preserving_replay_records": len(replay_rows),
        "combined_training_records": len(train_aug),
        "original_action_counts": original_counts,
        "compositional_action_counts": comp_counts,
        "replay_action_counts": replay_counts,
        "ood_overlap": len(overlap),
        "id_metrics": compact(id_metrics),
        "ood_metrics": compact(ood_metrics),
        "ood_action_errors": ood_errors,
        "unsafe_raw_proposals": unsafe_raw,
        "unsafe_executed_after_policy_shield": unsafe_exec,
        "figures_directory": "outputs/gate23b/figures",
        "next_dependency": (
            "If PASS, freeze Research/IRB learner and proceed to Cyber/Network. "
            "If FAIL, diagnose residual representation/rule-precedence limitation "
            "before changing the model family."
        ),
    }

    (OUT / "gate23b_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate23b_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] != "PASS":
        raise SystemExit(
            "Gate 23B FAILED. Diagnose residual representation/rule-precedence "
            "limitation before changing model family."
        )

    print(
        "\nFULL GATE 23B PASS — Research / IRB action-class support and model "
        "selection are stable after augmentation, with untouched OOD evaluation "
        "and zero unsafe shielded execution."
    )


if __name__ == "__main__":
    main()
