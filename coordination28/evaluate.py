"""Frozen, additive Gate 28 runner. Standard library only; no trained model is loaded."""
from __future__ import annotations
import argparse, ast, csv, gzip, hashlib, importlib.metadata, itertools, json
import platform, statistics, sys, time, traceback
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from final_validation.common import ROOT, ROLES, read_json, write_json, filehash, digest
from final_validation.engine import Session, SAFE_FIELDS, ACTION_OWNER
from final_validation.knowledge import PolicyCorpus
from .schedulers import (MeasuredSession, STRATEGIES, DEPENDENCIES,
                         arrival_order, execute_cycle)

DATA = ROOT / 'data/coordination28'
OUT = ROOT / 'outputs/gate28_coordination'
UPSTREAM = [
    'final_validation/__init__.py', 'final_validation/common.py',
    'final_validation/engine.py', 'final_validation/knowledge.py',
    'data/final_validation/freeze_manifest.json',
    'data/final_validation/workflow_families.json',
    'data/final_validation/workflow_oracle.json',
    'data/final_validation/source_review.json',
    'data/policy/candidate_v0.4/policy_records_v0.4_candidate.json',
]
NEW_CORE = ['coordination28/__init__.py', 'coordination28/schedulers.py',
            'coordination28/evaluate.py', 'coordination28/tests.py',
            'medverse/gates/gate28_coordination_mechanism.py',
            'docs/coordination28/PROTOCOL.md', 'data/coordination28/schedule_bank.json']


def all_families():
    return read_json(ROOT / 'data/final_validation/workflow_families.json')['families']


def write_csv(path, rows):
    rows = list(rows)
    if not rows:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open('w', encoding='utf-8', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict, tuple)) else v
                        for k, v in r.items()})


def create_schedule_bank():
    """Enumerate delivery schedules without using oracle labels or executing actions.

    Collapse templates that produce identical observable proposal ordering across
    every released event. This avoids counting absent-role permutations as extra tests.
    """
    result = {}
    for family in all_families():
        if family['split'] != 'CONFIRMATION':
            continue
        s = Session()
        proposal_batches = []
        for event in family['events']:
            s.advance(event, run=False)
            proposal_batches.append(s.propose())
        unique = {}
        for roles in itertools.permutations(ROLES):
            for release_first in (False, True):
                signature = tuple(tuple((p.owner, p.action) for p in arrival_order(batch, roles, release_first))
                                  for batch in proposal_batches)
                key = digest(signature)
                if key not in unique:
                    unique[key] = {
                        'schedule_id': f'{family["family_id"]}-S{len(unique)+1:03d}',
                        'role_order': list(roles), 'release_first': release_first,
                        'order_signature_sha256': key, 'equivalent_template_count': 0,
                    }
                unique[key]['equivalent_template_count'] += 1
        result[family['family_id']] = list(unique.values())
    return {
        'status': 'INPUT_ONLY_BEFORE_OUTCOME_EVALUATION',
        'templates_per_family': 240,
        'event_chronology_changed': False,
        'oracle_used_for_schedule_generation': False,
        'deduplication': 'identical owner/action delivery sequences at every event',
        'families': result,
    }


def freeze():
    manifest = DATA / 'freeze_manifest.json'
    if manifest.exists():
        raise RuntimeError('Gate28 freeze exists. Never overwrite it after observing outcomes.')
    DATA.mkdir(parents=True, exist_ok=True)
    write_json(DATA / 'schedule_bank.json', create_schedule_bank())
    files = UPSTREAM + NEW_CORE
    missing = [f for f in files if not (ROOT / f).is_file()]
    if missing:
        raise FileNotFoundError(missing)
    item = {
        'gate': 'GATE_28_COORDINATION_MECHANISM', 'version': '1.0.0',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'files': {f: filehash(ROOT / f) for f in files},
        'training': False, 'threshold_selection': False,
        'original_gates_modified': False,
        'evaluation_type': 'exhaustive proposal-order perturbations of previously seen workflow families',
        'independent_clinical_or_legal_confirmation': False,
    }
    write_json(manifest, item)
    return item


