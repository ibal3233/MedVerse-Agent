"""Schedule actual issued proposals through the unchanged Gate 27 validator.

Only the scheduler changes. This module never creates an approval, modifies a
policy, rewrites a proposal, or uses expected outcomes to select an action.
The dependency map exposes a dependency already enforced by Session.validate.
It is an engineered workflow specification, not a new interpretation of law.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from typing import Iterable

from final_validation.engine import Session, Proposal

STRATEGIES = (
    'SNAPSHOT_ONCE', 'SEQUENTIAL_ONCE', 'STATEFUL_FIXED_POINT',
    'DEPENDENCY_ORDERED', 'DEPENDENCY_EDGES_REMOVED',
)
DEPENDENCIES = {
    'RELEASE_MINIMIZED_VIEW': ('ATTEST_PRIVACY_SCOPE', 'ATTEST_RESEARCH_BASIS'),
}

class MeasuredSession(Session):
    """Instrumentation only; action authorization remains in the original code."""
    def __init__(self, *args, **kwargs):
        self.validation_calls = 0
        super().__init__(*args, **kwargs)

    def validate(self, *args, **kwargs):
        self.validation_calls += 1
        return super().validate(*args, **kwargs)


def arrival_order(proposals: Iterable[Proposal], roles: tuple[str, ...],
                  release_first: bool) -> list[Proposal]:
    """Permute delivery order, not observations, proposals, or event chronology."""
    rank = {role: i for i, role in enumerate(roles)}
    def key(p: Proposal):
        if p.owner == 'research_irb_agent':
            within = (0 if p.action == 'RELEASE_MINIMIZED_VIEW' else 1) if release_first else (
                0 if p.action == 'ATTEST_RESEARCH_BASIS' else 1)
        else:
            within = 0
        return rank[p.owner], within, p.proposal_id
    return sorted(proposals, key=key)


def dependency_order(proposals: list[Proposal], dependencies: dict) -> list[Proposal]:
    """Stable Kahn ordering. The shared validator still checks committed prerequisites.

    Same-action dependencies are linked only within the same request and authorization
    epoch. An absent proposal does not manufacture a satisfied prerequisite.
    """
    remaining = list(proposals)
    ordered: list[Proposal] = []
    while remaining:
        ready = next((p for p in remaining if not any(
            q.action in dependencies.get(p.action, ()) and
            q.request_id == p.request_id and q.authorization_epoch == p.authorization_epoch
            for q in remaining
        )), None)
        if ready is None:
            raise ValueError('CYCLIC_PROPOSAL_DEPENDENCIES: no execution performed')
        ordered.append(ready)
        remaining.remove(ready)
    return ordered


def _record_nonexecution(s: Session, p: Proposal, verdict: dict, round_number: int):
    """Retain denied/conditional outcomes; do not convert a rejected action to a permit."""
    receipt = {
        'receipt_id': f'R{len(s.receipts)+1:05d}',
        'event_id': s.state['event_id'], 'owner': p.owner, 'proposal': p.to_dict(),
        'preflight': deepcopy(verdict), 'final_validation': deepcopy(verdict),
        'effect': None, 'current_revision': s.state['revision'],
        'current_authorization_epoch': s.state['authorization_epoch'],
        'scheduler_round': round_number,
    }
    s.receipts.append(receipt)
    s._audit('EXECUTION_RECEIPT', receipt)
    return receipt


def execute_cycle(s: MeasuredSession, strategy: str, role_order: tuple[str, ...],
                  release_first: bool) -> dict:
    if strategy not in STRATEGIES:
        raise ValueError(f'Unknown scheduling strategy: {strategy}')
    before_calls = s.validation_calls
    proposals = s.propose()  # Actual unchanged Gate 27 proposer, after the event arrives.
    ordered = arrival_order(proposals, role_order, release_first)
    delivered_ids = [p.proposal_id for p in ordered]
    if strategy == 'DEPENDENCY_ORDERED':
        ordered = dependency_order(ordered, DEPENDENCIES)
    elif strategy == 'DEPENDENCY_EDGES_REMOVED':
        ordered = dependency_order(ordered, {})
    initial_attestations = deepcopy(s.attestations)
    pending = list(ordered)
    attempts: list[dict] = []
    rounds = 0
    # At most n successful removals plus a no-progress round. No cost-based selection.
    bound = len(proposals) + 1
    while pending:
        rounds += 1
        if rounds > bound:
            raise RuntimeError('FIXED_POINT_BOUND_EXCEEDED')
        retry: list[Proposal] = []
        effects_before = len(s.effects)
        for p in pending:
            verdict = s.validate(p, attestations=(initial_attestations
                                 if strategy == 'SNAPSHOT_ONCE' else None))
            if verdict['status'] == 'PERMIT':
                receipt = s.commit(p, preflight=verdict)  # Original final revalidation.
            else:
                receipt = _record_nonexecution(s, p, verdict, rounds)
                # Only a dependency wait can be resolved by actions in this cycle.
                # New policy evidence / approvals require a new externally released event.
                if verdict['status'] == 'CONDITIONAL':
                    retry.append(p)
            attempts.append({
                'event_id': s.state['event_id'], 'cursor': s.state['cursor'],
                'round': rounds, 'proposal_id': p.proposal_id,
                'owner': p.owner, 'action': p.action,
                'request_id': p.request_id, 'authorization_epoch': p.authorization_epoch,
                'pre_status': verdict['status'], 'pre_reason': verdict['reason'],
                'final_status': receipt['final_validation']['status'],
                'final_reason': receipt['final_validation']['reason'],
                'committed': receipt['effect'] is not None,
                'effect_sequence': receipt['effect']['sequence'] if receipt['effect'] else None,
            })
        if strategy != 'STATEFUL_FIXED_POINT' or not retry or len(s.effects) == effects_before:
            break
        pending = retry
    # No agent-specific observations are exchanged to reorder the public proposal descriptors.
    s._audit('COORDINATION_SCHEDULER', {
        'strategy': strategy, 'arrival_ids': delivered_ids,
        'execution_order_ids': [p.proposal_id for p in ordered], 'rounds': rounds,
        'coordinator_is_institution': False,
    })
    return {
        'proposal_count': len(proposals), 'rounds': rounds,
        'validation_calls': s.validation_calls - before_calls,
        'attempts': attempts, 'arrival_ids': delivered_ids,
        'planned_ids': [p.proposal_id for p in ordered],
    }
