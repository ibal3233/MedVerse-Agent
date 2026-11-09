from __future__ import annotations

from pathlib import Path
from collections import Counter, defaultdict
import copy
import csv
import hashlib
import json
import math
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

from medverse.learning.privacy_agent_model import (
    clean_features,
    make_classifier,
    load_bundle,
    save_bundle,
)
from medverse.learning.gate22c_compositional_augmentation import (
    build_augmentation,
    core_signature,
)
from medverse.gates.gate22c_privacy_compositional_coverage import aug_to_training_row
from medverse.learning.gate22b6_privacy_targeted_repair_support import (
    build_targeted_repair_rows,
    DIAGNOSED_CORES,
    TARGET_SUPPORT_PER_DIAGNOSED_CORE,
)
from medverse.gates.gate22_privacy_agent_training import privacy_policy_shield

BASE_DATA = ROOT / "data" / "learning" / "gate21a" / "privacy_agent.csv"
REPLICATION = (
    ROOT / "data" / "learning" / "gate22b5" /
    "privacy_repair_replication_context_v3.csv"
)
PROTOCOL = ROOT / "outputs" / "gate22b5" / "gate22b5_frozen_protocol.json"
BASE_MODEL = ROOT / "outputs" / "gate22b3" / "privacy_agent_confirmation_model.joblib"

OUT = ROOT / "outputs" / "gate22b6"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

EXPECTED_SHA256 = "c7c0d4fc60eba832e24ea60c4d9db43654022512b83f789da5944d86cf58550d"
CANDIDATES = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
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


def tri(v):
    if v == "__MISSING__":
        return None
    if v in ("True", "true", True):
        return True
    if v in ("False", "false", False):
        return False
    return v


def load_replication():
    with REPLICATION.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    out = []
    for r in rows:
        features = {
            "jurisdiction": r["jurisdiction"],
            "disclosure_authorized": tri(r["disclosure_authorized"]),
            "minimum_necessary": tri(r["minimum_necessary"]),
            "purpose_declared": tri(r["purpose_declared"]),
            "audit_required": tri(r["audit_required"]),
            "request_context": r["request_context"],
        }
        out.append({
            "record_id": r["record_id"],
            "features_json": json.dumps(features, sort_keys=True),
            "features": features,
            "protected_diagnosed_core": r["protected_diagnosed_core"] == "True",
            "target_assessment": r["target_assessment"],
            "target_action": r["target_action"],
            "target_boundary_status": r["target_boundary_status"],
            "target_enforcement": r["target_enforcement"],
            "target_evidence_request": (
                "" if r["target_evidence_request"] == "NONE"
                else r["target_evidence_request"]
            ),
        })
    return out


def action_training_rows(base_train):
    aug = build_augmentation()
    aug_rows = [aug_to_training_row(a) for a in aug]
    for i, r in enumerate(aug_rows):
        r["record_id"] = aug[i]["record_id"]
    return list(base_train) + aug_rows, len(aug_rows)


def support_map(rows):
    c = Counter()
    for r in rows:
        c[core_signature(json.loads(r["features_json"]))] += 1
    return c


def repair_to_row(r):
    return {
        "record_id": r["record_id"],
        "features_json": json.dumps(r["features"], sort_keys=True),
        "target_action": r["target_action"],
        "repair_family": r["repair_family"],
    }


def fit_action(rows, C):
    model = make_classifier(C)
    X = [clean_features(r["features_json"]) for r in rows]
    y = [r["target_action"] for r in rows]
    model.fit(X, y)
    return model


def eval_action(model, rows):
    X = [clean_features(r["features_json"]) for r in rows]
    yt = [r["target_action"] for r in rows]
    yp = list(model.predict(X))
    return {
        "accuracy": float(accuracy_score(yt, yp)),
        "macro_f1": float(f1_score(yt, yp, average="macro", zero_division=0)),
    }, yt, yp


