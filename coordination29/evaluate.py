"""Run an immutable finite study; expected results never enter the selectors."""
from __future__ import annotations
import csv
import json
import platform
import time
import ast
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from .common import ROOT, DATA, OUT, STRATEGIES, load, save, digest, filehash, outcome
from .selectors import select
from .validator import execute, verify_chain, eligibility
from .reference_evaluator import reference_outcomes, assess_execution
from .specification_checks import audit
from .handoffs import evaluate_adapters, handoff_records
from .tests import run_tests


def write_csv(path, rows):
    if not rows:return
    with Path(path).open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader()
        for r in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict,tuple)) else v for k,v in r.items()})


def verify_freeze():
    m=load(DATA/'freeze_manifest.json');bad=[]
    for p,h in m['files'].items():
        if not (ROOT/p).is_file() or filehash(ROOT/p)!=h:bad.append(p)
    if bad:raise RuntimeError('Frozen artifacts changed: '+', '.join(bad)+'. Do not re-freeze after results.')
    return m


def preserve_previous():
    baseline=load(DATA/'upstream_manifest.json')
    return {'note':'Differences from packaged historical outputs are reported; frozen dependencies are checked separately.', 'files_checked':len(baseline),'unchanged':sum((ROOT/k).is_file() and filehash(ROOT/k)==v for k,v in baseline.items()),
            'changed':[k for k,v in baseline.items() if not (ROOT/k).is_file() or filehash(ROOT/k)!=v]}


def runtime_input(c):
    hidden={'family_id','track','split','motif','provenance','interpretation_review','operator_private_views','event_history'}
    return {k:v for k,v in c.items() if k not in hidden}


