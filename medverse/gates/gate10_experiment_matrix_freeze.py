from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate10"
OUT.mkdir(parents=True, exist_ok=True)

REGRESSION_STATUS = (
    ROOT / "outputs" / "regression_post_gate9"
    / "regression_status.json"
)
MATRIX = (
    ROOT / "data" / "experiments"
    / "gate10_experiment_matrix.json"
)

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 10")
    print(" Final Experiment-Matrix Freeze")
    print("========================================\n")

    if not REGRESSION_STATUS.exists():
        status = {
            "gate": "GATE_10_EXPERIMENT_MATRIX_FREEZE",
            "status": "HOLD",
            "reason": (
                "Post-Gate-9 regression has not been run. "
                "Run regression_post_gate9_patch.py first."
            ),
        }
        (OUT / "gate10_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    regression = json.loads(
        REGRESSION_STATUS.read_text(encoding="utf-8")
    )

    if regression.get("status") != "PASS":
        status = {
            "gate": "GATE_10_EXPERIMENT_MATRIX_FREEZE",
            "status": "HOLD",
            "reason": "Post-Gate-9 regression is not PASS.",
            "regression_status": regression,
        }
        (OUT / "gate10_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    matrix = json.loads(
        MATRIX.read_text(encoding="utf-8")
    )

    checks = []

    systems = matrix["systems"]
    metrics = matrix["metrics"]
    scenario_ids = {
        s["scenario_id"]
        for s in matrix["scenario_families"]
    }

    checks.append(check(
        "three_systems_defined",
        systems == [
            "B1_SINGLE_OMNISCIENT",
            "B2_UNCONSTRAINED_ROLES",
            "B3_MEDVERSE_AGENT",
        ],
        systems,
        "B1/B2/B3",
    ))

    checks.append(check(
        "all_seven_metrics_defined",
        set(metrics) == {
            "ARA", "MCR", "CSR", "CDR",
            "EAR", "PGA", "ILR",
        },
        sorted(metrics),
        ["ARA", "CDR", "CSR", "EAR", "ILR", "MCR", "PGA"],
    ))

    checks.append(check(
        "four_scenario_families_defined",
        scenario_ids == {
            "S1_COMPLEMENTARY_RISK",
            "S2_CARE_VS_RESEARCH",
            "S3_STALE_DT_AI_RECOMMENDATION",
            "S4_UNAUTHORIZED_DISCLOSURE",
        },
        sorted(scenario_ids),
        "S1-S4",
    ))

    checks.append(check(
        "perturbation_axes_nonempty",
        len(matrix["perturbation_axes"]) >= 5
        and all(a["values"] for a in matrix["perturbation_axes"]),
        len(matrix["perturbation_axes"]),
        ">=5 nonempty axes",
    ))

    checks.append(check(
        "claim_map_nonempty",
        len(matrix["claim_map"]) >= 3,
        len(matrix["claim_map"]),
        ">=3 claims",
    ))

    # Every claim must map to a valid metric, baseline and scenario.
    claim_integrity = True
    integrity_details = []

    for claim in matrix["claim_map"]:
        bad_metrics = [
            m for m in claim["primary_metrics"]
            if m not in metrics
        ]
        bad_baselines = [
            b for b in claim["baselines"]
            if b not in systems
        ]
        bad_scenarios = [
            s for s in claim["required_scenarios"]
            if s not in scenario_ids
        ]

        ok = (
            not bad_metrics
            and not bad_baselines
            and not bad_scenarios
            and bool(claim["report_artifact"])
        )
        claim_integrity = claim_integrity and ok

        integrity_details.append({
            "claim_id": claim["claim_id"],
            "ok": ok,
            "bad_metrics": bad_metrics,
            "bad_baselines": bad_baselines,
            "bad_scenarios": bad_scenarios,
        })

    checks.append(check(
        "claim_to_experiment_mapping_valid",
        claim_integrity,
        integrity_details,
        "all claim mappings valid",
    ))

    rules = matrix["final_reporting_rules"]

    checks.append(check(
        "fixture_results_prohibited_as_final",
        rules["no_fixture_as_final_result"] is True,
        rules["no_fixture_as_final_result"],
        True,
    ))

    checks.append(check(
        "raw_results_required",
        rules["raw_csv_preserved"] is True,
        rules["raw_csv_preserved"],
        True,
    ))

    checks.append(check(
        "stochastic_uncertainty_rule_present",
        rules["uncertainty_required_for_stochastic_components"] is True,
        rules["uncertainty_required_for_stochastic_components"],
        True,
    ))

    checks.append(check(
        "live_llm_separated_from_core",
        rules["live_llm_results_separate_from_deterministic_core"] is True,
        rules["live_llm_results_separate_from_deterministic_core"],
        True,
    ))

    # Save a human-readable experiment table.
    rows = []
    for claim in matrix["claim_map"]:
        rows.append({
            "claim_id": claim["claim_id"],
            "claim": claim["claim"],
            "metrics": "|".join(claim["primary_metrics"]),
            "baselines": "|".join(claim["baselines"]),
            "scenarios": "|".join(claim["required_scenarios"]),
            "report_artifact": claim["report_artifact"],
        })

    with (OUT / "gate10_claim_experiment_map.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "claim_id",
                "claim",
                "metrics",
                "baselines",
                "scenarios",
                "report_artifact",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    with (OUT / "gate10_checks.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "observed", "expected"],
        )
        writer.writeheader()
        writer.writerows(checks)

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)
    gate_pass = passed == total

    status = {
        "gate": "GATE_10_EXPERIMENT_MATRIX_FREEZE",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "matrix_version": matrix["matrix_version"],
        "scenario_families": len(matrix["scenario_families"]),
        "perturbation_axes": len(matrix["perturbation_axes"]),
        "claims_mapped": len(matrix["claim_map"]),
        "final_results_generated": False,
    }

    (OUT / "gate10_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 10 FAILED. Diagnose experiment-matrix inconsistency "
            "before generating final benchmark data."
        )

    print(
        "\nFULL GATE 10 PASS — experiment matrix is eligible to freeze. "
        "Final benchmark generation may begin."
    )

if __name__ == "__main__":
    main()
