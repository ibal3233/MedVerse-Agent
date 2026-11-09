"""Versioned Gate 32 evaluation; no tuning, model training or automatic refreezing."""
from __future__ import annotations
import csv,sys,time,platform,inspect,itertools
from datetime import datetime,timezone
from collections import defaultdict
from copy import deepcopy as cp
from .common import DATA,OUT,ROOT,load,save,hashfile,digest,STRATEGIES,ROLES
from .runtime import Session,verify_receipts
from .publisher import Publisher
from .reference import assess,full_information,public_snapshots
from .tests import run_checks

def write_csv(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 if not rows:path.write_text('',encoding='utf-8');return
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,keys);w.writeheader()
  for r in rows:w.writerow({k:__import__('json').dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items()})

def verify_freeze():
 manifest=load(DATA/'freeze.json');bad=[]
 for rel,expected in manifest['files'].items():
  p=ROOT/rel
  if not p.is_file() or hashfile(p)!=expected:bad.append(rel)
 if bad:raise RuntimeError('FROZEN_FILE_MISMATCH: '+', '.join(bad))
 prior=load(DATA/'predecessor_manifest.json');missing=[]
 for rel,expected in prior.items():
  p=ROOT/rel
  if not p.is_file() or hashfile(p)!=expected:missing.append(rel)
 if missing:raise RuntimeError('PREDECESSOR_FILE_CHANGED: '+', '.join(missing))
 return manifest,len(prior)

def specification_audit(families):
 ids=[f['family_id'] for f in families]
 assert len(ids)==len(set(ids))
 prefixes={};shape={};records=[]
 for f in families:
  first=[b['events'][:f['shared_prefix_end']] for b in f['branches']]
  assert all(digest(x)==digest(first[0]) for x in first)
  prefix=digest(first[0]);prefixes.setdefault(prefix,[]).append(f['split'])
  # Conservative graph summary; shared action primitives and subgraphs are expected.
  signatures=[]
  for b in f['branches']:
   acts=[a for e in b['events'] for a in e['actions']]
   shape_fields=[(a['kind'],len(a['needs']),len(a['forbids']),len(a['fields']),len(a['exclusive_groups'])) for a in acts]
   signatures.append(sorted(shape_fields))
  fingerprint=digest(sorted(signatures));shape.setdefault(fingerprint,[]).append(f['split'])
  records.append({'family':f['family_id'],'split':f['split'],'branches':len(f['branches']),'prefix_hash':prefix,'structure_fingerprint':fingerprint})
 no_prefix=all(len(set(v))==1 for v in prefixes.values());no_shape=all(len(set(v))==1 for v in shape.values())
 if not (no_prefix and no_shape):raise AssertionError('CROSS_SPLIT_GROUP_OVERLAP')
 return {'families':records,'cross_split_exact_prefix_overlap':not no_prefix,'cross_split_structure_fingerprint_overlap':not no_shape,
         'scope':'A conservative authored grouping, not proof of complete semantic independence. All branches of a family stay together.'}

def legacy_regression():
 from coordination30.common import source_cases
 from coordination30.engine import IntegratedSession
 from coordination30.schedule import released_input
 records=[];source=source_cases()
 for c in source:
  for selector in ['REQUEST_ONLY','FAIR_STATEFUL_SELECTOR','INDEPENDENT_CONSTRAINT_PLANNER','MEDVERSE_HARMONIZER']:
   old=IntegratedSession(c['family_id'],selector,'PROGRESSIVE');new=Session('MEDVERSE_COMMITMENT',selector)
   for phase in range(1,7):
    os=old.advance();p=new.begin_snapshot(released_input(c,phase));ns=new.commit(p['plan_id'])
    equal=(os['committed_ids']==ns['committed'] and os['achieved_tokens']==ns['achieved'])
    records.append({'family':c['family_id'],'selector':selector,'event':phase,'same_committed_prefix_and_effects':equal,'legacy_wait_metadata_present':False})
 return records

