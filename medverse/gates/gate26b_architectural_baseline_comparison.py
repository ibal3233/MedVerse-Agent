from __future__ import annotations

from pathlib import Path
from collections import defaultdict, Counter
import csv
import hashlib
import json
import math
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from medverse.evaluation.gate26_baseline_benchmark import BASELINES

DATA = ROOT / "data" / "evaluation" / "gate26" / "gate26_architectural_baseline_cases.json"
PROTOCOL = ROOT / "outputs" / "gate26a" / "gate26a_frozen_protocol.json"
OUT = ROOT / "outputs" / "gate26"
FIG = OUT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

INTENT_ORDER = {
    "RESTRICT": 5,
    "VERIFY": 4,
    "CONTINUE": 3,
    "ALLOW": 2,
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def token(agent, action):
    return f"{agent}::{action}"


def _output(state, actions, *,
            messages=None,
            evidence_requests=None,
            escalation=False,
            exposed_fields=None):
    return {
        "coordination_state": state,
        "executed_actions": sorted(set(actions)),
        "messages": sorted(set(messages or [])),
        "evidence_requests": sorted(set(evidence_requests or [])),
        "escalation": bool(escalation),
        "exposed_fields": list(exposed_fields or []),
    }


def B1(case):
    """
    Single omniscient policy-aware central agent.

    It sees all evidence and can globally recognize policy-valid actions, but
    actions are issued under a single central authority rather than the owning
    institution. This is intentionally not given MedVerse mandate harmonization.
    """
    valid = [
        p for p in case["positions"]
        if p["policy_valid"] and p["evidence_sufficient"]
    ]
    actions = [
        token("omniscient_agent", p["action"])
        for p in valid
    ]

    # Conservative central decision: human-restricted cases escalate; otherwise
    # it emits globally valid actions but cannot preserve institutional ownership.
    escalation = any(p["human_authority_required"] for p in valid)
    state = (
        "HUMAN_AUTHORITY_REQUIRED"
        if escalation
        else "CENTRALIZED_DECISION"
    )
    return _output(
        state,
        actions,
        escalation=escalation,
        exposed_fields=case["all_sensitive_fields"],
    )


def B2(case):
    """
    Role-labelled but unconstrained MAS.
    Every role executes its proposal; policy, mandate, and evidence flags are
    not enforced.
    """
    actions = [
        token(p["agent_id"], p["action"])
        for p in case["positions"]
    ]
    # Broadcast all local evidence to all participating roles.
    n = len(case["positions"])
    exposed = []
    for _ in range(max(1, n)):
        exposed.extend(case["all_sensitive_fields"])
    return _output(
        "PARALLEL_ROLE_ACTIONS",
        actions,
        escalation=False,
        exposed_fields=exposed,
    )


def B3(case):
    """
    Consensus/debate MAS.
    Roles vote on high-level intent. Only actions aligned with the majority
    intent survive. Ties are escalated. No policy/mandate filter is provided.
    """
    counts = Counter(p["intent"] for p in case["positions"])
    best = max(counts.values())
    winners = sorted([k for k, v in counts.items() if v == best])

    # Tie -> debate fails to resolve and escalates.
    if len(winners) > 1:
        actions = []
        escalation = True
        state = "CONSENSUS_UNRESOLVED"
    else:
        win = winners[0]
        actions = [
            token(p["agent_id"], p["action"])
            for p in case["positions"]
            if p["intent"] == win
        ]
        escalation = False
        state = "CONSENSUS_REACHED"

    # Debate broadcasts evidence summaries among all participants.
    n = len(case["positions"])
    exposed = []
    for _ in range(max(1, n)):
        exposed.extend(case["all_sensitive_fields"])

    return _output(
        state,
        actions,
        escalation=escalation,
        exposed_fields=exposed,
    )


def B4(case):
    """
    Policy/mandate filtering without harmonization.
    Invalid actions are removed. Evidence-insufficient actions are withheld.
    Valid conflict/dependency cases are escalated because no compliant joint
    workflow is synthesized.
    """
    valid = [
        p for p in case["positions"]
        if p["policy_valid"]
        and p["mandate_valid"]
        and p["evidence_sufficient"]
    ]
    actions = [token(p["agent_id"], p["action"]) for p in valid]

    ctx = case["context"]
    evidence_requests = []
    if any(not p["evidence_sufficient"] for p in case["positions"]):
        evidence_requests = ["AUTHORIZED_EVIDENCE"]

    unresolved_joint = (
        ctx.get("institutional_conflict") == "CARE_VS_DISCLOSURE"
        or ctx.get("dependency") == "TRUST_BEFORE_DT_USE"
    )
    human_required = any(
        p["human_authority_required"] for p in case["positions"]
    )

    escalation = bool(unresolved_joint or human_required)
    state = (
        "HUMAN_AUTHORITY_REQUIRED"
        if human_required
        else "FILTERED_UNRESOLVED_CONFLICT"
        if unresolved_joint
        else "POLICY_FILTERED_ACTIONS"
    )

    return _output(
        state,
        actions,
        evidence_requests=evidence_requests,
        escalation=escalation,
        exposed_fields=[],
    )


def B5(case):
    """
    MedVerse-Agent reference harmonization.
    This implements the frozen architectural rules generically from case facts;
    it does not read the expected_coordination_state field.
    """
    positions = case["positions"]
    ctx = case["context"]

    invalid = [
        p for p in positions
        if not p["policy_valid"] or not p["mandate_valid"]
    ]
    insufficient = [
        p for p in positions
        if p["policy_valid"]
        and p["mandate_valid"]
        and not p["evidence_sufficient"]
    ]
    valid = [
        p for p in positions
        if p["policy_valid"]
        and p["mandate_valid"]
        and p["evidence_sufficient"]
    ]

    actions = [token(p["agent_id"], p["action"]) for p in valid]

    if invalid:
        return _output(
            "POLICY_CONFLICT",
            actions,
            exposed_fields=[],
        )

    if insufficient:
        return _output(
            "INSUFFICIENT_EVIDENCE",
            actions,
            evidence_requests=["AUTHORIZED_EVIDENCE"],
            exposed_fields=[],
        )

    if (
        ctx.get("human_authority_required") is True
        or any(p["human_authority_required"] for p in positions)
    ):
        return _output(
            "HUMAN_AUTHORITY_REQUIRED",
            actions,
            escalation=True,
            exposed_fields=[],
        )

    if ctx.get("institutional_conflict") == "CARE_VS_DISCLOSURE":
        if ctx.get("alternative_available", False):
            actions = actions + [
                token(
                    "hospital_agent",
                    ctx.get(
                        "compliant_alternative",
                        "REQUEST_MINIMUM_NECESSARY_CLINICAL_DATA",
                    ),
                )
            ]
            return _output(
                "INSTITUTIONAL_CONFLICT",
                actions,
                messages=["minimum_necessary_scope"],
                exposed_fields=["minimum_necessary_scope"],
            )
        return _output(
            "HUMAN_AUTHORITY_REQUIRED",
            actions,
            escalation=True,
            exposed_fields=[],
        )

    if ctx.get("dependency") == "TRUST_BEFORE_DT_USE":
        return _output(
            "CONDITIONAL_HARMONIZATION",
            actions,
            messages=["telemetry_trust", "clinical_priority"],
            exposed_fields=["telemetry_trust", "clinical_priority"],
        )

    if ctx.get("all_agents_agree") is True:
        return _output(
            "AGREEMENT",
            actions,
            exposed_fields=[],
        )

    return _output(
        "COMPLEMENTARY",
        actions,
        messages=(
            ["telemetry_trust", "clinical_priority"]
            if ctx.get("complementary_risk")
            else []
        ),
        exposed_fields=(
            ["telemetry_trust", "clinical_priority"]
            if ctx.get("complementary_risk")
            else []
        ),
    )


RUNNERS = {
    "B1": B1,
    "B2": B2,
    "B3": B3,
    "B4": B4,
    "B5": B5,
}


def f1_set(expected, observed):
    e, o = set(expected), set(observed)
    if not e and not o:
        return 1.0
    if not e and o:
        return 0.0
    tp = len(e & o)
    p = tp / len(o) if o else 0.0
    r = tp / len(e) if e else 0.0
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def institutional_correctness(case, out):
    executed = set(out["executed_actions"])
    req = set(case["required_actions"])
    forbidden = set(case["forbidden_actions"])

    decisions = len(req) + len(forbidden)
    if decisions == 0:
        return 1.0

    correct_required = len(req & executed)
    correct_forbidden = len(forbidden - executed)
    return (correct_required + correct_forbidden) / decisions


def action_policy_violation(case, action_token):
    # Wrong institutional ownership is an authority/mandate violation.
    if action_token.startswith("omniscient_agent::"):
        return True

    pos_map = {
        token(p["agent_id"], p["action"]): p
        for p in case["positions"]
    }

    # Synthesized actions are safe only when explicitly frozen as allowed.
    if action_token not in pos_map:
        return action_token not in set(case["allowed_actions"])

    p = pos_map[action_token]
    return (
        not p["policy_valid"]
        or not p["mandate_valid"]
        or not p["evidence_sufficient"]
    )


def policy_violation_rate(case, out):
    acts = out["executed_actions"]
    if not acts:
        return 0.0
    return sum(action_policy_violation(case, a) for a in acts) / len(acts)


def unsafe_execution_rate(case, out):
    acts = out["executed_actions"]
    if not acts:
        return 0.0
    allowed = set(case["allowed_actions"])
    return sum(a not in allowed for a in acts) / len(acts)


def information_overexposure_rate(case, out):
    exposed = list(out["exposed_fields"])
    if not exposed:
        return 0.0

    required = set(case["required_shared_fields"])
    excessive = sum(x not in required for x in exposed)
    return excessive / len(exposed)


def unnecessary_escalation(case, out):
    return int(out["escalation"] and not case["expected_escalation"])


def coordination_quality(case, out):
    state = float(
        out["coordination_state"] == case["expected_coordination_state"]
    )
    action = f1_set(
        case["required_actions"],
        out["executed_actions"],
    )
    communication = f1_set(
        sorted(
            set(case["required_messages"])
            | set(case["required_evidence_requests"])
        ),
        sorted(
            set(out["messages"])
            | set(out["evidence_requests"])
        ),
    )
    escalation = float(
        out["escalation"] == case["expected_escalation"]
    )
    return (state + action + communication + escalation) / 4.0


def exact_match(case, out):
    return int(
        out["coordination_state"] == case["expected_coordination_state"]
        and set(out["executed_actions"]) == set(case["required_actions"])
        and (
            set(out["messages"]) | set(out["evidence_requests"])
        ) == (
            set(case["required_messages"])
            | set(case["required_evidence_requests"])
        )
        and out["escalation"] == case["expected_escalation"]
    )


def measure_latency(runner, case, repeats=300):
    # Warm up.
    for _ in range(20):
        runner(case)

    xs = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        runner(case)
        xs.append((time.perf_counter_ns() - t0) / 1000.0)
    xs.sort()
    med = statistics.median(xs)
    p95 = xs[min(len(xs)-1, math.ceil(0.95 * len(xs)) - 1)]
    return med, p95


def save_capability_plot(protocol):
    caps = protocol["capability_contract"]
    attributes = [
        ("separate_institutional_authority", "Institutional authority"),
        ("policy_filter", "Policy filter"),
        ("cross_agent_harmonization", "Harmonization"),
    ]
    baselines = ["B1", "B2", "B3", "B4", "B5"]
    matrix = np.array([
        [1 if caps[b][k] else 0 for k, _ in attributes]
        for b in baselines
    ])

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    im = ax.imshow(matrix, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(attributes)))
    ax.set_xticklabels([x[1] for x in attributes])
    ax.set_yticks(range(len(baselines)))
    ax.set_yticklabels([
        f"{b}: {BASELINES[b]}" for b in baselines
    ])
    ax.set_title("Gate 26 Baseline Capability Matrix")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j, i,
                "Yes" if matrix[i, j] else "No",
                ha="center", va="center",
            )
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
    fig.tight_layout()
    fig.savefig(FIG / "fig26_baseline_capability_matrix.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig26_baseline_capability_matrix.pdf", bbox_inches="tight")
    plt.close(fig)


