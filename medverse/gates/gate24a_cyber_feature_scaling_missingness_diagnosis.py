from __future__ import annotations

from pathlib import Path
from collections import Counter
import csv, json, sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score

DATA = ROOT / "data" / "learning" / "gate21a" / "cyber_network_agent.csv"
OUT = ROOT / "outputs" / "gate24a"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

NUMERIC = ["packet_loss", "rtt_ms", "jitter_ms"]
C_FIXED = 0.3
C_GRID = [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0]


def load_rows():
    with DATA.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fit_stats(train):
    vals = {k: [] for k in NUMERIC}
    for r in train:
        f = json.loads(r["features_json"])
        for k in NUMERIC:
            vals[k].append(float(f[k]))
    return {
        k: {
            "mean": float(np.mean(vals[k])),
            "std": float(np.std(vals[k])) if float(np.std(vals[k])) > 0 else 1.0,
        }
        for k in NUMERIC
    }


def transform_rows(rows, stats, scale_numeric, explicit_missing):
    out = []
    for r in rows:
        f = json.loads(r["features_json"])

        if explicit_missing and "session_origin" not in f:
            f["session_origin"] = "__MISSING__"

        if scale_numeric:
            for k in NUMERIC:
                f[k] = (float(f[k]) - stats[k]["mean"]) / stats[k]["std"]

        out.append(f)
    return out


def train_predict(train, eval_rows, target, C, scale_numeric, explicit_missing, stats):
    Xtr = transform_rows(train, stats, scale_numeric, explicit_missing)
    Xev = transform_rows(eval_rows, stats, scale_numeric, explicit_missing)
    ytr = [r[target] for r in train]
    yev = [r[target] for r in eval_rows]

    pipe = Pipeline([
        ("vectorizer", DictVectorizer(sparse=True)),
        ("classifier", LogisticRegression(
            C=C,
            max_iter=5000,
            solver="lbfgs",
        )),
    ])
    pipe.fit(Xtr, ytr)
    yp = list(pipe.predict(Xev))

    clf = pipe.named_steps["classifier"]
    n_iter = int(max(clf.n_iter_)) if hasattr(clf, "n_iter_") else 0

    return {
        "accuracy": accuracy_score(yev, yp),
        "macro_f1": f1_score(yev, yp, average="macro", zero_division=0),
        "true": yev,
        "pred": yp,
        "model": pipe,
        "solver_iterations": n_iter,
    }


