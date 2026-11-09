"""Selectors have equal authorized inputs and no reference outcomes or case labels.

The fair stateful selector exhausts its finite search space: it is not artificially
budget-limited. The central planner retains each action's institutional ownership.
"""
from __future__ import annotations
from itertools import combinations, product
from .validator import eligibility, validate
from .common import outcome, tokens


class Checks:
    def __init__(self): self.calls=0; self.states=0
    def check(self,case,action,done,optimistic=False):
        self.calls+=1
        return validate(case,action,done,optimistic)[0]


def _best(case,plans):
    return min(plans,key=lambda p:(outcome(case,p),tuple(p)))


def stateful_search(case,allowed=None,optimistic=False):
    stats=Checks(); actions=[a for a in case['actions'] if allowed is None or a['id'] in allowed]
    queue=[()]; visited={frozenset()}; plans=[]
    while queue:
        sequence=queue.pop();plans.append(sequence);stats.states+=1
        for a in actions:
            if a['id'] in sequence:continue
            if stats.check(case,a,sequence,optimistic):
                new=sequence+(a['id'],);signature=frozenset(new)
                if signature not in visited:visited.add(signature);queue.append(new)
    return _best(case,plans),stats


def independent_planner(case):
    """Central subset-constraint planner; separate from goal-directed search.

    Local admissibility is supplied by the same runtime checks as other selectors.
    It cannot read the evaluation-only reference evaluator.
    """
    stats=Checks(); actions=case['actions'];plans=[()]
    for count in range(1,len(actions)+1):
        for subset in combinations(actions,count):
            stats.states+=1
            # independent set-consistency checks before constructing a valid order
            groups=[g for a in subset for g in a['exclusive_groups']]
            if len(groups)!=len(set(groups)):continue
            provides=set(case['initial_tokens']) | {t for a in subset for t in a['provides']}
            if any(not set(a['needs'])<=provides for a in subset):continue
            if any(set(a['forbids']) & (set(case['initial_tokens']) | {t for b in subset if b!=a for t in b['provides']}) for a in subset):continue
            remaining=list(subset);seq=[]
            while remaining:
                eligible=[a for a in remaining if stats.check(case,a,seq)]
                if not eligible:break
                a=min(eligible,key=lambda x:x['id']);seq.append(a['id']);remaining.remove(a)
            if not remaining:plans.append(tuple(seq))
    return _best(case,plans),stats


def harmonizer(case):
    """Goal-directed assembly of institution-owned alternatives and prerequisite closure."""
    stats=Checks();actions={a['id']:a for a in case['actions']}; initial=set(case['initial_tokens'])
    candidates={k:a for k,a in actions.items() if eligibility(case,a)[0]}
    plans=[()];considered=set()
    def fulfill(needed, selected):
        available=initial | {t for aid in selected for t in candidates[aid]['provides']}
        pending=set(needed)-available
        signature=(tuple(sorted(pending)),tuple(sorted(selected)))
        if signature in considered:return
        considered.add(signature);stats.states+=1
        if not pending:
            remaining=[candidates[i] for i in sorted(selected)];sequence=[]
            while remaining:
                enabled=[a for a in remaining if stats.check(case,a,sequence)]
                if not enabled:return
                a=min(enabled,key=lambda x:x['id']);sequence.append(a['id']);remaining.remove(a)
            plans.append(tuple(sequence));return
        goal=min(pending)
        for aid,a in candidates.items():
            if goal not in a['provides'] or aid in selected:continue
            chosen=selected|{aid}
            # Existing action contracts describe obligations; no reference labels are used.
            requirements=(set(needed)-set(a['provides']))|set(a['needs'])
            # Include needs of every selected action to reject cycles at ordering stage.
            requirements|={t for i in chosen for t in candidates[i]['needs']}
            fulfill(requirements,chosen)
    goals=list(case['goals'])
    # Partial plans remain possible when the whole task is not executable now.
    for k in range(len(goals)+1):
        for goal_subset in combinations(goals,k):fulfill(set(goal_subset),set())
    return _best(case,plans),stats


def select(case, strategy):
    if strategy=='REQUEST_ONLY':
        sequence, stats=stateful_search(case,{a['id'] for a in case['actions'] if a['priority']=='REQUESTED'})
    elif strategy=='FAIR_STATEFUL_SELECTOR':sequence,stats=stateful_search(case)
    elif strategy=='INDEPENDENT_CONSTRAINT_PLANNER':sequence,stats=independent_planner(case)
    elif strategy=='MEDVERSE_HARMONIZER':sequence,stats=harmonizer(case)
    else:raise ValueError('Unknown strategy: '+strategy)
    score=outcome(case,sequence)
    # Common feasibility/uncertainty classifier is held constant to isolate choice.
    if sum(score[:2])==0:disposition='FEASIBLE_NOW'
    else:
        attainable,_=stateful_search(case)
        possible,_=stateful_search(case,optimistic=True)
        if sum(outcome(case,attainable)[:2])==0:
            disposition='FEASIBLE_ALTERNATIVE_NOT_SELECTED'
        elif sum(outcome(case,possible)[:2])==0:
            pending=any((case['authority_register'].get(g) or {}).get('status') in {None,'PENDING'} for a in case['actions'] for g in a['grant_ids'])
            disposition='HUMAN_AUTHORITY_REQUIRED' if pending else 'INSUFFICIENT_EVIDENCE'
        else:disposition='NO_FEASIBLE_WORKFLOW_UNDER_MODELED_CONSTRAINTS'
    if sum(score[:2])>0 and disposition=='FEASIBLE_NOW':raise AssertionError('Inconsistent disposition')
    return {'sequence':list(sequence),'objective':list(score),'disposition':disposition,
            'selection_validator_calls':stats.calls,'search_states':stats.states,
            'coordination_messages_measured':False,
            'note':'Common uncertainty classifier held fixed; not an independent treatment variable.'}