def select_c(train_rows, dev_rows):
    table = []
    best = None

    for C in CANDIDATES:
        model = fit_action(train_rows, C)
        tr, _, _ = eval_action(model, train_rows)
        dv, _, _ = eval_action(model, dev_rows)
        n_iter = int(max(model.named_steps["classifier"].n_iter_))

        rec = {
            "C": C,
            "train_action_accuracy": tr["accuracy"],
            "train_action_macro_f1": tr["macro_f1"],
            "dev_action_accuracy": dv["accuracy"],
            "dev_action_macro_f1": dv["macro_f1"],
            "action_solver_iterations": n_iter,
            "selected": False,
        }
        table.append(rec)

        key = (dv["macro_f1"], dv["accuracy"], -C)
        if best is None or key > best[0]:
            best = (key, C)

    chosen = best[1]
    for r in table:
        r["selected"] = r["C"] == chosen
    return chosen, table


def evaluate_bundle(bundle, rows):
    X = [clean_features(r["features_json"]) for r in rows]
    spec = {
        "assessment": ("assessment_model", "target_assessment"),
        "action": ("action_model", "target_action"),
        "boundary": ("boundary_model", "target_boundary_status"),
        "enforcement": ("enforcement_model", "target_enforcement"),
        "evidence": ("evidence_model", "target_evidence_request"),
    }
    metrics = {}
    preds = {}

    for name, (attr, field) in spec.items():
        yt = [(r[field] if r[field] else "NONE") for r in rows]
        yp = list(getattr(bundle, attr).predict(X))
        metrics[name] = {
            "accuracy": float(accuracy_score(yt, yp)),
            "macro_f1": float(f1_score(yt, yp, average="macro", zero_division=0)),
        }
        preds[name] = {"true": yt, "pred": yp}
    return metrics, preds


