from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.data.loader import load_json
from medverse.evaluation.harness import Gate9EvaluationHarness
from medverse.evaluation.baselines import (
    SingleOmniscientBaseline,
    UnconstrainedRoleBaseline,
)

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate9"
OUT.mkdir(parents=True, exist_ok=True)

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 9")
    print(" Evaluation Harness and Baselines")
    print("========================================\n")

    checks = []

    try:
        harness = Gate9EvaluationHarness(ROOT)
        medverse = harness.run_medverse()
    except Exception as exc:
        status = {
            "gate": "GATE_9_EVALUATION_HARNESS",
            "status": "HOLD",
            "reason": str(exc),
        }
        (OUT / "gate9_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    expected_metrics = {
        "ARA": 1.0,
        "MCR": 1.0,
        "CSR": 1.0,
        "CDR": 1.0,
        "EAR": 1.0,
        "PGA": 1.0,
        "ILR": 0.0,
    }

    for metric, expected in expected_metrics.items():
        observed = medverse["metrics"][metric]
        checks.append(check(
            f"medverse_{metric}",
            observed == expected,
            observed,
            expected,
        ))

    # Metric range checks
    checks.append(check(
        "all_rates_in_valid_range",
        all(
            v is None or 0.0 <= v <= 1.0
            for v in medverse["metrics"].values()
        ),
        medverse["metrics"],
        "all metrics in [0,1]",
    ))


    # Counterfactual coordinator-domain regression checks.
    coordination_by_case = {
        r["case_id"]: r["correct"]
        for r in medverse["coordination_results"]
    }

    checks.append(check(
        "counterfactual_coordination_cases_reachable",
        all(
            coordination_by_case.get(case_id) is True
            for case_id in [
                "C1_S1_FULL",
                "C2_CLINICAL_ONLY",
                "C3_TECHNICAL_ONLY",
                "C4_NO_RISK",
            ]
        ),
        coordination_by_case,
        "all four coordinator cases correct",
    ))

    # Baseline construction sanity checks
    scenario = load_json(
        ROOT / "data" / "reference" / "MVKR-S01.json"
    )

    b1 = SingleOmniscientBaseline().evaluate_full_s1(
        scenario
    )
    b2 = UnconstrainedRoleBaseline().evaluate_full_s1(
        scenario
    )

    checks.append(check(
        "B1_coordination_outcome_defined",
        b1["coordination_state"] == "COMPLEMENTARY_RISK",
        b1["coordination_state"],
        "COMPLEMENTARY_RISK",
    ))

    checks.append(check(
        "B1_does_not_claim_institutional_partition",
        b1["institutional_partition_enforced"] is False,
        b1["institutional_partition_enforced"],
        False,
    ))

    checks.append(check(
        "B2_role_labels_without_hard_boundaries",
        b2["institutional_partition_enforced"] is False
        and b2["mandate_validation_enforced"] is False
        and b2["minimum_necessary_exchange_enforced"] is False,
        b2,
        "all three hard-boundary flags false",
    ))

    # Exact deterministic replay
    medverse2 = Gate9EvaluationHarness(ROOT).run_medverse()
    checks.append(check(
        "evaluation_replay_exact",
        medverse == medverse2,
        medverse == medverse2,
        True,
    ))

    # Results are harness validation only, not final scientific estimates.
    result_rows = [
        {
            "system": "MEDVERSE_AGENT",
            **medverse["metrics"],
        },
        {
            "system": "B1_SINGLE_OMNISCIENT",
            "ARA": "N/A",
            "MCR": "N/A",
            "CSR": "not_finally_estimated",
            "CDR": "not_finally_estimated",
            "EAR": "not_finally_estimated",
            "PGA": "N/A",
            "ILR": "not_finally_estimated",
        },
        {
            "system": "B2_UNCONSTRAINED_ROLES",
            "ARA": "not_applicable_without_partition",
            "MCR": "not_applicable_without_mandate_enforcement",
            "CSR": "not_finally_estimated",
            "CDR": "not_finally_estimated",
            "EAR": "not_finally_estimated",
            "PGA": "N/A",
            "ILR": "not_finally_estimated",
        },
    ]

    with (OUT / "gate9_harness_metrics.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "system", "ARA", "MCR", "CSR",
                "CDR", "EAR", "PGA", "ILR",
            ],
        )
        writer.writeheader()
        writer.writerows(result_rows)

    (OUT / "gate9_medverse_details.json").write_text(
        json.dumps(
            medverse,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    (OUT / "gate9_baseline_sanity.json").write_text(
        json.dumps(
            {
                "B1_SINGLE_OMNISCIENT": b1,
                "B2_UNCONSTRAINED_ROLES": b2,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with (OUT / "gate9_checks.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "check",
                "status",
                "observed",
                "expected",
            ],
        )
        writer.writeheader()
        writer.writerows(checks)

    passed = sum(
        c["status"] == "PASS"
        for c in checks
    )
    total = len(checks)
    gate_pass = passed == total

    status = {
        "gate": "GATE_9_EVALUATION_HARNESS",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "metrics_validated": list(
            expected_metrics.keys()
        ),
        "baselines_constructed": [
            "B1_SINGLE_OMNISCIENT",
            "B2_UNCONSTRAINED_ROLES",
        ],
        "final_scientific_results": False,
    }

    (OUT / "gate9_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 9 FAILED. Diagnose metric/baseline implementation "
            "before final experiment generation."
        )

    print(
        "\nFULL GATE 9 PASS — evaluation harness validated. "
        "No final scientific performance claim is made yet."
    )

if __name__ == "__main__":
    main()
