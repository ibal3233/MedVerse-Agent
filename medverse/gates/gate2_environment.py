from __future__ import annotations

from pathlib import Path
import sys
import csv
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.data.loader import load_json
from medverse.environment.env import MedVerseEnvironment

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate2"
OUT.mkdir(parents=True, exist_ok=True)

def diagnostic_check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 2")
    print(" Deterministic Environment")
    print("========================================\n")

    scenario = load_json(ROOT / "data" / "reference" / "MVKR-S01.json")
    env = MedVerseEnvironment()
    initial = env.reset()

    checks = []
    trajectory = []

    checks.append(diagnostic_check(
        "initial_spo2", initial.clinical.spo2 == 97.0, initial.clinical.spo2, 97.0
    ))
    checks.append(diagnostic_check(
        "initial_hr", initial.clinical.heart_rate == 81.0, initial.clinical.heart_rate, 81.0
    ))
    checks.append(diagnostic_check(
        "initial_dt_validity", initial.dt.validity == "VALID", initial.dt.validity, "VALID"
    ))

    for event in scenario["events"]:
        state = env.step(event)

        trajectory.append({
            "event_id": event["event_id"],
            "t": event["t"],
            "event_type": event["event_type"],
            "spo2": state.clinical.spo2,
            "heart_rate": state.clinical.heart_rate,
            "packet_loss": state.network.packet_loss,
            "rtt_ms": state.network.rtt_ms,
            "jitter_ms": state.network.jitter_ms,
            "certificate_status": state.security.certificate_status,
            "session_origin": state.security.session_origin,
            "dt_validity": state.dt.validity,
            "dt_trust": state.dt.trust_score,
        })

    e1, e2, e3 = trajectory

    checks.append(diagnostic_check(
        "E1_clinical_state",
        e1["spo2"] == 78 and e1["heart_rate"] == 122,
        (e1["spo2"], e1["heart_rate"]),
        (78, 122),
    ))
    checks.append(diagnostic_check(
        "E1_dt_validity",
        e1["dt_validity"] == "VALID",
        e1["dt_validity"],
        "VALID",
    ))

    checks.append(diagnostic_check(
        "E2_network_state",
        e2["packet_loss"] == 0.27 and e2["rtt_ms"] == 840 and e2["jitter_ms"] == 180,
        (e2["packet_loss"], e2["rtt_ms"], e2["jitter_ms"]),
        (0.27, 840, 180),
    ))
    checks.append(diagnostic_check(
        "E2_dt_validity",
        e2["dt_validity"] == "DEGRADED",
        e2["dt_validity"],
        "DEGRADED",
    ))

    checks.append(diagnostic_check(
        "E3_security_state",
        e3["certificate_status"] == "mismatch" and e3["session_origin"] == "abnormal",
        (e3["certificate_status"], e3["session_origin"]),
        ("mismatch", "abnormal"),
    ))
    checks.append(diagnostic_check(
        "E3_dt_validity",
        e3["dt_validity"] == "UNVERIFIED",
        e3["dt_validity"],
        "UNVERIFIED",
    ))

    checks.append(diagnostic_check(
        "clinical_state_persists",
        e3["spo2"] == 78 and e3["heart_rate"] == 122,
        (e3["spo2"], e3["heart_rate"]),
        (78, 122),
    ))
    checks.append(diagnostic_check(
        "network_state_persists",
        e3["packet_loss"] == 0.27 and e3["rtt_ms"] == 840 and e3["jitter_ms"] == 180,
        (e3["packet_loss"], e3["rtt_ms"], e3["jitter_ms"]),
        (0.27, 840, 180),
    ))

    validity_path = [r["dt_validity"] for r in trajectory]
    checks.append(diagnostic_check(
        "dt_validity_progression",
        validity_path == ["VALID", "DEGRADED", "UNVERIFIED"],
        validity_path,
        ["VALID", "DEGRADED", "UNVERIFIED"],
    ))

    env2 = MedVerseEnvironment()
    env2.reset()
    traj2 = [env2.step(e).to_dict() for e in scenario["events"]]

    env3 = MedVerseEnvironment()
    env3.reset()
    traj3 = [env3.step(e).to_dict() for e in scenario["events"]]

    checks.append(diagnostic_check(
        "deterministic_replay",
        traj2 == traj3,
        traj2 == traj3,
        True,
    ))

    rejected = False
    try:
        env3.step({
            "event_id": "BAD",
            "t": 3,
            "event_type": "CLINICAL_ALARM",
            "payload": {"SpO2": 80, "heart_rate": 100},
        })
    except ValueError:
        rejected = True

    checks.append(diagnostic_check(
        "reject_nonincreasing_time",
        rejected,
        rejected,
        True,
    ))

    with (OUT / "gate2_state_trajectory.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(f, fieldnames=list(trajectory[0].keys()))
        writer.writeheader()
        writer.writerows(trajectory)

    with (OUT / "gate2_checks.csv").open(
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
        "gate": "GATE_2_DETERMINISTIC_ENVIRONMENT",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "dt_trajectory": validity_path,
    }

    (OUT / "gate2_status.json").write_text(
        json.dumps(status, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(status, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 2 FAILED. Diagnose before changing the model."
        )

    print("\nFULL GATE 2 PASS — eligible to proceed to Gate 3.")

if __name__ == "__main__":
    main()
