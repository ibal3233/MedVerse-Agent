from __future__ import annotations

from pathlib import Path
from collections import Counter, defaultdict
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from medverse.learning.gate22c_compositional_augmentation import (
    build_augmentation,
    core_signature,
)

BASE_DATA = ROOT / "data" / "learning" / "gate21a" / "privacy_agent.csv"
PRED = ROOT / "outputs" / "gate22b3" / "gate22b3_confirmation_predictions.csv"
OUT = ROOT / "outputs" / "gate22b4"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)


def load_base_train():
    with BASE_DATA.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["split"] == "train"]


def load_predictions():
    with PRED.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_training_core_support():
    support = Counter()
    action_support = Counter()

    for r in load_base_train():
        f = json.loads(r["features_json"])
        sig = core_signature(f)
        support[sig] += 1
        action_support[r["target_action"]] += 1

    for a in build_augmentation():
        sig = core_signature(a["features"])
        support[sig] += 1
        action_support[a["action"]] += 1

    return support, action_support


def classify_error_family(features, true_action, pred_action):
    auth = features.get("disclosure_authorized")
    minimum = features.get("minimum_necessary")
    purpose = features.get("purpose_declared")
    jurisdiction = features.get("jurisdiction")

    if (
        jurisdiction == "KR"
        and auth is True
        and minimum is False
        and purpose is False
        and true_action == "LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY"
        and pred_action == "REQUEST_ADDITIONAL_AUTHORIZATION"
    ):
        return "minimum_necessary_precedence_over_purpose"

    if (
        jurisdiction == "KR"
        and auth is False
        and purpose is False
        and true_action == "DENY_UNAUTHORIZED_DISCLOSURE"
        and pred_action == "REQUEST_ADDITIONAL_AUTHORIZATION"
    ):
        return "authorization_denial_precedence_over_purpose"

    if (
        jurisdiction == "KR"
        and auth is False
        and minimum is None
        and true_action == "REQUEST_ADDITIONAL_AUTHORIZATION"
        and pred_action == "DENY_UNAUTHORIZED_DISCLOSURE"
    ):
        return "missing_evidence_precedence_over_authorization_denial"

    return "other"


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 22B.4")
    print(" Privacy Confirmation Error Diagnosis")
    print("========================================\n")

    support, training_action_support = build_training_core_support()
    rows = load_predictions()
    errors = [r for r in rows if r["true_action"] != r["pred_action"]]

    error_rows = []
    family_counts = Counter()
    error_pair_counts = Counter()
    unique_error_cores = Counter()

    for r in errors:
        f = json.loads(r["features_json"])
        sig = core_signature(f)
        fam = classify_error_family(
            f,
            r["true_action"],
            r["pred_action"],
        )

        family_counts[fam] += 1
        error_pair_counts[(r["true_action"], r["pred_action"])] += 1
        unique_error_cores[(sig, r["true_action"], r["pred_action"])] += 1

        error_rows.append({
            "record_id": r["record_id"],
            "request_context": f.get("request_context"),
            "core_signature": repr(sig),
            "training_core_support": support[sig],
            "true_action": r["true_action"],
            "pred_action": r["pred_action"],
            "error_family": fam,
        })

    core_rows = []
    for (sig, true_action, pred_action), n in sorted(
        unique_error_cores.items(),
        key=lambda x: repr(x[0]),
    ):
        core_rows.append({
            "core_signature": repr(sig),
            "true_action": true_action,
            "pred_action": pred_action,
            "confirmation_error_repetitions": n,
            "combined_training_core_support": support[sig],
            "support_status": (
                "ZERO_SUPPORT" if support[sig] == 0
                else "LOW_SUPPORT" if support[sig] <= 1
                else "SUPPORTED"
            ),
        })

    # Context replication check: every failing policy core should repeat across
    # the three fresh nuisance contexts if the failure is policy-core driven.
    context_by_core = defaultdict(set)
    for r in error_rows:
        context_by_core[r["core_signature"]].add(r["request_context"])

    all_error_cores_context_invariant = all(
        len(v) == 3 for v in context_by_core.values()
    )

    zero_support_error_cores = sum(
        r["combined_training_core_support"] == 0 for r in core_rows
    )
    low_or_zero_support_error_cores = sum(
        r["combined_training_core_support"] <= 1 for r in core_rows
    )

    # Save raw diagnostics
    with (OUT / "gate22b4_error_trace.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(error_rows[0].keys()))
        w.writeheader()
        w.writerows(error_rows)

    with (OUT / "gate22b4_error_core_support.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(core_rows[0].keys()))
        w.writeheader()
        w.writerows(core_rows)

    diagnosis = {
        "gate": "GATE_22B4_PRIVACY_CONFIRMATION_ERROR_DIAGNOSIS",
        "training_performed": False,
        "hyperparameter_retuning_performed": False,
        "confirmation_records": len(rows),
        "confirmation_action_errors": len(errors),
        "error_pairs": {
            f"{a} -> {b}": n
            for (a, b), n in error_pair_counts.items()
        },
        "error_families": dict(family_counts),
        "unique_error_policy_cores": len(core_rows),
        "zero_support_error_cores": zero_support_error_cores,
        "low_or_zero_support_error_cores": low_or_zero_support_error_cores,
        "all_error_cores_repeat_across_all_three_fresh_contexts": (
            all_error_cores_context_invariant
        ),
        "combined_training_action_support": dict(training_action_support),
        "diagnostic_classification": (
            "sparse_precedence_interaction_support_with_minority_action_coverage_"
            "limitation_not_hyperparameter_failure"
        ),
        "interpretation": [
            "All 21 action errors fall into three policy-precedence families.",
            "Every failing policy core repeats under all three fresh request contexts, so the residual errors are core-policy/precedence errors rather than request-context-specific failures.",
            "All seven unique failing policy cores have at most one combined-training example; two have zero exact core support.",
            "LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY is a minority training action and its failed cases specifically require minimum-necessary=False to dominate purpose=False.",
            "The confirmation benchmark has now been opened and may be used only for diagnosis, not for C selection or final confirmation after repair.",
        ],
        "authorized_next_intervention": (
            "Add balanced, oracle-consistent training support for the three diagnosed "
            "precedence families while keeping the model family and adopted oracle "
            "unchanged; then evaluate on a newly frozen confirmation benchmark."
        ),
    }

    (OUT / "gate22b4_diagnosis.json").write_text(
        json.dumps(diagnosis, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Publication figures
    # 1. Error families
    fam_labels = list(family_counts.keys())
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(fam_labels, [family_counts[x] for x in fam_labels])
    ax.set_ylabel("Confirmation action errors")
    ax.set_title("Privacy Confirmation Errors by Precedence Family")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b4_error_families.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b4_error_families.pdf", bbox_inches="tight")
    plt.close(fig)

    # 2. Error-core support
    labels = [f"Core {i+1}" for i in range(len(core_rows))]
    vals = [r["combined_training_core_support"] for r in core_rows]
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(labels, vals)
    ax.set_ylabel("Combined training support")
    ax.set_title("Training Support for Failing Privacy Policy Cores")
    fig.tight_layout()
    fig.savefig(FIG / "fig22b4_error_core_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b4_error_core_support.pdf", bbox_inches="tight")
    plt.close(fig)

    # 3. Training action support
    action_labels = sorted(training_action_support)
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.bar(
        action_labels,
        [training_action_support[x] for x in action_labels],
    )
    ax.set_ylabel("Combined training records")
    ax.set_title("Privacy Combined-Training Action-Class Support")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b4_training_action_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b4_training_action_support.pdf", bbox_inches="tight")
    plt.close(fig)

    # 4. Error pair decomposition
    pair_labels = [f"{a}\n→ {b}" for (a,b) in error_pair_counts]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(
        pair_labels,
        list(error_pair_counts.values()),
    )
    ax.set_ylabel("Count")
    ax.set_title("Privacy Confirmation Action Error Pairs")
    fig.tight_layout()
    fig.savefig(FIG / "fig22b4_error_pairs.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b4_error_pairs.pdf", bbox_inches="tight")
    plt.close(fig)

    checks = [
        {
            "check": "all_confirmation_action_errors_traced",
            "pass": len(errors) == 21 and len(error_rows) == 21,
            "observed": len(error_rows),
            "expected": 21,
        },
        {
            "check": "all_errors_classified_into_known_precedence_families",
            "pass": family_counts.get("other", 0) == 0,
            "observed": dict(family_counts),
            "expected": "other = 0",
        },
        {
            "check": "error_core_support_quantified",
            "pass": len(core_rows) == 7,
            "observed": len(core_rows),
            "expected": 7,
        },
        {
            "check": "sparse_support_detected",
            "pass": low_or_zero_support_error_cores == len(core_rows),
            "observed": {
                "low_or_zero_support": low_or_zero_support_error_cores,
                "total_error_cores": len(core_rows),
                "zero_support": zero_support_error_cores,
            },
            "expected": "all failing cores have <=1 combined-training example",
        },
        {
            "check": "context_invariance_of_error_cores",
            "pass": all_error_cores_context_invariant,
            "observed": {
                k: sorted(v) for k, v in context_by_core.items()
            },
            "expected": "each failing core appears in all 3 fresh contexts",
        },
        {
            "check": "no_retraining_or_retuning",
            "pass": True,
            "observed": True,
            "expected": True,
        },
        {
            "check": "publication_outputs",
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
        "gate": "GATE_22B4_PRIVACY_CONFIRMATION_ERROR_DIAGNOSIS",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "training_performed": False,
        "hyperparameter_retuning_performed": False,
        "confirmation_action_errors": len(errors),
        "error_families": dict(family_counts),
        "unique_error_policy_cores": len(core_rows),
        "zero_support_error_cores": zero_support_error_cores,
        "low_or_zero_support_error_cores": low_or_zero_support_error_cores,
        "diagnostic_classification": diagnosis["diagnostic_classification"],
        "opened_confirmation_status": "DIAGNOSTIC_ONLY_AFTER_FIRST_EVALUATION",
        "figures_directory": "outputs/gate22b4/figures",
        "next_dependency": (
            "Gate 22B.5: pre-freeze another fresh Privacy confirmation benchmark "
            "before adding balanced training support for the three diagnosed "
            "precedence families."
        ),
    }

    (OUT / "gate22b4_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate22b4_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print("\nError-core support:")
    print(json.dumps(core_rows, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit("Gate 22B.4 diagnostic infrastructure failed.")

    print(
        "\nFULL GATE 22B.4 PASS — The residual Privacy confirmation failure "
        "is localized to sparse support for three precedence families; no "
        "hyperparameter or model-family change is justified."
    )


if __name__ == "__main__":
    main()
