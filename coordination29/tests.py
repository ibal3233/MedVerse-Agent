"""Hand-authored development fixtures and failure probes. Never trains or tunes."""
from __future__ import annotations
from copy import deepcopy
import ast
from .common import ROOT, DATA, load, digest, STRATEGIES
from .validator import validate, execute, verify_chain, envelope_check
from .reference_evaluator import reference_outcomes, assess_execution
from .selectors import select
from .specification_checks import audit


def run_tests():
    cases=load(DATA/'scenario_families.json')['families']; dev={c['family_id']:c for c in cases if c['split']=='DEVELOPMENT'}
    results=[]
    def check(name, condition):
        results.append({'name':name,'passed':bool(condition)})
    # Explicit finite expected outcomes authored from the specification, not model outputs.
    fixtures={'D01':('FEASIBLE_NOW',[0,0,0,1]),'D04':('FEASIBLE_NOW',[0,0,1,3]),
              'D05':('FEASIBLE_NOW',[0,0,2,1]),'D06':('INSUFFICIENT_EVIDENCE',[0,1,0,0])}
    for fid,(state,obj) in fixtures.items():
        c=dev[fid];r=reference_outcomes(c)
        check(fid+'_reference_disposition',r['disposition']==state)
        check(fid+'_hand_specified_objective',r['best_objective']==obj)
        for s in STRATEGIES[1:]:
            p=select(c,s);trace=execute(c,p['sequence'])
            check(fid+'_'+s,p['objective']==obj and not assess_execution(c,trace['committed']) and verify_chain(trace['receipts']))
    care=deepcopy(dev['D01']);a=care['actions'][0]
    check('unknown_proposal_rejected',execute(care,['NEVER_PROPOSED'])['committed']==[])
    check('replay_action_rejected',len(execute(care,[a['id'],a['id']])['committed'])==1)
    wrong=deepcopy(a);wrong['owner']='cyber_network_agent';check('cross_role_action_rejected',not validate(care,wrong,[])[0])
    changed=deepcopy(care);changed['jurisdiction']='OTHER';check('jurisdiction_rejected',not validate(changed,a,[])[0])
    changed=deepcopy(care);changed['epoch']+=1;check('stale_proposal_rejected',not validate(changed,a,[])[0])
    changed=deepcopy(care);changed['authority_register'][a['grant_ids'][0]]['fields'].append('unapproved');check('authority_record_tamper_rejected',not validate(changed,a,[])[0])
    changed=deepcopy(care);changed['adequacy']['clinical_review']=['unavailable_capability'];check('task_inadequacy_rejected',not validate(changed,a,[])[0])
    changed=deepcopy(a);changed['purpose']='marketing';check('silent_purpose_substitution_rejected',not validate(care,changed,[])[0])
    check('commit_epoch_rechecked',execute(care,[a['id']],{'before_step':0,'kind':'REVOKE'})['committed']==[])
    check('commit_purpose_rechecked',execute(care,[a['id']],{'before_step':0,'kind':'PURPOSE_CHANGE'})['committed']==[])
    log=execute(care,[a['id']]);log['receipts'][0]['owner']='other';check('receipt_tamper_detected',not verify_chain(log['receipts']))
    dt=deepcopy(dev['D05']);a=dt['actions'][0];e=deepcopy(dt['envelopes']['E1'])
    check('valid_dt_context_accepted',envelope_check(dt,a,e)[0])
    for key in e:
        copy=deepcopy(e);del copy[key];check('missing_'+key+'_rejected',not envelope_check(dt,a,copy)[0])
    for key,value in [('authority_epoch',0),('validity','UNVERIFIED'),('observed_event',0),('observed_event',9),('recipient','other'),('purpose','marketing'),('policy_snapshot','OTHER'),('expires_event',0)]:
        copy=deepcopy(e);copy[key]=value;check('changed_'+key+'_'+str(value)+'_rejected',not envelope_check(dt,a,copy)[0])
    mixed=deepcopy(dev['D06']);mixed['envelopes']['E1']['policy_snapshot']='KNOWN_WRONG'
    check('missing_context_does_not_erase_known_policy_conflict',reference_outcomes(mixed)['disposition']=='NO_FEASIBLE_WORKFLOW_UNDER_MODELED_CONSTRAINTS')
    check('runtime_diagnostic_preserves_known_conflict',select(mixed,'MEDVERSE_HARMONIZER')['disposition']=='NO_FEASIBLE_WORKFLOW_UNDER_MODELED_CONSTRAINTS')
    grouped=audit(cases);check('no_cross_split_structure_groups',not grouped['cross_split_structural_groups'])
    check('no_duplicate_input_records',grouped['duplicate_input_records']==0)
    text=(ROOT/'coordination29/selectors.py').read_text()
    imports=[n for n in ast.walk(ast.parse(text)) if isinstance(n,(ast.Import,ast.ImportFrom))]
    check('selectors_do_not_import_reference_evaluator',all('reference' not in str(getattr(n,'module','')) for n in imports))
    check('selectors_do_not_read_files',not any(x in text for x in ('read_text(','read_json(','load(')))
    # Distinguish untrusted coordinator fields from input to the runtime action gate.
    check('coordinator_is_not_an_action_owner','medverse_agent' not in {x['owner'] for c in cases for x in c['actions']})
    return results

if __name__=='__main__':
    import json
    r=run_tests();print(json.dumps(r,indent=2));print('PASSED',sum(x['passed'] for x in r),'/',len(r))
    if not all(x['passed'] for x in r):raise SystemExit(2)
