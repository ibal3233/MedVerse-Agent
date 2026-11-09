from __future__ import annotations
from typing import Dict, Any, List, Tuple
import hashlib, json

from medverse.learning.privacy_precedence_oracle_v2 import privacy_precedence_oracle

TARGET_SUPPORT_PER_DIAGNOSED_CORE = 6

DIAGNOSED_CORES = [
    ("KR", False, False, False, False),
    ("KR", False, False, False, True),
    ("KR", False, None, True, True),
    ("KR", False, True, False, False),
    ("KR", False, True, False, True),
    ("KR", True, False, False, False),
    ("KR", True, False, False, True),
]

CORE_KEYS = (
    "jurisdiction",
    "disclosure_authorized",
    "minimum_necessary",
    "purpose_declared",
    "audit_required",
)

def features_from_core(sig):
    return dict(zip(CORE_KEYS, sig))

def record_id(sig, rep):
    raw = json.dumps({"core": sig, "rep": rep}, sort_keys=True, default=str)
    return "G22B6-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:18]

def build_targeted_repair_rows(existing_support):
    rows = []
    for sig in DIAGNOSED_CORES:
        existing = int(existing_support.get(sig, 0))
        needed = max(0, TARGET_SUPPORT_PER_DIAGNOSED_CORE - existing)
        features = features_from_core(sig)
        y = privacy_precedence_oracle(features)

        if sig[1] is True and sig[2] is False and sig[3] is False:
            family = "minimum_necessary_precedence_over_purpose"
        elif sig[1] is False and sig[2] is None:
            family = "missing_evidence_precedence_over_authorization_denial"
        else:
            family = "authorization_denial_precedence_over_purpose"

        for rep in range(needed):
            rows.append({
                "record_id": record_id(sig, rep),
                "features": features,
                "core_signature": sig,
                "target_action": y["action"],
                "repair_family": family,
                "support_before": existing,
                "support_target": TARGET_SUPPORT_PER_DIAGNOSED_CORE,
            })
    rows.sort(key=lambda r: r["record_id"])
    return rows
