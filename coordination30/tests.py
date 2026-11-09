"""Bounded engineering checks on existing development families and explicit probes."""
from copy import deepcopy
from .common import source_cases,digest
from .engine import IntegratedSession,IntegrationError,verify_receipts
from .schedule import released_input
from .client import Client
from coordination29.reference_evaluator import assess_execution

def run_tests(url):
 rows=[]
 def check(name,result,detail=''):
  rows.append({'check':name,'passed':bool(result),'detail':detail})
 c=Client(url)
 status,health=c.call('/api30/health');check('HTTP health is modeled',status==200 and health['simulated'] and not health['external_actions'])
 status,config=c.call('/api30/config');check('Five roles / coordinator separate',len(config['roles'])==5)
 check('Four fair-scope configurations available',len(config['strategies'])==4)
 for bad in ['bad','..']:
  status,_=c.call('/api30/session',{'family_id':bad});check('Reject unknown family '+bad,status==400)
 status,_=c.call('/api30/session',{'strategy':'injected'});check('Reject unknown selector',status==400)
 status,_=c.call('/api30/session',{'family_id':'D01','authority_register':{}});check('No client-supplied authority register',status==400)
 c.start('D01')
 status,_=c.call('/api30/advance',{'session_id':c.session['session_id']},'bad');check('Session token required',status==403)
 status,_=c.call('/api30/advance',{'session_id':c.session['session_id']},c.session['token'],{'Origin':'https://untrusted.invalid'});check('Cross-origin POST rejected',status==403)
 status,_=c.call('/api30/commit',{'session_id':c.session['session_id'],'plan_id':'fake','sequence':['A01']},c.session['token']);check('No client-supplied replacement sequence',status==400)
 s=c.post('/api30/advance');check('First event has no future proposals',s['proposals']==[] and s['authority_records']=={} and s['committed_ids']==[])
 for role in config['roles']:
  view=c.post('/api30/view',role=role)
  check('Only own proposals in '+role,all(a['owner']==role for a in view['own_proposals']))
  if role!='hospital_agent':check('No Hospital observation in '+role,'modeled_symptom' not in str(view))
 s=c.post('/api30/advance',auto_commit=False);pid=s['pending_plan']['plan_id'];check('Selection without automatic commitment',bool(s['selection']['sequence']) and s['committed_ids']==[])
 before=list(s['committed_ids']);s=c.post('/api30/commit',plan_id=pid);check('Actual proposal reaches committed effect',s['committed_ids']==['A01'] and s['receipts'][-1]['actual_proposal']['id']=='A01')
 status,_=c.call('/api30/commit',{'session_id':c.session['session_id'],'plan_id':pid},c.session['token']);check('Committed plan cannot be replayed',status==400)
 for _ in range(4):s=c.post('/api30/advance')
 check('No duplicate effect after later events',s['committed_ids']==['A01'])
 check('Receipt chain valid',verify_receipts(s['receipts']))
 copy=deepcopy(s['receipts']);copy[0]['reason']='TAMPERED';check('Receipt alteration detected',not verify_receipts(copy))
 status,_=c.call('/api30/advance',{'session_id':c.session['session_id']},c.session['token']);check('Cannot release past final event',status==400)
 e=c.post('/api30/export');check('Export contains original proposals and released context','released_runtime' in e and e['snapshot']['receipts'][0]['actual_proposal']['id']=='A01')
 for kind in ['REVOKE','PURPOSE_CHANGE','POLICY_VERSION_CHANGE']:
  c.start('D01');c.post('/api30/advance');s=c.post('/api30/advance',auto_commit=False);pid=s['pending_plan']['plan_id'];c.post('/api30/change',kind=kind);s=c.post('/api30/commit',plan_id=pid)
  check(kind+' blocks actual pending proposal',len(s['receipts'])==1 and not s['receipts'][0]['permitted'] and not s['committed_ids'])
  check(kind+' rejected action has no effect',s['receipts'][0]['modeled_side_effect'] is None)
 for family in ['D01','D04','D05','D06']:
  c.start(family,mode='SNAPSHOT');s=c.post('/api30/advance');export=c.post('/api30/export')
  check('Snapshot '+family+' independently assessed',not assess_execution(export['released_runtime'],s['committed_ids']) and verify_receipts(s['receipts']))
 # The exact-ID boundary is inherited and routed through the real service.
 status,r=c.call('/api/search',{'query':'KR-NONEXISTENT-999','role':'privacy_agent'})
 check('Exact unknown citation is not substituted',status==200 and r['hits']==[] and r['status']=='UNKNOWN_EXACT_CITATION')
 status,r=c.call('/api/search',{'query':'pseudonymized research safeguards','role':'privacy_agent','jurisdiction':'NOT_KR'})
 check('Wrong-jurisdiction retrieval does not return evidence',status==200 and not r['hits'])
 # Prefix noninterference: changes only to unreleased alternative contracts do not
 # change released runtime input. Use a development family rather than confirmation.
 f=next(x for x in source_cases() if x['family_id']=='D04');other=deepcopy(f)
 for a in other['actions']:
  if a['priority']=='ALTERNATIVE':a['fields'].append('NEVER_RELEASED_CANARY')
 check('Unreleased alternative cannot affect event-3 input',digest(released_input(f,3))==digest(released_input(other,3)))
 return rows
