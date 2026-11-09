from pathlib import Path
import json, hashlib, sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "gate16"
OUT.mkdir(parents=True, exist_ok=True)

CAND = ROOT / "data" / "policy" / "candidate_v0.4"
REG = CAND / "CORPUS_REGISTRY_v0.4_candidate.json"
REC = CAND / "policy_records_v0.4_candidate.json"

REQUIRED_LAYER_TITLES = {
    "Medical Service Act",
    "Personal Information Protection Act",
    "Bioethics and Safety Act",
    "Medical Devices Act",
}

def main():
    registry = json.loads(REG.read_text(encoding="utf-8"))
    kb = json.loads(REC.read_text(encoding="utf-8"))
    records = kb["records"]

    checks = []

    def add(name, ok, observed, expected):
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
            "observed": observed,
            "expected": expected
        })

    add("jurisdiction_is_KR",
        registry.get("jurisdiction") == "KR",
        registry.get("jurisdiction"), "KR")

    add("canonical_four_layers_present",
        set(registry.get("canonical_layers", {})) == {
            "Statutes", "Decrees / Enforcement Rules",
            "Official Guidelines", "Institutional Governance"
        },
        list(registry.get("canonical_layers", {}).keys()),
        "four canonical corpus layers")

    ids = [r.get("chunk_id") for r in records]
    add("unique_chunk_ids",
        len(ids) == len(set(ids)),
        {"records": len(ids), "unique": len(set(ids))},
        "all unique")

    kr = [r for r in records if r.get("jurisdiction") == "KR"]
    add("all_candidate_records_KR",
        len(kr) == len(records),
        f"{len(kr)}/{len(records)}",
        "all records jurisdiction=KR")

    required_fields = [
        "chunk_id", "title", "agent_access", "source_type",
        "jurisdiction", "retrieval_eligible"
    ]
    missing = {}
    for r in records:
        m = [f for f in required_fields if f not in r]
        if m:
            missing[r.get("chunk_id", "<unknown>")] = m
    add("required_metadata_complete",
        not missing, missing or "complete", "no missing required metadata")

    # Ensure press releases never enter normative retrieval.
    press = [r for r in records if r.get("source_type") == "press_release"]
    add("press_releases_non_retrieval",
        all(r.get("retrieval_eligible") is False for r in press),
        {r["chunk_id"]: r.get("retrieval_eligible") for r in press},
        "False for all press releases")

    # Ensure full official health-data guideline is represented.
    hmd = [r for r in records if r.get("document_id") == "KR-HMDUG-2025"]
    add("health_guideline_operational_chunks_present",
        len(hmd) >= 8,
        len(hmd), ">= 8 operational chunks")

    agents = {
        "hospital_agent", "cyber_network_agent", "privacy_agent",
        "research_irb_agent", "regulator_agent"
    }
    covered = set()
    for r in records:
        covered.update(r.get("agent_access", []))
    add("all_five_agents_have_policy_coverage",
        agents.issubset(covered),
        sorted(covered), sorted(agents))

    # Required full 2026 pseudonymized-information guide is an external dependency.
    source_docs = registry.get("source_documents", [])
    full_guide = next(
        (x for x in source_docs
         if x.get("filename") ==
         "Pseudonymized_Information_Processing_Guideline_2026-03.pdf"),
        None
    )
    full_guide_present = (
        full_guide is not None
        and full_guide.get("status") == "obtained"
        and (ROOT / "data" / "policy" / "source_documents" /
             full_guide["filename"]).exists()
    )

    failed = [c for c in checks if c["status"] == "FAIL"]
    if failed:
        status = "FAIL"
        reason = "Corpus structure/provenance checks failed."
    elif not full_guide_present:
        status = "HOLD"
        reason = (
            "Core corpus assembly checks passed, but the full official "
            "Pseudonymized Information Processing Guideline (2026.03) "
            "is still missing. The press release is intentionally not "
            "accepted as normative policy evidence."
        )
    else:
        status = "PASS"
        reason = "Complete v0.4 source-controlled Korean policy corpus foundation validated."

    result = {
        "gate": "GATE_16_KR_POLICY_CORPUS_FOUNDATION",
        "status": status,
        "passed_checks": sum(c["status"] == "PASS" for c in checks),
        "failed_checks": len(failed),
        "total_checks": len(checks),
        "candidate_records": len(records),
        "health_guideline_chunks": len(hmd),
        "full_2026_pseudonymized_guideline_present": full_guide_present,
        "reason": reason
    }

    (OUT / "gate16_checks.json").write_text(
        json.dumps(checks, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "gate16_status.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print("\n========================================")
    print(" MedVerse-Agent - Gate 16")
    print(" Korean Policy Corpus Foundation")
    print("========================================\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if status == "FAIL":
        raise SystemExit("Gate 16 FAIL - diagnose corpus metadata/provenance.")
    elif status == "HOLD":
        print("\nGATE 16 HOLD - missing external full 2026 pseudonymized-information guideline.")
        print("Download from official KISA page:")
        print("https://www.kisa.or.kr/2060202/form?lang_type=KO&postSeq=138")
        print("Save as:")
        print(ROOT / "data" / "policy" / "source_documents" /
              "Pseudonymized_Information_Processing_Guideline_2026-03.pdf")
    else:
        print("\nFULL GATE 16 PASS.")

if __name__ == "__main__":
    main()