def action_class_metrics(yt, yp):
    labels = sorted(set(yt) | set(yp))
    p, r, f, s = precision_recall_fscore_support(
        yt, yp, labels=labels, zero_division=0
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


def deterministic_fraction(rows, frac):
    if frac <= 0:
        return []
    by_family = defaultdict(list)
    for r in rows:
        by_family[r["repair_family"]].append(r)

    out = []
    for fam in sorted(by_family):
        members = sorted(by_family[fam], key=lambda x: x["record_id"])
        n = max(1, math.ceil(len(members) * frac))
        out.extend(members[:n])
    return out


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 22B.6 PATCHED")
    print(" Privacy Targeted ACTION Repair")
    print(" + Cumulative Multi-Output Regression Check")
    print("========================================\n")

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    observed_hash = sha256(REPLICATION)

    base = load_base()
    base_plus_aug, aug_count = action_training_rows(base["train"])
    before = support_map(base_plus_aug)

    repair_raw = build_targeted_repair_rows(before)
    repair_rows = [repair_to_row(r) for r in repair_raw]

    after = Counter(before)
    for r in repair_raw:
        after[r["core_signature"]] += 1

    combined_action_train = base_plus_aug + repair_rows
    dev_rows = base["dev"]
    replication_rows = load_replication()

    # DEV-only action-head C selection.
    chosen_C, hp_table = select_c(combined_action_train, dev_rows)

    # Training history: action head only.
    history = []
    for step, frac in enumerate([0.0, 0.25, 0.50, 0.75, 1.0]):
        subset = deterministic_fraction(repair_rows, frac)
        train_now = base_plus_aug + subset
        model = fit_action(train_now, chosen_C)
        tr, _, _ = eval_action(model, train_now)
        dv, _, _ = eval_action(model, dev_rows)
        history.append({
            "step": step,
            "repair_fraction": frac,
            "repair_records": len(subset),
            "training_records": len(train_now),
            "train_action_macro_f1": tr["macro_f1"],
            "dev_action_macro_f1": dv["macro_f1"],
            "action_solver_iterations": int(max(model.named_steps["classifier"].n_iter_)),
        })

    # One-component intervention:
    # load Gate22B.3 multi-output bundle and replace ONLY action_model.
    base_bundle = load_bundle(BASE_MODEL)
    repaired_bundle = copy.deepcopy(base_bundle)
    repaired_bundle.action_model = fit_action(combined_action_train, chosen_C)
    repaired_bundle.chosen_C = chosen_C
    save_bundle(repaired_bundle, OUT / "privacy_agent_action_repaired_model.joblib")

    repl_metrics, repl_pred = evaluate_bundle(repaired_bundle, replication_rows)
    id_metrics, _ = evaluate_bundle(repaired_bundle, base["test"])

    cls = action_class_metrics(
        repl_pred["action"]["true"],
        repl_pred["action"]["pred"],
    )
    min_recall = min(r["recall"] for r in cls)

    protected_idx = [
        i for i, r in enumerate(replication_rows)
        if r["protected_diagnosed_core"]
    ]
    protected_true = [repl_pred["action"]["true"][i] for i in protected_idx]
    protected_pred = [repl_pred["action"]["pred"][i] for i in protected_idx]
    protected_acc = float(accuracy_score(protected_true, protected_pred))

    unsafe_proposals = 0
    unsafe_executions = 0
    raw_rows = []
    for i, row in enumerate(replication_rows):
        f = row["features"]
        pa = repl_pred["action"]["pred"][i]
        ta = repl_pred["action"]["true"][i]
        ss, se = privacy_policy_shield(pa, f)
        raw_unsafe = (
            pa == "ALLOW_AUTHORIZED_DISCLOSURE"
            and not (
                f.get("jurisdiction") == "KR"
                and f.get("disclosure_authorized") is True
                and f.get("minimum_necessary") is True
                and f.get("purpose_declared") is True
            )
        )
        unsafe_proposals += int(raw_unsafe)
        unsafe_executions += int(raw_unsafe and se == "PERMIT")

        raw_rows.append({
            "record_id": row["record_id"],
            "protected_diagnosed_core": row["protected_diagnosed_core"],
            "true_action": ta,
            "pred_action": pa,
            "action_correct": ta == pa,
            "shield_status": ss,
            "shield_enforcement": se,
            "unsafe_allow_proposal": raw_unsafe,
            "unsafe_allow_execution": raw_unsafe and se == "PERMIT",
        })

    unsafe_rate = unsafe_executions / len(replication_rows)

    # Tables
    with (OUT / "gate22b6_hyperparameter_results.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(hp_table[0].keys()))
        w.writeheader()
        w.writerows(hp_table)

    hp_md = OUT / "gate22b6_hyperparameter_results_table.md"
    lines = [
        "# Gate 22B.6 Hyperparameter Selection — Action Head Only",
        "",
        "Selection uses DEV only. Replication metrics are excluded.",
        "",
        "| C | Train action F1 | Dev action F1 | Solver iter. | Selected |",
        "|---:|---:|---:|---:|:---:|",
    ]
    for r in hp_table:
        lines.append(
            f"| {r['C']:.2g} | {r['train_action_macro_f1']:.3f} | "
            f"{r['dev_action_macro_f1']:.3f} | {r['action_solver_iterations']} | "
            f"{'✓' if r['selected'] else ''} |"
        )
    hp_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with (OUT / "gate22b6_training_history.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        w.writeheader()
        w.writerows(history)

    with (OUT / "gate22b6_action_class_metrics.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(
            f,
            fieldnames=["class", "precision", "recall", "f1", "support"],
        )
        w.writeheader()
        w.writerows(cls)

    with (OUT / "gate22b6_replication_predictions.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(raw_rows[0].keys()))
        w.writeheader()
        w.writerows(raw_rows)

    support_rows = []
    for sig in DIAGNOSED_CORES:
        support_rows.append({
            "core_signature": repr(sig),
            "support_before": before[sig],
            "repair_added": after[sig] - before[sig],
            "support_after": after[sig],
            "target_support": TARGET_SUPPORT_PER_DIAGNOSED_CORE,
        })

    with (OUT / "gate22b6_repair_support_table.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(support_rows[0].keys()))
        w.writeheader()
        w.writerows(support_rows)

    eval_rows = []
    for output in ["assessment", "action", "boundary", "enforcement", "evidence"]:
        eval_rows.append({
            "output": output,
            "accuracy": repl_metrics[output]["accuracy"],
            "macro_f1": repl_metrics[output]["macro_f1"],
        })
    with (OUT / "gate22b6_replication_results_table.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(eval_rows[0].keys()))
        w.writeheader()
        w.writerows(eval_rows)

    # Figures
    Cs = [r["C"] for r in hp_table]
    fig, ax = plt.subplots(figsize=(8.3, 5.0))
    ax.plot(Cs, [r["dev_action_macro_f1"] for r in hp_table], marker="o", label="DEV action macro-F1")
    ax.plot(Cs, [r["train_action_macro_f1"] for r in hp_table], marker="o", label="Train action macro-F1")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("C")
    ax.set_ylabel("Macro-F1")
    ax.set_title("Privacy Action-Head Hyperparameter Selection")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b6_hyperparameter_selection.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b6_hyperparameter_selection.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.3, 5.0))
    x = [r["training_records"] for r in history]
    ax.plot(x, [r["train_action_macro_f1"] for r in history], marker="o", label="Train action macro-F1")
    ax.plot(x, [r["dev_action_macro_f1"] for r in history], marker="o", label="DEV action macro-F1")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Training records")
    ax.set_ylabel("Macro-F1")
    ax.set_title("Privacy Targeted Action-Repair Training History")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b6_training_history.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b6_training_history.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.plot(Cs, [r["action_solver_iterations"] for r in hp_table], marker="o")
    ax.set_xscale("log")
    ax.set_xlabel("C")
    ax.set_ylabel("LBFGS iterations")
    ax.set_title("Privacy Action-Head Solver Convergence")
    fig.tight_layout()
    fig.savefig(FIG / "fig22b6_solver_iterations.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b6_solver_iterations.pdf", bbox_inches="tight")
    plt.close(fig)

    labels = [x["output"].title() for x in eval_rows]
    xx = np.arange(len(labels))
    w = 0.36
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(xx-w/2, [x["accuracy"] for x in eval_rows], w, label="Accuracy")
    ax.bar(xx+w/2, [x["macro_f1"] for x in eval_rows], w, label="Macro-F1")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(xx)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylabel("Score")
    ax.set_title("Privacy Patched Repair: Multi-Output Replication Performance")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b6_replication_metrics.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b6_replication_metrics.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([r["class"] for r in cls], [r["recall"] for r in cls])
    ax.axhline(0.80, linestyle="--", linewidth=1)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Recall")
    ax.set_title("Privacy Action Recall by Class")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(FIG / "fig22b6_action_class_recall.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b6_action_class_recall.pdf", bbox_inches="tight")
    plt.close(fig)

    cm_labels = sorted(set(repl_pred["action"]["true"]) | set(repl_pred["action"]["pred"]))
    cm = confusion_matrix(repl_pred["action"]["true"], repl_pred["action"]["pred"], labels=cm_labels)
    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(cm, aspect="auto")
    ax.set_title("Privacy Action Replication Confusion Matrix")
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
    fig.savefig(FIG / "fig22b6_action_confusion.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b6_action_confusion.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    pos = np.arange(len(support_rows))
    ww = 0.35
    ax.bar(pos-ww/2, [r["support_before"] for r in support_rows], ww, label="Before")
    ax.bar(pos+ww/2, [r["support_after"] for r in support_rows], ww, label="After")
    ax.set_xticks(pos)
    ax.set_xticklabels([f"Core {i+1}" for i in range(len(support_rows))])
    ax.set_ylabel("Training support")
    ax.set_title("Diagnosed-Core Support Before vs After Action Repair")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig22b6_repair_support.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig22b6_repair_support.pdf", bbox_inches="tight")
    plt.close(fig)

    # Cumulative thresholds: retain Gate22B.3 non-action requirements as regressions.
    checks = [
        {
            "check": "replication_benchmark_hash_matches",
            "pass": observed_hash == EXPECTED_SHA256,
            "observed": observed_hash,
            "expected": EXPECTED_SHA256,
        },
        {
            "check": "all_diagnosed_cores_reach_support_target",
            "pass": all(after[s] == TARGET_SUPPORT_PER_DIAGNOSED_CORE for s in DIAGNOSED_CORES),
            "observed": {repr(s): after[s] for s in DIAGNOSED_CORES},
            "expected": TARGET_SUPPORT_PER_DIAGNOSED_CORE,
        },
        {
            "check": "one_component_intervention_action_head_only",
            "pass": True,
            "observed": "Only action_model replaced; four non-action heads loaded unchanged from Gate22B.3",
            "expected": True,
        },
        {
            "check": "action_accuracy",
            "pass": repl_metrics["action"]["accuracy"] >= 0.95,
            "observed": repl_metrics["action"]["accuracy"],
            "expected": ">=0.95",
        },
        {
            "check": "action_macro_f1",
            "pass": repl_metrics["action"]["macro_f1"] >= 0.90,
            "observed": repl_metrics["action"]["macro_f1"],
            "expected": ">=0.90",
        },
        {
            "check": "minimum_action_class_recall",
            "pass": min_recall >= 0.80,
            "observed": min_recall,
            "expected": ">=0.80",
        },
        {
            "check": "protected_diagnosed_core_action_accuracy",
            "pass": protected_acc >= 0.90,
            "observed": protected_acc,
            "expected": ">=0.90",
        },
        {
            "check": "assessment_cumulative_threshold",
            "pass": (
                repl_metrics["assessment"]["accuracy"] >= 0.95
                and repl_metrics["assessment"]["macro_f1"] >= 0.90
            ),
            "observed": repl_metrics["assessment"],
            "expected": "accuracy>=0.95 and macro_f1>=0.90",
        },
        {
            "check": "boundary_cumulative_threshold",
            "pass": repl_metrics["boundary"]["accuracy"] >= 0.95,
            "observed": repl_metrics["boundary"]["accuracy"],
            "expected": ">=0.95",
        },
        {
            "check": "enforcement_cumulative_threshold",
            "pass": repl_metrics["enforcement"]["accuracy"] >= 0.95,
            "observed": repl_metrics["enforcement"]["accuracy"],
            "expected": ">=0.95",
        },
        {
            "check": "evidence_cumulative_threshold",
            "pass": repl_metrics["evidence"]["accuracy"] >= 0.95,
            "observed": repl_metrics["evidence"]["accuracy"],
            "expected": ">=0.95",
        },
        {
            "check": "unsafe_allow_execution_rate",
            "pass": unsafe_rate == 0.0,
            "observed": unsafe_rate,
            "expected": 0.0,
        },
        {
            "check": "reporting_outputs",
            "pass": (
                hp_md.exists()
                and (OUT / "gate22b6_training_history.csv").exists()
                and (OUT / "gate22b6_replication_results_table.csv").exists()
                and (OUT / "gate22b6_action_class_metrics.csv").exists()
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

    passed = sum(x["pass"] for x in checks)

    result = {
        "gate": "GATE_22B6_PRIVACY_TARGETED_ACTION_REPAIR",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "agent": "Privacy Agent",
        "intervention_scope": "ACTION_HEAD_ONLY",
        "base_non_action_model_source": "Gate22B.3",
        "action_model_family": "multinomial_logistic_regression",
        "chosen_action_C": chosen_C,
        "original_train_records": len(base["train"]),
        "gate22c_augmentation_records": aug_count,
        "targeted_repair_records": len(repair_rows),
        "combined_action_training_records": len(combined_action_train),
        "replication_records": len(replication_rows),
        "replication_metrics": repl_metrics,
        "opened_id_test_metrics": id_metrics,
        "action_class_metrics": cls,
        "minimum_action_class_recall": min_recall,
        "protected_diagnosed_core_action_accuracy": protected_acc,
        "unsafe_allow_execution_rate": unsafe_rate,
        "training_history_steps": len(history),
        "claim_boundary": protocol["claim_boundary"],
        "model_path": "outputs/gate22b6/privacy_agent_action_repaired_model.joblib",
        "figures_directory": "outputs/gate22b6/figures",
        "next_dependency": (
            "If PASS, Privacy is closed for hackathon purposes under the finite-state "
            "claim boundary; resume Cyber Gate24C. If FAIL, document residual Privacy "
            "limits rather than opening another adaptive repair cycle."
        ),
    }

    (OUT / "gate22b6_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate22b6_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print("\nHyperparameter table:")
    for r in hp_table:
        print({
            "C": r["C"],
            "train_action_macro_f1": round(r["train_action_macro_f1"], 4),
            "dev_action_macro_f1": round(r["dev_action_macro_f1"], 4),
            "selected": r["selected"],
        })
    print("\nTraining history:")
    print(json.dumps(history, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] != "PASS":
        raise SystemExit(
            "Gate 22B.6 FAILED. Do not open another adaptive Privacy cycle for "
            "the hackathon; document the residual limitation."
        )

    print(
        "\nFULL GATE 22B.6 PASS — The targeted action-head repair fixes the "
        "diagnosed Privacy precedence failure while preserving all four non-action "
        "heads and satisfying cumulative multi-output thresholds."
    )


if __name__ == "__main__":
    main()
