from __future__ import annotations

from pathlib import Path
import json
import sys
import importlib

ROOT = Path(__file__).resolve().parents[2]

# Ensure this cumulative package takes precedence over older MedVerse copies.
root_str = str(ROOT)
if root_str in sys.path:
    sys.path.remove(root_str)
sys.path.insert(0, root_str)

# Spyder may retain stale namespace-package state after switching cumulative
# folders. Invalidate finder caches before importing the newly packaged module.
importlib.invalidate_caches()

# If medverse.learning was previously loaded as a namespace package, remove only
# that package and its Gate-21A builder so Python resolves them from this ROOT.
for stale_name in [
    "medverse.learning.gate21a_dataset_builder",
    "medverse.learning",
]:
    sys.modules.pop(stale_name, None)

from medverse.learning.gate21a_dataset_builder import write_dataset, AGENT_LABELS

OUT = ROOT / "outputs" / "gate21a"
OUT.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "data" / "learning" / "gate21a"


def ck(name, ok, observed, expected):
    return {
        "check": name,
        "status": "PASS" if ok else "FAIL",
        "observed": observed,
        "expected": expected,
    }


def main():
    print("\n========================================")
    print(" MedVerse-Agent - Gate 21A")
    print(" Learning Dataset Adequacy")
    print(" & Split Strengthening")
    print("========================================\n")

    reg = json.loads(
        (ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8")
    )

    if reg.get("promoted_gates", {}).get("GATE_21", {}).get("status") != "PASS":
        result = {
            "gate": "GATE_21A_LEARNING_DATASET_ADEQUACY",
            "status": "HOLD",
            "reason": "Gate 21 not promoted PASS",
        }
        (OUT / "gate21a_status.json").write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(result, indent=2))
        return

    rows, manifest = write_dataset(DATA)
    checks = []

    checks.append(
        ck(
            "minimum_total_records",
            len(rows) >= 400,
            len(rows),
            ">=400",
        )
    )

    observed_agents = sorted({r["agent_id"] for r in rows})
    expected_agents = sorted(AGENT_LABELS)
    checks.append(
        ck(
            "all_five_agents",
            observed_agents == expected_agents,
            observed_agents,
            expected_agents,
        )
    )

    per_agent = manifest["agent_split_counts"]
    adequate = all(
        per_agent[a]["train"] >= 40
        and per_agent[a]["dev"] >= 12
        and per_agent[a]["test"] >= 12
        for a in AGENT_LABELS
    )
    checks.append(
        ck(
            "per_agent_split_adequacy",
            adequate,
            per_agent,
            "train>=40, dev>=12, test>=12 for every agent",
        )
    )

    group_split = {}
    leaks = []
    for r in rows:
        group_id = r["split_group"]
        split = r["split"]
        if group_id in group_split and group_split[group_id] != split:
            leaks.append((group_id, group_split[group_id], split))
        group_split[group_id] = split

    checks.append(
        ck(
            "no_group_split_leakage",
            not leaks,
            leaks[:20],
            [],
        )
    )

    signatures = [
        (r["agent_id"], r["features_json"])
        for r in rows
    ]
    checks.append(
        ck(
            "no_exact_feature_duplicates",
            len(signatures) == len(set(signatures)),
            {
                "rows": len(signatures),
                "unique": len(set(signatures)),
            },
            "equal",
        )
    )

    missing_actions = []
    for agent_id in AGENT_LABELS:
        train_actions = {
            r["target_action"]
            for r in rows
            if r["agent_id"] == agent_id and r["split"] == "train"
        }

        for split in ["dev", "test"]:
            heldout = {
                r["target_action"]
                for r in rows
                if r["agent_id"] == agent_id and r["split"] == split
            }
            for action in sorted(heldout - train_actions):
                missing_actions.append((agent_id, split, action))

    checks.append(
        ck(
            "heldout_actions_seen_in_train",
            not missing_actions,
            missing_actions,
            [],
        )
    )

    missing_assessments = []
    for agent_id in AGENT_LABELS:
        train_assessments = {
            r["target_assessment"]
            for r in rows
            if r["agent_id"] == agent_id and r["split"] == "train"
        }

        for split in ["dev", "test"]:
            heldout = {
                r["target_assessment"]
                for r in rows
                if r["agent_id"] == agent_id and r["split"] == split
            }
            for assessment in sorted(heldout - train_assessments):
                missing_assessments.append(
                    (agent_id, split, assessment)
                )

    checks.append(
        ck(
            "heldout_assessments_seen_in_train",
            not missing_assessments,
            missing_assessments,
            [],
        )
    )

    checks.append(
        ck(
            "no_patient_data",
            all(r["patient_data"] is False for r in rows),
            sorted({r["patient_data"] for r in rows}),
            [False],
        )
    )

    checks.append(
        ck(
            "agent_labels_explicit",
            all(r["agent_label"].endswith("Agent") for r in rows),
            sorted({r["agent_label"] for r in rows}),
            "all labels end with Agent",
        )
    )

    rows2, manifest2 = write_dataset(DATA)
    deterministic = rows == rows2 and manifest == manifest2
    checks.append(
        ck(
            "deterministic_regeneration",
            deterministic,
            deterministic,
            True,
        )
    )

    (OUT / "gate21a_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    passed = sum(x["status"] == "PASS" for x in checks)
    total = len(checks)

    result = {
        "gate": "GATE_21A_LEARNING_DATASET_ADEQUACY",
        "status": "PASS" if passed == total else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "dataset_id": manifest["dataset_id"],
        "total_records": manifest["total_records"],
        "agent_counts": manifest["agent_counts"],
        "split_counts": manifest["split_counts"],
        "agent_split_counts": manifest["agent_split_counts"],
        "patient_data": False,
        "training_performed": False,
        "next_gate": "GATE_22_PRIVACY_AGENT_TRAINING",
    }

    (OUT / "gate21a_status.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print(f"\nDataset saved to:\n{DATA}")
    print(f"\nOutputs saved to:\n{OUT}")

    if result["status"] == "FAIL":
        raise SystemExit(
            "Gate 21A FAILED. Diagnose learning-data adequacy before model training."
        )

    print(
        "\nFULL GATE 21A PASS — Per-agent train/dev/test coverage is adequate. "
        "Gate 22 may begin actual Privacy Agent training."
    )


if __name__ == "__main__":
    main()