def save_plots(summary_rows, archetype_rows):
    order = ["B1", "B2", "B3", "B4", "B5"]
    d = {r["baseline"]: r for r in summary_rows}

    # Main quality/safety panel as grouped bars.
    metrics = [
        ("institutional_correctness", "Institutional correctness"),
        ("coordination_quality", "Coordination quality"),
        ("workflow_exact_match", "Workflow exact match"),
    ]
    x = np.arange(len(order))
    w = 0.24
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for i, (key, label) in enumerate(metrics):
        ax.bar(
            x + (i-1)*w,
            [d[b][key] for b in order],
            w,
            label=label,
        )
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("Score")
    ax.set_title("Architectural Baseline Comparison: Coordination Quality")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig26_coordination_quality.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig26_coordination_quality.pdf", bbox_inches="tight")
    plt.close(fig)

    safety = [
        ("policy_violation_rate", "Policy violations"),
        ("unnecessary_escalation_rate", "Unnecessary escalation"),
        ("information_overexposure_rate", "Information over-exposure"),
        ("unsafe_execution_rate", "Unsafe execution"),
    ]
    w = 0.19
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for i, (key, label) in enumerate(safety):
        ax.bar(
            x + (i-1.5)*w,
            [d[b][key] for b in order],
            w,
            label=label,
        )
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x)
    ax.set_xticklabels(order)
    ax.set_ylabel("Rate (lower is better)")
    ax.set_title("Architectural Baseline Comparison: Safety and Governance")
    ax.legend(ncol=2)
    fig.tight_layout()
    fig.savefig(FIG / "fig26_safety_governance.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig26_safety_governance.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(
        order,
        [d[b]["median_latency_us"] for b in order],
    )
    ax.set_ylabel("Median reference runtime (µs)")
    ax.set_title("Reference Coordination-Logic Runtime")
    fig.tight_layout()
    fig.savefig(FIG / "fig26_latency.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig26_latency.pdf", bbox_inches="tight")
    plt.close(fig)

    # Exact workflow by coordination archetype.
    archetypes = sorted(set(r["archetype"] for r in archetype_rows))
    fig, ax = plt.subplots(figsize=(12, 6))
    xx = np.arange(len(archetypes))
    width = 0.15
    for i, b in enumerate(order):
        vals = [
            next(
                r["workflow_exact_match"]
                for r in archetype_rows
                if r["baseline"] == b and r["archetype"] == a
            )
            for a in archetypes
        ]
        ax.bar(xx + (i-2)*width, vals, width, label=b)
    ax.set_ylim(0, 1.05)
    ax.set_xticks(xx)
    ax.set_xticklabels(archetypes, rotation=25, ha="right")
    ax.set_ylabel("Exact workflow match")
    ax.set_title("Exact Workflow Match by Coordination Archetype")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig26_workflow_by_archetype.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig26_workflow_by_archetype.pdf", bbox_inches="tight")
    plt.close(fig)

    # Overall normalized utility display (for presentation only, not primary metric):
    # invert lower-is-better metrics and average equally.
    fig, ax = plt.subplots(figsize=(9, 4.8))
    utility = []
    for b in order:
        r = d[b]
        score = np.mean([
            r["institutional_correctness"],
            1-r["policy_violation_rate"],
            1-r["unnecessary_escalation_rate"],
            1-r["information_overexposure_rate"],
            1-r["unsafe_execution_rate"],
            r["coordination_quality"],
            r["workflow_exact_match"],
        ])
        utility.append(score)
    ax.bar(order, utility)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Equal-weight normalized summary")
    ax.set_title("Gate 26 Summary Index (Presentation Aid Only)")
    fig.tight_layout()
    fig.savefig(FIG / "fig26_summary_index.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / "fig26_summary_index.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 26B")
    print(" Architectural Baseline Comparison")
    print(" B1-B5")
    print("========================================\n")

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    benchmark = json.loads(DATA.read_text(encoding="utf-8"))
    cases = benchmark["cases"]

    observed_hash = sha256(DATA)
    frozen_hash = protocol["benchmark_sha256"]

    raw = []
    latency_cache = {}

    for b, runner in RUNNERS.items():
        for case in cases:
            out = runner(case)
            med_us, p95_us = measure_latency(runner, case)
            raw.append({
                "baseline": b,
                "baseline_name": BASELINES[b],
                "case_id": case["case_id"],
                "archetype": case["archetype"],
                "institutional_correctness":
                    institutional_correctness(case, out),
                "policy_violation_rate":
                    policy_violation_rate(case, out),
                "unnecessary_escalation":
                    unnecessary_escalation(case, out),
                "information_overexposure_rate":
                    information_overexposure_rate(case, out),
                "unsafe_execution_rate":
                    unsafe_execution_rate(case, out),
                "coordination_quality":
                    coordination_quality(case, out),
                "workflow_exact_match":
                    exact_match(case, out),
                "latency_median_us": med_us,
                "latency_p95_us": p95_us,
                "observed_state": out["coordination_state"],
                "expected_state": case["expected_coordination_state"],
                "executed_actions": "|".join(out["executed_actions"]),
                "expected_actions": "|".join(case["required_actions"]),
                "escalation": out["escalation"],
                "expected_escalation": case["expected_escalation"],
            })

    # Overall summary.
    summary_rows = []
    for b in ["B1", "B2", "B3", "B4", "B5"]:
        rr = [r for r in raw if r["baseline"] == b]
        nonhuman = [
            r for r in rr
            if not next(
                c["expected_escalation"]
                for c in cases
                if c["case_id"] == r["case_id"]
            )
        ]
        summary_rows.append({
            "baseline": b,
            "baseline_name": BASELINES[b],
            "n_cases": len(rr),
            "institutional_correctness":
                float(np.mean([r["institutional_correctness"] for r in rr])),
            "policy_violation_rate":
                float(np.mean([r["policy_violation_rate"] for r in rr])),
            "unnecessary_escalation_rate":
                float(np.mean([r["unnecessary_escalation"] for r in nonhuman])),
            "information_overexposure_rate":
                float(np.mean([r["information_overexposure_rate"] for r in rr])),
            "unsafe_execution_rate":
                float(np.mean([r["unsafe_execution_rate"] for r in rr])),
            "coordination_quality":
                float(np.mean([r["coordination_quality"] for r in rr])),
            "workflow_exact_match":
                float(np.mean([r["workflow_exact_match"] for r in rr])),
            "median_latency_us":
                float(statistics.median([r["latency_median_us"] for r in rr])),
            "p95_latency_us":
                float(np.percentile([r["latency_p95_us"] for r in rr], 95)),
        })

    # Per-archetype summary.
    archetype_rows = []
    archetypes = sorted(set(c["archetype"] for c in cases))
    for b in ["B1", "B2", "B3", "B4", "B5"]:
        for a in archetypes:
            rr = [
                r for r in raw
                if r["baseline"] == b and r["archetype"] == a
            ]
            archetype_rows.append({
                "baseline": b,
                "archetype": a,
                "institutional_correctness":
                    float(np.mean([r["institutional_correctness"] for r in rr])),
                "coordination_quality":
                    float(np.mean([r["coordination_quality"] for r in rr])),
                "workflow_exact_match":
                    float(np.mean([r["workflow_exact_match"] for r in rr])),
                "policy_violation_rate":
                    float(np.mean([r["policy_violation_rate"] for r in rr])),
                "unsafe_execution_rate":
                    float(np.mean([r["unsafe_execution_rate"] for r in rr])),
            })

    # Save CSVs.
    with (OUT / "gate26_case_results.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(raw[0].keys()))
        w.writeheader()
        w.writerows(raw)

    with (OUT / "gate26_baseline_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)

    with (OUT / "gate26_archetype_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.DictWriter(f, fieldnames=list(archetype_rows[0].keys()))
        w.writeheader()
        w.writerows(archetype_rows)

    # Markdown table.
    md = OUT / "gate26_baseline_comparison_table.md"
    lines = [
        "# Gate 26 Architectural Baseline Comparison",
        "",
        "| Baseline | Inst. correctness ↑ | Policy viol. ↓ | Unnecessary escalation ↓ | Info over-exposure ↓ | Unsafe execution ↓ | Coordination quality ↑ | Exact workflow ↑ | Median µs ↓ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary_rows:
        lines.append(
            f"| {r['baseline']} | "
            f"{r['institutional_correctness']:.3f} | "
            f"{r['policy_violation_rate']:.3f} | "
            f"{r['unnecessary_escalation_rate']:.3f} | "
            f"{r['information_overexposure_rate']:.3f} | "
            f"{r['unsafe_execution_rate']:.3f} | "
            f"{r['coordination_quality']:.3f} | "
            f"{r['workflow_exact_match']:.3f} | "
            f"{r['median_latency_us']:.2f} |"
        )
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    save_capability_plot(protocol)
    save_plots(summary_rows, archetype_rows)

    # Scientific interpretation is computed from results, not hard-coded as a PASS condition.
    by = {r["baseline"]: r for r in summary_rows}
    interpretation = {
        "B5_vs_B4_coordination_quality_delta":
            by["B5"]["coordination_quality"] - by["B4"]["coordination_quality"],
        "B5_vs_B4_exact_workflow_delta":
            by["B5"]["workflow_exact_match"] - by["B4"]["workflow_exact_match"],
        "B5_vs_B1_institutional_correctness_delta":
            by["B5"]["institutional_correctness"] - by["B1"]["institutional_correctness"],
        "B5_policy_violation_rate":
            by["B5"]["policy_violation_rate"],
        "B5_unsafe_execution_rate":
            by["B5"]["unsafe_execution_rate"],
        "B5_information_overexposure_rate":
            by["B5"]["information_overexposure_rate"],
        "fastest_baseline":
            min(summary_rows, key=lambda r: r["median_latency_us"])["baseline"],
        "highest_coordination_quality":
            max(summary_rows, key=lambda r: r["coordination_quality"])["baseline"],
        "highest_exact_workflow_match":
            max(summary_rows, key=lambda r: r["workflow_exact_match"])["baseline"],
        "important_boundary": (
            "A positive MedVerse result supports the value of the frozen "
            "harmonization architecture on this controlled synthetic benchmark. "
            "It does not establish superiority on external clinical deployments."
        ),
    }

    (OUT / "gate26_interpretation.json").write_text(
        json.dumps(interpretation, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    checks = [
        {
            "check": "frozen_benchmark_hash_matches",
            "pass": observed_hash == frozen_hash,
            "observed": observed_hash,
            "expected": frozen_hash,
        },
        {
            "check": "all_five_baselines_executed",
            "pass": sorted(set(r["baseline"] for r in raw))
                    == ["B1", "B2", "B3", "B4", "B5"],
            "observed": sorted(set(r["baseline"] for r in raw)),
            "expected": ["B1", "B2", "B3", "B4", "B5"],
        },
        {
            "check": "same_70_cases_per_baseline",
            "pass": all(
                sum(r["baseline"] == b for r in raw) == 70
                for b in ["B1", "B2", "B3", "B4", "B5"]
            ),
            "observed": {
                b: sum(r["baseline"] == b for r in raw)
                for b in ["B1", "B2", "B3", "B4", "B5"]
            },
            "expected": 70,
        },
        {
            "check": "no_training_or_baseline_tuning",
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
            "check": "all_requested_metrics_reported",
            "pass": all(
                k in summary_rows[0]
                for k in [
                    "institutional_correctness",
                    "policy_violation_rate",
                    "unnecessary_escalation_rate",
                    "information_overexposure_rate",
                    "unsafe_execution_rate",
                    "median_latency_us",
                    "coordination_quality",
                ]
            ),
            "observed": list(summary_rows[0]),
            "expected": "all seven requested metrics",
        },
        {
            "check": "raw_case_results_complete",
            "pass": len(raw) == 350,
            "observed": len(raw),
            "expected": 350,
        },
        {
            "check": "archetype_breakdown_complete",
            "pass": len(archetype_rows) == 35,
            "observed": len(archetype_rows),
            "expected": 35,
        },
        {
            "check": "publication_outputs",
            "pass": (
                len(list(FIG.glob("*.png"))) >= 6
                and len(list(FIG.glob("*.pdf"))) >= 6
            ),
            "observed": {
                "png": len(list(FIG.glob("*.png"))),
                "pdf": len(list(FIG.glob("*.pdf"))),
            },
            "expected": ">=6 PNG and >=6 PDF",
        },
        {
            "check": "machine_readable_and_report_tables_created",
            "pass": (
                (OUT / "gate26_baseline_summary.csv").exists()
                and (OUT / "gate26_case_results.csv").exists()
                and md.exists()
                and (OUT / "gate26_interpretation.json").exists()
            ),
            "observed": True,
            "expected": True,
        },
    ]

    passed = sum(c["pass"] for c in checks)
    status = {
        "gate": "GATE_26_ARCHITECTURAL_BASELINE_COMPARISON",
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed_checks": passed,
        "total_checks": len(checks),
        "training_performed": False,
        "baseline_specific_tuning_performed": False,
        "benchmark_records": len(cases),
        "baseline_runs": len(raw),
        "baseline_summary": summary_rows,
        "interpretation": interpretation,
        "figures_directory": "outputs/gate26/figures",
        "main_table": "outputs/gate26/gate26_baseline_comparison_table.md",
        "next_dependency": (
            "No additional experimental tuning is authorized. Integrate Gate26 "
            "into the technical report, judge narrative, and demo/video."
        ),
    }

    (OUT / "gate26_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (OUT / "gate26_status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2, ensure_ascii=False))
    print("\nBaseline comparison:")
    for r in summary_rows:
        print({
            "baseline": r["baseline"],
            "institutional_correctness":
                round(r["institutional_correctness"], 3),
            "policy_violation_rate":
                round(r["policy_violation_rate"], 3),
            "unnecessary_escalation_rate":
                round(r["unnecessary_escalation_rate"], 3),
            "information_overexposure_rate":
                round(r["information_overexposure_rate"], 3),
            "unsafe_execution_rate":
                round(r["unsafe_execution_rate"], 3),
            "coordination_quality":
                round(r["coordination_quality"], 3),
            "workflow_exact_match":
                round(r["workflow_exact_match"], 3),
            "median_latency_us":
                round(r["median_latency_us"], 2),
        })

    print(f"\nOutputs:\n{OUT}")

    if status["status"] != "PASS":
        raise SystemExit(
            "Gate26B infrastructure failed. Do not alter baseline behavior based "
            "on observed comparative performance."
        )

    print(
        "\nFULL GATE 26 PASS — B1-B5 were compared on the same frozen "
        "70-case architectural benchmark with no training or baseline-specific "
        "tuning. The measured comparative result may now be reported."
    )


if __name__ == "__main__":
    main()
