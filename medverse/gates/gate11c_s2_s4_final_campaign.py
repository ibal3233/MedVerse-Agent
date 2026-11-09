from __future__ import annotations

from pathlib import Path
import sys
import csv
import json
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.experiments.institutional_campaign import (
    InstitutionalCampaignRunner,
)

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate11c"
OUT.mkdir(parents=True, exist_ok=True)

SPEC = (
    ROOT / "data" / "experiments"
    / "gate11c_s2_s4_variants.json"
)

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def aggregate(rows, system):
    subset = [r for r in rows if r["system"] == system]
    metrics = ["ARA", "MCR", "CSR", "CDR", "EAR", "PGA", "ILR"]
    out = {"system": system, "n_variants": len(subset)}

    for metric in metrics:
        vals = [r[metric] for r in subset if r[metric] is not None]
        out[metric] = None if not vals else mean(vals)

    return out

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 11C")
    print(" S2-S4 Final Benchmark Campaign")
    print("========================================\n")

    registry = json.loads(
        (ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8")
    )
    gate11b = registry.get("promoted_gates", {}).get("GATE_11B", {})

    if gate11b.get("status") != "PASS":
        status = {
            "gate": "GATE_11C_S2_S4_FINAL_CAMPAIGN",
            "status": "HOLD",
            "reason": "Gate 11B is not promoted PASS in FREEZE_REGISTRY.json.",
        }
        (OUT / "gate11c_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    variants = spec["variants"]
    repetitions = 10

    runner = InstitutionalCampaignRunner(ROOT)

    rows = []
    for variant in variants:
        scenario = runner.load_scenario(variant["scenario_file"])

        for rep in range(1, repetitions + 1):
            for result in [
                runner.run_b1(scenario, variant),
                runner.run_b2(scenario, variant),
                runner.run_medverse(scenario, variant),
            ]:
                result["repetition"] = rep
                rows.append(result)

    checks = []

    expected_rows = len(variants) * repetitions * 3
    checks.append(check(
        "expected_raw_row_count",
        len(rows) == expected_rows,
        len(rows),
        expected_rows,
    ))

    deterministic_ok = True
    details = []

    for system in [
        "B1_SINGLE_OMNISCIENT",
        "B2_UNCONSTRAINED_ROLES",
        "B3_MEDVERSE_AGENT",
    ]:
        for variant in variants:
            subset = [
                r for r in rows
                if r["system"] == system
                and r["variant_id"] == variant["variant_id"]
            ]
            signatures = {
                json.dumps(
                    {k: v for k, v in r.items() if k != "repetition"},
                    sort_keys=True,
                )
                for r in subset
            }
            ok = len(signatures) == 1
            deterministic_ok = deterministic_ok and ok
            details.append({
                "system": system,
                "variant_id": variant["variant_id"],
                "unique_signatures": len(signatures),
            })

    checks.append(check(
        "exact_determinism_across_repetitions",
        deterministic_ok,
        details,
        "one unique result per system/variant",
    ))

    b3 = [r for r in rows if r["system"] == "B3_MEDVERSE_AGENT"]

    for metric, expected in [
        ("ARA", 1.0),
        ("MCR", 1.0),
        ("CSR", 1.0),
        ("CDR", 1.0),
        ("EAR", 1.0),
        ("ILR", 0.0),
    ]:
        checks.append(check(
            f"medverse_all_{metric}",
            all(r[metric] == expected for r in b3),
            sorted(set(r[metric] for r in b3)),
            [expected],
        ))

    # PGA is intentionally unscored until authoritative policy evidence for
    # Privacy/IRB/Regulator is ingested and validated.
    checks.append(check(
        "PGA_intentionally_deferred",
        all(r["PGA"] is None for r in b3),
        sorted(set(str(r["PGA"]) for r in b3)),
        ["None"],
    ))

    raw_fields = [
        "system", "variant_id", "scenario_id", "repetition",
        "coordination_state", "human_review_required",
        "ARA", "MCR", "CSR", "CDR", "EAR", "PGA", "ILR",
    ]

    with (OUT / "gate11c_raw_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=raw_fields)
        writer.writeheader()
        writer.writerows(rows)

    unique_rows = []
    seen = set()

    for r in rows:
        key = (r["system"], r["variant_id"])
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append({k: v for k, v in r.items() if k != "repetition"})

    with (OUT / "gate11c_per_variant_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "system", "variant_id", "scenario_id",
                "coordination_state", "human_review_required",
                "ARA", "MCR", "CSR", "CDR", "EAR", "PGA", "ILR",
            ],
        )
        writer.writeheader()
        writer.writerows(unique_rows)

    aggregates = [
        aggregate(unique_rows, "B1_SINGLE_OMNISCIENT"),
        aggregate(unique_rows, "B2_UNCONSTRAINED_ROLES"),
        aggregate(unique_rows, "B3_MEDVERSE_AGENT"),
    ]

    with (OUT / "gate11c_aggregate_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "system", "n_variants",
                "ARA", "MCR", "CSR", "CDR", "EAR", "PGA", "ILR",
            ],
        )
        writer.writeheader()
        writer.writerows(aggregates)

    with (OUT / "gate11c_checks.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "observed", "expected"],
        )
        writer.writeheader()
        writer.writerows(checks)

    coverage = {
        "operational_final_evidence": {
            "S1": True,
            "S2": True,
            "S3": True,
            "S4": True,
        },
        "policy_grounding_final_evidence": {
            "S1": True,
            "S2": False,
            "S3": False,
            "S4": False,
        },
        "reason": (
            "Authoritative policy KB expansion for Privacy/IRB/Regulator "
            "has not yet been validated."
        ),
        "full_gate10_operational_coverage": True,
        "full_gate10_policy_grounding_coverage": False,
    }

    (OUT / "gate11c_coverage.json").write_text(
        json.dumps(coverage, indent=2),
        encoding="utf-8",
    )

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)
    gate_pass = passed == total

    status = {
        "gate": "GATE_11C_S2_S4_FINAL_CAMPAIGN",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "scenario_families": 3,
        "variants": len(variants),
        "deterministic_repetitions": repetitions,
        "systems": 3,
        "raw_rows": len(rows),
        "operational_final_results_generated": gate_pass,
        "policy_grounding_final_results_generated": False,
        "full_gate10_operational_coverage": gate_pass,
        "full_gate10_policy_grounding_coverage": False,
    }

    (OUT / "gate11c_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 11C FAILED. Diagnose S2-S4 campaign results before policy-KB expansion."
        )

    print(
        "\nFULL GATE 11C PASS — operational benchmark evidence now covers "
        "S1-S4. Policy-grounding evidence for S2-S4 remains explicitly deferred."
    )

if __name__ == "__main__":
    main()
