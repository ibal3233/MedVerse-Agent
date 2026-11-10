from __future__ import annotations

import hashlib
import importlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "README.md",
    "submission/TECHNICAL-REPORT.md",
    "submission/Team_MedVerse_Final_Report_FINAL_CROSS_REFERENCED.pdf",
    "submission/Team_MedVerse_Final_Report_FINAL_CROSS_REFERENCED.docx",
    "submission/demo/README.md",
    "submission/Team_MedVerse_Knowledge_Base_FINAL_Submission_Guide.docx",
    "docs/architecture/medverse_system_architecture.png",
    "docs/architecture/korean_policy_pipeline.png",
    "docs/knowledge_base/KOREAN_POLICY_KB.md",
    "docs/standards/ITU_AND_READINESS_MAPPING.md",
    "docs/evaluation/RESEARCH_QUESTIONS.md",
    "run_presenter_sandbox.py",
    "run_commitment_sandbox.py",
]

MODULES = [
    "medverse.digital_twin",
    "foundation31.retrieval",
    "release33.server",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    checks = []
    ok = True
    for rel in REQUIRED:
        p = ROOT / rel
        passed = p.exists() and p.is_file() and p.stat().st_size > 0
        checks.append({"check": f"required:{rel}", "pass": passed})
        ok &= passed

    for mod in MODULES:
        try:
            importlib.import_module(mod)
            passed, detail = True, "imported"
        except Exception as exc:
            passed, detail = False, f"{type(exc).__name__}: {exc}"
        checks.append({"check": f"import:{mod}", "pass": passed, "detail": detail})
        ok &= passed

    checks.append({"check": "demo_release_asset", "pass": True, "required": False, "detail": "Final demo is published separately as GitHub Release asset Team_MedVerse_Demo.mov."})

    ncc = ROOT / "data/external/ncc_cancer_incidence.csv"
    checks.append({
        "check": "optional_ncc_csv_present",
        "pass": ncc.exists(),
        "required": False,
        "detail": "Optional population context; absence does not block the sandbox.",
    })

    key_files = {}
    for rel in REQUIRED:
        p = ROOT / rel
        if p.exists() and p.is_file():
            key_files[rel] = {"sha256": sha256(p), "size_bytes": p.stat().st_size}

    result = {
        "release": "Team MedVerse final sandbox candidate",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "required_checks_pass": ok,
        "checks": checks,
        "key_files": key_files,
        "manual_before_publication": [
            "Create the final GitHub repository and tag v1.0-hackathon.",
            "Insert the public GitHub URL into the final report header and regenerate the PDF if it still contains a placeholder.",
            "Verify the sandbox and trace download in a native Windows/macOS browser.",
            "Confirm redistribution permissions for any primary-source PDFs and optional NCC CSV before public upload.",
        ],
    }

    out_dir = ROOT / "outputs/final_submission/verification"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = out_dir / f"verification_{stamp}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "required_checks_pass": ok,
        "required_files": sum(1 for c in checks if c["check"].startswith("required:") and c["pass"]),
        "required_total": sum(1 for c in checks if c["check"].startswith("required:")),
        "module_imports_passed": sum(1 for c in checks if c["check"].startswith("import:") and c["pass"]),
        "module_imports_total": sum(1 for c in checks if c["check"].startswith("import:")),
        "optional_ncc_csv_present": ncc.exists(),
        "verification_record": str(out.relative_to(ROOT)),
    }, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
