from __future__ import annotations
from typing import Dict, Any, Tuple
import itertools, json, hashlib

CORE_KEYS = (
    "research_consent",
    "irb_status",
    "pseudonymized",
    "audit_required",
)

def sig(f: Dict[str, Any]) -> Tuple[Any, ...]:
    return tuple(f.get(k) for k in CORE_KEYS)

def rid(prefix, f):
    raw = prefix + json.dumps(f, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:18]

def oracle(f: Dict[str, Any]):
    consent = f.get("research_consent")
    irb = f.get("irb_status")
    pseudo = f.get("pseudonymized", True)
    audit = f.get("audit_required", False)

    # Explicit precedence: withdrawn consent dominates all other research states.
    if consent == "withdrawn":
        return {
            "assessment": "RESEARCH_PROCESSING_NOT_AUTHORIZED",
            "action": "BLOCK_RESEARCH_PROCESSING",
            "boundary": "COMPLIANT",
            "enforcement": "PERMIT",
            "evidence": "NONE",
        }

    # Missing consent or IRB state is evidentiary insufficiency.
    if consent is None or irb in {None, "unknown"}:
        return {
            "assessment": "RESEARCH_AUTHORIZATION_UNKNOWN",
            "action": "REQUEST_IRB_REVIEW",
            "boundary": "INSUFFICIENT_EVIDENCE",
            "enforcement": "ESCALATE",
            "evidence": "RESEARCH_AUTHORIZATION_STATE",
        }

    # Active consent is not enough without IRB approval / adequate governance.
    if irb != "approved" or pseudo is False:
        return {
            "assessment": "RESEARCH_REVIEW_REQUIRED",
            "action": "REQUEST_IRB_REVIEW",
            "boundary": "COMPLIANT",
            "enforcement": "PERMIT",
            "evidence": "NONE",
        }

    if audit:
        return {
            "assessment": "RESEARCH_PROCESSING_AUTHORIZED",
            "action": "PRESERVE_RESEARCH_AUDIT_LOG",
            "boundary": "COMPLIANT",
            "enforcement": "PERMIT",
            "evidence": "NONE",
        }

    return {
        "assessment": "RESEARCH_PROCESSING_AUTHORIZED",
        "action": "ALLOW_AUTHORIZED_RESEARCH_PROCESSING",
        "boundary": "COMPLIANT",
        "enforcement": "PERMIT",
        "evidence": "NONE",
    }

def build_ood():
    # Deliberately interaction-rich combinations not used as original atomic templates.
    combos = [
        ("withdrawn", "not_approved", False, True),
        ("withdrawn", "unknown", True, False),
        ("withdrawn", None, False, False),
        (None, "approved", True, True),
        (None, "not_approved", False, False),
        (None, None, True, True),
        ("active", "unknown", False, True),
        ("active", None, True, False),
        ("active", "not_approved", False, True),
        ("active", "approved", False, False),
        ("active", "approved", False, True),
        ("active", "not_approved", True, True),
    ]
    contexts = ["digital_trial", "secondary_analysis"]
    out = []
    for c in combos:
        for context in contexts:
            f = {
                "research_consent": c[0],
                "irb_status": c[1],
                "pseudonymized": c[2],
                "audit_required": c[3],
                "research_context": context,
            }
            out.append({"record_id": rid("ood", f), "features": f, **oracle(f)})
    return out

def build_augmentation():
    ood_sigs = {sig(c["features"]) for c in build_ood()}
    rows = []
    for consent, irb, pseudo, audit in itertools.product(
        ["active", "withdrawn", None],
        ["approved", "not_approved", "unknown", None],
        [True, False],
        [False, True],
    ):
        f = {
            "research_consent": consent,
            "irb_status": irb,
            "pseudonymized": pseudo,
            "audit_required": audit,
        }
        if sig(f) in ood_sigs:
            continue

        # Target interaction-rich combinations only.
        interaction = (
            consent == "withdrawn"
            or consent is None
            or irb in {"unknown", None}
            or (irb != "approved" and pseudo is False)
            or (audit and (irb != "approved" or pseudo is False))
        )
        if not interaction:
            continue

        y = oracle(f)
        rows.append({
            "record_id": rid("aug", f),
            "features": f,
            **y,
        })
    rows.sort(key=lambda x: x["record_id"])
    return rows
