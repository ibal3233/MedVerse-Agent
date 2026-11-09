"""HTTP and projection checks for the additive operator integration (known inputs)."""
from copy import deepcopy
from .session import Workspace
from .common import ROLES


def run_checks(client):
 rows=[]
 def check(name,condition,detail=''):
  rows.append({'check':name,'passed':bool(condition),'detail':detail})
 def request(op,b,token=None):return client('/api33/'+op,b,token)
 status,cfg=client('/api33/config');check('catalog_available',status==200 and len(cfg['families'])==12)
 check('catalog_does_not_publish_scripts',not any('events' in f or 'actions' in f for f in cfg['families']))
 status,h=client('/api33/health');check('clinical_timing_not_enabled_globally',status==200 and h['timing_enabled_in_original_clinical_path'] is False)
 status,r=request('session',{'family_id':'P01','branch_id':'PROMPT','strategy':'MEDVERSE_COMMITMENT'});sid=r['session_id'];tok=r['token'];snap=r['snapshot']
 check('empty_prefix_no_proposals',not snap['proposal_rows'] and snap['clock']==0)
 check('review_pending_banner',snap['clinical_legal_review']=='PENDING')
 status,_=request('snapshot',{'session_id':sid},'wrong');check('wrong_session_token_rejected',status==403)
 status,_=request('advance',{'session_id':sid,'expected_clock':0,'event':{'fake':1}},tok);check('client_event_injection_rejected',status==400)
 status,_=request('advance',{'session_id':sid,'expected_clock':0,'auto_commit':'true'},tok);check('non_boolean_auto_commit_rejected',status==400)
 status,r=request('advance',{'session_id':sid,'expected_clock':0},tok);snap=r['snapshot']
 check('release_exactly_one_event',status==200 and snap['clock']==1)
 check('future_alternative_not_released','A05' not in [a['id'] for a in snap['proposal_rows']])
 check('wait_has_visible_contract',any(d['decision']=='WAIT' and d['pending_review_ref'] and d['wait_expiry'] for d in snap['decisions']))
 check('prepare_not_clinical_completion',any(r['permitted'] and r['stage']=='PREPARE' for r in snap['receipts']) and 'clinical_review_done' not in snap['achieved_tokens'])
 row=next(x for x in snap['proposal_rows'] if x['id']=='A04')
 check('commit_proposal_not_mislabelled_executed',row['decision']['decision']=='COMMIT' and row['actual_effect'] is None)
 before=snap['engine_state_hash'];status,_=request('advance',{'session_id':sid,'expected_clock':0},tok)
 _,r=request('snapshot',{'session_id':sid},tok);check('duplicate_click_does_not_release_future',status==400 and r['snapshot']['engine_state_hash']==before)
 for role in ROLES:
  status,r=request('role',{'session_id':sid,'role':role},tok)
  check('role_projection_'+role,status==200 and all(a['owner']==role for a in r['observed_contracts']) and all(d['owner']==role for d in r['decisions']) and all(q['owner']==role for q in r['receipts']))
 status,r=request('export',{'session_id':sid},tok)
 check('trace_contains_only_released_inputs',status==200 and len(r['runtime_trace']['policy_inputs'])==1 and r['future_events_included'] is False)
 check('trace_no_session_token',tok not in str(r))
 a=Workspace('P01','PROMPT');b=Workspace('P01','NEVER');a.advance(0);b.advance(0)
 check('same_history_same_engine_state',a.snapshot()['engine_state_hash']==b.snapshot()['engine_state_hash'])
 status,r=request('advance',{'session_id':sid,'expected_clock':1},tok);snap=r['snapshot']
 check('prompt_alternative_commits_after_release','clinical_review_done' in snap['achieved_tokens'] and 'stream_isolated' in snap['achieved_tokens'])
 check('receipts_preserve_ownership',all(r['owner']==r['actual_proposal']['owner'] for r in snap['receipts']))
 check('receipt_chain_valid',snap['receipt_chain_valid'])
 # Pause creates a real pending plan; an authority change is checked before effects.
 _,r=request('session',{'family_id':'P01','branch_id':'PROMPT'});sid2=r['session_id'];tok2=r['token']
 _,r=request('advance',{'session_id':sid2,'expected_clock':0,'auto_commit':False},tok2);p=r['snapshot']['pending_plan_id']
 check('pause_has_no_effect',p is not None and not r['snapshot']['receipts'] and not r['snapshot']['committed_ids'])
 code,_=request('advance',{'session_id':sid2,'expected_clock':1},tok2);check('pending_plan_blocks_next_release',code==400)
 code,_=request('commit',{'session_id':sid2,'plan_id':'wrong'},tok2);check('unknown_plan_rejected',code==400)
 _,r=request('change',{'session_id':sid2,'kind':'REVOKE'},tok2)
 _,r=request('commit',{'session_id':sid2,'plan_id':p},tok2);ss=r['snapshot']
 check('revocation_blocks_effect',not ss['committed_ids'] and len(ss['receipts'])>0 and all(not r['permitted'] for r in ss['receipts']))
 code,_=request('commit',{'session_id':sid2,'plan_id':p},tok2);check('replayed_plan_rejected',code==400)
 _,r=request('session',{'family_id':'P01','branch_id':'PROMPT'});sid3=r['session_id'];tok3=r['token']
 _,r=request('advance',{'session_id':sid3,'expected_clock':0},tok3);old=r['snapshot']['committed_ids']
 _,r=request('advance',{'session_id':sid3,'expected_clock':1,'auto_commit':False},tok3)
 _,r=request('cancel',{'session_id':sid3},tok3)
 check('cancel_does_not_undo_effects',r['snapshot']['committed_ids']==old and r['snapshot']['pending_plan_id'] is None)
 code,r=client('/api31/search',{'query':'KR-NONEXISTENT-ARTICLE-999','role':'privacy_agent','backend':'bm25','top_k':3,'jurisdiction':'KR'})
 check('unknown_exact_id_no_substitution',code==200 and r['status']=='UNKNOWN_EXACT_CITATION' and not r['hits'])
 code,r=client('/api31/search',{'query':'가명정보 연구','role':'privacy_agent','backend':'bm25','top_k':3,'jurisdiction':'KR'})
 check('korean_query_explicit_bm25',code==200 and r['backend']=='lexical_bilingual_bm25_v1' and r['fallback_used'] is False)
 check('retrieval_is_not_authorization',r['execution_authorized'] is False)
 code,r=client('/api31/search',{'query':'research','role':'privacy_agent','backend':'bm25','top_k':3,'jurisdiction':'OTHER'})
 check('wrong_jurisdiction_has_no_evidence',code==200 and not r['hits'])
 code,_=client('/api31/search',{'query':'research','role':'privacy_agent','backend':'bm25','top_k':4,'jurisdiction':'KR'})
 check('top_k_out_of_range_rejected',code==400)
 code,r=request('session',{'family_id':'P07','branch_id':'APPROVAL'});sid4=r['session_id'];tok4=r['token']
 _,r=request('advance',{'session_id':sid4,'expected_clock':0},tok4)
 check('regulator_owned_contract_visible',r['snapshot']['roles']['regulator_agent']['counts']['released_proposals']>0)
 check('no_invented_vital_signs',not any(k in str(r['snapshot']) for k in ['spo2','heart_rate_bpm','body_temperature']))
 code,_=request('session',{'family_id':'FAKE'});check('unknown_scenario_rejected',code==400)
 code,_=request('session',{'strategy':'FAKE'});check('unknown_controller_rejected',code==400)
 code,_=request('role',{'session_id':sid,'role':'FAKE'},tok);check('unknown_role_rejected',code==400)
 return rows
