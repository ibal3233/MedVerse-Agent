"""Run known-case integration through actual loopback HTTP. No method tuning."""
from __future__ import annotations
import json,sys,platform,threading,time,itertools
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from datetime import datetime,timezone
from copy import deepcopy
from collections import defaultdict
from .common import ROOT,OUT,ROLES,families,save,read,verify_freeze
from .server import make_server
from .tests import run_checks
from commitment32.runtime import Session,verify_receipts
from commitment32.common import digest,STRATEGIES
from commitment32.reference import assess,full_information
from commitment32.evaluate import write_csv,summarize


def client_for(server):
 base=f'http://127.0.0.1:{server.server_port}'
 def client(path,body=None,token=None,extra=None):
  headers={'Content-Type':'application/json'}
  if token:headers['X-Session-Token']=token
  if extra:headers.update(extra)
  req=Request(base+path,data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None,headers=headers)
  try:
   with urlopen(req,timeout=60) as r:raw=r.read();code=r.status;ct=r.headers.get('Content-Type','')
  except HTTPError as e:raw=e.read();code=e.code;ct=e.headers.get('Content-Type','')
  return code,json.loads(raw) if 'application/json' in ct else raw.decode('utf-8')
 return client


def evaluate():
 manifest,prior_count=verify_freeze();runid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');dest=OUT/runid;dest.mkdir(parents=True)
 save(dest/'freeze_used.json',manifest);save(dest/'environment.json',{'python':sys.version,'platform':platform.platform(),'transport':'actual urllib -> loopback ThreadingHTTPServer','training':False,'embedding_loaded_in_main_evaluation':False})
 server=make_server(0,'bm25');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();client=client_for(server)
 comparisons=[];raw={};rows=[];agent_rows=[];refs={};tracematches=[];checked=[];causality=[];temporal=[];historical=[]
 try:
  checked=run_checks(client)
  # HTTP envelope validation checks, independent of any policy decision.
  code,_=client('/api33/session',{},extra={'Origin':'https://not-this-workspace.invalid'});checked.append({'check':'cross_origin_request_rejected','passed':code==403})
  code,_=client('/api33/session',{},extra={'Content-Type':'text/plain'});checked.append({'check':'non_json_request_rejected','passed':code==415})
  for path,needle in [('/','When to commit'),('/foundation','Original Digital Twin'),('/release33.js','api33'),('/release33.css','commit')]:
   code,text=client(path);checked.append({'check':'serves_'+path,'passed':code==200 and needle in text})
  for f in families():
   print(f"{f['family_id']}: {len(f['branches'])} continuations x 3 controllers through HTTP",flush=True)
   for b in f['branches']:
    key=f['family_id']+'/'+b['branch_id'];ref=full_information(b);refs[key]=ref
    for strategy in STRATEGIES:
     direct=Session(strategy);code,r=client('/api33/session',{'family_id':f['family_id'],'branch_id':b['branch_id'],'strategy':strategy});assert code==200
     sid,token=r['session_id'],r['token']
     for event in b['events']:
      direct.advance(event);t=time.perf_counter_ns();code,r=client('/api33/advance',{'session_id':sid,'expected_clock':event['clock']-1},token);ms=(time.perf_counter_ns()-t)/1e6;assert code==200,r
      snap=r['snapshot'];matched=snap['engine_state_hash']==digest(direct.snapshot())
      comparisons.append({'family':f['family_id'],'continuation':b['branch_id'],'split':f['split'],'strategy':strategy,'event':event['clock'],'identical_state':matched,'receipt_chain_valid':snap['receipt_chain_valid'],'http_ms':ms})
     code,export=client('/api33/export',{'session_id':sid},token);assert code==200
     trace=export['runtime_trace'];raw[key+'/'+strategy]=export
     tracematches.append({'family':f['family_id'],'continuation':b['branch_id'],'strategy':strategy,'identical_trace':digest(trace)==digest(direct.export())})
     metrics=assess(b,trace);row={'family':f['family_id'],'branch':b['branch_id'],'title':f['title'],'split':f['split'],'strategy':strategy,**metrics,
      'offline_complete_feasible':ref['complete_within_declared_limits'],'offline_clinical_feasible':ref['clinical_within_limit'],'audit_chain_valid':verify_receipts(trace['snapshot']['receipts'])};rows.append(row)
     for role in ROLES:
      ds=[d for e in trace['snapshot']['events'] for d in e['decisions'] if d['owner']==role];rr=[r for r in trace['snapshot']['receipts'] if r['owner']==role]
      agent_rows.append({'family':f['family_id'],'branch':b['branch_id'],'split':f['split'],'strategy':strategy,'role':role,
       'distinct_proposal_contracts':len({d['proposal_id'] for d in ds}),'proposal_event_opportunities':len(ds),
       'WAIT':sum(d['decision']=='WAIT' for d in ds),'PREPARE_decisions':sum(d['decision']=='PREPARE' for d in ds),
       'COMMIT_decisions':sum(d['decision']=='COMMIT' for d in ds),'BLOCK_or_ESCALATE':sum(d['decision'] in ('BLOCK','ESCALATE') for d in ds),
       'prepared':sum(r['permitted'] and r['stage']=='PREPARE' for r in rr),'committed':sum(r['permitted'] and r['stage']=='COMMIT' for r in rr)})
  # Same-information prefix check excludes operator labels; compares only real policy inputs/engine effects.
  for f in families():
   for left,right in itertools.combinations(f['branches'],2):
    count=0
    for a,b in zip(left['events'],right['events']):
     if digest(a)!=digest(b):break
     count+=1
    for strategy in STRATEGIES:
     a=raw[f['family_id']+'/'+left['branch_id']+'/'+strategy]['runtime_trace'];b=raw[f['family_id']+'/'+right['branch_id']+'/'+strategy]['runtime_trace']
     for i in range(count):causality.append({'family':f['family_id'],'left':left['branch_id'],'right':right['branch_id'],'strategy':strategy,'event':i+1,'same_visible_inputs_and_decisions':a['policy_inputs'][i]==b['policy_inputs'][i] and a['snapshot']['events'][i]==b['snapshot']['events'][i]})
  # Pause/change/commit is exercised through the same HTTP routes used by the interface.
  for f in families():
   if f['split']!='CONFIRMATION':continue
   for strategy in STRATEGIES:
    for kind in ['REVOKE','PURPOSE_CHANGE','POLICY_VERSION_CHANGE']:
     _,r=client('/api33/session',{'family_id':f['family_id'],'branch_id':f['branches'][0]['branch_id'],'strategy':strategy});sid,token=r['session_id'],r['token']
     code,r=client('/api33/advance',{'session_id':sid,'expected_clock':0,'auto_commit':False},token);assert code==200;pid=r['snapshot']['pending_plan_id']
     code,_=client('/api33/change',{'session_id':sid,'kind':kind},token);assert code==200
     code,r=client('/api33/commit',{'session_id':sid,'plan_id':pid},token);assert code==200;s=r['snapshot']
     temporal.append({'family':f['family_id'],'strategy':strategy,'change':kind,'no_side_effect':not s['committed_ids'],'rejected_receipts':len(s['receipts']),'audit_valid':s['receipt_chain_valid']})
  # Preserve original clinical/DT surface; no waiting profile is introduced into these sessions.
  from foundation31.session import FoundationSession
  from coordination30.common import source_cases
  # Use original configuration list rather than importing any new policy.
  _,config=client('/api30/config');original_methods=list(config['strategies'])
  for case in source_cases():
   for method in original_methods:
    direct=FoundationSession(case['family_id'],method,'PROGRESSIVE');code,r=client('/api30/session',{'family_id':case['family_id'],'strategy':method,'mode':'PROGRESSIVE'});assert code==200
    sid,token=r['session_id'],r['token']
    for event in range(1,7):
     d=direct.advance();code,r=client('/api30/advance',{'session_id':sid},token);assert code==200
     s=r['snapshot'];historical.append({'family':case['family_id'],'strategy':method,'event':event,'same_commit_ids_and_effects':s['committed_ids']==d['committed_ids'] and s['achieved_tokens']==d['achieved_tokens']})
  # Explicit backend state; exact IDs do not need model weights.
  code,dense_probe=client('/api31/search',{'query':'pseudonymized scientific research','role':'privacy_agent','backend':'dense','jurisdiction':'KR','top_k':3})
  save(dest/'dense_endpoint_probe.json',dense_probe)
 finally:
  server.shutdown();server.server_close();thread.join(timeout=5)
 summary=summarize(rows,refs);roles=[]
 for role in ROLES:
  rs=[r for r in agent_rows if r['role']==role and r['split']=='CONFIRMATION' and r['strategy']=='MEDVERSE_COMMITMENT']
  values={k:sum(x[k] for x in rs) for k in ['distinct_proposal_contracts','proposal_event_opportunities','WAIT','PREPARE_decisions','COMMIT_decisions','BLOCK_or_ESCALATE','prepared','committed']}
  roles.append({'role':role,'continuations_with_owned_proposal':sum(x['distinct_proposal_contracts']>0 for x in rs),**values})
 archived=read(ROOT/'outputs/gate32_commitment/20261104T013623_796085Z/status.json')['summary']
 summary_equal=summary==archived
 valid=all(c['passed'] for c in checked) and all(x['identical_state'] and x['receipt_chain_valid'] for x in comparisons) and all(x['identical_trace'] for x in tracematches) and all(x['same_visible_inputs_and_decisions'] for x in causality) and all(x['no_side_effect'] and x['audit_valid'] for x in temporal) and all(x['same_commit_ids_and_effects'] for x in historical) and all(r['invalid_commits']==0 for r in rows) and summary_equal
 status={'gate':'GATE_33_COMMITMENT_WORKSPACE_INTEGRATION','run_id':runid,'engineering_integrity':'PASS' if valid else 'FAIL',
 'checks_passed':sum(x['passed'] for x in checked),'checks_total':len(checked),
 'controller_runs':len(rows),'event_comparisons':len(comparisons),'identical_events':sum(x['identical_state'] for x in comparisons),
 'trace_comparisons':len(tracematches),'identical_traces':sum(x['identical_trace'] for x in tracematches),
 'same_history_checks':len(causality),'same_history_passed':sum(x['same_visible_inputs_and_decisions'] for x in causality),
 'change_before_commit_probes':len(temporal),'change_no_side_effect':sum(x['no_side_effect'] for x in temporal),
 'nonvacuous_change_probes':sum(x['rejected_receipts']>0 for x in temporal),
 'original_clinical_event_checks':len(historical),'original_clinical_events_unchanged':sum(x['same_commit_ids_and_effects'] for x in historical),
 'known_gate32_summary_unchanged':summary_equal,'strategy_summary':summary,'role_summary':roles,
 'original_files_unchanged':prior_count,'dense_probe_status':dense_probe.get('status'),'dense_performance_remeasured':False,
 'clinical_legal_review':'PENDING','proposal_backend':'Frozen institution-owned modeled contracts; no trained/LLM proposal inference',
 'scope':'Actual loopback HTTP replay of known cases. No new confirmation, clinical validity or timing-policy repair.',
 'timing_not_enabled_globally':True,'same_host_separate_scenarios':True,
 'browser_status':'NOT_RUN_IN_MAIN_EVALUATION','windows_spyder_status':'NOT_TESTED_HERE',
 'next_dependency':'Local native replay and qualified review of active timing and policy interpretations; finalize submission and record the selected release.'}
 save(dest/'status.json',status);save(dest/'http_exports.json',raw);save(dest/'checks.json',checked);save(dest/'case_metrics.json',rows)
 save(dest/'reference_outcomes.json',refs)
 for name,rs in [('event_comparisons',comparisons),('trace_comparisons',tracematches),('case_metrics',rows),('strategy_summary',summary),('agent_behavior',agent_rows),('role_summary',roles),('same_history_checks',causality),('temporal_revalidation',temporal),('original_clinical_regression',historical)]:write_csv(dest/(name+'.csv'),rs)
 verify_freeze();return status,dest