def summarize(rows,refs):
 result=[]
 for method in STRATEGIES:
  r=[x for x in rows if x['strategy']==method and x['split']=='CONFIRMATION'];groups=defaultdict(list)
  for x in r:groups[x['family']].append(x)
  clinical=[x for x in r if x['clinical_required'] and x['offline_clinical_feasible']]
  feasible=[x for x in r if x['offline_complete_feasible']]
  result.append({'strategy':method,'prefix_families':len(groups),'branch_continuations':len(r),
   'completed_branches':sum(x['complete_within_limits'] for x in r),'completion_fraction':sum(x['complete_within_limits'] for x in r)/len(r),
   'macro_family_completion':sum(sum(z['complete_within_limits'] for z in v)/len(v) for v in groups.values())/len(groups),
   'offline_feasible_branches':len(feasible),'completed_offline_feasible':sum(x['complete_within_limits'] for x in feasible),
   'clinical_feasible_branches':len(clinical),'clinical_on_time_in_feasible':sum(x['clinical_on_time'] for x in clinical),
   'clinical_commit_event_mean':sum(x['clinical_commit_event'] for x in r if x['clinical_commit_event'] is not None)/max(1,sum(x['clinical_commit_event'] is not None for x in r)),
   'mean_proposal_wait_steps':sum(x['proposal_wait_steps'] for x in r)/len(r),'total_proposal_wait_steps':sum(x['proposal_wait_steps'] for x in r),
   'invalid_commits':sum(x['invalid_commits'] for x in r),'unjustified_waits':sum(x['unjustified_waits'] for x in r),
   'committed_actions':sum(x['committed_actions'] for x in r),'prepared_actions':sum(x['prepared_actions'] for x in r),
   'disclosure_units':sum(x['disclosure_units'] for x in r),'audit_chains_valid':all(x['audit_chain_valid'] for x in r)})
 return result

