from __future__ import annotations

from pathlib import Path
import sys
import csv
import json
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.experiments.s1_campaign import S1CampaignRunner

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate11a"
OUT.mkdir(parents=True, exist_ok=True)

VARIANTS = (
    ROOT / "data" / "experiments"
    / "gate11a_s1_variants.json"
)

FREEZE_REGISTRY = (
    ROOT / "FREEZE_REGISTRY.json"
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
        vals = [
            r[metric] for r in subset
            if r[metric] is not None
        ]
        out[metric] = None if not vals else mean(vals)

    return out

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 11A")
    print(" S1 Final Benchmark Campaign")
    print("========================================\n")

    if not FREEZE_REGISTRY.exists():
        status = {
            "gate": "GATE_11A_S1_FINAL_CAMPAIGN",
            "status": "HOLD",
            "reason": "Persistent freeze registry not found.",
        }
        (OUT / "gate11a_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    registry = json.loads(
        FREEZE_REGISTRY.read_text(encoding="utf-8")
    )

    gate10 = registry.get(
        "promoted_gates", {}
    ).get("GATE_10", {})

    if gate10.get("status") != "PASS":
        status = {
            "gate": "GATE_11A_S1_FINAL_CAMPAIGN",
            "status": "HOLD",
            "reason": "Gate 10 is not promoted PASS in FREEZE_REGISTRY.json.",
            "gate10_registry_entry": gate10,
        }
        (OUT / "gate11a_status.json").write_text(
            json.dumps(status, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(status, indent=2))
        return

    spec = json.loads(
        VARIANTS.read_text(encoding="utf-8")
    )
    variants = spec["variants"]

    runner = S1CampaignRunner(ROOT)

    rows = []

    # Frozen repetition count from Gate 10 deterministic core.
    repetitions = 10

    for variant in variants:
        for rep in range(1, repetitions + 1):
            for result in [
                runner.run_b1(variant),
                runner.run_b2(variant),
                runner.run_medverse(variant),
            ]:
                result["repetition"] = rep
                rows.append(result)

    checks = []

    expected_rows = (
        len(variants)
        * repetitions
        * 3
    )

    checks.append(check(
        "expected_raw_row_count",
        len(rows) == expected_rows,
        len(rows),
        expected_rows,
    ))

    # Exact determinism: each system/variant should have one unique result
    # across the 10 repetitions when repetition index is ignored.
    deterministic_ok = True
    deterministic_details = []

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
                    {
                        k: v for k, v in r.items()
                        if k != "repetition"
                    },
                    sort_keys=True,
                )
                for r in subset
            }

            ok = len(signatures) == 1
            deterministic_ok = deterministic_ok and ok

            deterministic_details.append({
                "system": system,
                "variant_id": variant["variant_id"],
                "unique_signatures": len(signatures),
            })

    checks.append(check(
        "exact_determinism_across_repetitions",
        deterministic_ok,
        deterministic_details,
        "one unique result per system/variant",
    ))

    # MedVerse must satisfy all implemented S1 expectations.
    b3 = [
        r for r in rows
        if r["system"] == "B3_MEDVERSE_AGENT"
    ]

    checks.append(check(
        "medverse_all_S1_CSR",
        all(r["CSR"] == 1.0 for r in b3),
        sorted(set(r["CSR"] for r in b3)),
        [1.0],
    ))

    checks.append(check(
        "medverse_all_S1_EAR",
        all(r["EAR"] == 1.0 for r in b3),
        sorted(set(r["EAR"] for r in b3)),
        [1.0],
    ))

    checks.append(check(
        "medverse_all_S1_ARA",
        all(r["ARA"] == 1.0 for r in b3),
        sorted(set(r["ARA"] for r in b3)),
        [1.0],
    ))

    checks.append(check(
        "medverse_all_S1_MCR",
        all(r["MCR"] == 1.0 for r in b3),
        sorted(set(r["MCR"] for r in b3)),
        [1.0],
    ))

    checks.append(check(
        "medverse_all_S1_PGA",
        all(r["PGA"] == 1.0 for r in b3),
        sorted(set(r["PGA"] for r in b3)),
        [1.0],
    ))

    # ILR may be None for a variant with no unauthorized probe only if there
    # were no cross-agent alternatives. Here each implemented variant has at
    # least one unauthorized-observation probe.
    checks.append(check(
        "medverse_all_S1_ILR_zero",
        all(r["ILR"] == 0.0 for r in b3),
        sorted(set(r["ILR"] for r in b3)),
        [0.0],
    ))

    # Coverage boundary: S2-S4 are still not implemented.
    implemented_families = {"S1_COMPLEMENTARY_RISK"}
    missing_families = [
        "S2_CARE_VS_RESEARCH",
        "S3_STALE_DT_AI_RECOMMENDATION",
        "S4_UNAUTHORIZED_DISCLOSURE",
    ]

    # This is deliberately reported, not failed: Gate 11A scope is explicitly S1.
    coverage = {
        "implemented_final_campaign_families": sorted(implemented_families),
        "not_yet_implemented": missing_families,
        "overall_gate10_claims_ready": False,
    }

    # Save raw rows
    raw_fields = [
        "system",
        "variant_id",
        "repetition",
        "coordination_state",
        "human_review_required",
        "ARA",
        "MCR",
        "CSR",
        "CDR",
        "EAR",
        "PGA",
        "ILR",
    ]

    with (OUT / "gate11a_raw_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=raw_fields,
        )
        writer.writeheader()
        writer.writerows(rows)

    # Per-variant unique results, one per system/variant.
    unique_rows = []
    seen = set()
    for r in rows:
        key = (r["system"], r["variant_id"])
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append({
            k: v for k, v in r.items()
            if k != "repetition"
        })

    with (OUT / "gate11a_per_variant_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "system",
                "variant_id",
                "coordination_state",
                "human_review_required",
                "ARA",
                "MCR",
                "CSR",
                "CDR",
                "EAR",
                "PGA",
                "ILR",
            ],
        )
        writer.writeheader()
        writer.writerows(unique_rows)

    aggregates = [
        aggregate(unique_rows, "B1_SINGLE_OMNISCIENT"),
        aggregate(unique_rows, "B2_UNCONSTRAINED_ROLES"),
        aggregate(unique_rows, "B3_MEDVERSE_AGENT"),
    ]

    with (OUT / "gate11a_aggregate_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "system",
                "n_variants",
                "ARA",
                "MCR",
                "CSR",
                "CDR",
                "EAR",
                "PGA",
                "ILR",
            ],
        )
        writer.writeheader()
        writer.writerows(aggregates)

    with (OUT / "gate11a_checks.csv").open(
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

    (OUT / "gate11a_coverage.json").write_text(
        json.dumps(
            coverage,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    passed = sum(
        c["status"] == "PASS"
        for c in checks
    )
    total = len(checks)
    gate_pass = passed == total

    status = {
        "gate": "GATE_11A_S1_FINAL_CAMPAIGN",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "scenario_family": "S1_COMPLEMENTARY_RISK",
        "variants": len(variants),
        "deterministic_repetitions": repetitions,
        "systems": 3,
        "raw_rows": len(rows),
        "s1_final_results_generated": gate_pass,
        "full_gate10_matrix_final_results_generated": False,
        "blocked_families": missing_families,
    }

    (OUT / "gate11a_status.json").write_text(
        json.dumps(
            status,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            status,
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 11A FAILED. Diagnose the S1 campaign before implementing S2-S4."
        )

    print(
        "\nFULL GATE 11A PASS — final evidence for the implemented S1 family "
        "is generated. S2-S4 must still be implemented before making claims "
        "across the full Gate 10 experiment matrix."
    )

if __name__ == "__main__":
    main()
