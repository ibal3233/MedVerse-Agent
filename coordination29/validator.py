"""Shared runtime enforcement for every Gate 29 selector.

Trusted inputs: frozen modeled authority register and released event publisher.
This is NOT Korean legal approval, a real signature service, or production access control.
"""
from __future__ import annotations
from copy import deepcopy
from .common import OWNERS, ENVELOPE_KEYS, digest, tokens


def envelope_check(case: dict, action: dict, envelope: dict | None) -> tuple[bool, str]:
    if not isinstance(envelope, dict) or any(k not in envelope for k in ENVELOPE_KEYS):
        return False, 'INSUFFICIENT_DT_CONTEXT'
    if envelope['validity'] != 'VALID': return False, 'UNVERIFIED_DT'
    if not envelope['provenance_ref']: return False, 'MISSING_PROVENANCE'
    if envelope['policy_snapshot'] != case['policy_snapshot']: return False, 'POLICY_SNAPSHOT_MISMATCH'
    if envelope['authority_epoch'] != case['epoch']: return False, 'STALE_AUTHORITY_EPOCH'
    if envelope['expires_event'] < case['cursor']: return False, 'EXPIRED_DT_CONTEXT'
    age = case['cursor'] - envelope['observed_event']
    if age < 0 or age > case['freshness_events']: return False, 'STALE_OR_FUTURE_DT'
    if envelope['purpose'] != action['purpose'] or envelope['recipient'] != action['recipient']:
        return False, 'DT_PURPOSE_RECIPIENT_MISMATCH'
    if not set(action['fields']).issubset(envelope['fields']): return False, 'DT_FIELD_SCOPE_MISMATCH'
    if digest(envelope) not in case['trusted_envelope_hashes']:
        return False, 'UNTRUSTED_DT_CONTEXT'
    return True, 'DT_CONTEXT_VALID'


def eligibility(case: dict, action: dict, optimistic: bool=False) -> tuple[bool, str]:
    """Local mandate, evidence, trusted-state, scope, and authority checks."""
    if case['jurisdiction'] != 'KR': return False, 'WRONG_JURISDICTION'
    if OWNERS.get(action['kind']) != action['owner']: return False, 'OUTSIDE_MANDATE'
    if action['bound_epoch'] != case['epoch']: return False, 'STALE_PROPOSAL'
    if action['policy_snapshot'] != case['policy_snapshot']: return False, 'STALE_POLICY_BINDING'
    if action['purpose'] not in case['task_purposes']: return False, 'UNREQUESTED_PURPOSE'
    if action['task'] not in case['adequacy'] or not set(case['adequacy'][action['task']]).issubset(action['capabilities']):
        return False, 'INADEQUATE_FOR_TASK'
    for check in action['state_requirements']:
        actual = case['facts'].get(check['key'])
        if actual is None and optimistic: continue
        if actual != check['value']:
            return False, 'INSUFFICIENT_EVIDENCE' if actual is None else 'STATE_REQUIREMENT_FAILED'
    for ref in action['evidence']:
        record = case['evidence_register'].get(ref)
        if record is None or record['status'] == 'MISSING':
            if optimistic: continue
            return False, 'INSUFFICIENT_EVIDENCE'
        if record['status'] != 'AVAILABLE' or record['policy_snapshot'] != case['policy_snapshot']:
            return False, 'INELIGIBLE_POLICY_EVIDENCE'
    for name in action['grant_ids']:
        grant = case['authority_register'].get(name)
        if grant is None or grant['status'] == 'PENDING':
            if optimistic: continue
            return False, 'HUMAN_AUTHORITY_REQUIRED'
        if grant['status'] != 'APPROVED': return False, 'AUTHORITY_DENIED'
        trusted = case['authority_register_hashes'].get(name)
        if trusted != digest(grant): return False, 'UNTRUSTED_AUTHORITY_RECORD'
        if grant['epoch'] != case['epoch'] or grant['expires_event'] < case['cursor']:
            return False, 'EXPIRED_OR_REVOKED_AUTHORITY'
        if (action['id'] not in grant['action_ids'] or grant['purpose'] != action['purpose']
                or grant['recipient'] != action['recipient'] or not set(action['fields']).issubset(grant['fields'])):
            return False, 'AUTHORITY_SCOPE_MISMATCH'
    if action['envelope_id']:
        ok, reason = envelope_check(case, action, case['envelopes'].get(action['envelope_id']))
        if not ok:
            if not (optimistic and reason in {'INSUFFICIENT_DT_CONTEXT','MISSING_PROVENANCE'}):
                return False, reason
            # Diagnostic possibility only, never permission: fill unknown fields but
            # retain every known contradiction (e.g., wrong recipient or policy).
            hypothetical = deepcopy(case)
            existing = deepcopy(case['envelopes'].get(action['envelope_id']) or {})
            defaults = {'dt_ref':'pending-ref','data_version':'pending-version',
                        'observed_event':case['cursor'],'provenance_ref':'pending-provenance',
                        'validity':'VALID','purpose':action['purpose'],'recipient':action['recipient'],
                        'fields':action['fields'],'policy_snapshot':case['policy_snapshot'],
                        'authority_epoch':case['epoch'],'expires_event':case['cursor']}
            for key,value in defaults.items():
                if key not in existing or (key=='provenance_ref' and not existing[key]):
                    existing[key]=value
            hypothetical['trusted_envelope_hashes'] += [digest(existing)]
            future_ok,future_reason = envelope_check(hypothetical,action,existing)
            if not future_ok:return False,future_reason
    return True, 'ELIGIBLE'


