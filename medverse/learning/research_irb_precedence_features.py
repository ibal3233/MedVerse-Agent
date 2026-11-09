from __future__ import annotations
from typing import Dict, Any
import json

MISSING_SENTINEL = "__MISSING__"


def enrich_research_irb_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add policy-structure interaction features without encoding target labels.

    These features are derived only from observable Research/IRB state:
    consent, IRB status, pseudonymization status and audit requirement.

    They expose interactions that the frozen institutional oracle already
    treats hierarchically, but they do not contain action/assessment labels.
    """
    f = dict(features)

    consent = f.get("research_consent")
    irb = f.get("irb_status")
    pseudo = f.get("pseudonymized")
    audit = f.get("audit_required", False)

    missing_consent = consent is None
    missing_irb = irb in {None, "unknown"}

    consent_withdrawn = consent == "withdrawn"
    consent_active = consent == "active"

    irb_approved = irb == "approved"
    irb_known_not_approved = irb == "not_approved"

    pseudo_ok = pseudo is True
    pseudo_deficient = pseudo is False

    evidence_missing = missing_consent or missing_irb

    # Explicit interaction terms. These describe governance state, not outputs.
    f.update({
        "ix_missing_consent": missing_consent,
        "ix_missing_irb": missing_irb,
        "ix_evidence_missing": evidence_missing,
        "ix_consent_withdrawn": consent_withdrawn,
        "ix_consent_active": consent_active,
        "ix_irb_approved": irb_approved,
        "ix_irb_known_not_approved": irb_known_not_approved,
        "ix_pseudonymization_ok": pseudo_ok,
        "ix_pseudonymization_deficient": pseudo_deficient,

        "ix_active_and_irb_approved": consent_active and irb_approved,
        "ix_active_approved_and_pseudo_ok": (
            consent_active and irb_approved and pseudo_ok
        ),
        "ix_active_approved_but_pseudo_deficient": (
            consent_active and irb_approved and pseudo_deficient
        ),
        "ix_audit_with_complete_authorization": (
            bool(audit) and consent_active and irb_approved and pseudo_ok
        ),
        "ix_audit_with_missing_evidence": (
            bool(audit) and evidence_missing
        ),
        "ix_audit_with_pseudonymization_deficiency": (
            bool(audit) and pseudo_deficient
        ),
        "ix_withdrawn_with_other_deficiency": (
            consent_withdrawn and (
                missing_irb or irb_known_not_approved or pseudo_deficient
            )
        ),
    })

    # Preserve meaningful unknown states as explicit categorical values.
    out = {}
    for k, v in f.items():
        out[k] = MISSING_SENTINEL if v is None else v
    return out


def enrich_from_json(features_json: str) -> Dict[str, Any]:
    return enrich_research_irb_features(json.loads(features_json))
