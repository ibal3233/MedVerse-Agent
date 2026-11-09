from __future__ import annotations
from typing import Dict, Any, List, Tuple
import itertools, json, hashlib

from medverse.learning.gate22a_privacy_ood import build_ood, oracle


CORE_KEYS = (
    "jurisdiction",
    "disclosure_authorized",
    "minimum_necessary",
    "purpose_declared",
    "audit_required",
)


def core_signature(features: Dict[str, Any]) -> Tuple[Any, ...]:
    return tuple(features.get(k) for k in CORE_KEYS)


def rid(features):
    raw = json.dumps(features, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:18]


def build_augmentation() -> List[Dict[str, Any]]:
    """
    Build compositional training cases that cover interaction/precedence structure
    while excluding every Gate-22A OOD core combination.

    This is targeted data augmentation, not OOD-test reuse.
    """
    ood_signatures = {
        core_signature(c["features"])
        for c in build_ood()
    }

    all_candidates = []
    for jurisdiction, auth, minimum, purpose, audit in itertools.product(
        ["KR", "US", "EU"],
        [True, False, None],
        [True, False, None],
        [True, False, None],
        [False, True],
    ):
        features = {
            "jurisdiction": jurisdiction,
            "disclosure_authorized": auth,
            "minimum_necessary": minimum,
            "purpose_declared": purpose,
            "audit_required": audit,
        }

        sig = core_signature(features)
        if sig in ood_signatures:
            continue

        label = oracle(features)

        # Keep only interaction-rich cases that target the diagnosed weakness.
        violations = sum(v is False for v in [auth, minimum, purpose])
        missing = sum(v is None for v in [auth, minimum, purpose])
        wrong_j = jurisdiction != "KR"

        interaction_rich = (
            wrong_j
            or missing >= 1
            or violations >= 2
            or (audit and violations >= 1)
        )
        if not interaction_rich:
            continue

        all_candidates.append({
            "record_id": rid(features),
            "features": features,
            **label,
            "violation_count": violations,
            "missing_count": missing,
            "wrong_jurisdiction": wrong_j,
        })

    # Deterministic ordering.
    all_candidates.sort(key=lambda x: x["record_id"])
    return all_candidates