def verify_freeze():
    m = read_json(DATA / 'freeze_manifest.json')
    bad = [p for p, h in m['files'].items() if not (ROOT / p).exists() or filehash(ROOT / p) != h]
    if bad:
        raise RuntimeError('FROZEN ARTIFACT CHANGED: ' + ', '.join(bad))
    return m


def environment():
    try:
        version = importlib.metadata.version('scikit-learn')
    except importlib.metadata.PackageNotFoundError:
        version = None
    return {
        'python': sys.version, 'platform': platform.platform(),
        'scikit_learn_installed': version, 'saved_model_sklearn_version': '1.8.0',
        'model_replay_environment': 'VERSION_MATCH_ONLY_NOT_REPLAYED' if version == '1.8.0'
             else 'BLOCKED_VERSION_MISMATCH' if version else 'NOT_INSTALLED',
        'models_loaded_by_gate28': False,
        'note': 'Gate28 uses the original deterministic proposer and validator; saved classifiers are not loaded.',
    }


def normalized_native(s: Session):
    """Compare behavior, not strategy labels, timings, nonces, or hash-chain bytes."""
    return {
        'effects': s.effects, 'role_observations': s.role_observations,
        'coordination_state': s.last_cycle['coordination_state'],
        'decisions': [{
            'proposal': r['proposal'], 'final_validation': r['final_validation'],
            'effect': r['effect'], 'policy_evidence': r.get('policy_evidence', []),
        } for r in s.receipts],
    }


def native_equivalence(run_dir: Path):
    rows, traces = [], {}
    for f in all_families():
        results = {}
        for name in ('MEDVERSE', 'STATEFUL_FILTER'):
            s = Session(strategy=name)
            for event in f['events']:
                s.advance(event)
            results[name] = normalized_native(s)
            traces[f['family_id'] + '_' + name] = results[name]
        rows.append({
            'family_id': f['family_id'], 'historical_split': f['split'],
            'equal_normalized_behavior': results['MEDVERSE'] == results['STATEFUL_FILTER'],
            'medverse_behavior_sha256': digest(results['MEDVERSE']),
            'stateful_behavior_sha256': digest(results['STATEFUL_FILTER']),
        })
    # Static evidence: only LOCAL_FILTER and DENY_ALL are distinguished by cycle().
    tree = ast.parse((ROOT / 'final_validation/engine.py').read_text())
    cycle = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'cycle')
    branch_literals = set()
    for n in ast.walk(cycle):
        if isinstance(n, ast.Compare) and any(isinstance(x, ast.Attribute) and x.attr == 'strategy'
                                              for x in ast.walk(n)):
            branch_literals.update(x.value for x in ast.walk(n) if isinstance(x, ast.Constant)
                                   and isinstance(x.value, str))
    write_csv(run_dir / 'native_equivalence.csv', rows)
    write_json(run_dir / 'native_equivalence_traces.json', traces)
    return {'families_checked': len(rows), 'equal_behavior': sum(r['equal_normalized_behavior'] for r in rows),
            'cycle_strategy_branch_literals': sorted(branch_literals),
            'conclusion': 'Native MEDVERSE and STATEFUL_FILTER use the same scheduling path; the tie is structural.'}


