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

from medverse.evaluation.gate26_baseline_benchmark import (
    build_cases,
    BASELINES,
    COORDINATION_STATES,
    AGENTS,
)

OUT = ROOT / "outputs" / "gate26a"
DATA_OUT = ROOT / "data" / "evaluation" / "gate26"
OUT.mkdir(parents=True, exist_ok=True)
DATA_OUT.mkdir(parents=True, exist_ok=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 26A")
    print(" Architectural Baseline Protocol Freeze")
    print("========================================\n")

    cases = build_cases()
    benchmark = {
        "dataset_id": "MEDVERSE-G26-ARCH-BASELINES-v1",
        "scientific_role": (
            "Architecture-only coordination ablation. Institutional proposals "
            "and ground-truth workflow requirements are held constant across B1-B5."
        ),
        "cases": cases,
    }

    bench_path = DATA_OUT / "gate26_architectural_baseline_cases.json"
    bench_path.write_text(
        json.dumps(benchmark, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    bench_hash = sha256(bench_path)

    archetypes = Counter(c["archetype"] for c in cases)
    agents_seen = sorted({
        p["agent_id"]
        for c in cases
        for p in c["positions"]
    })

    protocol = {
        "protocol_id": "MEDVERSE-G26-ARCH-BASELINE-COMPARISON-v1",
        "status": "PRE_FROZEN_BEFORE_BASELINE_EXECUTION",
        "training_performed": False,
        "baseline_specific_tuning_permitted": False,
        "benchmark_records": len(cases),
        "coordination_archetypes": dict(archetypes),
        "agents_exercised": agents_seen,
        "baselines": BASELINES,
        "capability_contract": {
            "B1": {
                "description": "Single omniscient policy-aware central agent",
                "separate_institutional_authority": False,
                "policy_filter": True,
                "cross_agent_harmonization": False,
                "sharing": "all evidence centralized",
            },
            "B2": {
                "description": "Role-labelled MAS with no policy/mandate enforcement",
                "separate_institutional_authority": True,
                "policy_filter": False,
                "cross_agent_harmonization": False,
                "sharing": "role evidence broadcast",
            },
            "B3": {
                "description": "Role-labelled majority/debate coordination",
                "separate_institutional_authority": True,
                "policy_filter": False,
                "cross_agent_harmonization": False,
                "sharing": "debate broadcast",
            },
            "B4": {
                "description": "Policy/mandate filtering without harmonization",
                "separate_institutional_authority": True,
                "policy_filter": True,
                "cross_agent_harmonization": False,
                "sharing": "no raw evidence sharing",
            },
            "B5": {
                "description": "MedVerse policy-aware institutional harmonization",
                "separate_institutional_authority": True,
                "policy_filter": True,
                "cross_agent_harmonization": True,
                "sharing": "minimum necessary messages",
            },
        },
        "metrics": {
            "institutional_correctness": (
                "Correct required actions plus correct non-execution of forbidden "
                "actions, divided by all scored institutional action decisions."
            ),
            "policy_violation_rate": (
                "Executed actions that violate policy, mandate, evidence sufficiency, "
                "or institutional ownership divided by executed actions."
            ),
            "unnecessary_escalation_rate": (
                "Escalations in cases where the frozen ground truth does not require "
                "human escalation, divided by non-human-escalation cases."
            ),
            "information_overexposure_rate": (
                "Evidence-field exposures beyond the frozen minimum-necessary "
                "sharing requirement divided by all evidence-field exposures."
            ),
            "unsafe_execution_rate": (
                "Executed actions outside the frozen allowed action set divided by "
                "executed actions."
            ),
            "outcome_latency": (
                "Reference Python coordination-logic runtime measured after warm-up; "
                "reported as median and p95 microseconds. Not LLM/network deployment latency."
            ),
            "coordination_quality": (
                "Mean of coordination-state correctness, action-set F1, communication/"
                "evidence-request F1, and escalation correctness."
            ),
            "workflow_exact_match": (
                "All state, action, communication/evidence-request, and escalation "
                "components match the frozen case specification."
            ),
        },
        "fairness_rules": [
            "Same cases and institutional proposals for B1-B5.",
            "No model training in Gate26.",
            "No baseline-specific hyperparameter tuning.",
            "No changing benchmark after baseline results are observed.",
            "No baseline receives MedVerse harmonization logic except B5.",
            "B1 receives all available evidence by design.",
            "B4 receives policy/mandate filtering by design.",
            "Latency measures reference coordination logic only.",
        ],
        "claim_boundary": (
            "This experiment isolates coordination-architecture behavior on a "
            "controlled synthetic benchmark derived from frozen MedVerse institutional "
            "semantics. It is not an external clinical deployment comparison."
        ),
        "benchmark_sha256": bench_hash,
    }

    (OUT / "gate26a_frozen_protocol.json").write_text(
        json.dumps(protocol, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    rows = []
    for k, v in BASELINES.items():
        cap = protocol["capability_contract"][k]
        rows.append({
            "baseline": k,
            "name": v,
            "policy_filter": cap["policy_filter"],
            "separate_institutional_authority":
                cap["separate_institutional_authority"],
            "harmonization": cap["cross_agent_harmonization"],
            "sharing": cap["sharing"],
        })
    with (OUT / "gate26a_baseline_capability_matrix.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    checks = [
        {
            "check": "benchmark_has_70_cases",
            "pass": len(cases) == 70,
            "observed": len(cases),
            "expected": 70,
        },
        {
            "check": "all_seven_coordination_archetypes",
            "pass": set(archetypes) == set(COORDINATION_STATES)
                    and all(v == 10 for v in archetypes.values()),
            "observed": dict(archetypes),
            "expected": "7 archetypes x 10 cases",
        },
        {
            "check": "all_five_institutional_agents_exercised",
            "pass": agents_seen == sorted(AGENTS),
            "observed": agents_seen,
            "expected": sorted(AGENTS),
        },
        {
            "check": "all_five_baselines_defined",
            "pass": sorted(BASELINES) == ["B1", "B2", "B3", "B4", "B5"],
            "observed": sorted(BASELINES),
            "expected": ["B1", "B2", "B3", "B4", "B5"],
        },
        {
            "check": "seven_metrics_frozen",
            "pass": len(protocol["metrics"]) == 8,
            "observed": list(protocol["metrics"]),
            "expected": "7 requested metrics + workflow exact match",
        },
        {
            "check": "no_training_or_tuning",
            "pass": (
                protocol["training_performed"] is False
                and protocol["baseline_specific_tuning_permitted"] is False
            ),
            "observed": {
                "training": protocol["training_performed"],
                "tuning": protocol["baseline_specific_tuning_permitted"],
            },
            "expected": False,
        },
        {
            "check": "benchmark_hash_recorded",
            "pass": len(bench_hash) == 64,
            "observed": bench_hash,
            "expected": "SHA256",
        },
        {
            "check": "protocol_frozen_before_evaluation",
            "pass": protocol["status"] == "PRE_FROZEN_BEFORE_BASELINE_EXECUTION",
            "observed": protocol["status"],
            "expected": "PRE_FROZEN_BEFORE_BASELINE_EXECUTION",
        },
    ]

    passed = sum(c["pass"] for c in checks)
    status = {
        "gate": "GATE_26A_ARCHITECTURAL_BASELINE_PROTOCOL_FREEZE",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "training_performed": False,
        "benchmark_records": len(cases),
        "archetypes": dict(archetypes),
        "baselines": BASELINES,
        "benchmark_sha256": bench_hash,
        "next_dependency": (
            "Gate26B: execute B1-B5 exactly once on the frozen benchmark; "
            "do not tune baselines after observing results."
        ),
    }

    (OUT / "gate26a_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate26a_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2, ensure_ascii=False))
    print(f"\nBenchmark:\n{bench_path}")
    print(f"SHA256:\n{bench_hash}")
    print(f"\nOutputs:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit("Gate26A failed. Do not execute baseline comparison.")

    print(
        "\nFULL GATE 26A PASS — The architectural baseline benchmark, "
        "baseline capabilities, fairness rules, and metrics are frozen before "
        "any B1-B5 result is observed."
    )


if __name__ == "__main__":
    main()
