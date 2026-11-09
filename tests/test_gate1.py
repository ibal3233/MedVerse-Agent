from pathlib import Path
import json
from medverse.data.validators import validate_scenario, validate_policy_manifest

ROOT=Path(__file__).resolve().parents[1]

def test_reference_scenario_passes():
    s=json.loads((ROOT/"data/reference/MVKR-S01.json").read_text())
    checks=validate_scenario(s)
    assert all(c["status"]=="PASS" for c in checks), checks

def test_policy_manifest_passes():
    p=json.loads((ROOT/"data/policy/policy_manifest.json").read_text())
    checks=validate_policy_manifest(p)
    assert all(c["status"]=="PASS" for c in checks), checks
