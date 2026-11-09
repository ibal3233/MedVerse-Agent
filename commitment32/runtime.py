"""Streaming engine with unchanged Gate 29 selection/authorization mechanisms.

New timing control filters released proposals; a shared preparatory-action handler
is available to every comparator. Effects are append-only. No state rollback.
"""
from __future__ import annotations
from copy import deepcopy as cp
from coordination29.selectors import select
from coordination29.validator import validate
from coordination29.common import tokens
from .publisher import Publisher
from .controllers import CommitmentController
from .common import digest
from coordination30.evidence import source_hashes

class Session:
 def __init__(self,strategy='MEDVERSE_COMMITMENT',selector='MEDVERSE_HARMONIZER'):
  self.publisher=Publisher();self.controller=CommitmentController(strategy);self.strategy=strategy;self.selector=selector
  self.done=[];self.receipts=[];self.events=[];self.pending=None;self.revision=0;self.plan_inputs=[]
 def view(self):return self.publisher.public()
 def residual(self):
  c=cp(self.publisher.case);c['initial_tokens']=sorted(tokens(c,self.done));prev=[a for a in c['actions'] if a['id'] in self.done]
  keep=[]
  for a in c['actions']:
   if a['id'] in self.done:continue
   _,why=validate(c,a,self.done)
   if why in {'JOINT_ACTION_CONFLICT','JOINT_DISCLOSURE_CONFLICT','EXCLUSIVE_ALTERNATIVE','CONFLICTING_STATE'}:continue
   keep.append(a)
  c['actions']=keep
  for r in c['field_constraints']:
   earlier={f for a in prev if a['recipient']==r['recipient'] for f in a['fields']}
   r['forbidden_combination']=sorted(set(r['forbidden_combination'])-earlier)
  return c
 def begin(self,event):
  if self.pending:raise ValueError('PENDING_PLAN_MUST_BE_COMMITTED_OR_CANCELLED')
  self.publisher.release(event);self.revision+=1
  return self._make_plan()
 def begin_snapshot(self,case):
  """Known-case integration regression only; accepts a released projection, not a family."""
  if self.pending:raise ValueError('PENDING_PLAN')
  self.publisher.case=cp(case);self.publisher.history.append({'released_snapshot':cp(case)});self.revision+=1
  return self._make_plan()
 def _make_plan(self):
  view=self.view();decisions=self.controller.decide(view,self.done)
  dmap={d['proposal_id']:d for d in decisions};res=self.residual()
  # Preparations are not scored as care or disclosure and are handled identically.
  residual=cp(res);residual['actions']=[a for a in res['actions'] if dmap[a['id']]['decision']=='COMMIT']
  result=select(residual,self.selector) if residual['actions'] or residual['goals'] else {'sequence':[],'objective':[0,0,0,0],'disposition':'AWAITING_EVIDENCE'}
  prep_requested={pid for a in view['case']['actions'] if a['id'] not in self.done for pid in view['timing'].get(a['id'],{}).get('allowed_preparation_ids',[])}
  preps=[a['id'] for a in res['actions'] if a['id'] in prep_requested and dmap[a['id']]['decision']=='PREPARE']
  self.pending={'plan_id':digest({'view':view,'done':self.done,'revision':self.revision})[:24],'revision':self.revision,'view':view,'decisions':decisions,'preparations':preps,'sequence':result['sequence'],'selection':result,'before_done':list(self.done)}
  self.plan_inputs.append(cp({'view':view,'done':self.done,'decisions':decisions,'selection_input':residual}))
  return cp(self.pending)
 def _try_commit(self,aid,phase,plan):
  c=self.publisher.case;a=next(x for x in c['actions'] if x['id']==aid);ok,reason=validate(c,a,self.done)
  # Time is a shared declared engineering limit, not an invented clinical rule.
  timing=self.publisher.timing.get(aid,{})
  if ok and c['cursor']>timing.get('latest_commit_time',10**9):ok,reason=False,'DECLARED_COMMIT_LIMIT_PASSED'
  if ok and plan['revision']!=self.revision:ok,reason=False,'STALE_PLAN_REVISION'
  row={'sequence':len(self.receipts)+1,'event':c['cursor'],'plan_id':plan['plan_id'],'proposal_id':aid,'owner':a['owner'],'stage':phase,
       'actual_proposal':cp(a),'permitted':ok,'reason':reason,'policy_snapshot':c['policy_snapshot'],'authority_epoch':c['epoch'],
       'source_ids':a['evidence'],'source_record_hashes':{k:source_hashes().get(k) for k in a['evidence']},'visible_history_hash':digest(self.publisher.history),
       'modeled_side_effect':{'tokens':a['provides'],'recipient':a['recipient'],'fields':a['fields']} if ok else None,
       'previous_hash':self.receipts[-1]['hash'] if self.receipts else '0'*64,'simulation_only':True}
  row['hash']=digest(row);self.receipts.append(row)
  if ok:self.done.append(aid)
 def commit(self,plan_id):
  if not self.pending or self.pending['plan_id']!=plan_id:raise ValueError('UNKNOWN_OR_REPLAYED_PLAN')
  p=self.pending
  for aid in p['preparations']:self._try_commit(aid,'PREPARE',p)
  # Same frozen selector reruns after common preparations, with the same timing exclusions.
  dmap={d['proposal_id']:d for d in p['decisions']};res=self.residual();res['actions']=[a for a in res['actions'] if dmap.get(a['id'],{}).get('decision')=='COMMIT']
  if p['revision']==self.revision:
   choice=select(res,self.selector) if res['actions'] or res['goals'] else {'sequence':[],'disposition':'AWAITING_EVIDENCE'}
   sequence=choice['sequence']
  else:choice=p['selection'];sequence=p['sequence']
  for aid in sequence:self._try_commit(aid,'COMMIT',p)
  achieved=sorted(tokens(self.publisher.case,self.done));missing=sorted(set(self.publisher.case['goals'])-set(achieved))
  self.events.append({'event':self.publisher.case['cursor'],'visible_history_hash':digest(self.publisher.history),'decisions':cp(p['decisions']),
                     'before_done':p['before_done'],'done':list(self.done),'achieved':achieved,'missing':missing,'selection':cp(choice),
                     'receipt_indices':[r['sequence'] for r in self.receipts if r['event']==self.publisher.case['cursor']]})
  self.pending=None;return self.snapshot()
 def advance(self,event):p=self.begin(event);return self.commit(p['plan_id'])
 def change_before_commit(self,kind):
  if not self.pending:raise ValueError('NO_PENDING_PLAN')
  c=self.publisher.case
  if kind=='REVOKE':c['epoch']+=1
  elif kind=='POLICY_VERSION_CHANGE':c['policy_snapshot']='CHANGED_MODEL_SNAPSHOT'
  elif kind=='PURPOSE_CHANGE':c['task_purposes']=['changed_without_new_authority']
  else:raise ValueError('UNKNOWN_CHANGE')
  self.revision+=1;self.publisher.history.append({'clock':c['cursor'],'change_before_commit':kind})
 def snapshot(self):
  c=self.publisher.case
  return {'strategy':self.strategy,'clock':c['cursor'],'committed':list(self.done),'achieved':sorted(tokens(c,self.done)),
          'known_goals':c['goals'],'missing_goals':sorted(set(c['goals'])-tokens(c,self.done)),
          'events':cp(self.events),'receipts':cp(self.receipts),'current':self.view(),'pending':cp(self.pending),
          'simulation_only':True,'effect_rollback_supported':False,'reference_outcomes_used_for_authorization':False}
 def export(self):return {'snapshot':self.snapshot(),'policy_inputs':cp(self.plan_inputs)}

def verify_receipts(rows):
 prev='0'*64
 for i,r in enumerate(rows,1):
  if r['sequence']!=i or r['previous_hash']!=prev or digest({k:v for k,v in r.items() if k!='hash'})!=r['hash']:return False
  prev=r['hash']
 return True
