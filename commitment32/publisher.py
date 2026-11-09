"""Trusted local modeled event publisher. No remote authenticity is claimed.

The online session receives ONE already-released event, never the family or timeline.
"""
from copy import deepcopy as cp
from .common import fresh_case,digest
ALLOWED={'clock','actions','grants','facts','evidence','envelopes','timing','reviews','goals','deadlines','purposes','field_constraints'}
class Publisher:
 def __init__(self):
  self.case=fresh_case();self.timing={};self.reviews={};self.deadlines={};self.history=[]
 def release(self,event):
  if set(event)-ALLOWED:raise ValueError('UNSUPPORTED_EVENT_FIELDS')
  if event['clock']!=self.case['cursor']+1:raise ValueError('NONSEQUENTIAL_EVENT')
  event=cp(event);self.case['cursor']=event['clock'];self.history.append(event)
  for a in event.get('actions',[]):
   if any(b['id']==a['id'] for b in self.case['actions']):raise ValueError('PROPOSAL_ID_REUSED')
   self.case['actions'].append(a);self.case['adequacy'][a['task']]=['adequate']
  self.case['facts'].update(event.get('facts',{}))
  for key,g in event.get('grants',{}).items():
   self.case['authority_register'][key]=g;self.case['authority_register_hashes'][key]=digest(g)
  self.case['evidence_register'].update(event.get('evidence',{}))
  for key,env in event.get('envelopes',{}).items():self.case['envelopes'][key]=env
  self.case['trusted_envelope_hashes']=[digest(e) for e in self.case['envelopes'].values()]
  self.case['task_purposes']=sorted(set(self.case['task_purposes'])|set(event.get('purposes',[])))
  self.case['goals']=sorted(set(self.case['goals'])|set(event.get('goals',[])))
  for goal,limit in event.get('deadlines',{}).items():
   if goal in self.deadlines and self.deadlines[goal]!=limit:raise ValueError('DEADLINE_REDEFINED')
   if not isinstance(limit,int) or limit<event['clock']:raise ValueError('INVALID_DECLARED_DEADLINE')
   self.deadlines[goal]=limit
  for constraint in event.get('field_constraints',[]):
   if constraint not in self.case['field_constraints']:self.case['field_constraints'].append(constraint)
  ids={a['id']:a for a in self.case['actions']}
  for aid,timing in event.get('timing',{}).items():
   if aid not in ids or timing['owner']!=ids[aid]['owner']:raise ValueError('TIMING_OWNER_MISMATCH')
   if aid in self.timing:raise ValueError('TIMING_CONTRACT_REDEFINED')
   if timing['effect']=='PREPARATORY' and (ids[aid]['fields'] or set(ids[aid]['provides'])&set(self.case['goals'])):raise ValueError('PREPARATION_HAS_FINAL_EFFECT')
   self.timing[aid]=timing
  for key,review in event.get('reviews',{}).items():
   if review['authority_effect'] is not False:raise ValueError('REVIEW_IS_NOT_AUTHORITY')
   self.reviews[key]=review
  return self.public()
 def public(self):return {'case':cp(self.case),'timing':cp(self.timing),'reviews':cp(self.reviews),'deadlines':cp(self.deadlines),'released_history_hash':digest(self.history)}
