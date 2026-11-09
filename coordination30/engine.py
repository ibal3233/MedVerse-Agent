"""Progressive and snapshot runtime backed by unmodified Gate 29 selectors/validator.

All authority records and effects are modeled. Reference evaluation is not imported
here. The runtime cannot see future event releases or evaluation answers.
"""
from __future__ import annotations
from copy import deepcopy
import secrets,time
from coordination29.selectors import select
from coordination29.validator import validate,eligibility,envelope_check
from coordination29.common import tokens
def runtime_input(c):
 hidden={"family_id","track","split","motif","provenance","interpretation_review","operator_private_views","event_history"}
 return {k:v for k,v in c.items() if k not in hidden}
from .common import digest,source_cases,ROLES
from .schedule import released_input,role_view,TITLE,EXPLANATION

class IntegrationError(ValueError):pass

class IntegratedSession:
 def __init__(self,family='C12',strategy='MEDVERSE_HARMONIZER',mode='PROGRESSIVE'):
  if strategy not in ('REQUEST_ONLY','FAIR_STATEFUL_SELECTOR','INDEPENDENT_CONSTRAINT_PLANNER','MEDVERSE_HARMONIZER'):raise IntegrationError('UNKNOWN_STRATEGY')
  if mode not in ('PROGRESSIVE','SNAPSHOT'):raise IntegrationError('UNKNOWN_MODE')
  cs={c['family_id']:c for c in source_cases()}
  if family not in cs:raise IntegrationError('UNKNOWN_FAMILY')
  self.source=deepcopy(cs[family]);self.family=family;self.strategy=strategy;self.mode=mode
  self.phase=0;self.current=released_input(self.source,0);self.done=[];self.receipts=[];self.events=[];self.plans=[];self.summaries=[];self.pending=None;self.changes=[]
  self.revision=0;self.last_selection={'sequence':[],'disposition':'AWAITING_RELEASED_INFORMATION','objective':[0,0,0,0]}
  self.last_constraints=[];self.latest_plan_input=None
 def _mutations(self,c):
  for kind in self.changes:
   if kind=='REVOKE':c['epoch']+=1
   elif kind=='POLICY_VERSION_CHANGE':c['policy_snapshot']='CHANGED_UNREVIEWED_SNAPSHOT'
   elif kind=='PURPOSE_CHANGE':c['task_purposes']=['changed_purpose_without_new_proposal']
  return c
 def residual(self):
  """Translate a committed prefix into a residual task without changing a frozen selector.

  Permanent joint conflicts against the committed prefix are removed; missing
  dependencies can still be fulfilled by other released proposals. The objective is
  incremental (newly selected field/recipient pairs), not globally optimal foresight.
  """
  c=deepcopy(self.current);c['initial_tokens']=sorted(tokens(c,self.done));lookup={a['id']:a for a in c['actions']}
  previous=[lookup[x] for x in self.done if x in lookup]
  keep=[]
  for a in c['actions']:
   if a['id'] in self.done:continue
   _,reason=validate(c,a,self.done)
   if reason in {'JOINT_ACTION_CONFLICT','JOINT_DISCLOSURE_CONFLICT','EXCLUSIVE_ALTERNATIVE','CONFLICTING_STATE'}:continue
   keep.append(a)
  c['actions']=keep
  for r in c['field_constraints']:
   earlier={f for a in previous if a['recipient']==r['recipient'] for f in a['fields']}
   r['forbidden_combination']=sorted(set(r['forbidden_combination'])-earlier)
  return c
 def _plan(self):
  residual=self.residual();self.latest_plan_input=deepcopy(residual)
  p=select(residual,self.strategy) if residual['actions'] or residual['goals'] else {'sequence':[],'objective':[0,0,0,0],'disposition':'AWAITING_RELEASED_INFORMATION','selection_validator_calls':0,'search_states':0}
  plan_id=secrets.token_hex(10)
  self.pending={'plan_id':plan_id,'revision':self.revision,'sequence':list(p['sequence']),'selection':deepcopy(p),'runtime_input_sha256':digest(residual),'created_phase':self.phase}
  self.last_selection=deepcopy(p)
  local=[]
  for a in self.current['actions']:
   if a['id'] in self.done:continue
   ok,reason=validate(self.current,a,self.done)
   local.append({'proposal_id':a['id'],'owner':a['owner'],'kind':a['kind'],'permitted_now':ok,'reason':reason,'priority':a['priority']})
  self.last_constraints=local
  self.plans.append(deepcopy(self.pending));return plan_id
 def _append_receipt(self,a,ok,reason,plan_id):
  refs=a['evidence']
  # These are candidate source-record hashes, not a legal-review certification.
  from .evidence import source_hashes
  row={'sequence':len(self.receipts)+1,'event':self.phase,'event_revision':self.revision,'plan_id':plan_id,'proposal_id':a['id'],'owner':a['owner'],'actual_proposal':deepcopy(a),'permitted':ok,'reason':reason,
       'authority_epoch_at_commit':self.current['epoch'],'policy_snapshot_at_commit':self.current['policy_snapshot'],'evidence_ids':refs,'source_record_hashes':{k:source_hashes().get(k) for k in refs},
       'modeled_side_effect':{'tokens':a['provides'],'recipient':a['recipient'],'fields':a['fields']} if ok else None,'previous_hash':self.receipts[-1]['hash'] if self.receipts else '0'*64,'simulation_only':True}
  row['hash']=digest(row);self.receipts.append(row)
 def commit(self,plan_id):
  if not self.pending or self.pending['plan_id']!=plan_id:raise IntegrationError('UNKNOWN_OR_ALREADY_COMMITTED_PLAN')
  p=self.pending;actions={a['id']:a for a in self.current['actions']}
  for aid in p['sequence']:
   a=actions.get(aid)
   if a is None:raise IntegrationError('UNKNOWN_PROPOSAL_IN_PLAN')
   ok,reason=validate(self.current,a,self.done)
   # The validator sees changed authority first; it cannot be bypassed with an old plan.
   if ok and p['revision']!=self.revision:ok,reason=False,'STALE_PLAN_REVISION'
   self._append_receipt(a,ok,reason,plan_id)
   if ok:self.done.append(aid)
  self.pending=None;return self.snapshot()
 def advance(self,auto_commit=True):
  if self.pending:raise IntegrationError('COMMIT_OR_CANCEL_PENDING_PLAN_FIRST')
  if self.phase>= (6 if self.mode=='PROGRESSIVE' else 1):raise IntegrationError('SCENARIO_COMPLETE')
  t0=time.perf_counter_ns();self.phase+=1;self.revision+=1
  self.current=self._mutations(released_input(self.source,self.phase) if self.mode=='PROGRESSIVE' else runtime_input(deepcopy(self.source)))
  title=TITLE[self.phase] if self.mode=='PROGRESSIVE' else 'Frozen Gate 29 snapshot through integrated runtime'
  self.events.append({'event':self.phase,'title':title,'detail':EXPLANATION.get(self.phase,'') if self.mode=='PROGRESSIVE' else 'Known snapshot; HTTP regression, not fresh confirmation.'})
  plan=self._plan()
  if auto_commit:self.commit(plan)
  s=self.snapshot();duration=(time.perf_counter_ns()-t0)/1e6
  self.summaries.append({'event':self.phase,'title':title,'committed_ids':list(self.done),'new_commit_ids':[r['proposal_id'] for r in self.receipts if r['event']==self.phase and r['permitted']],
      'goals':list(self.current['goals']),'achieved_tokens':s['achieved_tokens'],'missing_goals':s['missing_goals'],'disposition':self.last_selection['disposition'],'duration_ms':duration,'input_sha256':digest(self.latest_plan_input)})
  return self.snapshot()
 def change(self,kind):
  if kind not in {'REVOKE','PURPOSE_CHANGE','POLICY_VERSION_CHANGE'}:raise IntegrationError('UNKNOWN_CHANGE')
  self.changes.append(kind);self.revision+=1
  if kind=='REVOKE':self.current['epoch']+=1
  elif kind=='PURPOSE_CHANGE':self.current['task_purposes']=['changed_purpose_without_new_proposal']
  else:self.current['policy_snapshot']='CHANGED_UNREVIEWED_SNAPSHOT'
  self.events.append({'event':self.phase,'title':'Modeled change before commitment','detail':kind,'revision':self.revision})
  return self.snapshot()
 def cancel(self):self.pending=None
 def snapshot(self):
  achieved=sorted(tokens(self.current,self.done));missing=[g for g in self.current['goals'] if g not in achieved]
  actions={a['id']:a for a in self.current['actions']}
  views={}
  for role in ROLES:
   if self.mode=='PROGRESSIVE':views[role]=role_view(self.source,self.phase,role,self.receipts)
   else:views[role]={'role':role,'label':ROLES[role],'observation':deepcopy(self.source['operator_private_views'].get(role,{})) if self.phase else {},'own_proposals':[a for a in self.current['actions'] if a['owner']==role],'own_receipts':[r for r in self.receipts if r['owner']==role]}
  receiving=[]
  for a in self.current['actions']:
   if a['envelope_id']:
    e=self.current['envelopes'].get(a['envelope_id']);ok,reason=envelope_check(self.current,a,e)
    receiving.append({'proposal_id':a['id'],'envelope_id':a['envelope_id'],'accepted_now':ok,'reason':reason,'purpose':a['purpose'],'recipient':a['recipient'],'metadata':deepcopy(e)})
  return {'family_id':self.family,'strategy':self.strategy,'mode':self.mode,'phase':self.phase,'total_events':6 if self.mode=='PROGRESSIVE' else 1,'revision':self.revision,
      'events':deepcopy(self.events),'summaries':deepcopy(self.summaries),'roles':views,'proposals':deepcopy(self.current['actions']),'known_goals':self.current['goals'],
      'achieved_tokens':achieved,'missing_goals':missing,'committed_ids':list(self.done),'receipts':deepcopy(self.receipts),'selection':deepcopy(self.last_selection),'proposal_checks':deepcopy(self.last_constraints),
      'pending_plan':deepcopy(self.pending),'dt_context_checks':receiving,'authority_records':deepcopy(self.current['authority_register']),
      'active_epoch':self.current['epoch'],'simulation_only':True,'agent_backend':'frozen institution-owned action contracts; no live LLM or learned proposal inference',
      'review_status':'Clinical and Korean legal interpretation review pending','inspection_scope':'Local operator console. Role projections are not production access-control certification.'}
 def export(self):
  return {'snapshot':self.snapshot(),'plans':deepcopy(self.plans),'released_runtime':deepcopy(self.current),'last_selection_input':deepcopy(self.latest_plan_input),'simulation_only':True}

def verify_receipts(rows):
 previous='0'*64
 for i,r in enumerate(rows,1):
  if r['sequence']!=i or r['previous_hash']!=previous or digest({k:v for k,v in r.items() if k!='hash'})!=r['hash']:return False
  previous=r['hash']
 return True
