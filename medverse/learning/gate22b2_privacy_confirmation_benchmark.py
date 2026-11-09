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

# These contexts did not appear in Gate-21A or Gate-22A.
# Under the adopted synthetic oracle they are nuisance/context variables, not
# action-governing policy variables.
FRESH_CONTEXTS = [
    "institutional_quality_review",
    "cross_institutional_referral",
    "data_governance_audit",
]

CORE_KEYS = (
    "jurisdiction",
    "disclosure_authorized",
    "minimum_necessary",
    "purpose_declared",
    "audit_required",
)


def core_signature(features: Dict[str, Any]) -> Tuple[Any, ...]:
    return tuple(features.get(k) for k in CORE_KEYS)


def record_id(features: Dict[str, Any]) -> str:
    raw = json.dumps(features, sort_keys=True, ensure_ascii=False)
    return "G22B2-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:18]


def build_confirmation_benchmark() -> List[Dict[str, Any]]:
    rows = []

    for jurisdiction, auth, minimum, purpose, audit, context in itertools.product(
        JURISDICTIONS,
        TRISTATE,
        TRISTATE,
        TRISTATE,
        AUDIT,
        FRESH_CONTEXTS,
    ):
        features = {
            "jurisdiction": jurisdiction,
            "disclosure_authorized": auth,
            "minimum_necessary": minimum,
            "purpose_declared": purpose,
            "audit_required": audit,
            "request_context": context,
        }

        y = privacy_precedence_oracle(features)

        rows.append({
            "record_id": record_id(features),
            "features": features,
            "core_signature": core_signature(features),
            "oracle_version": ORACLE_VERSION,
            **y,
        })

    rows.sort(key=lambda r: r["record_id"])
    return rows
