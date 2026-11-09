"""Operator workbench for the unchanged Gate 32 engine.
The trusted fixture feeder stores a script, but sends only one released event to Session.
The controller never receives family/branch IDs, reference outcomes, or later events.
"""
from copy import deepcopy as cp
from commitment32.runtime import Session,verify_receipts
from commitment32.common import digest
from coordination29.validator import validate
from .common import ROLES,STRATEGIES,families

class WorkspaceError(ValueError):pass

class Workspace:
 def __init__(self,family_id='P01',branch_id='PROMPT',strategy='MEDVERSE_COMMITMENT'):
  if strategy not in STRATEGIES:raise WorkspaceError('UNKNOWN_STRATEGY')
  f=next((f for f in families() if f['family_id']==family_id),None)
  if f is None:raise WorkspaceError('UNKNOWN_FAMILY')
  b=next((b for b in f['branches'] if b['branch_id']==branch_id),None)
  if b is None:raise WorkspaceError('UNKNOWN_CONTINUATION')
  self.family=cp(f);self.branch=cp(b);self.engine=Session(strategy);self.ui_log=[];self.next_index=0
 def _expected(self,expected):
  if type(expected) is not int or expected!=self.engine.publisher.case['cursor']:raise WorkspaceError('STALE_EVENT_CURSOR')
 def advance(self,expected,auto_commit=True):
  self._expected(expected)
  if type(auto_commit) is not bool:raise WorkspaceError('AUTO_COMMIT_MUST_BE_BOOLEAN')
  if self.engine.pending:raise WorkspaceError('RESOLVE_PENDING_PLAN_FIRST')
  if self.next_index>=len(self.branch['events']):raise WorkspaceError('END_OF_RELEASED_SEQUENCE')
  # A single already-released event is the entire input to the original online engine.
  event=cp(self.branch['events'][self.next_index]);plan=self.engine.begin(event);self.next_index+=1
  self.ui_log.append({'operation':'release','clock':event['clock'],'released_event_hash':digest(event),'auto_commit':auto_commit})
  if auto_commit:self.engine.commit(plan['plan_id'])
  return self.snapshot()
 def commit(self,plan_id):
  if not isinstance(plan_id,str):raise WorkspaceError('PLAN_ID_REQUIRED')
  self.engine.commit(plan_id);self.ui_log.append({'operation':'commit_pending','clock':self.engine.publisher.case['cursor']})
  return self.snapshot()
 def change(self,kind):
  self.engine.change_before_commit(kind);self.ui_log.append({'operation':'modeled_change','kind':kind,'clock':self.engine.publisher.case['cursor']})
  return self.snapshot()
 def cancel(self):
  if not self.engine.pending:raise WorkspaceError('NO_PENDING_PLAN')
  pid=self.engine.pending['plan_id'];self.engine.pending=None
  self.ui_log.append({'operation':'cancel_uncommitted_plan','plan_id':pid,'clock':self.engine.publisher.case['cursor'],'undo_committed_effects':False})
  return self.snapshot()
 def roles(self):
  x=self.engine;c=x.publisher.case
  decisions=[d for e in x.events for d in e['decisions']]+(x.pending['decisions'] if x.pending else [])
  out={}
  for role in ROLES:
   own=[a for a in c['actions'] if a['owner']==role];ids={a['id'] for a in own};rr=[r for r in x.receipts if r['owner']==role];dd=[d for d in decisions if d['owner']==role]
   gr={g for a in own for g in a['grant_ids']};ev={v for a in own for v in a['evidence']}
   out[role]={'role':role,'inspection_scope':'OPERATOR_ONLY; not inter-agent data sharing or real institutional authentication',
    'observed_contracts':cp(own),'reviews':{k:cp(v) for k,v in x.publisher.reviews.items() if v['owner']==role},
    'timing':{k:cp(v) for k,v in x.publisher.timing.items() if k in ids},
    'authority_records':{k:cp(v) for k,v in c['authority_register'].items() if k in gr},
    'evidence_refs':sorted(ev),'decisions':cp(dd),'receipts':cp(rr),
    'counts':{'released_proposals':len(own),'decision_opportunities':len(dd),'wait_decisions':sum(d['decision']=='WAIT' for d in dd),
      'prepare_effects':sum(r['permitted'] and r['stage']=='PREPARE' for r in rr),
      'commit_effects':sum(r['permitted'] and r['stage']=='COMMIT' for r in rr),
      'blocked_or_escalated_decisions':sum(d['decision'] in ('BLOCK','ESCALATE') for d in dd)},
    'activity':'ACTIVE' if own else 'NO_RELEASED_OWNED_PROPOSAL'}
  return out
 def snapshot(self):
  x=self.engine;s=x.snapshot();c=x.publisher.case
  latest=x.pending['decisions'] if x.pending else (x.events[-1]['decisions'] if x.events else [])
  dmap={d['proposal_id']:d for d in latest};rows=[]
  for a in c['actions']:
   d=dmap.get(a['id']);rr=[r for r in x.receipts if r['proposal_id']==a['id']]
   ok,why=validate(c,a,x.done)
   effect=next((r for r in rr if r['permitted']),None)
   rows.append({'id':a['id'],'owner':a['owner'],'kind':a['kind'],'purpose':a['purpose'],'recipient':a['recipient'],
    'provides':a['provides'],'needs':a['needs'],'fields':a['fields'],'evidence':a['evidence'],
    'timing_contract':cp(x.publisher.timing.get(a['id'])),'decision':cp(d),
    'current_validation':{'permitted_now':ok,'reason':why},
    'actual_effect':{'stage':effect['stage'],'event':effect['event'],'receipt_sequence':effect['sequence']} if effect else None,
    'last_receipt':cp(rr[-1]) if rr else None})
  goals=[]
  for g in c['goals']:
   receipt=next((r for r in x.receipts if r['permitted'] and g in r['modeled_side_effect']['tokens']),None)
   deadline=x.publisher.deadlines.get(g)
   goals.append({'goal':g,'declared_limit':deadline,'commit_event':receipt['event'] if receipt else None,
    'status':('ACHIEVED_WITHIN_LIMIT' if deadline is None or receipt['event']<=deadline else 'ACHIEVED_LATE') if receipt else ('LIMIT_PASSED' if deadline is not None and c['cursor']>deadline else 'NOT_YET_ACHIEVED')})
  event_summaries=[]
  for h in x.publisher.history:
   if 'actions' in h:event_summaries.append({'clock':h['clock'],'proposals_released':len(h.get('actions',[])),
    'authority_records_released':len(h.get('grants',{})),'review_updates':len(h.get('reviews',{})),
    'context_transfers':len(h.get('envelopes',{}))})
  return {'release':'Gate33','family_id':self.family['family_id'],'family_title':self.family['title'],
    'continuation_id':self.branch['branch_id'],'operator_fixture_choice_not_controller_input':True,
    'strategy':x.strategy,'clock':c['cursor'],'max_events':len(self.branch['events']),
    'model_status':'SCENARIO-MODELED; CONTRACT REVIEW PENDING',
    'engine_state_hash':digest(s),'visible_history_hash':x.view()['released_history_hash'],
    'pending_plan_id':x.pending['plan_id'] if x.pending else None,'proposal_rows':rows,
    'goals':goals,'roles':self.roles(),'decisions':cp(latest),'events':cp(x.events),
    'released_event_summaries':event_summaries,'receipts':cp(x.receipts),'receipt_chain_valid':verify_receipts(x.receipts),
    'committed_ids':list(x.done),'achieved_tokens':s['achieved'],
    'reviews':cp(x.publisher.reviews),'envelopes':cp(c['envelopes']),
    'authority_epoch':c['epoch'],'simulation_only':True,'clinical_legal_review':'PENDING',
    'source_evidence_note':'Source-derived records are not clinical timing approval. Exact evidence is checked separately; retrieval cannot authorize execution.',
    'timing_units':'Declared model event steps, not minutes or clinical recommendations',
    'online_input_boundary':'Controller sees released contract metadata only. Future continuation labels are operator fixture controls, not policy inputs.'}
 def export(self):
  return {'release':'Gate33','family_id':self.family['family_id'],'continuation_id':self.branch['branch_id'],
    'strategy':self.engine.strategy,'runtime_trace':self.engine.export(), 'presentation_snapshot':self.snapshot(),
    'operator_operations':cp(self.ui_log),'future_events_included':False,'modeling_scope':'Review-pending timing contracts; simulated effects only.'}
