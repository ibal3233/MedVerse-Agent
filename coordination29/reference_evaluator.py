"""Evaluation-only reference outcomes from exhaustive subset enumeration.

Independently coded from the runtime validator and selectors; the same developer
specified both. This is implementation independence, NOT external clinical/legal
review. This module is never imported by selectors. All equally valid sets count.
"""
from __future__ import annotations
from itertools import combinations
from hashlib import sha256
import json


def _hash(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(',',':')).encode()).hexdigest()


def local_reference(case, a, possible=False):
    owners = {'CLINICAL_REVIEW':'hospital_agent','QUARANTINE_STREAM':'cyber_network_agent',
              'HANDOFF_ACK':'hospital_agent','PRIVACY_ATTEST':'privacy_agent',
              'RESEARCH_ATTEST':'research_irb_agent','RESEARCH_VIEW':'research_irb_agent',
              'DT_RECEIVE':'hospital_agent','OVERSIGHT_ATTEST':'regulator_agent'}
    if case['jurisdiction'] != 'KR' or owners.get(a['kind']) != a['owner']: return False
    if a['bound_epoch'] != case['epoch'] or a['policy_snapshot'] != case['policy_snapshot']: return False
    if a['purpose'] not in case['task_purposes']: return False
    if a['task'] not in case['adequacy']: return False
    if any(v not in a['capabilities'] for v in case['adequacy'][a['task']]): return False
    for term in a['state_requirements']:
        val = case['facts'].get(term['key'])
        if val is None and possible: continue
        if val != term['value']: return False
    for key in a['evidence']:
        r = case['evidence_register'].get(key)
        if r is None or r['status'] == 'MISSING':
            if possible: continue
            return False
        if r['status'] != 'AVAILABLE' or r['policy_snapshot'] != case['policy_snapshot']: return False
    for key in a['grant_ids']:
        g = case['authority_register'].get(key)
        if g is None or g['status'] == 'PENDING':
            if possible: continue
            return False
        if g['status'] != 'APPROVED' or case['authority_register_hashes'].get(key) != _hash(g): return False
        if g['epoch'] != case['epoch'] or case['cursor'] > g['expires_event']: return False
        if a['id'] not in g['action_ids'] or a['purpose'] != g['purpose'] or a['recipient'] != g['recipient']: return False
        if any(f not in g['fields'] for f in a['fields']): return False
    if a['envelope_id']:
        e = case['envelopes'].get(a['envelope_id'])
        keys = ('dt_ref','data_version','observed_event','provenance_ref','validity','purpose','recipient','fields','policy_snapshot','authority_epoch','expires_event')
        missing = not isinstance(e,dict) or any(k not in e for k in keys)
        hypothetical = missing or not e.get('provenance_ref')
        if hypothetical:
            if not possible:return False
            original=dict(e or {})
            e={'dt_ref':'pending-ref','data_version':'pending-version','observed_event':case['cursor'],
               'provenance_ref':'pending-provenance','validity':'VALID','purpose':a['purpose'],
               'recipient':a['recipient'],'fields':a['fields'],'policy_snapshot':case['policy_snapshot'],
               'authority_epoch':case['epoch'],'expires_event':case['cursor']}
            e.update(original)
            if not e['provenance_ref']:e['provenance_ref']='pending-provenance'
        if e['validity'] != 'VALID' or e['policy_snapshot'] != case['policy_snapshot']: return False
        if e['authority_epoch'] != case['epoch'] or case['cursor'] > e['expires_event']: return False
        if not 0 <= case['cursor']-e['observed_event'] <= case['freshness_events']: return False
        if e['purpose'] != a['purpose'] or e['recipient'] != a['recipient']: return False
        if any(f not in e['fields'] for f in a['fields']): return False
        if not hypothetical and _hash(e) not in case['trusted_envelope_hashes']: return False
    return True


def valid_subset(case, subset, possible=False):
    """Set constraints followed by a separate partial-order witness construction."""
    if any(not local_reference(case,a,possible) for a in subset): return None
    all_tokens = set(case['initial_tokens']) | {t for a in subset for t in a['provides']}
    for a in subset:
        if not set(a['needs']) <= all_tokens: return None
        other_tokens = set(case['initial_tokens']) | {t for b in subset if b['id'] != a['id'] for t in b['provides']}
        if set(a['forbids']) & other_tokens: return None
    for a,b in combinations(subset,2):
        if set(a['exclusive_groups']) & set(b['exclusive_groups']): return None
    for r in case['field_constraints']:
        fields = {f for a in subset if a['recipient']==r['recipient'] for f in a['fields']}
        if set(r['forbidden_combination']) <= fields: return None
    remaining = list(subset); witness=[]; available=set(case['initial_tokens'])
    while remaining:
        enabled = [a for a in remaining if set(a['needs']) <= available]
        if not enabled: return None
        a = sorted(enabled,key=lambda x:x['id'])[0]
        witness.append(a['id']);available.update(a['provides']);remaining.remove(a)
    return witness


def enumerate_reference(case, possible=False):
    actions=case['actions']; records=[]
    for mask in range(1 << len(actions)):
        group=[a for i,a in enumerate(actions) if mask & (1<<i)]
        witness=valid_subset(case,group,possible)
        if witness is None: continue
        achieved=set(case['initial_tokens']) | {t for a in group for t in a['provides']}
        fields={(a['recipient'],f) for a in group for f in a['fields']}
        objective=(int('clinical_review_done' in case['goals'] and 'clinical_review_done' not in achieved),len(set(case['goals'])-achieved),len(fields),len(group))
        records.append({'action_set':sorted(a['id'] for a in group),'witness':witness,
                        'objective':list(objective),'complete':objective[0]==0 and objective[1]==0})
    best=min(tuple(r['objective']) for r in records)
    return {'valid_sets':records,'valid_set_count':len(records),
            'feasible_sets':[r['action_set'] for r in records if r['complete']],
            'best_objective':list(best),'feasible_now':best[0]==0 and best[1]==0,
            'subsets_examined':1 << len(actions)}


def reference_outcomes(case):
    r=enumerate_reference(case)
    if r['feasible_now']:
        r['disposition']='FEASIBLE_NOW'
    else:
        possible=enumerate_reference(case,True)
        if possible['feasible_now']:
            pending=any((case['authority_register'].get(g) or {}).get('status') in {None,'PENDING'}
                        for a in case['actions'] for g in a['grant_ids'])
            r['disposition']='HUMAN_AUTHORITY_REQUIRED' if pending else 'INSUFFICIENT_EVIDENCE'
        else:r['disposition']='NO_FEASIBLE_WORKFLOW_UNDER_MODELED_CONSTRAINTS'
    return r


def assess_execution(case, sequence):
    """Validate actual ordered commits, not just equality to a preferred output."""
    lookup={a['id']:a for a in case['actions']}
    seen=[]; available=set(case['initial_tokens']); errors=[]
    for aid in sequence:
        a=lookup.get(aid)
        if a is None or aid in seen: errors.append({'action':aid,'reason':'UNKNOWN_OR_DUPLICATE'});continue
        if not set(a['needs']) <= available:errors.append({'action':aid,'reason':'PREMATURE_COMMIT'})
        selected=[lookup[s] for s in seen]+[a]
        if valid_subset(case,selected) is None:errors.append({'action':aid,'reason':'REFERENCE_CONSTRAINT_VIOLATION'})
        seen.append(aid);available.update(a['provides'])
    return errors
