from __future__ import annotations

from pathlib import Path
import sys
import json
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from medverse.digital_twin.model import PatientDigitalTwin
from medverse.data_grounding.ncc_context import NCCCancerContext
from medverse.data_grounding.evidence_bundle import EvidenceBundleBuilder
from medverse.data_grounding.policy_bundle import index_policy_records_by_agent
from medverse.reasoning.grounded_agent import DataPolicyGroundedAgent

ROOT = PROJECT_ROOT
OUT = ROOT / "outputs" / "gate15"
OUT.mkdir(parents=True, exist_ok=True)

NCC = ROOT / "data" / "external" / "ncc_cancer_incidence.csv"
POLICY = ROOT / "data" / "policy" / "seed" / "policy_seed_records.json"

def check(name, passed, observed, expected):
    return {
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "observed": observed,
        "expected": expected,
    }

def build_policy_index():
    seed = json.loads(POLICY.read_text(encoding="utf-8"))
    return index_policy_records_by_agent(seed)

def main():
    print("\n========================================")
    print(" MedVerse-Agent — Gate 15")
    print(" Data/Policy-Grounded Agent Reasoning")
    print("========================================\n")

    registry = json.loads(
        (ROOT / "FREEZE_REGISTRY.json").read_text(encoding="utf-8")
    )
    if (
        registry.get("promoted_gates", {})
        .get("GATE_14", {})
        .get("status") != "PASS"
    ):
        status = {
            "gate": "GATE_15_DATA_POLICY_GROUNDED_AGENT_REASONING",
            "status": "HOLD",
            "reason": "Gate 14 is not promoted PASS.",
        }
        (OUT / "gate15_status.json").write_text(
            json.dumps(status, indent=2), encoding="utf-8"
        )
        print(json.dumps(status, indent=2))
        return

    if not NCC.exists():
        status = {
            "gate": "GATE_15_DATA_POLICY_GROUNDED_AGENT_REASONING",
            "status": "HOLD",
            "reason": "NCC shared dataset is missing.",
            "expected_path": str(NCC),
        }
        (OUT / "gate15_status.json").write_text(
            json.dumps(status, indent=2), encoding="utf-8"
        )
        print(json.dumps(status, indent=2))
        return

    policy_index = build_policy_index()
    builder = EvidenceBundleBuilder(policy_index)
    ncc = NCCCancerContext(NCC)
    epi = ncc.query()

    checks = []
    trace = {}

    # ----------------------------------------------------------
    # S1-like DT
    # ----------------------------------------------------------
    dt1 = PatientDigitalTwin()
    dt1.update_domain(
        "clinical",
        {"SpO2": 78.0, "heart_rate": 122.0},
        t=1.0,
        source_type="wearable",
        source_id="demo_wearable_01",
    )
    dt1.update_domain(
        "network",
        {"packet_loss": 0.27, "rtt_ms": 840.0, "jitter_ms": 180.0},
        t=2.0,
        source_type="network_monitor",
        source_id="demo_netmon_01",
    )
    dt1.update_domain(
        "security",
        {"certificate_status": "mismatch", "session_origin": "abnormal"},
        t=3.0,
        source_type="security_monitor",
        source_id="demo_secmon_01",
    )

    hospital_bundle = builder.build("hospital_agent", dt1, epi)
    cyber_bundle = builder.build("cyber_network_agent", dt1, epi)

    hospital = DataPolicyGroundedAgent("hospital_agent").assess(hospital_bundle)
    cyber = DataPolicyGroundedAgent("cyber_network_agent").assess(cyber_bundle)

    checks.append(check(
        "S1_hospital_grounded_assessment",
        hospital.assessment_code == "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION",
        hospital.assessment_code,
        "POSSIBLE_CRITICAL_CLINICAL_DETERIORATION",
    ))
    checks.append(check(
        "S1_cyber_grounded_assessment",
        cyber.assessment_code == "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN",
        cyber.assessment_code,
        "DEVICE_IDENTITY_INTEGRITY_UNCERTAIN",
    ))
    checks.append(check(
        "S1_hospital_does_not_use_network_security",
        all(
            not x.startswith("network.")
            and not x.startswith("security.")
            for x in hospital.dt_evidence_used
        ),
        hospital.dt_evidence_used,
        "clinical evidence only",
    ))
    checks.append(check(
        "S1_cyber_does_not_use_clinical",
        all(
            not x.startswith("clinical.")
            for x in cyber.dt_evidence_used
        ),
        cyber.dt_evidence_used,
        "no clinical evidence",
    ))
    checks.append(check(
        "S1_population_context_not_patient_inference",
        (
            hospital.patient_level_inference_from_population_data is False
            and "NCC_population_epidemiological_context"
            in hospital.open_data_evidence_used
        ),
        hospital.to_dict(),
        "population context acknowledged without patient-level inference",
    ))

    trace["S1"] = {
        "hospital": hospital.to_dict(),
        "cyber": cyber.to_dict(),
    }

    # ----------------------------------------------------------
    # S2: care vs research
    # ----------------------------------------------------------
    dt2 = PatientDigitalTwin()
    dt2.update_domain(
        "consent",
        {
            "care_use_allowed": True,
            "research_use_allowed": False,
            "research_consent_status": "withdrawn",
        },
        t=1.0,
        source_type="consent_registry",
        source_id="demo_consent_01",
    )
    dt2.update_domain(
        "research",
        {
            "participant_consent_status": "withdrawn",
            "study_id": "DEMO-CANCER-001",
        },
        t=2.0,
        source_type="research_registry",
        source_id="demo_research_01",
    )

    privacy = DataPolicyGroundedAgent("privacy_agent").assess(
        builder.build("privacy_agent", dt2, epi)
    )
    research = DataPolicyGroundedAgent("research_irb_agent").assess(
        builder.build("research_irb_agent", dt2, epi)
    )

    checks.append(check(
        "S2_privacy_grounded_assessment",
        privacy.assessment_code == "CARE_ALLOWED_RESEARCH_WITHDRAWN",
        privacy.assessment_code,
        "CARE_ALLOWED_RESEARCH_WITHDRAWN",
    ))
    checks.append(check(
        "S2_research_grounded_assessment",
        research.assessment_code == "RESEARCH_PROCESSING_NOT_AUTHORIZED",
        research.assessment_code,
        "RESEARCH_PROCESSING_NOT_AUTHORIZED",
    ))
    checks.append(check(
        "S2_research_population_context_not_patient_inference",
        (
            research.patient_level_inference_from_population_data is False
            and "NCC_population_epidemiological_context"
            in research.open_data_evidence_used
        ),
        research.to_dict(),
        "population context only",
    ))

    trace["S2"] = {
        "privacy": privacy.to_dict(),
        "research_irb": research.to_dict(),
    }

    # ----------------------------------------------------------
    # S3: untrusted DT + high-impact AI
    # ----------------------------------------------------------
    dt3 = PatientDigitalTwin()
    dt3.update_domain(
        "security",
        {"certificate_status": "mismatch", "session_origin": "abnormal"},
        t=1.0,
        source_type="security_monitor",
        source_id="demo_secmon_03",
    )
    dt3.update_domain(
        "ai_state",
        {
            "decision_impact": "high",
            "requested_action": "automated_treatment_pathway_change",
        },
        t=2.0,
        source_type="ai_orchestrator",
        source_id="demo_ai_01",
    )

    regulator = DataPolicyGroundedAgent("regulator_agent").assess(
        builder.build("regulator_agent", dt3, epi)
    )

    checks.append(check(
        "S3_regulator_grounded_assessment",
        regulator.assessment_code
        == "HIGH_IMPACT_AI_REQUIRES_VALIDATED_EVIDENCE_AND_OVERSIGHT",
        regulator.assessment_code,
        "HIGH_IMPACT_AI_REQUIRES_VALIDATED_EVIDENCE_AND_OVERSIGHT",
    ))
    checks.append(check(
        "S3_regulator_no_population_context",
        regulator.open_data_evidence_used == [],
        regulator.open_data_evidence_used,
        [],
    ))

    trace["S3"] = {"regulator": regulator.to_dict()}

    # ----------------------------------------------------------
    # S4: unauthorized disclosure
    # ----------------------------------------------------------
    dt4 = PatientDigitalTwin()
    dt4.update_domain(
        "consent",
        {
            "disclosure_authorized": False,
            "minimum_necessary": False,
            "declared_purpose": "unspecified",
            "requesting_institution": "external_research_partner",
        },
        t=1.0,
        source_type="disclosure_request",
        source_id="demo_disclosure_01",
    )

    privacy4 = DataPolicyGroundedAgent("privacy_agent").assess(
        builder.build("privacy_agent", dt4, epi)
    )

    checks.append(check(
        "S4_privacy_grounded_assessment",
        privacy4.assessment_code
        == "UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST",
        privacy4.assessment_code,
        "UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST",
    ))

    trace["S4"] = {"privacy": privacy4.to_dict()}

    # ----------------------------------------------------------
    # Cross-scenario attribution checks
    # ----------------------------------------------------------
    all_assessments = [
        hospital, cyber, privacy, research, regulator, privacy4
    ]

    checks.append(check(
        "all_assessments_have_policy_attribution",
        all(len(a.policy_evidence_used) >= 1 for a in all_assessments),
        {
            a.agent_id: len(a.policy_evidence_used)
            for a in all_assessments
        },
        ">=1 authorized policy record per assessment",
    ))

    checks.append(check(
        "all_assessments_have_dt_provenance_attribution",
        all(len(a.provenance_evidence_used) >= 1 for a in all_assessments),
        {
            a.agent_id: len(a.provenance_evidence_used)
            for a in all_assessments
        },
        ">=1 DT provenance reference per assessment",
    ))

    checks.append(check(
        "no_assessment_declares_unauthorized_evidence_use",
        all(a.unauthorized_evidence_used is False for a in all_assessments),
        [a.unauthorized_evidence_used for a in all_assessments],
        [False] * len(all_assessments),
    ))

    checks.append(check(
        "no_population_data_patient_level_inference",
        all(
            a.patient_level_inference_from_population_data is False
            for a in all_assessments
        ),
        [
            a.patient_level_inference_from_population_data
            for a in all_assessments
        ],
        [False] * len(all_assessments),
    ))

    with (OUT / "gate15_checks.csv").open(
        "w", encoding="utf-8", newline=""
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["check", "status", "observed", "expected"],
        )
        writer.writeheader()
        writer.writerows(checks)

    (OUT / "gate15_grounded_trace.json").write_text(
        json.dumps(trace, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    passed = sum(c["status"] == "PASS" for c in checks)
    total = len(checks)
    gate_pass = passed == total

    result = {
        "gate": "GATE_15_DATA_POLICY_GROUNDED_AGENT_REASONING",
        "status": "PASS" if gate_pass else "FAIL",
        "passed_checks": passed,
        "total_checks": total,
        "scenario_families": ["S1", "S2", "S3", "S4"],
        "agents_grounded": [
            "hospital_agent",
            "cyber_network_agent",
            "privacy_agent",
            "research_irb_agent",
            "regulator_agent",
        ],
        "evidence_layers": [
            "authorized_digital_twin_view",
            "policy_records",
            "open_population_context_where_authorized",
            "provenance",
        ],
        "patient_level_inference_from_population_data": False,
    }

    (OUT / "gate15_status.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    print(json.dumps(result, indent=2))
    print(f"\nOutputs saved to:\n{OUT}")

    if not gate_pass:
        raise SystemExit(
            "Gate 15 FAILED. Diagnose evidence attribution or agent grounding."
        )

    print(
        "\nFULL GATE 15 PASS — institutional assessments are now explicitly "
        "grounded in bounded Digital-Twin evidence, policy records, authorized "
        "open-data context, and provenance."
    )

if __name__ == "__main__":
    main()
