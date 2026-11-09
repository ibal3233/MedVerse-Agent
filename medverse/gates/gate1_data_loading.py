from __future__ import annotations
from pathlib import Path
import csv, json
from medverse.data.loader import load_json, load_csv_rows, sha256_file
from medverse.data.validators import validate_scenario, validate_policy_manifest, validate_ncc_csv

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "gate1"
OUT.mkdir(parents=True, exist_ok=True)

def save_checks(name, checks):
    path=OUT/f"{name}.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=["check","status","observed","expected"])
        w.writeheader()
        for r in checks:
            w.writerow(r)
    return path

def summarize(checks):
    counts={}
    for c in checks:
        counts[c["status"]]=counts.get(c["status"],0)+1
    return counts

def main():
    manifest=load_json(ROOT/"config"/"data_manifest.json")
    scenario=load_json(ROOT/"data"/"reference"/"MVKR-S01.json")
    policies=load_json(ROOT/"data"/"policy"/"policy_manifest.json")

    scenario_checks=validate_scenario(scenario)
    policy_checks=validate_policy_manifest(policies)
    save_checks("gate1a_scenario_checks", scenario_checks)
    save_checks("gate1a_policy_manifest_checks", policy_checks)

    core_checks=scenario_checks+policy_checks
    core_pass=all(c["status"]=="PASS" for c in core_checks)

    source=manifest["sources"][0]
    ncc_path=ROOT/source["local_path"]
    external_status="HOLD"
    external_checks=[]
    fingerprint=None

    if ncc_path.exists():
        headers,rows=load_csv_rows(ncc_path)
        external_checks=validate_ncc_csv(headers,rows,source["required_columns_ko"])
        save_checks("gate1b_ncc_checks", external_checks)
        external_status="PASS" if all(c["status"]=="PASS" for c in external_checks) else "FAIL"
        fingerprint=sha256_file(ncc_path)

    status={
        "gate":"GATE_1_DATA_LOADING",
        "core_status":"PASS" if core_pass else "FAIL",
        "external_public_data_status":external_status,
        "external_public_data_sha256":fingerprint,
        "core_summary":summarize(core_checks),
        "external_summary":summarize(external_checks),
        "interpretation":{
            "PASS":"All predefined checks passed.",
            "FAIL":"At least one predefined validation failed. Diagnose before changing schema/data.",
            "HOLD":"Authoritative external file is not present yet; do not substitute fabricated data."
        }
    }
    (OUT/"gate1_status.json").write_text(json.dumps(status,indent=2),encoding="utf-8")

    print(json.dumps(status,indent=2))
    if not core_pass:
        raise SystemExit(2)
    if external_status=="FAIL":
        raise SystemExit(3)

if __name__=="__main__":
    main()