def validate(case: dict, action: dict, chosen: tuple | list, optimistic: bool=False) -> tuple[bool, str]:
    if action['id'] in chosen: return False, 'DUPLICATE_ACTION'
    ok, reason = eligibility(case, action, optimistic)
    if not ok: return ok, reason
    available = tokens(case, chosen)
    if not set(action['needs']).issubset(available): return False, 'PENDING_DEPENDENCY'
    if set(action['forbids']) & available: return False, 'CONFLICTING_STATE'
    others = [a for a in case['actions'] if a['id'] in chosen]
    if any(set(a['forbids']) & set(action['provides']) for a in others):
        return False, 'JOINT_ACTION_CONFLICT'
    if any(set(a['exclusive_groups']) & set(action['exclusive_groups']) for a in others):
        return False, 'EXCLUSIVE_ALTERNATIVE'
    combined = others + [action]
    for restriction in case['field_constraints']:
        fields = set().union(*(set(a['fields']) for a in combined if a['recipient'] == restriction['recipient']))
        if set(restriction['forbidden_combination']).issubset(fields):
            return False, 'JOINT_DISCLOSURE_CONFLICT'
    return True, 'PERMIT'


def execute(case: dict, sequence: list[str], intervention: dict | None=None) -> dict:
    """Commit actual selected proposals, rechecking immediately before every action.

    An optional mutation is a separately logged temporal probe; it is never used to
    improve selection scores or to change the evidence in the primary comparison.
    """
    current = deepcopy(case)
    actions = {a['id']: a for a in current['actions']}
    done: list[str] = []
    receipts = []
    previous = '0'*64
    for step, action_id in enumerate(sequence):
        if intervention and step == intervention.get('before_step'):
            if intervention['kind'] == 'REVOKE': current['epoch'] += 1
            elif intervention['kind'] == 'POLICY_VERSION_CHANGE':
                current['policy_snapshot'] = 'NEW_UNREVIEWED_SNAPSHOT'
            elif intervention['kind'] == 'PURPOSE_CHANGE':
                current['task_purposes'] = ['changed_purpose_without_new_proposal']
        proposal = actions.get(action_id)
        ok, reason = validate(current, proposal, done) if proposal else (False, 'UNKNOWN_PROPOSAL')
        receipt = {
            'sequence': step+1, 'proposal_id': action_id,
            'owner': proposal['owner'] if proposal else None,
            'actual_proposal': proposal, 'permitted': ok, 'reason': reason,
            'authority_epoch_at_commit': current['epoch'],
            'evidence_ids': proposal['evidence'] if proposal else [],
            'modeled_side_effect': {'tokens': proposal['provides'], 'recipient': proposal['recipient'],
                                    'fields': proposal['fields']} if ok else None,
            'previous_hash': previous,
        }
        receipt['hash'] = digest(receipt); previous = receipt['hash']; receipts.append(receipt)
        if ok: done.append(action_id)
    return {'committed': done, 'receipts': receipts, 'intervention': intervention, 'final_epoch': current['epoch'],
            'simulation_only': True}


def verify_chain(receipts: list) -> bool:
    previous = '0'*64
    for i, row in enumerate(receipts, 1):
        body = {k:v for k,v in row.items() if k != 'hash'}
        if row['sequence'] != i or row['previous_hash'] != previous or digest(body) != row['hash']: return False
        previous = row['hash']
    return True