def score_trace(s: Session, family: dict, target: dict):
    """Separate scoring; preserves the existing positive/negative workflow obligations.

    No oracle fields are supplied to proposer/scheduler/validator.
    Additional invariants use actual receipts and side-effect ordering.
    """
    actions = [e['action'] for e in s.effects]
    releases = [e for e in s.effects if e['action'] == 'RELEASE_MINIMIZED_VIEW']
    deadline = target['requires_release_by_cursor']
    care_ok = not target['requires_clinical_review'] or 'REQUEST_CLINICAL_REVIEW' in actions
    flag_ok = not target['requires_telemetry_flag'] or 'FLAG_TELEMETRY' in actions
    release_ok = not releases if deadline is None else any(e['cursor'] <= deadline for e in releases)
    forbidden = int(bool(target['forbid_research_release'] and releases)) + int(bool(
        target['forbid_dt_summary'] and 'USE_DT_SUMMARY' in actions))
    payload_errors = sum(not set(e['payload']).issubset(SAFE_FIELDS) for e in releases)
    owner_errors = sum(ACTION_OWNER.get(e['action']) != e['owner'] for e in s.effects)
    order_errors = 0
    for e in releases:
        past = {p['action'] for p in s.effects if p['sequence'] < e['sequence'] and
                p['request_id'] == e['request_id'] and p['authorization_epoch'] == e['authorization_epoch']}
        order_errors += not {'ATTEST_PRIVACY_SCOPE', 'ATTEST_RESEARCH_BASIS'}.issubset(past)
    duplicate_releases = len(releases) - len({(e['request_id'], e['authorization_epoch']) for e in releases})
    lineage_errors = sum(r['proposal']['proposal_id'] != r['effect']['proposal_id'] or
                         r['final_validation']['status'] != 'PERMIT'
                         for r in s.receipts if r['effect'] is not None)
    violations = forbidden + payload_errors + owner_errors + order_errors + duplicate_releases + lineage_errors
    return {
        'workflow_complete': bool(care_ok and flag_ok and release_ok and violations == 0),
        'clinical_review_requirement_met': care_ok, 'telemetry_flag_requirement_met': flag_ok,
        'release_requirement_met': release_ok, 'release_required': deadline is not None,
        'required_release_deadline_cursor': deadline,
        'first_release_cursor': min((e['cursor'] for e in releases), default=None),
        'committed_actions': len(s.effects), 'research_releases': len(releases),
        'forbidden_outcomes': forbidden, 'payload_errors': payload_errors,
        'owner_errors': owner_errors, 'prerequisite_order_errors': int(order_errors),
        'duplicate_releases': duplicate_releases, 'proposal_lineage_errors': lineage_errors,
        'total_invariant_violations': int(violations), 'audit_chain_valid': s.verify_audit(),
    }


def summarize(rows):
    grouped = defaultdict(list)
    for r in rows:
        grouped[r['strategy']].append(r)
    summary, by_family = [], []
    for name in STRATEGIES:
        rs = grouped[name]
        families = defaultdict(list)
        for r in rs:
            families[r['family_id']].append(r)
        family_success = []
        for family_id, fr in sorted(families.items()):
            rate = sum(r['workflow_complete'] for r in fr) / len(fr)
            family_success.append(rate)
            by_family.append({
                'strategy': name, 'family_id': family_id,
                'effective_schedules': len(fr),
                'completed_schedules': sum(r['workflow_complete'] for r in fr),
                'completion_fraction': rate,
                'robust_to_all_schedules': all(r['workflow_complete'] for r in fr),
                'mean_validation_calls': statistics.mean(r['validation_calls'] for r in fr),
                'max_rounds_per_event': max(r['max_rounds_per_event'] for r in fr),
                'invariant_violations': sum(r['total_invariant_violations'] for r in fr),
            })
        summary.append({
            'strategy': name, 'semantic_families': len(families),
            'effective_family_schedule_runs': len(rs),
            'completed_runs': sum(r['workflow_complete'] for r in rs),
            'pooled_completion_fraction': sum(r['workflow_complete'] for r in rs) / len(rs),
            'macro_family_completion_fraction': statistics.mean(family_success),
            'families_robust_to_all_schedules': sum(all(r['workflow_complete'] for r in fr)
                                                   for fr in families.values()),
            'total_validation_calls': sum(r['validation_calls'] for r in rs),
            'mean_validation_calls_per_workflow': statistics.mean(r['validation_calls'] for r in rs),
            'max_rounds_per_event': max(r['max_rounds_per_event'] for r in rs),
            'total_invariant_violations': sum(r['total_invariant_violations'] for r in rs),
            'all_audit_chains_valid': all(r['audit_chain_valid'] for r in rs),
        })
    return summary, by_family


