"""Same HTTP service as the UI; reference checks run offline, never in the service."""
from __future__ import annotations
import csv,json,random,threading,time,platform,sys
from datetime import datetime,timezone
from pathlib import Path
from .common import ROOT,DATA,OUT,STRATEGIES,source_cases,load,save,digest,filehash
from .server import make_server
from .client import Client
from .tests import run_tests
from .engine import verify_receipts
from .freeze import verify
from coordination29.reference_evaluator import reference_outcomes,assess_execution
from coordination29.common import outcome
from coordination29.evaluate import runtime_input

def csvsave(path,rows):
 if not rows:return
 with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
  for r in rows:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def percentiles(values):
 v=sorted(values)
 def q(p):
  if not v:return None
  a=(len(v)-1)*p;i=int(a);return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(a-i)
 return {'n':len(v),'p50_ms':q(.5),'p95_ms':q(.95),'p99_ms':q(.99),'min_ms':min(v) if v else None,'max_ms':max(v) if v else None}
def run():
 verify();run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');dest=OUT/run_id;dest.mkdir(parents=True)
 prior=load(DATA/'upstream_manifest.json');changed=[p for p,h in prior.items() if not(ROOT/p).is_file() or filehash(ROOT/p)!=h]
 preservation={'files_checked':len(prior),'unchanged':len(prior)-len(changed),'changed':changed};save(dest/'upstream_preservation.json',preservation)
 server=make_server();thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_address[1]);client=Client(url)
 snapshot_rows=[];progressive_rows=[];perfamily=[];traces={};probes=[];latency=[]
 try:
  checks=run_tests(url);save(dest/'engineering_checks.json',checks)
  if not all(r['passed'] for r in checks) or changed:
   save(dest/'status.json',{'gate':'GATE_30','run_id':run_id,'engineering_integrity':'FAIL','failed_checks':[r for r in checks if not r['passed']],'upstream_changed':changed})
   raise RuntimeError('Pre-evaluation engineering failure; evidence retained.')
  families=source_cases()
  for source in families:
   fid=source['family_id'];ref=reference_outcomes(runtime_input(source))
   print('HTTP replay:',fid,source['track'],source['split'],flush=True)
   for strategy in STRATEGIES:
    client.start(fid,strategy,'SNAPSHOT');s=client.post('/api30/advance');e=client.post('/api30/export')
    errors=assess_execution(e['released_runtime'],s['committed_ids']);obj=list(outcome(e['released_runtime'],s['committed_ids']))
    row={'family_id':fid,'track':source['track'],'prior_split':source['split'],'strategy':strategy,'reference_feasible':ref['feasible_now'],'complete':sum(obj[:2])==0,'objective_matches':obj==ref['best_objective'],'disposition_correct':s['selection']['disposition']==ref['disposition'],'objective':obj,'reference_objective':ref['best_objective'],'disposition':s['selection']['disposition'],'reference_disposition':ref['disposition'],'invalid_commits':len(errors),'audit_valid':verify_receipts(s['receipts']),'original_snapshot_input_matches':digest(e['released_runtime'])==digest(runtime_input(source)),'committed_actions':len(s['committed_ids'])}
    snapshot_rows.append(row);traces[fid+'_'+strategy+'_SNAPSHOT']=e
    client.start(fid,strategy,'PROGRESSIVE');steps=[];old_done=[]
    for phase in range(1,7):
     t=time.perf_counter_ns();s=client.post('/api30/advance');duration=(time.perf_counter_ns()-t)/1e6
     e=client.post('/api30/export');residual=e['last_selection_input'];r=reference_outcomes(residual)
     new=[x for x in s['committed_ids'] if x not in old_done];obj=list(outcome(residual,new));errors=assess_execution(residual,new)
     expected='AWAITING_RELEASED_INFORMATION' if not residual['goals'] and not residual['actions'] else r['disposition']
     ids=s['committed_ids'];duplicate=len(ids)!=len(set(ids));owner_errors=sum(a['owner']!=role for role,view in s['roles'].items() for a in view['own_proposals'])
     clinical_exposure=sum('modeled_symptom' in json.dumps(v,ensure_ascii=False) for role,v in s['roles'].items() if role!='hospital_agent')
     rr={'family_id':fid,'track':source['track'],'prior_split':source['split'],'strategy':strategy,'event':phase,'new_commits':len(new),'new_commit_ids':new,'objective_matches':obj==r['best_objective'],'disposition_correct':s['selection']['disposition']==expected,'expected_disposition':expected,'disposition':s['selection']['disposition'],'invalid_commits':len(errors),'duplicate_effect':duplicate,'role_projection_errors':owner_errors+clinical_exposure,'audit_valid':verify_receipts(s['receipts']),'complete_current_goals':bool(s['known_goals']) and not s['missing_goals'],'known_goals':s['known_goals'],'achieved_tokens':s['achieved_tokens'],'missing_goals':s['missing_goals'],'http_latency_ms':duration}
     progressive_rows.append(rr);steps.append({'response':s,'export':e,'reference':{'best_objective':r['best_objective'],'expected_disposition':expected,'assessment_errors':errors}});old_done=list(ids)
    perfamily.append({'family_id':fid,'track':source['track'],'prior_split':source['split'],'strategy':strategy,'final_complete':not s['missing_goals'],'final_missing_goals':s['missing_goals'],'clinical_completed':'clinical_review_done' in s['achieved_tokens'],'committed_actions':len(s['committed_ids'])})
    traces[fid+'_'+strategy+'_PROGRESSIVE']=steps
  # All probes occur on separately reset sessions, never on the measured main trajectory.
  for source in families:
   if source['split']!='CONFIRMATION':continue
   for mutation in ('REVOKE','PURPOSE_CHANGE','POLICY_VERSION_CHANGE'):
    client.start(source['family_id'],'MEDVERSE_HARMONIZER','SNAPSHOT');s=client.post('/api30/advance',auto_commit=False);plan=s['pending_plan']
    client.post('/api30/change',kind=mutation);s=client.post('/api30/commit',plan_id=plan['plan_id'])
    probes.append({'family_id':source['family_id'],'mutation':mutation,'planned_actions':len(plan['sequence']),'rejected_actions':sum(not r['permitted'] for r in s['receipts']),'no_side_effect':not s['committed_ids'],'all_planned_actions_rejected':bool(plan['sequence']) and all(not r['permitted'] for r in s['receipts']),'audit_valid':verify_receipts(s['receipts'])})
  rng=random.Random(3001)
  for strategy in STRATEGIES:
   client.start('C12',strategy)
   for _ in range(6):client.post('/api30/advance')
  for repetition in range(10):
   order=list(STRATEGIES);rng.shuffle(order)
   for strategy in order:
    client.start('C12',strategy)
    for phase in range(1,7):
     t=time.perf_counter_ns();s=client.post('/api30/advance');dt=(time.perf_counter_ns()-t)/1e6
     latency.append({'strategy':strategy,'repetition':repetition+1,'event':phase,'http_latency_ms':dt})
  summary=[]
  for strategy in STRATEGIES:
   sr=[r for r in snapshot_rows if r['strategy']==strategy and r['prior_split']=='CONFIRMATION'];pr=[r for r in progressive_rows if r['strategy']==strategy and r['prior_split']=='CONFIRMATION'];fr=[r for r in perfamily if r['strategy']==strategy and r['prior_split']=='CONFIRMATION']
   feasible=[r for r in sr if r['reference_feasible']]
   summary.append({'strategy':strategy,'snapshot_families':len(sr),'snapshot_objective_matches':sum(r['objective_matches'] for r in sr),'snapshot_disposition_matches':sum(r['disposition_correct'] for r in sr),'snapshot_feasible_families':len(feasible),'snapshot_feasible_completed':sum(r['complete'] for r in feasible),'progressive_steps':len(pr),'progressive_reference_matches':sum(r['objective_matches'] and r['disposition_correct'] for r in pr),'progressive_complete_final_families':sum(r['final_complete'] for r in fr),'progressive_families':len(fr),'invalid_commits':sum(r['invalid_commits'] for r in sr+pr),'audit_chains_valid':all(r['audit_valid'] for r in sr+pr),'role_projection_errors':sum(r['role_projection_errors'] for r in pr),'timing':percentiles([r['http_latency_ms'] for r in latency if r['strategy']==strategy])})
  capable=[r for r in snapshot_rows if r['strategy']!='REQUEST_ONLY']
  safety=all(r['invalid_commits']==0 and r['audit_valid'] for r in snapshot_rows+progressive_rows) and all(not r['duplicate_effect'] and r['role_projection_errors']==0 for r in progressive_rows)
  parity=all(r['original_snapshot_input_matches'] for r in snapshot_rows) and all(r['objective_matches'] and r['disposition_correct'] for r in capable)
  # Scope-control misses do not invalidate the experiment. Capable progressive
  # disagreement is recorded separately and does not trigger outcome-driven repairs.
  progressive_matches=all(r['objective_matches'] and r['disposition_correct'] for r in progressive_rows if r['strategy']!='REQUEST_ONLY')
  status={'gate':'GATE_30_INTEGRATED_RELEASE','run_id':run_id,'engineering_integrity':'PASS' if safety and parity and all(p['all_planned_actions_rejected'] for p in probes) else 'FAIL','checks_passed':sum(r['passed'] for r in checks),'checks_total':len(checks),'snapshot_runs':len(snapshot_rows),'progressive_sessions':len(perfamily),'progressive_event_responses':len(progressive_rows),'source_families':len(families),'previous_confirmation_families':14,'evaluation_scope':'Known Gate 29 families replayed through the live HTTP runtime; integration regression, not new confirmation.','summary':summary,'snapshot_capable_reference_agreement':parity,'progressive_capable_reference_agreement':progressive_matches,'observed_invalid_commits':sum(r['invalid_commits'] for r in snapshot_rows+progressive_rows),'temporal_probes':len(probes),'temporal_rejections':sum(p['all_planned_actions_rejected'] for p in probes),'loopback_timing_samples':len(latency),'timing_protocol':'10 repetitions/configuration; six C12 event calls; one excluded warmup replay/configuration; seed 3001; includes loopback HTTP and JSON, no LLM/network/human services.','browser_status':'NOT_YET_RUN','source_and_clinical_review':'PENDING','dense_backend':'NOT_USED_LEXICAL_BM25','trained_proposals':'NOT_USED_FROZEN_INSTITUTION_OWNED_CONTRACTS','all_original_files_preserved':not changed,'original_file_count':len(prior),'unique_superiority_established':False,'presentation_files':[],'protocol_sha256':filehash(ROOT/'docs/coordination30/PROTOCOL.md'),'freeze_manifest_sha256':filehash(DATA/'freeze_manifest.json')}
  for name,rows in [('snapshot_metrics',snapshot_rows),('progressive_metrics',progressive_rows),('family_final_outcomes',perfamily),('temporal_probes',probes),('latency_samples',latency)]:save(dest/(name+'.json'),rows);csvsave(dest/(name+'.csv'),rows)
  save(dest/'http_traces.json',traces);save(dest/'status.json',status)
  save(dest/'environment.json',{'python':sys.version,'platform':platform.platform(),'measurement_endpoint':'loopback HTTP','trained_models_loaded':False,'external_services':False})
  print(json.dumps(status,indent=2));print('Raw results:',dest,flush=True)
  return status,dest
 finally:server.shutdown();server.server_close();thread.join(timeout=5)
