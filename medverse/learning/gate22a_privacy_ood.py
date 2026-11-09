from __future__ import annotations
from typing import Dict, Any, List
import json, hashlib

def rid(i, f):
    return hashlib.sha256((str(i)+json.dumps(f,sort_keys=True)).encode()).hexdigest()[:16]

def oracle(features: Dict[str, Any]):
    j = features.get("jurisdiction", "KR")
    auth = features.get("disclosure_authorized")
    mn = features.get("minimum_necessary")
    purpose = features.get("purpose_declared")
    audit = features.get("audit_required", False)

    if j != "KR":
        return {
            "assessment":"FOREIGN_POLICY_NOT_GOVERNING_AUTHORITY",
            "action":"DENY_UNAUTHORIZED_DISCLOSURE",
            "boundary":"WRONG_JURISDICTION",
            "enforcement":"BLOCK",
            "evidence":"NONE",
        }

    if auth is None or mn is None or purpose is None:
        return {
            "assessment":"DISCLOSURE_AUTHORIZATION_UNKNOWN",
            "action":"REQUEST_ADDITIONAL_AUTHORIZATION",
            "boundary":"INSUFFICIENT_EVIDENCE",
            "enforcement":"ESCALATE",
            "evidence":"DISCLOSURE_AUTHORIZATION_AND_PURPOSE",
        }

    if auth is False:
        return {
            "assessment":"UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST",
            "action":"DENY_UNAUTHORIZED_DISCLOSURE",
            "boundary":"COMPLIANT",
            "enforcement":"PERMIT",
            "evidence":"NONE",
        }

    if mn is False:
        return {
            "assessment":"UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST",
            "action":"LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY",
            "boundary":"COMPLIANT",
            "enforcement":"PERMIT",
            "evidence":"NONE",
        }

    if purpose is False:
        return {
            "assessment":"UNAUTHORIZED_OR_EXCESSIVE_DISCLOSURE_REQUEST",
            "action":"REQUEST_ADDITIONAL_AUTHORIZATION",
            "boundary":"COMPLIANT",
            "enforcement":"PERMIT",
            "evidence":"NONE",
        }

    if audit:
        return {
            "assessment":"AUTHORIZED_MINIMUM_NECESSARY_DISCLOSURE",
            "action":"PRESERVE_PRIVACY_AUDIT_LOG",
            "boundary":"COMPLIANT",
            "enforcement":"PERMIT",
            "evidence":"NONE",
        }

    return {
        "assessment":"AUTHORIZED_MINIMUM_NECESSARY_DISCLOSURE",
        "action":"ALLOW_AUTHORIZED_DISCLOSURE",
        "boundary":"COMPLIANT",
        "enforcement":"PERMIT",
        "evidence":"NONE",
    }

def build_ood():
    cases = []
    jurisdictions = ["KR","US","EU"]
    auths = [True,False,None]
    mins = [True,False,None]
    purposes = [True,False,None]
    audits = [False,True]

    # Select deliberately cross-combined states absent from Gate-21A templates.
    selected = [
        ("KR",True,False,False,False),
        ("KR",False,False,True,False),
        ("KR",False,True,False,True),
        ("KR",True,False,True,True),
        ("KR",True,True,False,True),
        ("KR",None,True,True,False),
        ("KR",True,None,True,True),
        ("KR",True,True,None,True),
        ("KR",False,None,False,False),
        ("KR",None,False,True,True),
        ("KR",None,None,True,True),
        ("KR",True,None,None,False),
        ("US",False,False,False,True),
        ("US",None,True,True,False),
        ("US",True,None,False,True),
        ("US",True,True,None,False),
        ("EU",False,True,False,True),
        ("EU",None,None,True,False),
        ("EU",True,False,None,True),
        ("EU",False,None,None,False),
    ]

    # 20 base combinations x two context variants = 40 OOD cases.
    idx = 0
    for tup in selected:
        j,a,m,p,au = tup
        for context in ["care_coordination","research_secondary_use"]:
            f = {
                "jurisdiction":j,
                "disclosure_authorized":a,
                "minimum_necessary":m,
                "purpose_declared":p,
                "audit_required":au,
                "request_context":context,
            }
            y = oracle(f)
            cases.append({
                "record_id":rid(idx,f),
                "features":f,
                **y,
            })
            idx += 1
    return cases
