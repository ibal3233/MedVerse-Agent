from __future__ import annotations

from typing import Dict, Any, List, Tuple
import hashlib
import itertools
import json

from medverse.learning.privacy_precedence_oracle_v2 import (
    privacy_precedence_oracle,
    ORACLE_VERSION,
)

JURISDICTIONS = ["KR", "US", "EU"]
TRISTATE = [True, False, None]
AUDIT = [False, True]

# Fresh exact-record contexts. These are nuisance/context variables in this
# synthetic benchmark; they do not alter the adopted policy oracle.
REPLICATION_CONTEXTS = [
    "clinical_data_quality_review",
    "institutional_access_recertification",
    "privacy_impact_reassessment",
]

CORE_KEYS = (
    "jurisdiction",
    "disclosure_authorized",
    "minimum_necessary",
    "purpose_declared",
    "audit_required",
)

# Seven cores diagnosed in Gate22B.4.
PROTECTED_DIAGNOSED_CORES = {
    ("KR", False, False, False, False),
    ("KR", False, False, False, True),
    ("KR", False, None, True, True),
    ("KR", False, True, False, False),
    ("KR", False, True, False, True),
    ("KR", True, False, False, False),
    ("KR", True, False, False, True),
}


def core_signature(features: Dict[str, Any]) -> Tuple[Any, ...]:
    return tuple(features.get(k) for k in CORE_KEYS)


def record_id(features: Dict[str, Any]) -> str:
    raw = json.dumps(features, sort_keys=True, ensure_ascii=False)
    return "G22B5-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:18]


def build_replication_benchmark() -> List[Dict[str, Any]]:
    rows = []

    for jurisdiction, auth, minimum, purpose, audit, context in itertools.product(
        JURISDICTIONS,
        TRISTATE,
        TRISTATE,
        TRISTATE,
        AUDIT,
        REPLICATION_CONTEXTS,
    ):
        features = {
            "jurisdiction": jurisdiction,
            "disclosure_authorized": auth,
            "minimum_necessary": minimum,
            "purpose_declared": purpose,
            "audit_required": audit,
            "request_context": context,
        }
        sig = core_signature(features)
        y = privacy_precedence_oracle(features)

        rows.append({
            "record_id": record_id(features),
            "features": features,
            "core_signature": sig,
            "protected_diagnosed_core": sig in PROTECTED_DIAGNOSED_CORES,
            "oracle_version": ORACLE_VERSION,
            **y,
        })

    rows.sort(key=lambda r: r["record_id"])
    return rows
