"""Modeled workspace round trips and cross-institution handoff receipts.

Two local adapters; no claim of full ITU conformance or an authenticated remote peer.
"""
from __future__ import annotations
from copy import deepcopy
import json
from .common import ENVELOPE_KEYS, digest
from .validator import envelope_check


def direct_adapter(envelope):
    return json.loads(json.dumps(envelope,ensure_ascii=False))


def mapped_adapter(envelope):
    """Translate key names without altering policy/evidence semantics."""
    mapping={key:'workspace_'+str(i) for i,key in enumerate(ENVELOPE_KEYS)}
    wire={mapping.get(k,'extension_'+k):v for k,v in envelope.items()}
    inverse={v:k for k,v in mapping.items()}
    wire=json.loads(json.dumps(wire,ensure_ascii=False))
    return {inverse.get(k,k.removeprefix('extension_')):v for k,v in wire.items()}


def independent_receiving_check(case,a,e):
    # Separate receiving-side implementation for parity tests, not external legal review.
    required={'dt_ref','data_version','observed_event','provenance_ref','validity','purpose','recipient',
              'fields','policy_snapshot','authority_epoch','expires_event'}
    if not isinstance(e,dict) or not required<=set(e):return False
    if e['provenance_ref'] in {None,''} or e['validity']!='VALID':return False
    if e['authority_epoch']!=case['epoch'] or e['policy_snapshot']!=case['policy_snapshot']:return False
    if case['cursor']>e['expires_event'] or e['observed_event']>case['cursor']:return False
    if case['cursor']-e['observed_event']>case['freshness_events']:return False
    if (e['purpose'],e['recipient'])!=(a['purpose'],a['recipient']):return False
    return set(a['fields'])<=set(e['fields']) and digest(e) in case['trusted_envelope_hashes']


def evaluate_adapters(cases):
    rows=[]
    for c in cases:
        for a in c['actions']:
            if not a['envelope_id']:continue
            env=c['envelopes'][a['envelope_id']]
            if not independent_receiving_check(c,a,env):continue
            variants=[('complete',deepcopy(env))]
            for key in ENVELOPE_KEYS:
                item=deepcopy(env);item.pop(key);variants.append(('omit_'+key,item))
            for key,value in [('validity','UNVERIFIED'),('authority_epoch',0),('purpose','marketing'),
                              ('recipient','unauthorized_workspace'),('policy_snapshot','OLD'),
                              ('observed_event',0),('expires_event',0)]:
                item=deepcopy(env);item[key]=value;variants.append(('change_'+key,item))
            for label,item in variants:
                for adapter_name,adapter in [('DIRECT_JSON',direct_adapter),('MAPPED_KEYS',mapped_adapter)]:
                    received=adapter(item);valid,reason=envelope_check(c,a,received)
                    expected=independent_receiving_check(c,a,received)
                    rows.append({'family_id':c['family_id'],'proposal_id':a['id'],'adapter':adapter_name,
                        'variant':label,'accepted':valid,'reference_accepts':expected,'agreement':valid==expected,
                        'exact_context_preserved':received==item,'reason':reason,
                        'wire_bytes':len(json.dumps(received,ensure_ascii=False).encode()),
                        'simulated_fields_only':True})
    return rows


def handoff_records(case,execution):
    records=[]
    for receipt in execution['receipts']:
        if not receipt['permitted']:continue
        a=receipt['actual_proposal']
        if a['kind'] in {'QUARANTINE_STREAM','HANDOFF_ACK','CLINICAL_REVIEW','RESEARCH_VIEW','DT_RECEIVE'}:
            records.append({'proposal_id':a['id'],'responsible_institution':a['owner'],
                'activity':a['kind'],'depends_on':a['needs'],'established_obligations':a['provides'],
                'purpose':a['purpose'],'recipient':a['recipient'],'disclosed_field_names':a['fields'],
                'clinical_requirement_preserved_separately':'clinical_review_done' in case['goals'],
                'receipt_hash':receipt['hash'],'raw_patient_values_in_message':False})
    return records
