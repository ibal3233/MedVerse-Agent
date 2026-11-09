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

from medverse.learning.privacy_agent_model import clean_features
from medverse.learning.gate22a_privacy_ood import build_ood
from medverse.learning.gate22c_compositional_augmentation import build_augmentation
from medverse.learning.gate22b2_privacy_confirmation_benchmark import (
    build_confirmation_benchmark,
    core_signature,
    FRESH_CONTEXTS,
)
from medverse.learning.privacy_precedence_oracle_v2 import ORACLE_VERSION

OUT = ROOT / "outputs" / "gate22b2"
FIG = OUT / "figures"
DATA_OUT = ROOT / "data" / "learning" / "gate22b2"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
DATA_OUT.mkdir(parents=True, exist_ok=True)

GATE21A = ROOT / "data" / "learning" / "gate21a" / "privacy_agent.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_gate21a():
    with GATE21A.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def visible_signature(features):
    return json.dumps(
        clean_features(json.dumps(features, sort_keys=True)),
        sort_keys=True,
    )


def plot_action_support(rows):
    counts = Counter(r["action"] for r in rows)
    labels = sorted(counts)

    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.bar(labels, [counts[x] for x in labels])
    ax.set_ylabel("Prospective records")
    ax.set_title("Privacy Fresh-Confirmation Action-Class Support")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b2_action_class_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b2_action_class_support.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_assessment_support(rows):
    counts = Counter(r["assessment"] for r in rows)
    labels = sorted(counts)

    fig, ax = plt.subplots(figsize=(9, 4.9))
    ax.bar(labels, [counts[x] for x in labels])
    ax.set_ylabel("Prospective records")
    ax.set_title("Privacy Fresh-Confirmation Assessment-Class Support")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b2_assessment_class_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b2_assessment_class_support.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_context_support(rows):
    counts = Counter(r["features"]["request_context"] for r in rows)
    labels = list(FRESH_CONTEXTS)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(labels, [counts[x] for x in labels])
    ax.set_ylabel("Records")
    ax.set_title("Fresh Request-Context Variants")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b2_context_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b2_context_support.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_core_overlap(core_overlap):
    labels = [
        "Gate-21A core",
        "Gate-22A core",
        "Gate-22C augmentation core",
        "All prospective cores",
    ]
    vals = [
        core_overlap["gate21a_core_overlap"],
        core_overlap["gate22a_core_overlap"],
        core_overlap["gate22c_core_overlap"],
        core_overlap["prospective_unique_core_states"],
    ]

    fig, ax = plt.subplots(figsize=(8.7, 4.8))
    ax.bar(labels, vals)
    ax.set_ylabel("Unique core signatures")
    ax.set_title("Privacy Confirmation Benchmark: Core-State Overlap Transparency")
    ax.tick_params(axis="x", rotation=22)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b2_core_overlap_transparency.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b2_core_overlap_transparency.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 22B.2")
    print(" Privacy Precedence Oracle Adoption")
    print(" & Fresh Confirmation Benchmark Freeze")
    print("========================================\n")

    rows = build_confirmation_benchmark()
    gate21a = load_gate21a()
    gate22a = build_ood()
    gate22c = build_augmentation()

    # --------------------------------------------------------------
    # Existing model-visible signatures.
    # --------------------------------------------------------------
    existing_visible = set()

    for r in gate21a:
        existing_visible.add(
            json.dumps(clean_features(r["features_json"]), sort_keys=True)
        )

    for c in gate22a:
        existing_visible.add(visible_signature(c["features"]))

    for a in gate22c:
        existing_visible.add(visible_signature(a["features"]))

    prospective_visible = {
        visible_signature(r["features"])
        for r in rows
    }

    exact_visible_overlap = len(existing_visible & prospective_visible)

    # --------------------------------------------------------------
    # Core-state overlap is intentionally reported separately.
    # --------------------------------------------------------------
    def g21_core(r):
        f = json.loads(r["features_json"])
        return (
            f.get("jurisdiction"),
            f.get("disclosure_authorized"),
            f.get("minimum_necessary"),
            f.get("purpose_declared"),
            f.get("audit_required", False),
        )

    gate21a_core = {g21_core(r) for r in gate21a}
    gate22a_core = {core_signature(c["features"]) for c in gate22a}
    gate22c_core = {core_signature(a["features"]) for a in gate22c}
    prospective_core = {r["core_signature"] for r in rows}

    core_overlap = {
        "prospective_unique_core_states": len(prospective_core),
        "gate21a_core_overlap": len(prospective_core & gate21a_core),
        "gate22a_core_overlap": len(prospective_core & gate22a_core),
        "gate22c_core_overlap": len(prospective_core & gate22c_core),
    }

    # --------------------------------------------------------------
    # Materialize benchmark before any confirmation training.
    # --------------------------------------------------------------
    benchmark_path = DATA_OUT / "privacy_confirmation_factorial_context_v2.csv"

    fieldnames = [
        "record_id",
        "jurisdiction",
        "disclosure_authorized",
        "minimum_necessary",
        "purpose_declared",
        "audit_required",
        "request_context",
        "target_assessment",
        "target_action",
        "target_boundary_status",
        "target_enforcement",
        "target_evidence_request",
        "oracle_version",
        "synthetic_policy_benchmark",
        "patient_data",
    ]

    with benchmark_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for r in rows:
            x = r["features"]
            w.writerow({
                "record_id": r["record_id"],
                "jurisdiction": x["jurisdiction"],
                "disclosure_authorized": "__MISSING__" if x["disclosure_authorized"] is None else x["disclosure_authorized"],
                "minimum_necessary": "__MISSING__" if x["minimum_necessary"] is None else x["minimum_necessary"],
                "purpose_declared": "__MISSING__" if x["purpose_declared"] is None else x["purpose_declared"],
                "audit_required": x["audit_required"],
                "request_context": x["request_context"],
                "target_assessment": r["assessment"],
                "target_action": r["action"],
                "target_boundary_status": r["boundary"],
                "target_enforcement": r["enforcement"],
                "target_evidence_request": r["evidence"],
                "oracle_version": r["oracle_version"],
                "synthetic_policy_benchmark": True,
                "patient_data": False,
            })

    benchmark_hash = sha256(benchmark_path)

    action_counts = Counter(r["action"] for r in rows)
    assessment_counts = Counter(r["assessment"] for r in rows)
    boundary_counts = Counter(r["boundary"] for r in rows)
    enforcement_counts = Counter(r["enforcement"] for r in rows)

    protocol = {
        "protocol_id": "MEDVERSE-G22B2-PRIVACY-CONFIRMATION-v2",
        "oracle_version": ORACLE_VERSION,
        "status": "PRE_FROZEN_BEFORE_PRIVACY_CONFIRMATION_TRAINING",
        "training_performed": False,
        "benchmark_design": {
            "jurisdictions": 3,
            "authorization_states": 3,
            "minimum_necessary_states": 3,
            "purpose_states": 3,
            "audit_states": 2,
            "fresh_request_contexts": 3,
            "unique_core_states": len(prospective_core),
            "total_records": len(rows),
        },
        "scientific_role": (
            "Prospectively frozen synthetic confirmation benchmark under the "
            "explicitly adopted Privacy precedence oracle."
        ),
        "exact_model_visible_overlap_with_prior_learning_or_diagnostic_sets": (
            exact_visible_overlap
        ),
        "core_overlap_disclosure": core_overlap,
        "important_boundary": (
            "Freshness is at the exact model-visible record/context level. "
            "Many policy core states intentionally overlap previously adopted "
            "precedence semantics; this benchmark confirms the repaired oracle-"
            "consistent learner and context invariance, not externally novel law."
        ),
        "future_training_rule": (
            "Train only on Gate-21A TRAIN plus the Gate-22C compositional "
            "augmentation. Gate-22A's 40 opened OOD records must not be added."
        ),
        "future_hyperparameter_rule": (
            "Re-run C selection after augmentation using DEV only. "
            "The confirmation benchmark is never used for C selection."
        ),
        "hyperparameter_table_required": True,
        "hyperparameter_table_columns": [
            "C",
            "train_action_macro_f1",
            "dev_action_macro_f1",
            "train_assessment_macro_f1",
            "dev_assessment_macro_f1",
            "selected",
        ],
        "training_history_required": True,
        "training_history_definition": (
            "For non-iterative logistic regression, use data-growth learning "
            "history + TRAIN/DEV hyperparameter trajectory + solver iterations. "
            "Do not fabricate epoch histories."
        ),
        "confirmation_thresholds": {
            "action_accuracy": 0.95,
            "action_macro_f1": 0.90,
            "assessment_accuracy": 0.95,
            "assessment_macro_f1": 0.90,
            "boundary_accuracy": 0.95,
            "enforcement_accuracy": 0.95,
            "evidence_accuracy": 0.95,
            "minimum_action_class_recall": 0.80,
            "policy_inconsistent_execution_rate": 0.0,
        },
        "old_gate22a_status": "DIAGNOSTIC_ONLY",
        "gate22c_status": "INTERVENTION_EVIDENCE_PENDING_CONFIRMATION",
        "claim_boundary": (
            "Synthetic policy-state confirmation under explicitly adopted "
            "precedence semantics; not external clinical/legal validation."
        ),
        "benchmark_sha256": benchmark_hash,
    }

    (OUT / "gate22b2_frozen_protocol.json").write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    class_support = {
        "action": dict(action_counts),
        "assessment": dict(assessment_counts),
        "boundary": dict(boundary_counts),
        "enforcement": dict(enforcement_counts),
        "context": dict(Counter(r["features"]["request_context"] for r in rows)),
    }

    (OUT / "gate22b2_class_support.json").write_text(
        json.dumps(class_support, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    manifest = {
        "protocol_id": protocol["protocol_id"],
        "oracle_version": ORACLE_VERSION,
        "benchmark_file": str(
            benchmark_path.relative_to(ROOT)
        ).replace("\\", "/"),
        "benchmark_sha256": benchmark_hash,
        "records": len(rows),
        "unique_record_ids": len({r["record_id"] for r in rows}),
        "unique_model_visible_signatures": len(prospective_visible),
        "unique_core_states": len(prospective_core),
        "exact_model_visible_overlap_with_prior_sets": exact_visible_overlap,
        "created_before_confirmation_training": True,
        "training_performed_in_gate22b2": False,
    }

    (OUT / "gate22b2_freeze_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Publication plots.
    plot_action_support(rows)
    plot_assessment_support(rows)
    plot_context_support(rows)
    plot_core_overlap(core_overlap)

    expected_records = 3 * 3 * 3 * 3 * 2 * 3

    checks = [
        {
            "check": "complete_factorial_context_benchmark",
            "pass": len(rows) == expected_records and len(prospective_core) == 162,
            "observed": {
                "records": len(rows),
                "unique_core_states": len(prospective_core),
            },
            "expected": {
                "records": 486,
                "unique_core_states": 162,
            },
        },
        {
            "check": "unique_record_ids",
            "pass": len({r["record_id"] for r in rows}) == 486,
            "observed": len({r["record_id"] for r in rows}),
            "expected": 486,
        },
        {
            "check": "zero_exact_model_visible_overlap",
            "pass": exact_visible_overlap == 0,
            "observed": exact_visible_overlap,
            "expected": 0,
        },
        {
            "check": "all_five_action_classes_present",
            "pass": len(action_counts) == 5,
            "observed": dict(action_counts),
            "expected": 5,
        },
        {
            "check": "all_assessment_classes_present",
            "pass": len(assessment_counts) == 4,
            "observed": dict(assessment_counts),
            "expected": 4,
        },
        {
            "check": "fresh_contexts_balanced",
            "pass": all(
                class_support["context"][c] == 162
                for c in FRESH_CONTEXTS
            ),
            "observed": class_support["context"],
            "expected": "162 records per context",
        },
        {
            "check": "precedence_oracle_versioned",
            "pass": ORACLE_VERSION == "KR-PRIVACY-PRECEDENCE-v2",
            "observed": ORACLE_VERSION,
            "expected": "KR-PRIVACY-PRECEDENCE-v2",
        },
        {
            "check": "benchmark_sha256_recorded",
            "pass": len(benchmark_hash) == 64,
            "observed": benchmark_hash,
            "expected": "SHA256",
        },
        {
            "check": "protocol_frozen_before_training",
            "pass": (
                protocol["status"]
                == "PRE_FROZEN_BEFORE_PRIVACY_CONFIRMATION_TRAINING"
                and protocol["training_performed"] is False
            ),
            "observed": {
                "status": protocol["status"],
                "training_performed": protocol["training_performed"],
            },
            "expected": "pre-frozen; no training",
        },
        {
            "check": "reporting_contract_frozen",
            "pass": (
                protocol["hyperparameter_table_required"] is True
                and protocol["training_history_required"] is True
            ),
            "observed": {
                "hyperparameter_table_required": protocol["hyperparameter_table_required"],
                "training_history_required": protocol["training_history_required"],
            },
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
        "gate": "GATE_22B2_PRIVACY_CONFIRMATION_BENCHMARK_FREEZE",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "training_performed": False,
        "protocol_id": protocol["protocol_id"],
        "oracle_version": ORACLE_VERSION,
        "prospective_records": len(rows),
        "unique_core_states": len(prospective_core),
        "fresh_contexts": FRESH_CONTEXTS,
        "exact_model_visible_overlap_with_prior_sets": exact_visible_overlap,
        "core_overlap_transparency": core_overlap,
        "action_class_support": dict(action_counts),
        "assessment_class_support": dict(assessment_counts),
        "benchmark_sha256": benchmark_hash,
        "hyperparameter_table_required_in_next_gate": True,
        "training_history_required_in_next_gate": True,
        "old_gate22a_status": "DIAGNOSTIC_ONLY",
        "gate22c_status": "INTERVENTION_EVIDENCE_PENDING_CONFIRMATION",
        "figures_directory": "outputs/gate22b2/figures",
        "next_dependency": (
            "Gate 22B.3: retrain Privacy using Gate-21A TRAIN + Gate-22C "
            "augmentation; perform DEV-only C selection; save hyperparameter "
            "results table and training-history diagnostics; evaluate once on "
            "the frozen 486-record confirmation benchmark."
        ),
    }

    (OUT / "gate22b2_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate22b2_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nBenchmark saved to:\n{benchmark_path}")
    print(f"SHA256:\n{benchmark_hash}")
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit(
            "Gate 22B.2 FAILED. Do not train Privacy confirmation model until "
            "the prospective benchmark and adopted oracle are valid."
        )

    print(
        "\nFULL GATE 22B.2 PASS — The richer Privacy precedence oracle is "
        "explicitly versioned and a 486-record prospective confirmation "
        "benchmark is frozen before confirmation training."
    )


if __name__ == "__main__":
    main()
