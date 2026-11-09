"""One-time authored source construction. Not called automatically by experiment runners.

No controller, selector, reference evaluator, or result file is read by this module.
All clinical times, reviews and permissions are modeled assumptions pending review.
"""
from __future__ import annotations
from copy import deepcopy as cp
from .common import DATA,save,digest,fresh_case
from coordination29.common import OWNERS,EVIDENCE_IDS

class Builder:
 def __init__(self):
  self.actions=[];self.events=[{'clock':t,'actions':[],'grants':{},'facts':{},'evidence':{},'envelopes':{},'timing':{},'reviews':{},'goals':[],'deadlines':{},'purposes':[],'field_constraints':[]} for t in range(1,7)]
 def event(self,t):return self.events[t-1]
 def action(self,kind,provides,*,at=1,needs=(),forbids=(),groups=(),fields=(),purpose=None,recipient=None,grant='APPROVED',expiry=20,conditions=(),envelope=None,priority='REQUESTED',prep=False):
  aid='A%02d'%(len(self.actions)+1);owner=OWNERS[kind]
  purpose=purpose or ('care' if owner=='hospital_agent' else 'safety' if owner in ['cyber_network_agent','regulator_agent'] else 'trial_analysis')
  recipient=recipient or ('clinical_workspace' if owner=='hospital_agent' else 'technical_workspace' if owner=='cyber_network_agent' else 'oversight_workspace' if owner=='regulator_agent' else 'research_workspace')
  a={'id':aid,'owner':owner,'kind':kind,'task':'task_'+aid,'provides':list(provides),'needs':list(needs),'forbids':list(forbids),'exclusive_groups':list(groups),'fields':list(fields),'recipient':recipient,'purpose':purpose,'state_requirements':[{'key':k,'value':v} for k,v in conditions],'priority':priority,'capabilities':['adequate'],'grant_ids':['G-'+aid],'evidence':list(EVIDENCE_IDS[kind]),'bound_epoch':1,'policy_snapshot':'G32-MODELED-1','envelope_id':envelope,'origin':'INSTITUTION_OWNED_MODELED_PROPOSAL'}
  self.actions.append(a);e=self.event(at);e['actions'].append(cp(a));e['purposes'].append(purpose)
  e['grants']['G-'+aid]={'status':grant,'issued_by':'modeled_authority_for_'+owner,'action_ids':[aid],'purpose':purpose,'recipient':recipient,'fields':list(fields),'epoch':1,'expires_event':expiry,'simulation_only':True}
  for ref in a['evidence']:e['evidence'][ref]={'status':'AVAILABLE','policy_snapshot':'G32-MODELED-1','interpretation_status':'PENDING_REVIEW'}
  e['timing'][aid]={'owner':owner,'effect':'PREPARATORY' if prep else 'IRREVERSIBLE','can_defer':False,'required_immediate':False,'latest_commit_time':6,'review_ref':None,'allowed_preparation_ids':[]}
  return aid
 def timed(self,aid,*,review=None,expiry=3,deadline=5,immediate=False,preparations=(),at=1):
  a=next(a for a in self.actions if a['id']==aid)
  self.event(at)['timing'][aid].update(can_defer=bool(review),required_immediate=immediate,latest_commit_time=deadline,review_ref=review,allowed_preparation_ids=list(preparations))
  if review:self.event(at)['reviews'][review]={'id':review,'owner':a['owner'],'status':'PENDING','opened':at,'expires':expiry,'reason':'Visible unresolved institutional scope/route review; not an approval','authority_effect':False}
 def goals(self,goals,deadlines=None,at=1):
  e=self.event(at);e['goals']=list(goals);e['deadlines']=deadlines or {g:6 for g in goals}
 def close(self,review,t,status='RESOLVED'):
  r=next(cp(e['reviews'][review]) for e in self.events if review in e['reviews']);r['status']=status;self.event(t)['reviews'][review]=r
 def grant_update(self,aid,t,status):
  g=next(cp(e['grants']['G-'+aid]) for e in self.events if 'G-'+aid in e['grants']);g['status']=status;self.event(t)['grants']['G-'+aid]=g
 def context(self,ref,t,fields=('episode_code',),**kw):
  e={'dt_ref':ref,'data_version':'v1','observed_event':t,'provenance_ref':'modeled_publisher','validity':'VALID','purpose':'care','recipient':'clinical_workspace','fields':list(fields),'policy_snapshot':'G32-MODELED-1','authority_epoch':1,'expires_event':6};e.update(kw);self.event(t)['envelopes'][ref]=e
 def prep(self,provides='prepared_context',granted=True):
  return self.action('HANDOFF_ACK',[provides],prep=True,grant='APPROVED' if granted else 'DENIED')
 def branch(self,label):return {'branch_id':label,'events':cp(self.events)}