def evaluate():
 manifest,prior_count=verify_freeze();families=load(DATA/'prefix_families.json')['families'];audit=specification_audit(families)
 runid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');dest=OUT/runid;dest.mkdir(parents=True)
 save(dest/'environment.json',{'python':sys.version,'platform':platform.platform(),'executable':sys.executable,'training':False,'saved_models_loaded':False})
 save(dest/'freeze_used.json',manifest);save(dest/'split_audit.json',audit)
 checks=run_checks();save(dest/'development_checks.json',checks)
 traces={};refs={};rows=[];role=[]
 for f in families:
  print(f"{f['family_id']}: {len(f['branches'])} continuations x {len(STRATEGIES)} controllers",flush=True)
  for b in f['branches']:
   key=f['family_id']+'/'+b['branch_id'];ref=full_information(b);refs[key]=ref
   for strategy in STRATEGIES:
    x=Session(strategy);t=time.perf_counter_ns()
    for event in b['events']:x.advance(event)
    elapsed=(time.perf_counter_ns()-t)/1e6;trace=x.export();traces[key+'/'+strategy]=trace
    m=assess(b,trace);row={'family':f['family_id'],'branch':b['branch_id'],'title':f['title'],'split':f['split'],'strategy':strategy,**m,
       'offline_complete_feasible':ref['complete_within_declared_limits'],'offline_clinical_feasible':ref['clinical_within_limit'],
       'audit_chain_valid':verify_receipts(x.receipts),'single_run_ms':elapsed}
    rows.append(row)
    if row['complete_within_limits'] and not row['offline_complete_feasible']:raise AssertionError('ONLINE_EXCEEDS_REFERENCE_BOUND')
    for agent in ROLES:
     decisions=[d for e in x.events for d in e['decisions'] if d['owner']==agent];rr=[r for r in x.receipts if r['owner']==agent]
     role.append({'family':f['family_id'],'branch':b['branch_id'],'split':f['split'],'strategy':strategy,'role':agent,
        'proposal_event_opportunities':len(decisions),'distinct_proposals':len({d['proposal_id'] for d in decisions}),
        'WAIT':sum(d['decision']=='WAIT' for d in decisions),'PREPARE_decisions':sum(d['decision']=='PREPARE' for d in decisions),
        'BLOCK_or_ESCALATE':sum(d['decision'] in {'BLOCK','ESCALATE'} for d in decisions),
        'prepared':sum(r['permitted'] and r['stage']=='PREPARE' for r in rr),'committed':sum(r['permitted'] and r['stage']=='COMMIT' for r in rr),
        'invalid_commits':sum(r['id'] in {q['proposal_id'] for q in rr} for r in m['errors'])})
 # Same-history determinism across every continuation pair until its first differing event.
 causality=[]
 for f in families:
  for left,right in itertools.combinations(f['branches'],2):
   common=0
   for a,b in zip(left['events'],right['events']):
    if digest(a)!=digest(b):break
    common+=1
   for s in STRATEGIES:
    l=traces[f['family_id']+'/'+left['branch_id']+'/'+s];r=traces[f['family_id']+'/'+right['branch_id']+'/'+s]
    for t in range(common):
     matched=(l['snapshot']['events'][t]==r['snapshot']['events'][t] and l['policy_inputs'][t]==r['policy_inputs'][t])
     causality.append({'family':f['family_id'],'left':left['branch_id'],'right':right['branch_id'],'strategy':s,'event':t+1,'identical_input_and_decision':matched})
 # Temporal probes are separate, not new semantic samples. One intervention per probe.
 temporal=[]
 for f in families:
  if f['split']!='CONFIRMATION':continue
  for s in STRATEGIES:
   b=f['branches'][0]
   for kind in ['REVOKE','PURPOSE_CHANGE','POLICY_VERSION_CHANGE']:
    x=Session(s);p=x.begin(b['events'][0]);x.change_before_commit(kind);x.commit(p['plan_id'])
    temporal.append({'family':f['family_id'],'strategy':s,'change':kind,'no_side_effect':not x.done,'receipt_integrity':verify_receipts(x.receipts),
       'candidates_rejected':len(x.receipts),'note':'A zero-action plan is vacuous; see rejected candidate count.'})
 legacy=legacy_regression();summary=summarize(rows,refs)
 lookup={(r['family'],r['branch'],r['strategy']):r for r in rows}
 paired=[]
 for f in families:
  if f['split']!='CONFIRMATION':continue
  for b in f['branches']:
   e=lookup[(f['family_id'],b['branch_id'],'EAGER')];w=lookup[(f['family_id'],b['branch_id'],'MEDVERSE_COMMITMENT')];fair=lookup[(f['family_id'],b['branch_id'],'FAIR_BOUNDED_WAIT')]
   same_keys=['complete_within_limits','objective','first_effect_events','proposal_wait_steps','invalid_commits']
   paired.append({'family':f['family_id'],'branch':b['branch_id'],'eager_complete':e['complete_within_limits'],'medverse_complete':w['complete_within_limits'],
      'completion_gain':int(w['complete_within_limits'])-int(e['complete_within_limits']),
      'clinical_event_eager':e['clinical_commit_event'],'clinical_event_medverse':w['clinical_commit_event'],
      'capable_tie':all(fair[k]==w[k] for k in same_keys)})
 failures=[r for r in rows if r['split']=='CONFIRMATION' and not r['complete_within_limits']]
 valid=all(r['invalid_commits']==0 and r['unjustified_waits']==0 and r['audit_chain_valid'] for r in rows)
 integrity=valid and all(c['identical_input_and_decision'] for c in causality) and all(x['no_side_effect'] for x in temporal) and all(x['same_committed_prefix_and_effects'] for x in legacy)
 status={'gate':'GATE_32_BOUNDED_COMMITMENT_CONTROL','run_id':runid,'engineering_integrity':'PASS' if integrity else 'FAIL',
 'development_checks_passed':sum(c['passed'] for c in checks),'development_checks_total':len(checks),
 'confirmation_prefix_families':8,'confirmation_continuations':32,'development_prefix_families':4,'development_continuations':8,
 'controller_runs':len(rows),'progressive_events':sum(len(t['snapshot']['events']) for t in traces.values()),
 'same_history_checks':len(causality),'same_history_checks_passed':sum(c['identical_input_and_decision'] for c in causality),
 'precommit_probes':len(temporal),'precommit_no_side_effect':sum(r['no_side_effect'] for r in temporal),
 'precommit_nonvacuous_probes':sum(r['candidates_rejected']>0 for r in temporal),
 'prior_files_preserved':prior_count,'known_legacy_event_comparisons':len(legacy),'known_legacy_events_unchanged':sum(r['same_committed_prefix_and_effects'] for r in legacy),
 'summary':summary,'paired_completion_gains':sum(r['completion_gain']>0 for r in paired),'paired_completion_losses':sum(r['completion_gain']<0 for r in paired),
 'fair_bounded_wait_ties':sum(r['capable_tie'] for r in paired),'comparison_branches':len(paired),
 'c01_c02_status':'RETAINED_UNCHANGED; no timing hints were inserted into those old cases',
 'original_selector_changed':False,'original_authorization_validator_changed':False,'training_performed':False,
 'dense_model_loaded':False,'clinical_legal_review':'PENDING','timing_units':'modeled event steps, NOT a clinical deadline',
 'claim_boundary':'Finite internally authored online commitment study. Branches are correlated. Full-information reference is noncausal. All ties/losses retained; no clinical/legal deployment claim.',
 'next_dependency':'Independent contract review and separate integration into the final clinical interface/video. Do not present this study as a repair of old cases lacking visible wait reasons.'}
 save(dest/'status.json',status);save(dest/'raw_traces.json',traces);save(dest/'reference_outcomes.json',refs)
 save(dest/'retained_incomplete_cases.json',failures);write_csv(dest/'case_metrics.csv',rows);write_csv(dest/'strategy_summary.csv',summary)
 write_csv(dest/'paired_comparisons.csv',paired);write_csv(dest/'same_history_checks.csv',causality);write_csv(dest/'temporal_revalidation.csv',temporal)
 write_csv(dest/'agent_behavior.csv',role);write_csv(dest/'legacy_regression.csv',legacy)
 # Common source grounding remains real-source-derived candidates, NOT approved interpretations.
 verify_freeze()
 return status,dest
