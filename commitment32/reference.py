"""Assessment ONLY. No online runtime imports this file.

Current-state legality is checked separately from the full-information diagnostic
upper bound. The latter sees the full continuation and is not a causal baseline.
The same developer authored both; external clinical/legal review is pending.
"""
from __future__ import annotations
from copy import deepcopy as cp
from coordination29.reference_evaluator import local_reference
from .publisher import Publisher

def permitted(case,a,done,timing=None):
 """Validate only the NEW action's current permission; never revoke past effects."""
 if a['id'] in done or not local_reference(case,a):return False
 previous=[b for b in case['actions'] if b['id'] in done]
 have=set(case['initial_tokens'])|{t for b in previous for t in b['provides']}
 if not set(a['needs'])<=have or set(a['forbids'])&have:return False
 if any(set(b['forbids'])&set(a['provides']) for b in previous):return False
 if any(set(b['exclusive_groups'])&set(a['exclusive_groups']) for b in previous):return False
 for r in case['field_constraints']:
  disclosed={f for b in previous+[a] if b['recipient']==r['recipient'] for f in b['fields']}
  if set(r['forbidden_combination'])<=disclosed:return False
 if timing and case['cursor']>timing.get(a['id'],{}).get('latest_commit_time',10**9):return False
 return True

def public_snapshots(branch):
 p=Publisher();out=[]
 for e in branch['events']:out.append(p.release(e))
 return out

def first_times(receipts):
 times={}
 for r in receipts:
  if r['permitted']:
   for tok in r['actual_proposal']['provides']:times.setdefault(tok,r['event'])
 return times

def score(view,times,done):
 goals=view['case']['goals'];late=[g for g in goals if times.get(g,10**9)>view['deadlines'].get(g,10**9)]
 clinical=int('clinical_review_done' in goals and 'clinical_review_done' in late)
 fields={(a['recipient'],f) for a in view['case']['actions'] if a['id'] in done for f in a['fields']}
 return (clinical,len(late),len(fields),sum(times.get(g,0) for g in goals if g in times),len(done))

def full_information(branch):
 """Finite state enumeration over the published timeline; offline upper bound only."""
 snapshots=public_snapshots(branch);last=snapshots[-1]
 states={(frozenset(),()):{'done':[],'times':{},'witness':[]}}
 examined=0
 for view in snapshots:
  c=view['case'];next_states={}
  for state in states.values():
   stack=[state];seen=set()
   while stack:
    s=stack.pop();key=frozenset(s['done'])
    if key in seen:continue
    seen.add(key);examined+=1
    # For a fixed committed set and timeliness signature retain the earliest witness.
    timely=tuple(g for g in last['case']['goals'] if s['times'].get(g,10**9)<=last['deadlines'].get(g,10**9))
    sig=(key,timely);old=next_states.get(sig)
    if old is None or score(last,s['times'],s['done'])<score(last,old['times'],old['done']):next_states[sig]=s
    for a in c['actions']:
     if permitted(c,a,s['done'],view['timing']):
      times=dict(s['times'])
      for tok in a['provides']:times.setdefault(tok,c['cursor'])
      stack.append({'done':s['done']+[a['id']],'times':times,'witness':s['witness']+[{'event':c['cursor'],'proposal_id':a['id']}]})
  states=next_states
 best=min(states.values(),key=lambda s:(score(last,s['times'],s['done']),s['done']))
 objective=score(last,best['times'],best['done'])
 return {'noncausal':True,'available_to_controller':False,'objective':list(objective),
         'complete_within_declared_limits':objective[1]==0,'clinical_within_limit':objective[0]==0,
         'witness':best['witness'],'achieved_times':best['times'],'states_examined':examined,
         'interpretation':'Offline full-information upper bound. No independent clinical/legal approval.'}

def assess(branch,trace):
 views=public_snapshots(branch);receipts=trace['snapshot']['receipts'];done=[];errors=[]
 for r in receipts:
  v=views[r['event']-1];a=r['actual_proposal']
  ok=permitted(v['case'],a,done,v['timing'])
  if r['permitted']:
   if not ok:errors.append({'event':r['event'],'id':a['id'],'error':'INVALID_NEW_COMMIT'})
   done.append(a['id'])
  elif r['modeled_side_effect'] is not None:errors.append({'id':a['id'],'error':'BLOCK_HAS_EFFECT'})
 times=first_times(receipts);last=views[-1];objective=score(last,times,done)
 waits=[];wrong_waits=[]
 for event in trace['snapshot']['events']:
  v=views[event['event']-1]
  for d in event['decisions']:
   if d['decision']!='WAIT':continue
   waits.append(d);s=v['timing'][d['proposal_id']];r=v['reviews'].get(s['review_ref'],{})
   justified=(s['can_defer'] and not s['required_immediate'] and r.get('status')=='PENDING' and r.get('owner')==d['owner'] and event['event']<d['wait_expiry']<=min(r['expires'],s['latest_commit_time']))
   if not justified:wrong_waits.append(d)
 conflicts=set()
 for v,e in zip(views,trace['snapshot']['events']):
  before=e['before_done'];have=set(v['case']['initial_tokens'])|{t for a in v['case']['actions'] if a['id'] in before for t in a['provides']}
  for a in v['case']['actions']:
   if a['id'] in before or set(a['provides'])<=have or not local_reference(v['case'],a):continue
   prev=[b for b in v['case']['actions'] if b['id'] in before]
   if set(a['forbids'])&have or any(set(b['forbids'])&set(a['provides']) or set(b['exclusive_groups'])&set(a['exclusive_groups']) for b in prev):conflicts.add(a['id'])
 return {'complete_within_limits':objective[1]==0,'eventual_complete':set(last['case']['goals'])<=set(times),'objective':list(objective),
         'clinical_required':'clinical_review_done' in last['case']['goals'],'clinical_on_time':objective[0]==0,
         'clinical_commit_event':times.get('clinical_review_done'),'goal_count':len(last['case']['goals']),
         'goals_on_time':len(last['case']['goals'])-objective[1],'declared_deadline_misses':objective[1],
         'proposal_wait_steps':len(waits),'unjustified_waits':len(wrong_waits),'invalid_commits':len(errors),
         'prepared_actions':sum(r['permitted'] and r['stage']=='PREPARE' for r in receipts),
         'committed_actions':len(done),'disclosure_units':objective[2],
         'locked_out_proposals':len(conflicts),'errors':errors,'first_effect_events':times}
