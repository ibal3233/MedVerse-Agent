"""Deterministic unit/integrity checks using DEV primitives, not new evaluation labels."""
from __future__ import annotations
from itertools import permutations
from copy import deepcopy
from pathlib import Path
from final_validation.common import ROLES
from final_validation.engine import Session
from .schedulers import (MeasuredSession, STRATEGIES, DEPENDENCIES, execute_cycle,
                         dependency_order)

REQ = {'id': 'G28-DEV', 'purpose': 'scientific_research', 'data_form': 'pseudonymized',
       'fields': ['episode_code', 'symptom_band'], 'basis': 'pseudonymized_research_reviewed',
       'jurisdiction': 'KR', 'consent': False}
REVERSED = ('research_irb_agent', 'privacy_agent', 'hospital_agent', 'cyber_network_agent', 'regulator_agent')


def ready(privacy=True, research=True, request=None):
    s = MeasuredSession()
    events = [{'id': 'D1', 'kind': 'request', 'payload': deepcopy(request or REQ)}]
    if privacy:
        events.append({'id': 'DP', 'kind': 'approval', 'payload': {'kind': 'privacy'}})
    if research:
        events.append({'id': 'DR', 'kind': 'approval', 'payload': {'kind': 'research'}})
    for e in events:
        s.advance(e, run=False)
    return s


def run_tests():
    results = []
    def check(name, fn):
        try:
            value = bool(fn())
            results.append({'check': name, 'passed': value, 'error': None})
        except Exception as ex:
            results.append({'check': name, 'passed': False, 'error': type(ex).__name__ + ': ' + str(ex)})

    def owners_stable():
        s = ready()
        original = s.propose()
        ordered = dependency_order(list(reversed(original)), DEPENDENCIES)
        return set(original) == set(ordered) and all(s.proposals[p.proposal_id] == p for p in ordered)
    check('scheduler_preserves_issued_proposals_and_owners', owners_stable)

    def topological():
        s = ready(); ps = list(reversed(s.propose()))
        ordered = dependency_order(ps, DEPENDENCIES)
        names = [p.action for p in ordered]
        return all(names.index(a) < names.index('RELEASE_MINIMIZED_VIEW')
                   for a in DEPENDENCIES['RELEASE_MINIMIZED_VIEW'])
    check('dependency_order_respects_both_prerequisites', topological)

    def no_edges_identity():
        ps = list(reversed(ready().propose()))
        return dependency_order(ps, {}) == ps
    check('removing_edges_preserves_arrival_order', no_edges_identity)

    def cycles():
        s = ready(); ps = s.propose()
        try:
            dependency_order(ps, {**DEPENDENCIES, 'ATTEST_PRIVACY_SCOPE': ('RELEASE_MINIMIZED_VIEW',)})
        except ValueError:
            return not s.effects
        return False
    check('cyclic_graph_rejected_without_execution', cycles)

    def proposals_are_real():
        s = ready()
        execute_cycle(s, 'DEPENDENCY_ORDERED', REVERSED, True)
        return all(s.proposals[e['proposal_id']].owner == e['owner'] for e in s.effects)
    check('effects_link_to_actual_issued_proposals', proposals_are_real)

    def missing_approval():
        for mode in STRATEGIES:
            s = ready(privacy=False)
            execute_cycle(s, mode, REVERSED, True)
            if any(e['action'] == 'RELEASE_MINIMIZED_VIEW' for e in s.effects):
                return False
        return True
    check('scheduler_cannot_manufacture_missing_review', missing_approval)

    def revocation():
        s = ready(); s.advance({'id': 'REVOKE', 'kind': 'revoke', 'payload': {}}, run=False)
        execute_cycle(s, 'DEPENDENCY_ORDERED', REVERSED, True)
        return not any(e['action'] == 'RELEASE_MINIMIZED_VIEW' for e in s.effects)
    check('revocation_respected_at_execution_boundary', revocation)

    def fixed_point_bound():
        s = ready()
        cycle = execute_cycle(s, 'STATEFUL_FIXED_POINT', REVERSED, True)
        return cycle['rounds'] <= cycle['proposal_count'] + 1
    check('fixed_point_terminates_within_structural_bound', fixed_point_bound)

    def all_blocked_terminates():
        s = ready(False, False)
        c = execute_cycle(s, 'STATEFUL_FIXED_POINT', REVERSED, True)
        return c['rounds'] == 1 and not s.effects
    check('no_progress_stops_without_waiting_for_future_events', all_blocked_terminates)

    def counter():
        s = ready()
        c = execute_cycle(s, 'STATEFUL_FIXED_POINT', REVERSED, True)
        expected = len(c['attempts']) + sum(r['pre_status'] == 'PERMIT' for r in c['attempts'])
        return s.validation_calls == expected == c['validation_calls']
    check('counts_include_preflight_and_final_revalidation', counter)

    def private_view():
        s = ready()
        s.advance({'id': 'SYM', 'kind': 'clinical', 'payload': {'fever_reported': True, 'episode_code': 'TEST'}}, run=False)
        execute_cycle(s, 'DEPENDENCY_ORDERED', ROLES, False)
        return 'clinical' not in s.observe('cyber_network_agent') and 'clinical' not in s.observe('research_irb_agent')
    check('reordering_does_not_expand_role_observations', private_view)

    def care_continues():
        req = {**REQ, 'purpose': 'marketing'}
        s = ready(request=req)
        s.advance({'id': 'SYM', 'kind': 'clinical', 'payload': {'fever_reported': True, 'episode_code': 'TEST'}}, run=False)
        execute_cycle(s, 'DEPENDENCY_ORDERED', REVERSED, True)
        acts = [e['action'] for e in s.effects]
        return 'REQUEST_CLINICAL_REVIEW' in acts and 'RELEASE_MINIMIZED_VIEW' not in acts
    check('blocked_research_does_not_block_clinical_review', care_continues)

    def evidence():
        s = ready()
        s.advance({'id': 'MISS', 'kind': 'source_status', 'payload': {'unavailable': ['KR-PIPA-ART28-2-PSEUDONYM-001']}}, run=False)
        execute_cycle(s, 'DEPENDENCY_ORDERED', REVERSED, True)
        return not any(e['action'] == 'RELEASE_MINIMIZED_VIEW' for e in s.effects)
    check('missing_evidence_cannot_be_replaced_by_scheduling', evidence)

    def idempotence():
        s = ready()
        execute_cycle(s, 'DEPENDENCY_ORDERED', REVERSED, True)
        n = len(s.effects)
        execute_cycle(s, 'DEPENDENCY_ORDERED', REVERSED, True)
        return len(s.effects) == n and s.verify_audit()
    check('repeat_cycle_does_not_duplicate_side_effect', idempotence)

    def foreign():
        s = ready(request={**REQ, 'jurisdiction': 'OTHER'})
        execute_cycle(s, 'DEPENDENCY_ORDERED', REVERSED, True)
        return not s.effects
    check('foreign_jurisdiction_not_overridden', foreign)

    def labels_not_imported():
        text = Path(__file__).with_name('schedulers.py').read_text()
        return not any(word in text for word in ('workflow_oracle', 'requires_release_by_cursor', 'expected_outcome'))
    check('scheduler_does_not_read_scoring_oracle', labels_not_imported)
    return results