def development():
 out=[]
 # Elementary fixtures only; multi-goal conflict structures held out below.
 for number,typ in enumerate(['simple','wait_expiry','urgent','pending_authority'],1):
  b=Builder();a=b.action('CLINICAL_REVIEW',['clinical_review_done']);b.goals(['clinical_review_done'],{'clinical_review_done':3})
  if typ=='wait_expiry':b.timed(a,review='R1',expiry=2,deadline=3)
  if typ=='urgent':b.timed(a,review='R1',expiry=3,deadline=1,immediate=True);b.goals(['clinical_review_done'],{'clinical_review_done':1})
  if typ=='pending_authority':b.event(1)['grants']['G-'+a]['status']='PENDING'
  one=b.branch('UNCHANGED')
  if typ=='pending_authority':b.grant_update(a,2,'APPROVED')
  elif typ in ['wait_expiry','urgent']:b.close('R1',2)
  else:b.event(2)['facts']['administrative_update']=True
  out.append({'family_id':f'D{number:02d}','split':'DEVELOPMENT','title':typ,'branches':[one,b.branch('UPDATE')],'shared_prefix_end':1})
 return out

def confirmation():
 out=[]
 # P01: choosing an irreversible care route can prevent later containment.
 branches=[]
 for label,arrival,approved in [('PROMPT',2,True),('LATE',4,True),('NEVER',None,False),('DENIED_ALTERNATIVE',2,False)]:
  b=Builder();p=b.prep();a=b.action('CLINICAL_REVIEW',['clinical_review_done'],forbids=['stream_isolated'],groups=['care_route']);q=b.action('QUARANTINE_STREAM',['stream_isolated']);h=b.action('HANDOFF_ACK',['handoff_ack'],needs=['stream_isolated'])
  b.goals(['clinical_review_done','stream_isolated'],{'clinical_review_done':4,'stream_isolated':5})
  b.timed(a,review='R1',expiry=3,deadline=4,preparations=[p]);b.timed(q,review='R2',expiry=3,deadline=5,preparations=[p])
  if arrival:
   b.action('CLINICAL_REVIEW',['clinical_review_done'],at=arrival,needs=['handoff_ack','prepared_context'],groups=['care_route'],grant='APPROVED' if approved else 'DENIED',priority='ALTERNATIVE');b.close('R1',arrival);b.close('R2',arrival)
  branches.append(b.branch(label))
 out.append({'family_id':'P01','split':'CONFIRMATION','title':'Clinical route and containment review','branches':branches,'shared_prefix_end':1})
 # P02: broad containment shuts the only current route; narrow alternative may arrive.
 branches=[]
 for label,t in [('PROMPT',2),('LATE',4),('NEVER',None),('INVALID_SCOPE',2)]:
  b=Builder();p=b.prep();a=b.action('CLINICAL_REVIEW',['clinical_review_done'],needs=['contained'],forbids=['all_links_down'],groups=['care_route']);q=b.action('QUARANTINE_STREAM',['contained','all_links_down'],groups=['containment_mode'])
  b.goals(['clinical_review_done','contained'],{'clinical_review_done':5,'contained':4});b.timed(q,review='R1',expiry=3,deadline=4,preparations=[p])
  if t:
   alt=b.action('QUARANTINE_STREAM',['contained','affected_stream_down'],at=t,needs=['prepared_context'],groups=['containment_mode'],priority='ALTERNATIVE');b.close('R1',t)
   if label=='INVALID_SCOPE':b.event(t)['grants']['G-'+alt]['purpose']='not_the_declared_purpose'
  branches.append(b.branch(label))
 out.append({'family_id':'P02','split':'CONFIRMATION','title':'Containment breadth and future care route','branches':branches,'shared_prefix_end':1})
 # P03: independently authorized individual views conflict when joined.
 branches=[]
 for label,t in [('PROMPT',2),('LATE',4),('NEVER',None),('INADEQUATE_ALTERNATIVE',2)]:
  b=Builder();c=b.action('CLINICAL_REVIEW',['clinical_review_done']);pa=b.action('PRIVACY_ATTEST',['privacy_review_done']);ra=b.action('RESEARCH_ATTEST',['research_review_done']);a=b.action('RESEARCH_VIEW',['research_one'],needs=['privacy_review_done','research_review_done'],fields=['age_band'],groups=['view_one'])
  b.goals(['clinical_review_done','research_one','research_two'],{'clinical_review_done':1,'research_one':5,'research_two':5});b.timed(c,immediate=True,deadline=1);b.timed(a,review='R1',expiry=3,deadline=5)
  b.event(1)['field_constraints']=[{'recipient':'research_workspace','forbidden_combination':['age_band','location_band'],'basis':'modeled joint contract, not a statutory inference'}]
  b.action('RESEARCH_VIEW',['research_two'],at=2,needs=['privacy_review_done','research_review_done'],fields=['location_band'])
  if t:
   alt=b.action('RESEARCH_VIEW',['research_one'],at=t,needs=['privacy_review_done','research_review_done'],fields=['cohort_count'],groups=['view_one'],priority='ALTERNATIVE');b.close('R1',t)
   if label=='INADEQUATE_ALTERNATIVE':next(a for a in b.event(t)['actions'] if a['id']==alt)['capabilities']=['not_adequate']
  branches.append(b.branch(label))
 out.append({'family_id':'P03','split':'CONFIRMATION','title':'Joint disclosure and task-adequate substitute','branches':branches,'shared_prefix_end':1})
 # P04: pre-revocation permission was genuine; revocation is not retroactive.
 branches=[]
 for label in ['VALID_REPLACEMENT','NO_REPLACEMENT','PENDING_REPLACEMENT','EVIDENCE_NOT_AUTHORITY']:
  b=Builder();c=b.action('CLINICAL_REVIEW',['clinical_review_done']);p=b.action('PRIVACY_ATTEST',['privacy_ok']);r=b.action('RESEARCH_ATTEST',['research_ok']);a=b.action('RESEARCH_VIEW',['research_done'],needs=['privacy_ok','research_ok'],fields=['episode_code','symptom_band'],groups=['research_view'])
  b.goals(['clinical_review_done','research_done'],{'clinical_review_done':1,'research_done':5});b.timed(c,immediate=True,deadline=1);b.timed(a,review='R1',expiry=3,deadline=5)
  b.grant_update(a,2,'DENIED');b.close('R1',2)
  if label!='NO_REPLACEMENT':
   alt=b.action('RESEARCH_VIEW',['research_done'],at=2,needs=['privacy_ok','research_ok'],fields=['cohort_count'],groups=['research_view'],priority='ALTERNATIVE',grant='APPROVED' if label=='VALID_REPLACEMENT' else 'PENDING')
   if label=='EVIDENCE_NOT_AUTHORITY':b.event(3)['facts']['new_document_received']=True
  branches.append(b.branch(label))
 out.append({'family_id':'P04','split':'CONFIRMATION','title':'Authority changes after a valid earlier opportunity','branches':branches,'shared_prefix_end':1})
 # P05: immediate clinical and protective duties cannot be sacrificed for future options.
 branches=[]
 for label in ['ALTERNATIVE','NONE','REVIEW_EXTENDED','LATE_REVOCATION']:
  b=Builder();q=b.action('QUARANTINE_STREAM',['stream_isolated']);h=b.action('HANDOFF_ACK',['handoff_ack'],needs=['stream_isolated']);c=b.action('CLINICAL_REVIEW',['clinical_review_done'],needs=['handoff_ack'],groups=['care_route'])
  b.goals(['stream_isolated','clinical_review_done'],{'stream_isolated':1,'clinical_review_done':1});b.timed(q,review='R1',expiry=3,deadline=1,immediate=True);b.timed(c,review='R2',expiry=3,deadline=1,immediate=True)
  if label=='ALTERNATIVE':b.action('CLINICAL_REVIEW',['clinical_review_done'],at=2,groups=['care_route'],priority='ALTERNATIVE')
  if label=='REVIEW_EXTENDED':
   r=cp(b.event(1)['reviews']['R1']);r['expires']=6;b.event(2)['reviews']['R1']=r
  if label=='LATE_REVOCATION':b.grant_update(c,2,'DENIED')
  branches.append(b.branch(label))
 out.append({'family_id':'P05','split':'CONFIRMATION','title':'Immediate obligations override optional waiting','branches':branches,'shared_prefix_end':1})
 # P06: same receiving-side validator; a preparation never supplies authority.
 branches=[]
 for label in ['FRESH_MINIMAL','MISSING_PROVENANCE','WRONG_RECIPIENT','SOURCE_VERSION_CHANGED']:
  b=Builder();p=b.prep();b.context('E1',1,fields=['episode_code','symptom_band']);a=b.action('DT_RECEIVE',['dt_received'],fields=['episode_code','symptom_band'],envelope='E1',groups=['dt_view']);c=b.action('CLINICAL_REVIEW',['clinical_review_done'],needs=['dt_received'])
  b.goals(['dt_received','clinical_review_done'],{'dt_received':4,'clinical_review_done':4});b.timed(a,review='R1',expiry=3,deadline=4,preparations=[p])
  kw={}
  if label=='MISSING_PROVENANCE':kw['provenance_ref']=''
  if label=='WRONG_RECIPIENT':kw['recipient']='research_workspace'
  if label=='SOURCE_VERSION_CHANGED':kw['policy_snapshot']='OTHER_REVIEW_PENDING_SNAPSHOT'
  b.context('E2',2,fields=['episode_code'],**kw);b.action('DT_RECEIVE',['dt_received'],at=2,needs=['prepared_context'],fields=['episode_code'],envelope='E2',groups=['dt_view'],priority='ALTERNATIVE');b.close('R1',2)
  branches.append(b.branch(label))
 out.append({'family_id':'P06','split':'CONFIRMATION','title':'Prepared DT-context exchange with recipient checks','branches':branches,'shared_prefix_end':1})
 # P07: missing authority cannot be supplied by WAIT/PREPARE or a new evidence file.
 branches=[]
 for label in ['APPROVAL','NEVER','EVIDENCE_ONLY','DENIAL']:
  b=Builder();c=b.action('CLINICAL_REVIEW',['clinical_review_done']);p=b.prep(granted=False);o=b.action('OVERSIGHT_ATTEST',['oversight_recorded'],grant='PENDING');v=b.action('RESEARCH_VIEW',['research_done'],needs=['oversight_recorded'],fields=['cohort_count'])
  b.goals(['clinical_review_done','oversight_recorded','research_done'],{'clinical_review_done':1,'oversight_recorded':4,'research_done':5});b.timed(c,immediate=True,deadline=1);b.timed(v,review='R1',expiry=3,deadline=5,preparations=[p])
  if label=='APPROVAL':b.grant_update(o,2,'APPROVED');b.close('R1',2)
  if label=='DENIAL':b.grant_update(o,2,'DENIED');b.close('R1',2)
  if label=='EVIDENCE_ONLY':b.event(2)['facts']['oversight_document_available']=True
  branches.append(b.branch(label))
 out.append({'family_id':'P07','split':'CONFIRMATION','title':'Oversight authority is not manufactured by preparation','branches':branches,'shared_prefix_end':1})
 # P08: no visible timing reason. A hidden later objective creates an unavoidable online trade-off.
 branches=[]
 for label in ['UNANNOUNCED_ALTERNATIVE','NO_NEW_REQUEST','DENIED_ALTERNATIVE','TOO_LATE']:
  b=Builder();c=b.action('CLINICAL_REVIEW',['clinical_review_done']);a=b.action('RESEARCH_VIEW',['research_one'],fields=['age_band'],groups=['view_one']);b.goals(['clinical_review_done','research_one'],{'clinical_review_done':1,'research_one':4});b.timed(c,immediate=True,deadline=1)
  b.event(1)['field_constraints']=[{'recipient':'research_workspace','forbidden_combination':['age_band','location_band'],'basis':'modeled contract'}]
  if label!='NO_NEW_REQUEST':
   b.goals(['research_two'],{'research_two':5},at=2);b.action('RESEARCH_VIEW',['research_two'],at=2,fields=['location_band']);t=6 if label=='TOO_LATE' else 2
   b.action('RESEARCH_VIEW',['research_one'],at=t,fields=['cohort_count'],groups=['view_one'],priority='ALTERNATIVE',grant='DENIED' if label=='DENIED_ALTERNATIVE' else 'APPROVED')
  branches.append(b.branch(label))
 out.append({'family_id':'P08','split':'CONFIRMATION','title':'Unannounced future need and irreversible earlier disclosure','branches':branches,'shared_prefix_end':1})
 return out

def main():
 families=development()+confirmation()
 # No descriptive scenario identifier enters any event payload or controller input.
 spec={'version':'1.0.0','scope':'scenario-based commitment modeling; no patient-derived records','clock':'declared event steps, not a clinical time unit','families':families}
 save(DATA/'prefix_families.json',spec)
 print('Authored',len(families),'prefix families;',sum(len(f['branches']) for f in families),'branches. No evaluation was run.')
if __name__=='__main__':main()
