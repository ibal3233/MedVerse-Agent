from __future__ import annotations
from typing import Dict, Any

ORACLE_VERSION = "KR-PRIVACY-PRECEDENCE-v2"


def privacy_precedence_oracle(features: Dict[str, Any]):
    """
    Explicitly adopted Privacy precedence semantics.

    Scientific provenance:
    - agrees with every Gate-21A Privacy base template actually observed;
    - extends beyond Gate-21A to simultaneous violations / missing fields;
    - adoption is explicit after Gate-22B.1, not claimed to have been learned
      from the original Gate-21A generator.

    The request_context feature is deliberately non-governing in this synthetic
    benchmark; institutional action is determined by the frozen policy state.
    """
    jurisdiction = features.get("jurisdiction", "KR")
    auth = features.get("disclosure_authorized")
    minimum = features.get("minimum_necessary")
    purpose = features.get("purpose_declared")
    audit = features.get("audit_required", False)

    if jurisdiction != "KR":
        return {
            "assessment": "FOREIGN_POLICY_NOT_GOVERNING_AUTHORITY",
            "action": "DENY_UNAUTHORIZED_DISCLOSURE",
            "boundary": "WRONG_JURISDICTION",
            "enforcement": "BLOCK",
            "evidence": "NONE",
        }

    if auth is None or minimum is None or purpose is None:
        return {
            "assessment": "DISCLOSURE_AUTHORIZATION_UNKNOWN",
            "action": "REQUEST_ADDITIONAL_AUTHORIZATION",
            "boundary": "INSUFFICIENT_EVIDENCE",
            "enforcement": "ESCALATE",
            "evidence": "DISCLOSURE_AUTHORIZATION_AND_PURPOSE",
        }

    if auth is False:
        return {
            "assessment": "UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST",
            "action": "DENY_UNAUTHORIZED_DISCLOSURE",
            "boundary": "COMPLIANT",
            "enforcement": "PERMIT",
            "evidence": "NONE",
        }

    if minimum is False:
        return {
            "assessment": "UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST",
            "action": "LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY",
            "boundary": "COMPLIANT",
            "enforcement": "PERMIT",
            "evidence": "NONE",
        }

    if purpose is False:
        return {
            "assessment": "UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST",
            "action": "REQUEST_ADDITIONAL_AUTHORIZATION",
            "boundary": "COMPLIANT",
            "enforcement": "PERMIT",
            "evidence": "NONE",
        }

    if audit:
        return {
            "assessment": "AUTHORIZED_MINIMUM_NECESSARY_DISCLOSURE",
            "action": "PRESERVE_PRIVACY_AUDIT_LOG",
            "boundary": "COMPLIANT",
            "enforcement": "PERMIT",
            "evidence": "NONE",
        }

    return {
        "assessment": "AUTHORIZED_MINIMUM_NECESSARY_DISCLOSURE",
        "action": "ALLOW_AUTHORIZED_DISCLOSURE",
        "boundary": "COMPLIANT",
        "enforcement": "PERMIT",
        "evidence": "NONE",
    }
