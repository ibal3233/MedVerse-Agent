from __future__ import annotations

from pathlib import Path
import sys
import json
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.digital_twin.model import PatientDigitalTwin
from medverse.data_grounding.evidence_bundle import EvidenceBundleBuilder
from medverse.data_grounding.ncc_context import NCCCancerContext

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate14"
OUT.mkdir(parents=True, exist_ok=True)

NCC = ROOT / "data" / "external" / "ncc_cancer_incidence.csv"

def check(name, status, observed, expected):
    return {
        "check": name,
        "status": status,
        "observed": observed,
        "expected": expected,
    }

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 14")
    print(" Data-Grounded Digital-Twin Foundation")
    print("========================================\n")

    checks = []

    dt = PatientDigitalTwin()

    # S1-like controlled updates.
    dt.update_domain(
        "clinical",
        {"SpO2": 78.0, "heart_rate": 122.0},
        t=1.0,
        source_type="wearable",
        source_id="demo_wearable_01",
    )
    checks.append(check(
        "clinical_update_preserves_validity_before_technical_failure",
        "PASS" if dt.validity == "VALID" else "FAIL",
        dt.validity,
        "VALID",
    ))

    dt.update_domain(
        "network",
        {"packet_loss": 0.27, "rtt_ms": 840.0, "jitter_ms": 180.0},
        t=2.0,
        source_type="network_monitor",
        source_id="demo_netmon_01",
    )
    checks.append(check(
        "network_degradation_derives_degraded_dt",
        "PASS" if dt.validity == "DEGRADED" else "FAIL",
        dt.validity,
        "DEGRADED",
    ))

    dt.update_domain(
        "security",
        {"certificate_status": "mismatch", "session_origin": "abnormal"},
        t=3.0,
        source_type="security_monitor",
        source_id="demo_secmon_01",
    )
    checks.append(check(
        "security_integrity_failure_derives_unverified_dt",
        "PASS" if dt.validity == "UNVERIFIED" else "FAIL",
        dt.validity,
        "UNVERIFIED",
    ))

    checks.append(check(
        "integrity_quality_zero_on_identity_failure",
        "PASS" if dt.quality.integrity == 0.0 else "FAIL",
        dt.quality.integrity,
        0.0,
    ))

    checks.append(check(
        "uncertainty_high_on_unverified_state",
        "PASS" if dt.quality.uncertainty == 1.0 else "FAIL",
        dt.quality.uncertainty,
        1.0,
    ))

    # Freshness must degrade with age.
    before = dt.quality.freshness
    dt.recompute_quality(current_t=603.0)
    after = dt.quality.freshness
    checks.append(check(
        "freshness_monotonically_degrades_with_age",
        "PASS" if after < before else "FAIL",
        {"before": before, "after": after},
        "after < before",
    ))

    # Provenance must exist for updated fields.
    prov = dt.provenance_for("clinical.SpO2")
    checks.append(check(
        "clinical_field_has_provenance",
        "PASS" if len(prov) == 1 else "FAIL",
        prov,
        "one provenance record",
    ))

    # Evidence boundaries.
    builder = EvidenceBundleBuilder()
    hospital = builder.build("hospital_agent", dt)
    cyber = builder.build("cyber_network_agent", dt)
    privacy = builder.build("privacy_agent", dt)

    checks.append(check(
        "hospital_cannot_receive_network_or_security_domain",
        "PASS" if (
            "network" not in hospital.digital_twin_view
            and "security" not in hospital.digital_twin_view
        ) else "FAIL",
        sorted(hospital.digital_twin_view.keys()),
        "no network/security",
    ))

    checks.append(check(
        "cyber_cannot_receive_clinical_domain",
        "PASS" if "clinical" not in cyber.digital_twin_view else "FAIL",
        sorted(cyber.digital_twin_view.keys()),
        "no clinical",
    ))

    checks.append(check(
        "privacy_receives_only_governance_relevant_dt_domains",
        "PASS" if set(privacy.digital_twin_view) == {
            "consent", "quality", "validity"
        } else "FAIL",
        sorted(privacy.digital_twin_view.keys()),
        ["consent", "quality", "validity"],
    ))

    # NCC data is an external dependency; absence is HOLD, not FAIL.
    ncc_context = None
    if NCC.exists():
        try:
            ncc = NCCCancerContext(NCC)
            ncc_context = ncc.query()
            safe = (
                ncc_context["patient_level_probability"] is None
                and ncc_context["clinical_inference_permitted"] is False
            )
            checks.append(check(
                "ncc_context_is_population_only",
                "PASS" if safe else "FAIL",
                {
                    "matched_rows": ncc_context["matched_rows"],
                    "patient_level_probability":
                        ncc_context["patient_level_probability"],
                    "clinical_inference_permitted":
                        ncc_context["clinical_inference_permitted"],
                },
                "population-only; no patient probability",
            ))
        except Exception as exc:
            checks.append(check(
                "ncc_context_is_population_only",
                "FAIL",
                str(exc),
                "valid NCC population context",
            ))
    else:
        checks.append(check(
            "ncc_context_is_population_only",
            "HOLD",
            str(NCC),
            "place shared NCC CSV at data/external/ncc_cancer_incidence.csv",
        ))

    # If context exists, only Hospital and Research/IRB may receive it.
    if ncc_context is not None:
        h = builder.build("hospital_agent", dt, ncc_context)
        r = builder.build("research_irb_agent", dt, ncc_context)
        c = builder.build("cyber_network_agent", dt, ncc_context)
        p = builder.build("privacy_agent", dt, ncc_context)
        g = builder.build("regulator_agent", dt, ncc_context)

        safe_access = (
            h.epidemiological_context is not None
            and r.epidemiological_context is not None
            and c.epidemiological_context is None
            and p.epidemiological_context is None
            and g.epidemiological_context is None
        )

        checks.append(check(
            "epidemiology_access_is_bounded",
            "PASS" if safe_access else "FAIL",
            {
                "hospital": h.epidemiological_context is not None,
                "research_irb": r.epidemiological_context is not None,
                "cyber": c.epidemiological_context is not None,
                "privacy": p.epidemiological_context is not None,
                "regulator": g.epidemiological_context is not None,
            },
            "Hospital/Research only",
        ))
    else:
        checks.append(check(
            "epidemiology_access_is_bounded",
            "HOLD",
            "NCC context unavailable",
            "requires NCC external CSV",
        ))

    with (OUT / "gate14_checks.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "observed", "expected"],
        )
        writer.writeheader()
        writer.writerows(checks)

    (OUT / "gate14_dt_snapshot.json").write_text(
        json.dumps(dt.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    failed = [c for c in checks if c["status"] == "FAIL"]
    held = [c for c in checks if c["status"] == "HOLD"]

    if failed:
        status = "FAIL"
    elif held:
        status = "HOLD"
    else:
        status = "PASS"

    result = {
        "gate": "GATE_14_DATA_GROUNDED_DT_FOUNDATION",
        "status": status,
        "passed_checks": sum(c["status"] == "PASS" for c in checks),
        "held_checks": len(held),
        "failed_checks": len(failed),
        "total_checks": len(checks),
        "dt_formalization": {
            "state_domains": [
                "clinical", "patient_context", "network", "security",
                "consent", "research", "ai_state"
            ],
            "quality_dimensions": [
                "freshness", "integrity", "completeness",
                "provenance", "uncertainty"
            ],
        },
        "ncc_external_dependency_present": NCC.exists(),
    }

    (OUT / "gate14_status.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if status == "FAIL":
        raise SystemExit(
            "Gate 14 FAILED. Diagnose DT/evidence-binding implementation."
        )

    if status == "HOLD":
        print(
            "\nGATE 14 HOLD — deterministic DT core passed, but the external "
            "NCC CSV is missing. Copy the shared CSV into data/external and rerun."
        )
    else:
        print(
            "\nFULL GATE 14 PASS — provenance-aware DT and bounded open-data "
            "evidence foundation validated."
        )

if __name__ == "__main__":
    main()
