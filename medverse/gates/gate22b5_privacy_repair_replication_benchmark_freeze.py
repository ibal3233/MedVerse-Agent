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

from medverse.learning.privacy_agent_model import clean_features
from medverse.learning.gate22a_privacy_ood import build_ood
from medverse.learning.gate22c_compositional_augmentation import build_augmentation
from medverse.learning.gate22b5_privacy_repair_replication_benchmark import (
    build_replication_benchmark,
    PROTECTED_DIAGNOSED_CORES,
    REPLICATION_CONTEXTS,
)
from medverse.learning.privacy_precedence_oracle_v2 import ORACLE_VERSION

OUT = ROOT / "outputs" / "gate22b5"
FIG = OUT / "figures"
DATA_OUT = ROOT / "data" / "learning" / "gate22b5"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
DATA_OUT.mkdir(parents=True, exist_ok=True)

G21 = ROOT / "data" / "learning" / "gate21a" / "privacy_agent.csv"
G22B2 = ROOT / "data" / "learning" / "gate22b2" / "privacy_confirmation_factorial_context_v2.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def visible_signature(features):
    return json.dumps(
        clean_features(json.dumps(features, sort_keys=True)),
        sort_keys=True,
    )


def load_gate21a():
    with G21.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_gate22b2_visible():
    with G22B2.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    out = set()
    for r in rows:
        def tri(v):
            if v == "__MISSING__":
                return None
            if v == "True":
                return True
            if v == "False":
                return False
            return v

        features = {
            "jurisdiction": r["jurisdiction"],
            "disclosure_authorized": tri(r["disclosure_authorized"]),
            "minimum_necessary": tri(r["minimum_necessary"]),
            "purpose_declared": tri(r["purpose_declared"]),
            "audit_required": tri(r["audit_required"]),
            "request_context": r["request_context"],
        }
        out.add(visible_signature(features))
    return out


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 22B.5")
    print(" Privacy Adaptive-Repair Replication")
    print(" Benchmark Freeze")
    print("========================================\n")

    rows = build_replication_benchmark()

    prior_visible = set()
    for r in load_gate21a():
        prior_visible.add(
            json.dumps(clean_features(r["features_json"]), sort_keys=True)
        )
    for c in build_ood():
        prior_visible.add(visible_signature(c["features"]))
    for a in build_augmentation():
        prior_visible.add(visible_signature(a["features"]))
    prior_visible |= load_gate22b2_visible()

    new_visible = {visible_signature(r["features"]) for r in rows}
    exact_visible_overlap = len(prior_visible & new_visible)

    core_states = {r["core_signature"] for r in rows}
    protected_rows = [r for r in rows if r["protected_diagnosed_core"]]
    protected_core_states = {r["core_signature"] for r in protected_rows}

    benchmark_path = DATA_OUT / "privacy_repair_replication_context_v3.csv"
    fields = [
        "record_id",
        "jurisdiction",
        "disclosure_authorized",
        "minimum_necessary",
        "purpose_declared",
        "audit_required",
        "request_context",
        "protected_diagnosed_core",
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
        w = csv.DictWriter(f, fieldnames=fields)
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
                "protected_diagnosed_core": r["protected_diagnosed_core"],
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
    protected_action_counts = Counter(r["action"] for r in protected_rows)
    context_counts = Counter(r["features"]["request_context"] for r in rows)

    protocol = {
        "protocol_id": "MEDVERSE-G22B5-PRIVACY-ADAPTIVE-REPAIR-REPLICATION-v1",
        "oracle_version": ORACLE_VERSION,
        "status": "PRE_FROZEN_BEFORE_TARGETED_REPAIR_TRAINING",
        "training_performed": False,
        "records": len(rows),
        "unique_core_states": len(core_states),
        "fresh_request_contexts": REPLICATION_CONTEXTS,
        "exact_model_visible_overlap_with_all_prior_sets": exact_visible_overlap,
        "protected_diagnosed_cores": len(PROTECTED_DIAGNOSED_CORES),
        "protected_replication_records": len(protected_rows),
        "semantic_freshness_status": "NOT_SEMANTICALLY_UNSEEN",
        "scientific_role": (
            "Fresh exact-record/context replication benchmark for adaptive repair "
            "validation after the complete 162-state semantic core was already opened."
        ),
        "claim_boundary": (
            "A PASS may support repaired competence over the already-defined finite "
            "Privacy state space under fresh request contexts. It must NOT be described "
            "as unseen semantic-core generalization."
        ),
        "intervention_rule_for_next_gate": {
            "allowed": (
                "add balanced oracle-consistent support for the three diagnosed "
                "precedence families"
            ),
            "model_family_change": False,
            "oracle_change": False,
            "threshold_change": False,
            "C_selection": "DEV only",
            "opened_gate22b2_confirmation_used_for_C_selection": False,
        },
        "reporting_contract": {
            "hyperparameter_results_table": True,
            "training_history_plot": True,
            "hyperparameter_plot": True,
            "solver_convergence_plot": True,
            "per_class_table": True,
            "replication_results_table": True,
        },
        "evaluation_requirements": {
            "overall_action_accuracy": 0.95,
            "overall_action_macro_f1": 0.90,
            "minimum_action_class_recall": 0.80,
            "protected_diagnosed_core_action_accuracy": 0.90,
            "unsafe_allow_execution_rate": 0.0,
        },
        "benchmark_sha256": benchmark_hash,
    }

    (OUT / "gate22b5_frozen_protocol.json").write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    (OUT / "gate22b5_class_support.json").write_text(
        json.dumps({
            "overall_action": dict(action_counts),
            "protected_action": dict(protected_action_counts),
            "contexts": dict(context_counts),
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Figures
    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    labels = sorted(action_counts)
    ax.bar(labels, [action_counts[x] for x in labels])
    ax.set_ylabel("Records")
    ax.set_title("Gate 22B.5 Replication Action-Class Support")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b5_action_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b5_action_support.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(
        REPLICATION_CONTEXTS,
        [context_counts[x] for x in REPLICATION_CONTEXTS],
    )
    ax.set_ylabel("Records")
    ax.set_title("Gate 22B.5 Fresh Request-Context Support")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b5_context_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b5_context_support.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    ax.bar(
        ["All core states", "Diagnosed protected cores"],
        [len(core_states), len(protected_core_states)],
    )
    ax.set_ylabel("Unique core states")
    ax.set_title("Semantic-State Coverage and Protected Repair Cores")
    fig.tight_layout()
    fig.savefig(FIG / "fig22b5_core_scope.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b5_core_scope.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    p_labels = sorted(protected_action_counts)
    ax.bar(p_labels, [protected_action_counts[x] for x in p_labels])
    ax.set_ylabel("Protected replication records")
    ax.set_title("Diagnosed-Core Replication Support by True Action")
    ax.tick_params(axis="x", rotation=25)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b5_protected_core_action_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b5_protected_core_action_support.pdf", bbox_inches="tight")
    plt.close(fig)

    checks = [
        {
            "check": "complete_replication_factorial",
            "pass": len(rows) == 486 and len(core_states) == 162,
            "observed": {"records": len(rows), "core_states": len(core_states)},
            "expected": {"records": 486, "core_states": 162},
        },
        {
            "check": "fresh_exact_model_visible_records",
            "pass": exact_visible_overlap == 0,
            "observed": exact_visible_overlap,
            "expected": 0,
        },
        {
            "check": "all_seven_diagnosed_cores_protected",
            "pass": protected_core_states == PROTECTED_DIAGNOSED_CORES,
            "observed": len(protected_core_states),
            "expected": 7,
        },
        {
            "check": "three_replications_per_protected_core",
            "pass": len(protected_rows) == 21,
            "observed": len(protected_rows),
            "expected": 21,
        },
        {
            "check": "fresh_contexts_balanced",
            "pass": all(context_counts[x] == 162 for x in REPLICATION_CONTEXTS),
            "observed": dict(context_counts),
            "expected": "162 each",
        },
        {
            "check": "semantic_freshness_claim_is_bounded",
            "pass": protocol["semantic_freshness_status"] == "NOT_SEMANTICALLY_UNSEEN",
            "observed": protocol["semantic_freshness_status"],
            "expected": "NOT_SEMANTICALLY_UNSEEN",
        },
        {
            "check": "protocol_frozen_before_repair_training",
            "pass": (
                protocol["training_performed"] is False
                and protocol["status"] == "PRE_FROZEN_BEFORE_TARGETED_REPAIR_TRAINING"
            ),
            "observed": {
                "training_performed": protocol["training_performed"],
                "status": protocol["status"],
            },
            "expected": "pre-frozen, no training",
        },
        {
            "check": "benchmark_sha256_recorded",
            "pass": len(benchmark_hash) == 64,
            "observed": benchmark_hash,
            "expected": "SHA256",
        },
        {
            "check": "reporting_contract_frozen",
            "pass": all(protocol["reporting_contract"].values()),
            "observed": protocol["reporting_contract"],
            "expected": "all true",
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
        "gate": "GATE_22B5_PRIVACY_REPAIR_REPLICATION_BENCHMARK_FREEZE",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "training_performed": False,
        "protocol_id": protocol["protocol_id"],
        "oracle_version": ORACLE_VERSION,
        "replication_records": len(rows),
        "unique_core_states": len(core_states),
        "fresh_contexts": REPLICATION_CONTEXTS,
        "exact_model_visible_overlap_with_all_prior_sets": exact_visible_overlap,
        "protected_diagnosed_cores": len(protected_core_states),
        "protected_replication_records": len(protected_rows),
        "semantic_freshness_status": protocol["semantic_freshness_status"],
        "benchmark_sha256": benchmark_hash,
        "hyperparameter_table_required_in_next_gate": True,
        "training_history_required_in_next_gate": True,
        "opened_gate22b2_confirmation_status": "DIAGNOSTIC_ONLY",
        "figures_directory": "outputs/gate22b5/figures",
        "next_dependency": (
            "Gate 22B.6: add balanced oracle-consistent support for the three "
            "diagnosed precedence families, reselect C using DEV only, retain "
            "hyperparameter/training-history tables and plots, then evaluate once "
            "on the frozen Gate-22B.5 replication benchmark."
        ),
    }

    (OUT / "gate22b5_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate22b5_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nBenchmark saved to:\n{benchmark_path}")
    print(f"SHA256:\n{benchmark_hash}")
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit(
            "Gate 22B.5 FAILED. Do not perform targeted Privacy repair training."
        )

    print(
        "\nFULL GATE 22B.5 PASS — A fresh exact-record/context replication "
        "benchmark is frozen before targeted repair. The protocol explicitly "
        "does not claim semantically unseen core states."
    )


if __name__ == "__main__":
    main()