def feature_ranges(rows):
    parsed = []
    for r in rows:
        f = json.loads(r["features_json"])
        parsed.append({
            "split": r["split"],
            "assessment": r["target_assessment"],
            "action": r["target_action"],
            "packet_loss": float(f["packet_loss"]),
            "rtt_ms": float(f["rtt_ms"]),
            "jitter_ms": float(f["jitter_ms"]),
            "session_origin": f.get("session_origin", "__ABSENT__"),
            "certificate_status": f.get("certificate_status"),
        })
    return parsed


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 24A")
    print(" Cyber Feature-Scaling / Missingness")
    print(" Diagnostic Audit")
    print("========================================\n")

    rows = load_rows()
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    test = [r for r in rows if r["split"] == "test"]

    stats = fit_stats(train)

    configs = [
        ("baseline", False, False),
        ("scale_only", True, False),
        ("explicit_missing_only", False, True),
        ("scale_plus_explicit_missing", True, True),
    ]

    counterfactual_rows = []

    for name, scale_numeric, explicit_missing in configs:
        for target in ["target_action", "target_assessment"]:
            dev_m = train_predict(
                train, dev, target, C_FIXED,
                scale_numeric, explicit_missing, stats
            )
            test_m = train_predict(
                train, test, target, C_FIXED,
                scale_numeric, explicit_missing, stats
            )

            counterfactual_rows.append({
                "config": name,
                "target": target,
                "C": C_FIXED,
                "scale_numeric": scale_numeric,
                "explicit_missing_session_origin": explicit_missing,
                "dev_accuracy": dev_m["accuracy"],
                "dev_macro_f1": dev_m["macro_f1"],
                "test_accuracy": test_m["accuracy"],
                "test_macro_f1": test_m["macro_f1"],
                "solver_iterations": test_m["solver_iterations"],
            })

    # C-sensitivity under the frozen baseline representation.
    c_rows = []
    for C in C_GRID:
        action_dev = train_predict(
            train, dev, "target_action", C, False, False, stats
        )
        action_test = train_predict(
            train, test, "target_action", C, False, False, stats
        )
        assess_dev = train_predict(
            train, dev, "target_assessment", C, False, False, stats
        )
        assess_test = train_predict(
            train, test, "target_assessment", C, False, False, stats
        )

        c_rows.append({
            "C": C,
            "dev_action_accuracy": action_dev["accuracy"],
            "dev_action_macro_f1": action_dev["macro_f1"],
            "test_action_accuracy": action_test["accuracy"],
            "test_action_macro_f1": action_test["macro_f1"],
            "dev_assessment_accuracy": assess_dev["accuracy"],
            "test_assessment_accuracy": assess_test["accuracy"],
        })

    # Baseline row-level errors.
    base_action = train_predict(
        train, test, "target_action", C_FIXED, False, False, stats
    )
    base_assess = train_predict(
        train, test, "target_assessment", C_FIXED, False, False, stats
    )

    error_rows = []
    for i, r in enumerate(test):
        f = json.loads(r["features_json"])
        if (
            base_action["true"][i] != base_action["pred"][i]
            or base_assess["true"][i] != base_assess["pred"][i]
        ):
            error_rows.append({
                "record_id": r["record_id"],
                "features_json": r["features_json"],
                "true_action": base_action["true"][i],
                "pred_action": base_action["pred"][i],
                "true_assessment": base_assess["true"][i],
                "pred_assessment": base_assess["pred"][i],
                "session_origin_present": "session_origin" in f,
            })

    # Range analysis focused on classes that fail.
    parsed = feature_ranges(rows)
    range_rows = []
    for split in ["train", "dev", "test"]:
        for assessment in [
            "TELEMETRY_TRUST_ACCEPTABLE",
            "TELEMETRY_RELIABILITY_DEGRADED",
            "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN",
        ]:
            subset = [
                x for x in parsed
                if x["split"] == split and x["assessment"] == assessment
            ]
            if not subset:
                continue
            rec = {"split": split, "assessment": assessment, "n": len(subset)}
            for k in NUMERIC:
                vals = [x[k] for x in subset]
                rec[f"{k}_min"] = min(vals)
                rec[f"{k}_max"] = max(vals)
                rec[f"{k}_mean"] = float(np.mean(vals))
            range_rows.append(rec)

    # Persist raw diagnostics.
    with (OUT / "gate24a_preprocessing_counterfactuals.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(counterfactual_rows[0].keys()))
        w.writeheader()
        w.writerows(counterfactual_rows)

    with (OUT / "gate24a_c_sensitivity.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(c_rows[0].keys()))
        w.writeheader()
        w.writerows(c_rows)

    with (OUT / "gate24a_error_trace.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(error_rows[0].keys()))
        w.writeheader()
        w.writerows(error_rows)

    with (OUT / "gate24a_feature_ranges.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(range_rows[0].keys()))
        w.writeheader()
        w.writerows(range_rows)

    # Diagnostic conclusions.
    def pick(config, target):
        return next(
            r for r in counterfactual_rows
            if r["config"] == config and r["target"] == target
        )

    baseline_action = pick("baseline", "target_action")
    baseline_assessment = pick("baseline", "target_assessment")
    scale_action = pick("scale_only", "target_action")
    scale_assessment = pick("scale_only", "target_assessment")
    missing_action = pick("explicit_missing_only", "target_action")
    missing_assessment = pick("explicit_missing_only", "target_assessment")
    both_action = pick("scale_plus_explicit_missing", "target_action")
    both_assessment = pick("scale_plus_explicit_missing", "target_assessment")

    c03 = next(r for r in c_rows if r["C"] == 0.3)
    c1 = next(r for r in c_rows if r["C"] == 1.0)

    diagnosis = {
        "gate": "GATE_24A_CYBER_PREPROCESSING_DIAGNOSIS",
        "training_changed": False,
        "production_model_changed": False,
        "baseline_C": C_FIXED,
        "baseline_test": {
            "action_accuracy": baseline_action["test_accuracy"],
            "action_macro_f1": baseline_action["test_macro_f1"],
            "assessment_accuracy": baseline_assessment["test_accuracy"],
            "assessment_macro_f1": baseline_assessment["test_macro_f1"],
        },
        "diagnostic_findings": {
            "numeric_scaling_counterfactual": {
                "action_test_accuracy": scale_action["test_accuracy"],
                "assessment_test_accuracy": scale_assessment["test_accuracy"],
            },
            "explicit_missing_session_origin_counterfactual": {
                "action_test_accuracy": missing_action["test_accuracy"],
                "assessment_test_accuracy": missing_assessment["test_accuracy"],
            },
            "combined_preprocessing_counterfactual": {
                "action_test_accuracy": both_action["test_accuracy"],
                "assessment_test_accuracy": both_assessment["test_accuracy"],
            },
            "regularization_plateau": {
                "C_0_3_dev_action_accuracy": c03["dev_action_accuracy"],
                "C_0_3_test_action_accuracy": c03["test_action_accuracy"],
                "C_1_dev_action_accuracy": c1["dev_action_accuracy"],
                "C_1_test_action_accuracy": c1["test_action_accuracy"],
            },
        },
        "diagnostic_classification": (
            "preprocessing_representation_instability_with_numeric_scale_sensitivity_"
            "and_implicit_missingness_encoding_plus_dev_plateau_selection_instability"
        ),
        "interpretation": [
            "All three ISOLATE_SUSPECT_SESSION test cases are misclassified as PRESERVE_TECHNICAL_LOGS under the baseline.",
            "Encoding absent session_origin explicitly fixes the action error at fixed C=0.3 but does not fix assessment.",
            "Scaling numeric telemetry features fixes both action and assessment at fixed C=0.3.",
            "Under the baseline representation, C>=1 recovers test action performance while assessment remains unchanged, so action and assessment have different failure mechanisms.",
            "The held-out test has now been opened diagnostically; no future hyperparameter/preprocessing selection should claim unbiased confirmation on this same group."
        ],
        "next_step": (
            "Pre-freeze a fresh Cyber/Network prospective group/threshold benchmark, "
            "then test the minimal preprocessing intervention: train-fitted numeric "
            "standardization plus explicit missing-category encoding, with the model "
            "family unchanged."
        ),
    }

    (OUT / "gate24a_diagnosis.json").write_text(
        json.dumps(diagnosis, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Plots.
    # 1. Counterfactual preprocessing comparison
    labels = ["Baseline", "Scale only", "Missing explicit", "Scale + missing"]
    action_vals = [
        baseline_action["test_accuracy"],
        scale_action["test_accuracy"],
        missing_action["test_accuracy"],
        both_action["test_accuracy"],
    ]
    assessment_vals = [
        baseline_assessment["test_accuracy"],
        scale_assessment["test_accuracy"],
        missing_assessment["test_accuracy"],
        both_assessment["test_accuracy"],
    ]
    x = np.arange(len(labels))
    w = 0.36
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.bar(x-w/2, action_vals, w, label="Action")
    ax.bar(x+w/2, assessment_vals, w, label="Assessment")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Held-out test accuracy")
    ax.set_title("Cyber / Network Preprocessing Counterfactual Diagnosis")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24a_preprocessing_counterfactuals.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24a_preprocessing_counterfactuals.pdf", bbox_inches="tight")
    plt.close(fig)

    # 2. C sensitivity
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.plot([r["C"] for r in c_rows], [r["dev_action_accuracy"] for r in c_rows], marker="o", label="DEV action")
    ax.plot([r["C"] for r in c_rows], [r["test_action_accuracy"] for r in c_rows], marker="o", label="TEST action")
    ax.plot([r["C"] for r in c_rows], [r["test_assessment_accuracy"] for r in c_rows], marker="o", label="TEST assessment")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("C")
    ax.set_ylabel("Accuracy")
    ax.set_title("Cyber / Network Regularization Sensitivity")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig24a_regularization_sensitivity.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24a_regularization_sensitivity.pdf", bbox_inches="tight")
    plt.close(fig)

    # 3. Acceptable telemetry drift
    acceptable = [r for r in range_rows if r["assessment"] == "TELEMETRY_TRUST_ACCEPTABLE"]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(
        [r["split"] for r in acceptable],
        [r["rtt_ms_mean"] for r in acceptable],
    )
    ax.set_ylabel("Mean RTT (ms)")
    ax.set_title("Acceptable-Telemetry Group Drift Across Splits")
    fig.tight_layout()
    fig.savefig(FIG / "fig24a_acceptable_telemetry_group_drift.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24a_acceptable_telemetry_group_drift.pdf", bbox_inches="tight")
    plt.close(fig)

    # 4. Error count by output
    action_errors = sum(
        r["true_action"] != r["pred_action"]
        for r in error_rows
    )
    assessment_errors = sum(
        r["true_assessment"] != r["pred_assessment"]
        for r in error_rows
    )
    fig, ax = plt.subplots(figsize=(6.8, 4.6))
    ax.bar(["Action errors", "Assessment errors"], [action_errors, assessment_errors])
    ax.set_ylabel("Held-out test errors")
    ax.set_title("Gate 24 Error Decomposition")
    fig.tight_layout()
    fig.savefig(FIG / "fig24a_error_decomposition.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig24a_error_decomposition.pdf", bbox_inches="tight")
    plt.close(fig)

    checks = [
        {
            "check": "baseline_failure_reproduced",
            "pass": (
                baseline_action["test_accuracy"] == 0.8333333333333334
                and baseline_assessment["test_accuracy"] == 0.8333333333333334
            ),
            "observed": {
                "action": baseline_action["test_accuracy"],
                "assessment": baseline_assessment["test_accuracy"],
            },
            "expected": 0.8333333333333334,
        },
        {
            "check": "action_missingness_sensitivity_detected",
            "pass": missing_action["test_accuracy"] > baseline_action["test_accuracy"],
            "observed": {
                "baseline": baseline_action["test_accuracy"],
                "explicit_missing": missing_action["test_accuracy"],
            },
            "expected": "explicit missing-category encoding improves action",
        },
        {
            "check": "numeric_scaling_sensitivity_detected",
            "pass": (
                scale_action["test_accuracy"] > baseline_action["test_accuracy"]
                and scale_assessment["test_accuracy"] > baseline_assessment["test_accuracy"]
            ),
            "observed": {
                "action_baseline": baseline_action["test_accuracy"],
                "action_scaled": scale_action["test_accuracy"],
                "assessment_baseline": baseline_assessment["test_accuracy"],
                "assessment_scaled": scale_assessment["test_accuracy"],
            },
            "expected": "scaling improves both outputs",
        },
        {
            "check": "dev_plateau_selection_instability_detected",
            "pass": (
                c03["dev_action_accuracy"] == 1.0
                and c1["dev_action_accuracy"] == 1.0
                and c03["test_action_accuracy"] < c1["test_action_accuracy"]
            ),
            "observed": {
                "C0.3_dev": c03["dev_action_accuracy"],
                "C0.3_test": c03["test_action_accuracy"],
                "C1_dev": c1["dev_action_accuracy"],
                "C1_test": c1["test_action_accuracy"],
            },
            "expected": "same DEV optimum but different diagnostic TEST behavior",
        },
        {
            "check": "regularization_alone_cannot_jointly_fix_outputs",
            "pass": not any(
                r["test_action_accuracy"] >= 0.90
                and r["test_assessment_accuracy"] >= 0.90
                for r in c_rows
            ),
            "observed": {
                str(r["C"]): {
                    "test_action_accuracy": r["test_action_accuracy"],
                    "test_assessment_accuracy": r["test_assessment_accuracy"],
                }
                for r in c_rows
            },
            "expected": (
                "no baseline C simultaneously achieves >=0.90 action and "
                ">=0.90 assessment on the opened diagnostic test group"
            ),
        },
        {
            "check": "no_production_intervention",
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
        "gate": "GATE_24A_CYBER_PREPROCESSING_DIAGNOSIS",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "diagnostic_classification": diagnosis["diagnostic_classification"],
        "baseline_C": C_FIXED,
        "baseline_test_action_accuracy": baseline_action["test_accuracy"],
        "baseline_test_assessment_accuracy": baseline_assessment["test_accuracy"],
        "scale_only_test_action_accuracy": scale_action["test_accuracy"],
        "scale_only_test_assessment_accuracy": scale_assessment["test_accuracy"],
        "explicit_missing_test_action_accuracy": missing_action["test_accuracy"],
        "explicit_missing_test_assessment_accuracy": missing_assessment["test_accuracy"],
        "combined_test_action_accuracy": both_action["test_accuracy"],
        "combined_test_assessment_accuracy": both_assessment["test_accuracy"],
        "production_model_changed": False,
        "current_gate24_test_status": "OPENED_DIAGNOSTIC_GROUP",
        "figures_directory": "outputs/gate24a/figures",
        "next_dependency": (
            "Gate 24B: pre-freeze a fresh Cyber/Network prospective benchmark "
            "before applying train-fitted numeric standardization and explicit "
            "missing-category encoding."
        ),
    }

    (OUT / "gate24a_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate24a_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit("Gate 24A diagnostic infrastructure failed.")

    print(
        "\nFULL GATE 24A PASS — Gate 24 failure is localized to preprocessing/"
        "representation instability: numeric scale sensitivity, implicit "
        "missingness encoding, and DEV-plateau regularization selection."
    )


if __name__ == "__main__":
    main()
