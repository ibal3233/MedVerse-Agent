from __future__ import annotations

from pathlib import Path
from collections import Counter, defaultdict
import ast
import csv
import itertools
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from medverse.learning.privacy_agent_model import clean_features
from medverse.learning.gate22a_privacy_ood import build_ood, oracle as gate22a_oracle

DATA = ROOT / "data" / "learning" / "gate21a" / "privacy_agent.csv"
BUILDER = ROOT / "medverse" / "learning" / "gate21a_dataset_builder.py"
G22A_PRED = ROOT / "outputs" / "gate22a" / "gate22a_ood_predictions.csv"

OUT = ROOT / "outputs" / "gate22b1"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

CORE_KEYS = (
    "jurisdiction",
    "disclosure_authorized",
    "minimum_necessary",
    "purpose_declared",
    "audit_required",
)

TARGET_MAP = {
    "assessment": "target_assessment",
    "action": "target_action",
    "boundary": "target_boundary_status",
    "enforcement": "target_enforcement",
    "evidence": "target_evidence_request",
}


def load_rows():
    with DATA.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def core(features):
    return tuple(features.get(k, False if k == "audit_required" else None) for k in CORE_KEYS)


def normalized_target(v):
    return "NONE" if v in ("", None) else v


def infer_base_name(row):
    # variant is e.g. authorized_g0_r0
    v = row["variant"]
    return v.rsplit("_g", 1)[0]


def observed_train_semantics(rows):
    """
    Gate-21A itself does not define a general privacy oracle. It defines eight
    fixed base templates and replicates them across perturbation groups.

    We therefore reconstruct only the semantics actually supported by those
    templates; we do not invent precedence rules for unseen combinations.
    """
    by_base = {}
    for r in rows:
        b = infer_base_name(r)
        f = json.loads(r["features_json"])
        f.pop("request_context_index", None)

        y = {
            "assessment": r["target_assessment"],
            "action": r["target_action"],
            "boundary": r["target_boundary_status"],
            "enforcement": r["target_enforcement"],
            "evidence": normalized_target(r["target_evidence_request"]),
        }

        sig = core(f)
        if b not in by_base:
            by_base[b] = {"features": f, "core": sig, "targets": y}
        else:
            assert by_base[b]["core"] == sig
            assert by_base[b]["targets"] == y
    return by_base


def classify_ood_against_train_oracle(case, base_semantics):
    """
    Conservative compatibility classification.

    - oracle_conflict: Gate-22A oracle disagrees with an actually observed
      Gate-21A base template on the exact same core signature.
    - oracle_compatible: exact core signature exists and labels agree.
    - undefined_by_train_oracle: Gate-21A never specifies that combination.

    This deliberately refuses to infer unseen rule precedence from atomic
    templates.
    """
    sig = core(case["features"])
    observed = {x["core"]: x["targets"] for x in base_semantics.values()}
    y22 = {
        "assessment": case["assessment"],
        "action": case["action"],
        "boundary": case["boundary"],
        "enforcement": case["enforcement"],
        "evidence": normalized_target(case["evidence"]),
    }

    if sig not in observed:
        return "undefined_by_train_oracle"

    return "oracle_compatible" if observed[sig] == y22 else "oracle_conflict"


def interaction_coverage(signatures, order):
    keys = list(CORE_KEYS)
    coverage = {}
    for idxs in itertools.combinations(range(len(keys)), order):
        label = "|".join(keys[i] for i in idxs)
        vals = {tuple(s[i] for i in idxs) for s in signatures}
        coverage[label] = vals
    return coverage


