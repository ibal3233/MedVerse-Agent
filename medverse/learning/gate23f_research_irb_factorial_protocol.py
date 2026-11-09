from __future__ import annotations

from typing import Dict, Any, List, Tuple
import hashlib
import itertools
import json

from medverse.learning.gate23_research_irb_benchmark import oracle
from medverse.learning.research_irb_precedence_features import enrich_research_irb_features


CONSENT = ["active", "withdrawn", None]
IRB = ["approved", "not_approved", "unknown", None]
PSEUDO = [True, False]
AUDIT = [False, True]

INTERACTION_FEATURES = [
    "ix_missing_consent",
    "ix_missing_irb",
    "ix_evidence_missing",
    "ix_consent_withdrawn",
    "ix_consent_active",
    "ix_irb_approved",
    "ix_irb_known_not_approved",
    "ix_pseudonymization_ok",
    "ix_pseudonymization_deficient",
    "ix_active_and_irb_approved",
    "ix_active_approved_and_pseudo_ok",
    "ix_active_approved_but_pseudo_deficient",
    "ix_audit_with_complete_authorization",
    "ix_audit_with_missing_evidence",
    "ix_audit_with_pseudonymization_deficiency",
    "ix_withdrawn_with_other_deficiency",
]


def signature(f: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        f["research_consent"],
        f["irb_status"],
        f["pseudonymized"],
        f["audit_required"],
    )


def record_id(f: Dict[str, Any]) -> str:
    raw = json.dumps(f, sort_keys=True, ensure_ascii=False)
    return "G23F-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _base_index(f: Dict[str, Any]) -> int:
    """
    Deterministic index over the full factorial state space.

    Fold assignment deliberately separates the two audit variants of the same
    consent/IRB/pseudonymization state. This is important because the repaired
    learner should see a policy interaction under one audit condition while
    generalizing its precedence under the paired audit condition.
    """
    ci = CONSENT.index(f["research_consent"])
    ii = IRB.index(f["irb_status"])
    pi = PSEUDO.index(f["pseudonymized"])
    ai = AUDIT.index(f["audit_required"])

    base = ci * (len(IRB) * len(PSEUDO)) + ii * len(PSEUDO) + pi
    return base * 2 + ai


def outer_fold(f: Dict[str, Any]) -> int:
    """
    Four deterministic folds, 12 states each.

    Audit twins are forced into adjacent but distinct folds:
      audit=False -> base mod 4
      audit=True  -> (base + 1) mod 4
    """
    ci = CONSENT.index(f["research_consent"])
    ii = IRB.index(f["irb_status"])
    pi = PSEUDO.index(f["pseudonymized"])
    ai = AUDIT.index(f["audit_required"])

    base = ci * (len(IRB) * len(PSEUDO)) + ii * len(PSEUDO) + pi
    return (base + ai) % 4


def build_factorial_benchmark() -> List[Dict[str, Any]]:
    rows = []
    for consent, irb, pseudo, audit in itertools.product(
        CONSENT, IRB, PSEUDO, AUDIT
    ):
        f = {
            "research_consent": consent,
            "irb_status": irb,
            "pseudonymized": pseudo,
            "audit_required": audit,
        }
        y = oracle(f)
        enriched = enrich_research_irb_features(f)

        active_interactions = [
            k for k in INTERACTION_FEATURES
            if bool(enriched.get(k, False))
        ]

        rows.append({
            "record_id": record_id(f),
            "features": f,
            "signature": signature(f),
            "outer_fold": outer_fold(f),
            "active_interactions": active_interactions,
            **y,
        })

    rows.sort(key=lambda r: r["record_id"])
    return rows
