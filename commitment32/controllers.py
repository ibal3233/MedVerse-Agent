"""Causal timing policies. No dataset loader, future event, reference outcome or model.

Both bounded methods receive the same visible conditions and are deliberately capable.
A tie is valid. The fair implementation is written separately, not delegated to MedVerse.
"""
from copy import deepcopy
from coordination29.validator import eligibility
from .common import STRATEGIES

class CommitmentController:
 def __init__(self,strategy):
  if strategy not in STRATEGIES:raise ValueError('UNKNOWN_STRATEGY')
  self.strategy=strategy;self.waits={}
 def decide(self,view,done):
  c=view['case'];now=c['cursor'];records=[]
  for a in c['actions']:
   if a['id'] in done:continue
   spec=view['timing'].get(a['id'],{})
   ok,reason=eligibility(c,a)
   if not ok:
    disposition='ESCALATE' if reason in {'HUMAN_AUTHORITY_REQUIRED','INSUFFICIENT_EVIDENCE'} else 'BLOCK'
    d=self.record(view,a,disposition,reason)
   elif spec.get('effect')=='PREPARATORY':d=self.record(view,a,'PREPARE','AUTHORIZED_PREPARATION_IS_NOT_COMPLETION')
   elif now>spec.get('latest_commit_time',10**9):d=self.record(view,a,'ESCALATE','DECLARED_COMMIT_LIMIT_PASSED')
   elif self.strategy=='EAGER':d=self.record(view,a,'COMMIT','CURRENTLY_ELIGIBLE_EAGER_PROPOSAL')
   elif self.strategy=='FAIR_BOUNDED_WAIT':d=self.fair(view,a,spec)
   else:d=self.medverse(view,a,spec)
   records.append(d)
  return records
 def fair(self,view,a,spec):
  now=view['case']['cursor'];review=view['reviews'].get(spec.get('review_ref'))
  due=spec.get('required_immediate',False) or now>=spec.get('latest_commit_time',10**9)
  may_defer=(not due and spec.get('can_defer',False) and review is not None and review.get('status')=='PENDING' and review.get('owner')==a['owner'])
  if may_defer:
   end=min(review['expires'],spec['latest_commit_time'])
   if a['id'] in self.waits:end=min(end,self.waits[a['id']]['expiry'])
   if now<end:
    self.waits.setdefault(a['id'],{'start':now,'expiry':end})
    return self.record(view,a,'WAIT','VISIBLE_PENDING_REVIEW',expiry=end,start=self.waits[a['id']]['start'])
  return self.record(view,a,'COMMIT','IMMEDIATE_OR_DUE' if due else 'NO_ACTIVE_UNEXPIRED_WAIT')
 def medverse(self,view,a,spec):
  t=view['case']['cursor']
  if spec.get('required_immediate') or t>=spec.get('latest_commit_time',10**9):
   return self.record(view,a,'COMMIT','IMMEDIATE_OR_DUE')
  ref=spec.get('review_ref');review=view['reviews'].get(ref)
  if not spec.get('can_defer') or not review or review.get('owner')!=a['owner'] or review['status']!='PENDING':
   return self.record(view,a,'COMMIT','NO_ACTIVE_UNEXPIRED_WAIT')
  deadline=min(review['expires'],spec['latest_commit_time'])
  remembered=self.waits.get(a['id'])
  if remembered:deadline=min(deadline,remembered['expiry'])
  if t>=deadline:return self.record(view,a,'COMMIT','NO_ACTIVE_UNEXPIRED_WAIT')
  if not remembered:self.waits[a['id']]={'start':t,'expiry':deadline}
  return self.record(view,a,'WAIT','VISIBLE_PENDING_REVIEW',expiry=deadline,start=self.waits[a['id']]['start'])
 @staticmethod
 def record(view,a,decision,reason,expiry=None,start=None):
  spec=view['timing'].get(a['id'],{})
  return {'proposal_id':a['id'],'owner':a['owner'],'history_hash':view['released_history_hash'],
   'decision':decision,'current_reason':reason,'known_prerequisites':list(a['needs']),
   'pending_review_ref':spec.get('review_ref'),'latest_commit_time':spec.get('latest_commit_time'),
   'wait_expiry':expiry,'wait_start':start,'allowed_preparation_ids':list(spec.get('allowed_preparation_ids',[])),
   'final_revalidation_required':True,'authorizes_action':False}