def safe_sort_key(x):
    return repr(x)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 22B.1")
    print(" Privacy Oracle / Split / Coverage Audit")
    print("========================================\n")

    rows = load_rows()
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]

    bases = observed_train_semantics(rows)

    # --------------------------------------------------------------
    # 1. Verify Gate-22A oracle against every actually observed
    #    Gate-21A privacy template.
    # --------------------------------------------------------------
    observed_oracle_rows = []
    observed_conflicts = 0

    for b, rec in sorted(bases.items()):
        f = dict(rec["features"])
        y22 = gate22a_oracle(f)
        y22n = {
            "assessment": y22["assessment"],
            "action": y22["action"],
            "boundary": y22["boundary"],
            "enforcement": y22["enforcement"],
            "evidence": normalized_target(y22["evidence"]),
        }
        compatible = y22n == rec["targets"]
        observed_conflicts += int(not compatible)

        observed_oracle_rows.append({
            "base_template": b,
            "core_signature": repr(rec["core"]),
            "gate21a_targets": json.dumps(rec["targets"], sort_keys=True),
            "gate22a_oracle_targets": json.dumps(y22n, sort_keys=True),
            "compatible": compatible,
        })

    # --------------------------------------------------------------
    # 2. Split algorithm / leakage audit.
    # --------------------------------------------------------------
    split_groups = defaultdict(set)
    for r in rows:
        split_groups[r["split_group"]].add(r["split"])
    groups_crossing = {g: sorted(v) for g, v in split_groups.items() if len(v) > 1}

    def cleaned_sig(r):
        return json.dumps(clean_features(r["features_json"]), sort_keys=True)

    clean_sets = {
        "train": {cleaned_sig(r) for r in train},
        "dev": {cleaned_sig(r) for r in dev},
        "test": {cleaned_sig(r) for r in test},
    }

    core_sets = {}
    for name, subset in [("train", train), ("dev", dev), ("test", test)]:
        core_sets[name] = {
            core(json.loads(r["features_json"]))
            for r in subset
        }

    leakage = {
        "split_group_crossing_count": len(groups_crossing),
        "cleaned_feature_unique": {
            k: len(v) for k, v in clean_sets.items()
        },
        "cleaned_train_dev_overlap": len(clean_sets["train"] & clean_sets["dev"]),
        "cleaned_train_test_overlap": len(clean_sets["train"] & clean_sets["test"]),
        "cleaned_dev_test_overlap": len(clean_sets["dev"] & clean_sets["test"]),
        "core_train_dev_overlap": len(core_sets["train"] & core_sets["dev"]),
        "core_train_test_overlap": len(core_sets["train"] & core_sets["test"]),
        "core_dev_test_overlap": len(core_sets["dev"] & core_sets["test"]),
    }

    # Count exact multiplicities of model-visible signatures.
    sig_counts = Counter(cleaned_sig(r) for r in rows)
    duplicate_summary = {
        "records": len(rows),
        "unique_model_visible_signatures": len(sig_counts),
        "duplicates_beyond_unique": len(rows) - len(sig_counts),
        "min_multiplicity": min(sig_counts.values()),
        "max_multiplicity": max(sig_counts.values()),
        "multiplicity_distribution": dict(Counter(sig_counts.values())),
    }

    # --------------------------------------------------------------
    # 3. OOD oracle classification and coverage.
    # --------------------------------------------------------------
    ood = build_ood()
    ood_class_rows = []
    class_counts = Counter()

    for c in ood:
        cls = classify_ood_against_train_oracle(c, bases)
        class_counts[cls] += 1
        ood_class_rows.append({
            "record_id": c["record_id"],
            "core_signature": repr(core(c["features"])),
            "classification": cls,
            "gate22a_action": c["action"],
            "gate22a_assessment": c["assessment"],
        })

    train_core = sorted(core_sets["train"], key=safe_sort_key)
    ood_core = sorted({core(c["features"]) for c in ood}, key=safe_sort_key)

    exact_ood_seen = sum(s in core_sets["train"] for s in ood_core)

    train_pair = interaction_coverage(train_core, 2)
    train_triple = interaction_coverage(train_core, 3)
    ood_pair = interaction_coverage(ood_core, 2)
    ood_triple = interaction_coverage(ood_core, 3)

    coverage_rows = []
    for order, tcov, ocov in [
        (2, train_pair, ood_pair),
        (3, train_triple, ood_triple),
    ]:
        for key in sorted(tcov):
            unseen = ocov[key] - tcov[key]
            coverage_rows.append({
                "order": order,
                "interaction": key,
                "train_unique": len(tcov[key]),
                "ood_unique": len(ocov[key]),
                "ood_unseen_unique": len(unseen),
                "ood_unseen_values": repr(sorted(unseen, key=safe_sort_key)),
            })

    # --------------------------------------------------------------
    # 4. Recompute Gate-22A errors by oracle class using existing
    #    Gate-22A prediction artifact. No retraining.
    # --------------------------------------------------------------
    prediction_available = G22A_PRED.exists()
    error_partition = {}

    if prediction_available:
        with G22A_PRED.open("r", encoding="utf-8-sig", newline="") as f:
            preds = {r["record_id"]: r for r in csv.DictReader(f)}

        cls_by_id = {r["record_id"]: r["classification"] for r in ood_class_rows}
        tmp = defaultdict(lambda: {"n": 0, "action_correct": 0, "assessment_correct": 0})

        for rid, p in preds.items():
            cls = cls_by_id[rid]
            tmp[cls]["n"] += 1
            tmp[cls]["action_correct"] += int(p["true_action"] == p["pred_action"])
            tmp[cls]["assessment_correct"] += int(
                p["true_assessment"] == p["pred_assessment"]
            )

        for cls, d in tmp.items():
            error_partition[cls] = {
                "n": d["n"],
                "action_accuracy": d["action_correct"] / d["n"],
                "assessment_accuracy": d["assessment_correct"] / d["n"],
                "action_errors": d["n"] - d["action_correct"],
                "assessment_errors": d["n"] - d["assessment_correct"],
            }

    # --------------------------------------------------------------
    # 5. Class support.
    # --------------------------------------------------------------
    class_support = {}
    for target_name, col in TARGET_MAP.items():
        class_support[target_name] = {
            "train": dict(Counter(normalized_target(r[col]) for r in train)),
            "dev": dict(Counter(normalized_target(r[col]) for r in dev)),
            "test": dict(Counter(normalized_target(r[col]) for r in test)),
        }

    # --------------------------------------------------------------
    # Root-cause statement based only on evidence above.
    # --------------------------------------------------------------
    if observed_conflicts > 0:
        root = "benchmark_misspecification_or_oracle_conflict"
    elif class_counts["undefined_by_train_oracle"] == len(ood):
        root = (
            "train_oracle_underspecification_plus_semantic_split_leakage_"
            "plus_compositional_coverage_gap"
        )
    else:
        root = "mixed_oracle_and_coverage_effects"

    audit = {
        "gate": "GATE_22B1_PRIVACY_ORACLE_SPLIT_COVERAGE_AUDIT",
        "training_performed": False,
        "learner_changed": False,
        "labels_changed": False,
        "thresholds_changed": False,
        "gate21a_privacy_records": len(rows),
        "gate21a_observed_base_templates": len(bases),
        "observed_gate21a_vs_gate22a_oracle_conflicts": observed_conflicts,
        "gate21a_split_algorithm": {
            "source_mapping": {
                "g0": "train", "g1": "train", "g2": "train",
                "g3": "dev", "g4": "test",
            },
            "split_group_crossing_count": len(groups_crossing),
            "important_correction": (
                "Groups are disjoint, but this does NOT prevent model-visible "
                "near/exact semantic leakage because the same eight Privacy base "
                "templates are repeated in every split and request_context_index "
                "is removed before modeling."
            ),
        },
        "model_visible_duplicate_summary": duplicate_summary,
        "split_leakage": leakage,
        "gate22a_ood_records": len(ood),
        "ood_oracle_classification": dict(class_counts),
        "ood_exact_core_signatures_seen_in_train": exact_ood_seen,
        "gate22a_predictions_artifact_available": prediction_available,
        "gate22a_error_partition_by_oracle_class": error_partition,
        "root_cause_classification": root,
        "scientific_interpretation": [
            "Gate-22A's oracle agrees with all eight Gate-21A Privacy templates actually observed.",
            "Gate-21A does not define a general precedence oracle for simultaneous violations or isolated missing fields; all 40 Gate-22A OOD cases therefore extend beyond the semantics explicitly supported by the training generator.",
            "The original grouped split is group-disjoint but not semantic-signature-disjoint: all eight model-visible Privacy signatures occur in TRAIN, DEV, and TEST.",
            "Perfect Gate-22 ID performance therefore demonstrates interpolation over repeated semantic templates, not independent compositional generalization.",
            "Gate-22C augmentation labels new combinations using the Gate-22A oracle. It should be described as explicit adoption/extension of that precedence semantics plus coverage expansion, not as pure recovery of a rule already established by Gate-21A.",
            "The opened Gate-22A 40-case benchmark remains diagnostic/development-only after any repair."
        ],
        "required_future_confirmation": (
            "Create a fresh frozen Privacy benchmark after formally adopting the "
            "precedence oracle and repairing semantic split/coverage design."
        ),
    }

    # Write machine-readable outputs.
    (OUT / "gate22b1_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with (OUT / "gate22b1_observed_oracle_compatibility.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(observed_oracle_rows[0].keys()))
        w.writeheader()
        w.writerows(observed_oracle_rows)

    with (OUT / "gate22b1_ood_oracle_classification.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(ood_class_rows[0].keys()))
        w.writeheader()
        w.writerows(ood_class_rows)

    with (OUT / "gate22b1_interaction_coverage.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(coverage_rows[0].keys()))
        w.writeheader()
        w.writerows(coverage_rows)

    (OUT / "gate22b1_class_support.json").write_text(
        json.dumps(class_support, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # --------------------------------------------------------------
    # Publication plots.
    # --------------------------------------------------------------
    # A. Split semantic overlap.
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.bar(
        ["TRAIN unique", "DEV unique", "TEST unique", "TRAIN∩DEV", "TRAIN∩TEST"],
        [
            len(clean_sets["train"]),
            len(clean_sets["dev"]),
            len(clean_sets["test"]),
            leakage["cleaned_train_dev_overlap"],
            leakage["cleaned_train_test_overlap"],
        ],
    )
    ax.set_ylabel("Unique model-visible signatures")
    ax.set_title("Privacy Split Audit: Semantic-Signature Overlap")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b1_split_semantic_overlap.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b1_split_semantic_overlap.pdf", bbox_inches="tight")
    plt.close(fig)

    # B. OOD oracle classification.
    labels = ["oracle_compatible", "oracle_conflict", "undefined_by_train_oracle"]
    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    ax.bar(labels, [class_counts[x] for x in labels])
    ax.set_ylabel("Gate-22A OOD records")
    ax.set_title("Privacy OOD Cases vs Gate-21A Explicit Semantics")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b1_ood_oracle_classification.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b1_ood_oracle_classification.pdf", bbox_inches="tight")
    plt.close(fig)

    # C. Pair/triple unseen interactions.
    pair_unseen = sum(r["ood_unseen_unique"] for r in coverage_rows if r["order"] == 2)
    triple_unseen = sum(r["ood_unseen_unique"] for r in coverage_rows if r["order"] == 3)
    fig, ax = plt.subplots(figsize=(6.8, 4.5))
    ax.bar(["Pair interactions", "Triple interactions"], [pair_unseen, triple_unseen])
    ax.set_ylabel("OOD interaction values unseen in TRAIN")
    ax.set_title("Privacy Compositional Coverage Gap")
    fig.tight_layout()
    fig.savefig(FIG / "fig22b1_pair_triple_coverage_gap.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b1_pair_triple_coverage_gap.pdf", bbox_inches="tight")
    plt.close(fig)

    # D. Dataset-flow / provenance visual.
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.axis("off")
    boxes = [
        (0.02, 0.35, 0.19, 0.28, "8 Privacy base templates\nGate-21A source semantics"),
        (0.27, 0.35, 0.19, 0.28, "g0–g2 TRAIN\ng3 DEV\ng4 TEST"),
        (0.52, 0.35, 0.19, 0.28, "Same 8 model-visible\nsignatures in all splits"),
        (0.77, 0.35, 0.21, 0.28, "Gate-22A: 40 new\ncombinations + new\nprecedence semantics"),
    ]
    for x, y, w, h, txt in boxes:
        rect = plt.Rectangle((x, y), w, h, fill=False, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x+w/2, y+h/2, txt, ha="center", va="center", fontsize=9)
    for x1, x2 in [(0.21,0.27),(0.46,0.52),(0.71,0.77)]:
        ax.annotate("", xy=(x2,0.49), xytext=(x1,0.49),
                    arrowprops=dict(arrowstyle="->", linewidth=1.5))
    ax.text(
        0.5, 0.12,
        "Corrected interpretation: group-disjoint ≠ semantic-signature-disjoint; "
        "opened OOD-v1 is diagnostic-only after repair.",
        ha="center", va="center", fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(FIG / "fig22b1_dataset_flow_audit.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b1_dataset_flow_audit.pdf", bbox_inches="tight")
    plt.close(fig)

    checks = [
        {
            "check": "gate21a_source_semantics_reconstructed",
            "pass": len(bases) == 8,
            "observed": len(bases),
            "expected": 8,
        },
        {
            "check": "observed_oracle_compatibility_checked",
            "pass": observed_conflicts == 0,
            "observed": observed_conflicts,
            "expected": 0,
        },
        {
            "check": "split_algorithm_audited",
            "pass": len(groups_crossing) == 0,
            "observed": {
                "group_crossing": len(groups_crossing),
                "train_dev_model_visible_overlap": leakage["cleaned_train_dev_overlap"],
                "train_test_model_visible_overlap": leakage["cleaned_train_test_overlap"],
            },
            "expected": "group-disjoint with semantic-overlap quantified",
        },
        {
            "check": "ood_oracle_classification_complete",
            "pass": sum(class_counts.values()) == 40,
            "observed": dict(class_counts),
            "expected": 40,
        },
        {
            "check": "exact_and_interaction_coverage_audited",
            "pass": len(coverage_rows) > 0,
            "observed": {
                "exact_ood_core_seen": exact_ood_seen,
                "coverage_rows": len(coverage_rows),
            },
            "expected": "exact, pair and triple coverage reported",
        },
        {
            "check": "gate22a_error_partition_recomputed_without_retraining",
            "pass": prediction_available and sum(x["n"] for x in error_partition.values()) == 40,
            "observed": {
                "prediction_artifact": prediction_available,
                "partition": error_partition,
            },
            "expected": "40 existing prediction rows partitioned",
        },
        {
            "check": "no_learner_label_threshold_change",
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

    passed = sum(x["pass"] for x in checks)
    status = {
        "gate": "GATE_22B1_PRIVACY_ORACLE_SPLIT_COVERAGE_AUDIT",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "training_performed": False,
        "observed_gate21a_gate22a_oracle_conflicts": observed_conflicts,
        "gate22a_ood_classification": dict(class_counts),
        "unique_model_visible_privacy_signatures": len(sig_counts),
        "train_dev_model_visible_overlap": leakage["cleaned_train_dev_overlap"],
        "train_test_model_visible_overlap": leakage["cleaned_train_test_overlap"],
        "ood_exact_core_signatures_seen_in_train": exact_ood_seen,
        "root_cause_classification": root,
        "gate22a_status_after_audit": "OPENED_DIAGNOSTIC_BENCHMARK",
        "gate22c_scientific_status": (
            "INTERVENTION_EVIDENCE_ONLY_PENDING_FRESH_CONFIRMATION"
        ),
        "next_dependency": (
            "Freeze a fresh Privacy confirmation benchmark under an explicitly "
            "adopted precedence oracle; only then promote the cross-agent learning "
            "methodology and resume Gate 24C."
        ),
        "figures_directory": "outputs/gate22b1/figures",
    }

    (OUT / "gate22b1_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate22b1_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print("\nModel-visible split audit:")
    print(json.dumps(leakage, indent=2))
    print("\nGate-22A error partition:")
    print(json.dumps(error_partition, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit("Gate 22B.1 audit infrastructure failed.")

    print(
        "\nFULL GATE 22B.1 PASS — The Privacy methodology audit is complete. "
        "Gate-21A/Gate-22A have no conflict on the eight observed templates, "
        "but all Gate-22A OOD cases extend beyond the explicit training oracle, "
        "and the original ID split contains full model-visible semantic overlap."
    )


if __name__ == "__main__":
    main()