def run_orders(run_dir: Path):
    bank = read_json(DATA / 'schedule_bank.json')
    oracle = read_json(ROOT / 'data/final_validation/workflow_oracle.json')
    kb = PolicyCorpus()
    rows, canonical = [], []
    ledger_fields = ['family_id', 'schedule_id', 'strategy', 'event_id', 'cursor', 'round',
        'proposal_id', 'owner', 'action', 'request_id', 'authorization_epoch', 'pre_status',
        'pre_reason', 'final_status', 'final_reason', 'committed', 'effect_sequence']
    trace_dir = run_dir / 'representative_traces'
    trace_dir.mkdir()
    with gzip.open(run_dir / 'proposal_attempts.csv.gz', 'wt', encoding='utf-8', newline='') as stream:
        ledger = csv.DictWriter(stream, fieldnames=ledger_fields)
        ledger.writeheader()
        for family in all_families():
            if family['split'] != 'CONFIRMATION':
                continue
            fid = family['family_id']
            schedules = bank['families'][fid]
            print(f'{fid}: {len(schedules)} distinct proposal-order schedules x {len(STRATEGIES)} configurations', flush=True)
            first_failure_saved = set()
            for schedule in schedules:
                for name in STRATEGIES:
                    s = MeasuredSession(corpus=kb)
                    cycles = []
                    t0 = time.perf_counter_ns()
                    for event in family['events']:
                        s.advance(event, run=False)
                        cycle = execute_cycle(s, name, tuple(schedule['role_order']), schedule['release_first'])
                        cycles.append(cycle)
                        for attempt in cycle['attempts']:
                            ledger.writerow({'family_id': fid, 'schedule_id': schedule['schedule_id'],
                                             'strategy': name, **attempt})
                    elapsed = (time.perf_counter_ns() - t0) / 1e6
                    row = {'family_id': fid, 'schedule_id': schedule['schedule_id'], 'strategy': name,
                           'historical_split': 'CONFIRMATION_ALREADY_SEEN',
                           'role_order': schedule['role_order'], 'release_first': schedule['release_first'],
                           'events': len(family['events']), **score_trace(s, family, oracle[fid]),
                           'validation_calls': s.validation_calls,
                           'total_rounds': sum(c['rounds'] for c in cycles),
                           'max_rounds_per_event': max(c['rounds'] for c in cycles),
                           'proposal_count': sum(c['proposal_count'] for c in cycles),
                           'descriptive_single_run_ms': elapsed,
                           'effect_set_sha256': digest(sorted(
                               (e['action'], e['owner'], e['event_id'], e['request_id'], e['authorization_epoch'])
                               for e in s.effects))}
                    rows.append(row)
                    is_canonical = schedule is schedules[0]
                    if is_canonical:
                        canonical.append(row)
                    if is_canonical or (not row['workflow_complete'] and name not in first_failure_saved):
                        write_json(trace_dir / f'{fid}_{name}_{schedule["schedule_id"]}.json', {
                            'result': row, 'input_events': family['events'],
                            'schedule': schedule, 'cycles': cycles, 'trace': s.snapshot()})
                        if not row['workflow_complete']:
                            first_failure_saved.add(name)
    summary, by_family = summarize(rows)
    write_csv(run_dir / 'per_schedule_results.csv', rows)
    write_csv(run_dir / 'per_family_results.csv', by_family)
    write_csv(run_dir / 'canonical_schedule_results.csv', canonical)
    write_csv(run_dir / 'strategy_summary.csv', summary)
    lookup = {(r['family_id'], r['schedule_id'], r['strategy']): r for r in rows}
    pairs = []
    for fid, schedules in bank['families'].items():
        for sched in schedules:
            sid = sched['schedule_id']
            a, b, c, d = (lookup[fid, sid, n] for n in (
                'STATEFUL_FIXED_POINT', 'DEPENDENCY_ORDERED', 'SEQUENTIAL_ONCE', 'DEPENDENCY_EDGES_REMOVED'))
            pairs.append({'family_id': fid, 'schedule_id': sid,
                          'fixedpoint_graph_same_completion': a['workflow_complete'] == b['workflow_complete'],
                          'fixedpoint_graph_same_effect_set': a['effect_set_sha256'] == b['effect_set_sha256'],
                          'validation_calls_saved_by_graph': a['validation_calls'] - b['validation_calls'],
                          'sequential_edgeless_same_completion': c['workflow_complete'] == d['workflow_complete'],
                          'sequential_edgeless_same_effect_set': c['effect_set_sha256'] == d['effect_set_sha256']})
    write_csv(run_dir / 'paired_comparisons.csv', pairs)
    return rows, summary, by_family, pairs


