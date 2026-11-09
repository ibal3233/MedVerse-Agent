"""Development and invariant checks only. No confirmation branch is executed here."""
from copy import deepcopy as cp
from .common import DATA,load,digest,STRATEGIES
from .build_specification import Builder
from .runtime import Session,verify_receipts
from .publisher import Publisher
from .reference import full_information,assess

def run_checks():
 checks=[]
 def check(name,condition):
  checks.append({'name':name,'passed':bool(condition)})
  if not condition:raise AssertionError(name)
 def rejected(name,fn):
  try:fn()
  except (ValueError,KeyError):check(name,True)
  else:check(name,False)
 fs=[f for f in load(DATA/'prefix_families.json')['families'] if f['split']=='DEVELOPMENT']
 for f in fs:
  for s in STRATEGIES:
   b=f['branches'][0];x=Session(s)
   for e in b['events']:x.advance(e)
   m=assess(b,x.export());check(f['family_id']+' '+s+' valid',m['invalid_commits']==0 and m['unjustified_waits']==0 and verify_receipts(x.receipts))
   if f['family_id']=='D01':check('simple completes '+s,m['complete_within_limits'])
   if f['family_id']=='D02':check('bounded expiry '+s,m['clinical_commit_event']==(1 if s=='EAGER' else 2))
   if f['family_id']=='D03':check('urgent not deferred '+s,m['clinical_commit_event']==1)
   if f['family_id']=='D04':check('no invented approval '+s,not x.done)
 # Shared preparation is not clinical completion or disclosure.
 b=Builder();p=b.prep();a=b.action('CLINICAL_REVIEW',['clinical_review_done']);b.timed(a,review='R1',expiry=3,deadline=4,preparations=[p]);b.goals(['clinical_review_done'],{'clinical_review_done':4})
 x=Session();x.advance(b.events[0]);check('prepare without care',[r['proposal_id'] for r in x.receipts if r['permitted']]==[p]);check('prepare no fields',all(not r['actual_proposal']['fields'] for r in x.receipts));check('wait scoped to proposal',x.events[0]['decisions'][-1]['decision']=='WAIT')
 b.grant_update(p,1,'DENIED');x=Session();x.advance(b.events[0]);check('unauthorized preparation rejected',not x.done)
 # No visible review -> no artificial delay, even if a future alternative could be better.
 b=Builder();a=b.action('CLINICAL_REVIEW',['clinical_review_done']);b.goals(['clinical_review_done'],{'clinical_review_done':4});x=Session();x.advance(b.events[0]);check('no invented future opportunity',x.done==[a])
 # Revocation, policy change and purpose changes occur after planning, before actual commit.
 for strategy in STRATEGIES:
  for kind in ['REVOKE','POLICY_VERSION_CHANGE','PURPOSE_CHANGE']:
   x=Session(strategy);p=x.begin(b.events[0]);x.change_before_commit(kind);x.commit(p['plan_id']);check('precommit '+strategy+' '+kind,not x.done and all(not r['permitted'] for r in x.receipts))
 x=Session();plan=x.begin(b.events[0]);x.commit(plan['plan_id']);rejected('plan replay rejected',lambda:x.commit(plan['plan_id']))
 # Source and input constraints.
 rejected('future payload field rejected',lambda:Publisher().release(dict(b.events[0],future_events=[])))
 rejected('skipped clock rejected',lambda:Publisher().release(dict(b.events[0],clock=3)))
 bad=cp(b.events[0]);bad['timing'][a]['owner']='privacy_agent';rejected('timing owner mismatch',lambda:Publisher().release(bad))
 bad=cp(b.events[0]);bad['timing'][a]['effect']='PREPARATORY';rejected('prepare not care effect',lambda:Publisher().release(bad))
 bad=cp(b.events[0]);bad['actions'][0]['owner']='privacy_agent';bad['timing'][a]['owner']='privacy_agent';x=Session();x.advance(bad);check('wrong execution owner blocked',not x.done)
 bad=cp(b.events[0]);bad['grants']['G-'+a]['status']='PENDING';x=Session();x.advance(bad);check('approval request not permission',not x.done)
 # Extensions of the same review cannot silently restart an already recorded wait.
 b=Builder();a=b.action('CLINICAL_REVIEW',['clinical_review_done']);b.goals(['clinical_review_done'],{'clinical_review_done':5});b.timed(a,review='R1',expiry=2,deadline=5)
 rr=cp(b.event(1)['reviews']['R1']);rr['expires']=5;b.event(2)['reviews']['R1']=rr
 for s in STRATEGIES[1:]:
  x=Session(s);x.advance(b.events[0]);x.advance(b.events[1]);check('no perpetual extension '+s,x.done==[a])
 # Independent offline bound agrees with development fixtures.
 for f in fs:
  r=full_information(f['branches'][0]);check('reference dev '+f['family_id'],r['complete_within_declared_limits']==(f['family_id']!='D04'))
 # Receipt tampering is observable; local hashes are not remote signatures.
 tampered=cp(x.receipts);tampered[0]['reason']='edited';check('tampered chain rejected',not verify_receipts(tampered))
 return checks
if __name__=='__main__':
 import json
 checks=run_checks();print(json.dumps({'passed':len(checks),'checks':checks},indent=2))