def run(stage='all'):
    manifest=verify_freeze()
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    dest=OUT/run_id;dest.mkdir(parents=True,exist_ok=False)
    tests=run_tests();preservation=preserve_previous()
    save(dest/'engineering_checks.json',tests);save(dest/'upstream_preservation.json',preservation)
    if not all(r['passed'] for r in tests):
        save(dest/'status.json',{'engineering_integrity':'FAIL','checks':tests,'preservation':preservation});raise RuntimeError('Pre-evaluation integrity failure; no comparison run.')
    families=load(DATA/'scenario_families.json')['families']
    leak=audit(families);save(dest/'split_and_leakage_audit.json',leak)
    selected=[c for c in families if stage=='all' or c['split']==('DEVELOPMENT' if stage=='dev' else 'CONFIRMATION')]
    rows=[];reference_rows={};traces={};timing=[]
    for c in selected:
        print(c['family_id'],c['track'],c['split'],len(c['actions']),'institution-owned candidate actions')
        public=runtime_input(c)
        # Reference evaluation occurs separately and is never passed to the methods.
        ref=reference_outcomes(public);reference_rows[c['family_id']]=ref
        for strategy in STRATEGIES:
            begin=time.perf_counter_ns();plan=select(public,strategy);elapsed=(time.perf_counter_ns()-begin)/1e6
            execution=execute(public,plan['sequence']);errors=assess_execution(public,execution['committed'])
            score=list(outcome(public,execution['committed']))
            got={t for a in public['actions'] if a['id'] in execution['committed'] for t in a['provides']}|set(public['initial_tokens'])
            clinical_required='clinical_review_done' in public['goals']
            clinical_feasible=any(any(a['id'] in r['action_set'] and 'clinical_review_done' in a['provides'] for a in public['actions']) for r in ref['valid_sets']) if clinical_required else None
            row={'family_id':c['family_id'],'track':c['track'],'split':c['split'],'strategy':strategy,
                 'reference_feasible_now':ref['feasible_now'],'reference_disposition':ref['disposition'],
                 'complete':sum(score[:2])==0,'reference_constraint_violations':len(errors),
                 'committed_actions':len(execution['committed']), 'objective':score,
                 'reference_best_objective':ref['best_objective'],'objective_optimal':score==ref['best_objective'],
                 'disposition':plan['disposition'],'disposition_correct':plan['disposition']==ref['disposition'],
                 'clinical_required':clinical_required,'clinical_feasible':clinical_feasible,
                 'clinical_completed':'clinical_review_done' in got,
                 'valid_alternative_used':any(a['priority']=='ALTERNATIVE' and a['id'] in execution['committed'] for a in public['actions']),
                 'selection_validator_calls':plan['selection_validator_calls'],'search_states':plan['search_states'],
                 'audit_chain_valid':verify_chain(execution['receipts']),'selection_duration_ms':elapsed}
            rows.append(row)
            traces[c['family_id']+'_'+strategy]={'input_sha256':digest(public),'selection':plan,'execution':execution,
                     'reference_assessment_errors':errors,'handoffs':handoff_records(public,execution),
                     'local_rejection_reasons':[{ 'proposal_id':a['id'],'reason':eligibility(public,a)[1]} for a in public['actions'] if not eligibility(public,a)[0]]}
    confirmation=[r for r in rows if r['split']=='CONFIRMATION']
    summaries=[]
    for s in STRATEGIES:
        subset=[r for r in confirmation if r['strategy']==s];feasible=[r for r in subset if r['reference_feasible_now']]
        cared=[r for r in subset if r['clinical_required'] and r['clinical_feasible']]
        summaries.append({'strategy':s,'confirmation_families':len(subset),'reference_feasible_families':len(feasible),
            'completed_feasible':sum(r['complete'] for r in feasible),
            'feasible_workflow_recall':sum(r['complete'] for r in feasible)/len(feasible) if feasible else None,
            'optimal_partial_or_complete':sum(r['objective_optimal'] for r in subset),
            'disposition_correct':sum(r['disposition_correct'] for r in subset),
            'clinical_feasible_families':len(cared),'clinical_completed':sum(r['clinical_completed'] for r in cared),
            'execution_violations':sum(r['reference_constraint_violations'] for r in subset),
            'committed_actions':sum(r['committed_actions'] for r in subset),
            'validator_calls_selection_only':sum(r['selection_validator_calls'] for r in subset),
            'all_audit_chains_valid':all(r['audit_chain_valid'] for r in subset)})
    # Additional, separately reported temporal revalidation probes. Not extra families.
    probes=[]
    for c in selected:
        if c['split']!='CONFIRMATION':continue
        plan=traces[c['family_id']+'_MEDVERSE_HARMONIZER']['selection']['sequence']
        if not plan:continue
        for kind in ('REVOKE','PURPOSE_CHANGE','POLICY_VERSION_CHANGE'):
            mutation={'before_step':len(plan)-1,'kind':kind}
            trace=execute(runtime_input(c),plan,mutation)
            probes.append({'family_id':c['family_id'],'mutation':kind,'before_step':len(plan)-1,
                           'last_commit_blocked':not trace['receipts'][-1]['permitted'],
                           'reason':trace['receipts'][-1]['reason'],'audit_valid':verify_chain(trace['receipts'])})
    adapters=evaluate_adapters([runtime_input(c)|{'family_id':c['family_id']} for c in selected if c['split']=='CONFIRMATION'])
    capable=[r for r in confirmation if r['strategy']!='REQUEST_ONLY']
    agreement=all(r['objective_optimal'] and r['disposition_correct'] for r in capable)
    integrity=all(r['reference_constraint_violations']==0 and r['audit_chain_valid'] for r in rows)
    paired=[]
    for c in selected:
        if c['split']!='CONFIRMATION':continue
        rs={r['strategy']:r for r in confirmation if r['family_id']==c['family_id']}
        paired.append({'family_id':c['family_id'],
                       'same_objective_capable_selectors':len({tuple(rs[s]['objective']) for s in STRATEGIES[1:]})==1,
                       'medverse_vs_stateful_completion_difference':int(rs['MEDVERSE_HARMONIZER']['complete'])-int(rs['FAIR_STATEFUL_SELECTOR']['complete'])})
    status={'gate':'GATE_29_INSTITUTIONAL_WORKFLOW_CHOICE','run_id':run_id,'stage':stage,
        'engineering_integrity':'PASS' if integrity else 'FAIL','checks_passed':sum(r['passed'] for r in tests),'checks_total':len(tests),
        'source_and_interpretation_review':'HOLD_PENDING_INDEPENDENT_CLINICAL_AND_KOREAN_LEGAL_REVIEW',
        'reference_method':'independently coded finite reference evaluator; same-developer modeling assumptions',
        'evaluation_independence':'Internal, predeclared grouped confirmation. Shared rule/action vocabulary; not external validation.',
        'families':len(selected),'development_families':sum(c['split']=='DEVELOPMENT' for c in selected),
        'confirmation_families':len(confirmation)//len(STRATEGIES),'strategy_executions':len(rows),
        'confirmation_summary':summaries,'capable_selectors_match_reference_objective_and_disposition':agreement,
        'all_capable_selectors_tie':all(p['same_objective_capable_selectors'] for p in paired),
        'strict_medverse_superiority_established':False,
        'temporal_probes':len(probes),'temporal_probes_reject_changed_authority':sum(p['last_commit_blocked'] for p in probes),
        'adapter_tests':len(adapters),'adapter_reference_agreement':sum(r['agreement'] for r in adapters),
        'adapter_expected_valid_accepts':sum(r['accepted'] and r['variant']=='complete' for r in adapters),
        'adapter_corrupted_or_missing_context_accepts':sum(r['accepted'] and r['variant']!='complete' for r in adapters),
        'original_files_preserved':preservation['unchanged'],'original_files_checked':preservation['files_checked'],
        'training_performed':False,'classifiers_loaded':False,'source_retrieval_benchmarked':False,
        'main_interface_modified':False,'clinical_validation':'NOT_ESTABLISHED','legal_validation':'NOT_ESTABLISHED',
        'claim_boundary':'Finite developer-authored workflow choice and local context handoffs. No universal planner advantage or medical/ITU conformance claim.',
        'freeze_manifest_sha256':filehash(DATA/'freeze_manifest.json')}
    save(dest/'status.json',status);save(dest/'reference_outcomes.json',reference_rows)
    save(dest/'raw_traces.json',traces);write_csv(dest/'case_metrics.csv',rows)
    write_csv(dest/'paired_comparisons.csv',paired);write_csv(dest/'temporal_revalidation.csv',probes)
    write_csv(dest/'workspace_adapter_tests.csv',adapters);save(dest/'environment.json',{'python':platform.python_version(),'platform':platform.platform(),'timing':'single-run descriptive selection duration only; no latency superiority claim'})
    print(json.dumps(status,indent=2));print('Raw evidence:',dest)
    return status,dest