def execute(stage: str):
    m = verify_freeze()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    run_dir = OUT / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    write_json(run_dir / 'environment.json', environment())
    write_json(run_dir / 'input_manifest.json', m)
    from .tests import run_tests
    tests = run_tests()
    write_json(run_dir / 'deterministic_checks.json', tests)
    status = {
        'gate': 'GATE_28_COORDINATION_MECHANISM', 'stage': stage, 'run_id': run_id,
        'training_performed': False, 'original_artifacts_changed': False,
        'engineering_integrity': 'PENDING',
        'evaluation_independence': 'Known modeled families; new scheduling perturbations. Not external confirmation.',
        'saved_classifiers_loaded': False,
        'clinical_validation': 'NOT_ESTABLISHED', 'legal_review': 'PENDING',
    }
    try:
        if not all(r['passed'] for r in tests):
            raise AssertionError('Deterministic checks failed; evaluation not executed.')
        native = native_equivalence(run_dir)
        status['native_equivalence'] = native
        if stage != 'audit':
            rows, summary, by_family, pairs = run_orders(run_dir)
            status['strategy_summary'] = summary
            sm = {s['strategy']: s for s in summary}
            graph, fix, seq, snap = (sm[x] for x in ('DEPENDENCY_ORDERED', 'STATEFUL_FIXED_POINT',
                                                     'SEQUENTIAL_ONCE', 'SNAPSHOT_ONCE'))
            status['hypotheses'] = {
                'H1_graph_improves_order_robust_completion_over_single_pass': {
                    'supported_descriptively': graph['macro_family_completion_fraction'] > seq['macro_family_completion_fraction'],
                    'macro_difference': graph['macro_family_completion_fraction'] - seq['macro_family_completion_fraction']},
                'H2_graph_strictly_improves_completion_over_fair_fixed_point': {
                    'supported_descriptively': graph['macro_family_completion_fraction'] > fix['macro_family_completion_fraction'],
                    'paired_completion_differences': sum(not r['fixedpoint_graph_same_completion'] for r in pairs),
                    'interpretation': 'A tie is a valid scientific result; no stronger baseline is weakened.'},
                'H3_graph_reduces_validator_calls_at_equal_completion': {
                    'supported_descriptively': all(r['fixedpoint_graph_same_completion'] for r in pairs)
                         and graph['total_validation_calls'] < fix['total_validation_calls'],
                    'calls_saved': fix['total_validation_calls'] - graph['total_validation_calls'],
                    'relative_call_reduction': 1 - graph['total_validation_calls'] / fix['total_validation_calls']},
                'H4_removing_only_edges_reproduces_single_pass_behavior': {
                    'supported_descriptively': all(r['sequential_edgeless_same_effect_set'] for r in pairs)},
            }
            status['all_comparators_preserved_execution_invariants'] = all(r['total_invariant_violations'] == 0 for r in rows)
            status['all_audit_chains_valid'] = all(r['audit_chain_valid'] for r in rows)
            status['effective_family_schedule_pairs'] = len(pairs)
            status['total_workflow_executions'] = len(rows)
            status['unique_semantic_families'] = len({r['family_id'] for r in rows})
            status['timing_claim'] = 'Single-run durations are descriptive only; operation counts are the primary efficiency metric.'
        verify_freeze()
        status['deterministic_checks_passed'] = sum(r['passed'] for r in tests)
        status['deterministic_checks_total'] = len(tests)
        status['engineering_integrity'] = 'PASS'
        status['mechanism_claim'] = ('Dependency-aware scheduling is isolated from local authorization. '
            'Results do not establish unique institutional harmonization beyond an equivalent stateful scheduler, '
            'alternative-workflow synthesis, new legal reasoning, or trained-agent generalization.')
    except Exception:
        status['engineering_integrity'] = 'FAIL'
        status['error'] = traceback.format_exc()
        write_json(run_dir / 'status.json', status)
        raise
    write_json(run_dir / 'status.json', status)
    write_json(OUT / 'LATEST.json', {'run_id': run_id, 'relative_path': str(run_dir.relative_to(ROOT))})
    print(json.dumps(status, indent=2, ensure_ascii=False))
    print('\nRaw evidence: ' + str(run_dir))
    return status, run_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['all', 'audit', 'freeze'], default='all')
    args = parser.parse_args()
    if args.stage == 'freeze':
        print(json.dumps(freeze(), indent=2))
    else:
        execute(args.stage)

if __name__ == '__main__':
    main()
