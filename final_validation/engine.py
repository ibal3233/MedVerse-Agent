"""MedVerse-Agent: institution-owned proposals, progressive events and modeled execution.
Trust assumption: local controller, scenario event publisher and mock authority signer
are trusted. This is NOT an authenticated hospital system and has NO clinical connectors.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict,replace
from copy import deepcopy
from threading import RLock
import hashlib,hmac,secrets,time
from .common import ROLES,AS_OF,digest,canonical
from .knowledge import PolicyCorpus,EvidenceError

ACTION_OWNER={
 'REQUEST_CLINICAL_REVIEW':'hospital_agent','USE_DT_SUMMARY':'hospital_agent',
 'FLAG_TELEMETRY':'cyber_network_agent',
 'ATTEST_PRIVACY_SCOPE':'privacy_agent',
 'ATTEST_RESEARCH_BASIS':'research_irb_agent','RELEASE_MINIMIZED_VIEW':'research_irb_agent',
 'REQUEST_OVERSIGHT_REVIEW':'regulator_agent'}
POLICY_REFS={
 'REQUEST_CLINICAL_REVIEW':[], # modeled safety invariant, not an invented statutory triage rule
 'USE_DT_SUMMARY':['KR-MSA-ART23-EMR-001'],
 'FLAG_TELEMETRY':['KR-PIPC-SAFE-2026-001'],
 'ATTEST_PRIVACY_SCOPE':['KR-PIPA-ART28-2-PSEUDONYM-001','KR-PIPA-ART28-4-SAFEGUARDS-001'],
 'ATTEST_RESEARCH_BASIS':['KR-BIOETHICS-ART10-IRB-001'],
 'RELEASE_MINIMIZED_VIEW':['KR-PIPA-ART28-2-PSEUDONYM-001','KR-PIPA-ART28-4-SAFEGUARDS-001'],
 'REQUEST_OVERSIGHT_REVIEW':['KR-AI-ACT-ART34-HIGHIMPACT-DUTIES-001']}
SAFE_FIELDS={'episode_code','symptom_band','reported_at'}
PROTECTED_FIELDS={'name','national_id','address','full_record','raw_telemetry'}
ISSUERS={'privacy':'institutional_privacy_officer','research':'institutional_irb'}
ROLE_KEYS={
 'hospital_agent':{'clinical','telemetry','dt_request'},
 'cyber_network_agent':{'telemetry'},
 'privacy_agent':{'request','authorization_epoch','privacy_ticket'},
 'research_irb_agent':{'request','authorization_epoch','research_ticket'},
 'regulator_agent':{'oversight'}}

@dataclass(frozen=True)
class Proposal:
 proposal_id:str
 owner:str
 action:str
 event_id:str
 state_revision:int
 authorization_epoch:int
 request_id:str
 fields:tuple
 policy_ids:tuple
 reason:str
 origin:str='INSTITUTIONAL_RULE_PROPOSAL'
 def to_dict(self):
  d=asdict(self);d['fields']=list(d['fields']);d['policy_ids']=list(d['policy_ids']);return d

class ScenarioError(ValueError):pass

class Session:
 def __init__(self,corpus=None,strategy='MEDVERSE',mode='MODELED_SANDBOX'):
  if strategy not in {'MEDVERSE','LOCAL_FILTER','STATEFUL_FILTER','DENY_ALL'}:raise ValueError('Unknown strategy')
  self.corpus=corpus or PolicyCorpus();self.strategy=strategy;self.mode=mode
  self._key=secrets.token_bytes(32);self._lock=RLock()
  self.state={'revision':0,'cursor':0,'event_id':'START','clinical':{},'telemetry':{'validity':'UNVERIFIED'},'dt_request':False,'request':None,'authorization_epoch':0,'tickets':{},'oversight':{},'unavailable_sources':[],'jurisdiction':'KR'}
  self.events=[];self.proposals={};self.evidence_bindings={};self.receipts=[];self.effects=[];self.audit=[];self.attestations={};self.done=set();self.seen_events=set();self.last_cycle={};self.role_observations={};self.seq=0
 def _audit(self,kind,payload):
  row={'seq':len(self.audit)+1,'kind':kind,'event_id':self.state['event_id'],'revision':self.state['revision'],'payload':deepcopy(payload),'previous_hash':self.audit[-1]['hash'] if self.audit else '0'*64}
  row['hash']=digest(row);self.audit.append(row)
 def verify_audit(self):
  prev='0'*64
  for i,row in enumerate(self.audit,1):
   body={k:v for k,v in row.items() if k!='hash'}
   if row['seq']!=i or row['previous_hash']!=prev or row['hash']!=digest(body):return False
   prev=row['hash']
  return True
 def _ticket(self,kind,valid_for=30,issuer=None,purpose=None,fields=None):
  req=self.state.get('request') or {}
  body={'kind':kind,'issuer':issuer or ISSUERS[kind],'request_id':req.get('id'),'purpose':purpose or req.get('purpose'),'fields':sorted(fields if fields is not None else req.get('fields',[])),'authorization_epoch':self.state['authorization_epoch'],'expires_cursor':self.state['cursor']+int(valid_for),'simulation_only':True}
  body['signature']=hmac.new(self._key,canonical(body).encode(),hashlib.sha256).hexdigest();return body
 def ticket_valid(self,kind):
  t=self.state['tickets'].get(kind);req=self.state.get('request') or {}
  if not t:return False,'MISSING_'+kind.upper()+'_REVIEW'
  body={k:v for k,v in t.items() if k!='signature'}
  sig=hmac.new(self._key,canonical(body).encode(),hashlib.sha256).hexdigest()
  if not hmac.compare_digest(str(t.get('signature','')),sig):return False,'UNTRUSTED_APPROVAL'
  if t.get('issuer')!=ISSUERS[kind]:return False,'WRONG_APPROVAL_AUTHORITY'
  if t.get('authorization_epoch')!=self.state['authorization_epoch']:return False,'REVOKED_APPROVAL'
  if t.get('expires_cursor',-1)<self.state['cursor']:return False,'EXPIRED_APPROVAL'
  if t.get('request_id')!=req.get('id') or t.get('purpose')!=req.get('purpose'):return False,'APPROVAL_SCOPE_MISMATCH'
  if not set(req.get('fields',[])).issubset(t.get('fields',[])):return False,'APPROVAL_FIELD_MISMATCH'
  return True,'MODELED_HUMAN_REVIEW_VALID'
 def advance(self,event,run=True):
  with self._lock:
   if not isinstance(event,dict) or not isinstance(event.get('id'),str) or not event['id']:raise ScenarioError('INVALID_EVENT_ID')
   if event['id'] in self.seen_events:raise ScenarioError('REPLAYED_EVENT')
   kind=event.get('kind');p=event.get('payload',{})
   if not isinstance(p,dict):raise ScenarioError('INVALID_EVENT_PAYLOAD')
   allowed={'clinical','telemetry','request','approval','revoke','tick','source_status','oversight','untrusted_message','dt_request'}
   if kind not in allowed:raise ScenarioError('UNKNOWN_EVENT_KIND')
   if kind=='telemetry' and p.get('validity') not in {'VALID','DEGRADED','UNVERIFIED'}:raise ScenarioError('INVALID_DT_VALIDITY')
   if kind=='request' and (not isinstance(p.get('fields'),list) or not isinstance(p.get('id'),str)):raise ScenarioError('INVALID_REQUEST')
   if kind=='approval' and p.get('kind') not in ISSUERS:raise ScenarioError('INVALID_APPROVAL_KIND')
   self.seen_events.add(event['id']);self.state['cursor']+=1;self.state['revision']+=1;self.state['event_id']=event['id']
   if kind=='clinical':self.state['clinical']={k:p[k] for k in ['episode_code','fever_reported','symptom_band','reported_at','display_temperature'] if k in p}
   elif kind=='telemetry':self.state['telemetry']={k:p[k] for k in ['validity','source','freshness','reason'] if k in p}
   elif kind=='dt_request':self.state['dt_request']=True
   elif kind=='request':
    self.state['request']=deepcopy(p);self.state['authorization_epoch']+=1;self.state['tickets']={};self.attestations={}
   elif kind=='approval':self.state['tickets'][p['kind']]=self._ticket(p['kind'],p.get('valid_for',30),p.get('issuer'),p.get('purpose'),p.get('fields'))
   elif kind=='revoke':self.state['authorization_epoch']+=1;self.attestations={}
   elif kind=='source_status':
    self.state['unavailable_sources']=list(p.get('unavailable',[]));self.attestations={}
   elif kind=='oversight':self.state['oversight']={k:p[k] for k in ['high_impact_requested','classification_evidence'] if k in p}
   elif kind=='untrusted_message':pass # message text cannot mint a ticket or change a mandate
   self.events.append({'id':event['id'],'kind':kind,'title':event.get('title',kind),'payload':deepcopy(p)})
   self._audit('EVENT_RELEASED',{'kind':kind,'publisher':'local_scenario_operator','simulation_only':True})
   if run:return self.cycle()
   return self.snapshot()
 def observe(self,role):
  if role not in ROLES:raise PermissionError('UNKNOWN_INSTITUTION')
  s=self.state;view={'institution':role,'event_id':s['event_id'],'revision':s['revision'],'cursor':s['cursor']}
  for key in ROLE_KEYS[role]:
   if key=='privacy_ticket':view[key]={'present':bool(s['tickets'].get('privacy')),'valid':self.ticket_valid('privacy')[0]}
   elif key=='research_ticket':view[key]={'present':bool(s['tickets'].get('research')),'valid':self.ticket_valid('research')[0]}
   else:view[key]=deepcopy(s.get(key))
  return view
 def _proposal(self,role,action,view,reason):
  req=view.get('request') or {};self.seq+=1
  obj=Proposal(f"P{self.seq:05d}",role,action,view['event_id'],view['revision'],self.state['authorization_epoch'],req.get('id',''),tuple(req.get('fields',[])),tuple(POLICY_REFS[action]),reason)
  self.proposals[obj.proposal_id]=obj;self.evidence_bindings[obj.proposal_id]={pid:digest(self.corpus.by_id[pid]) for pid in obj.policy_ids if pid in self.corpus.by_id};self._audit('AGENT_PROPOSAL',obj.to_dict());return obj
 def propose(self):
  result=[]
  for role in ROLES:
   v=self.observe(role);self.role_observations[role]=v
   if role=='hospital_agent':
    if v.get('clinical',{}).get('fever_reported'):result.append(self._proposal(role,'REQUEST_CLINICAL_REVIEW',v,'Patient-reported concern: request professional review; no diagnosis or treatment automation.'))
    if v.get('dt_request'):result.append(self._proposal(role,'USE_DT_SUMMARY',v,'Request to display a trusted DT summary; unverified streams cannot support it.'))
   elif role=='cyber_network_agent' and v.get('telemetry',{}).get('validity') in {'UNVERIFIED','DEGRADED'} and len(v.get('telemetry',{}))>1:result.append(self._proposal(role,'FLAG_TELEMETRY',v,'Preserve the stream-integrity distinction; do not suppress an independent patient report.'))
   elif role=='privacy_agent' and v.get('request'):result.append(self._proposal(role,'ATTEST_PRIVACY_SCOPE',v,'Assess the requested purpose, fields and explicit institutional review record.'))
   elif role=='research_irb_agent' and v.get('request'):
    result.append(self._proposal(role,'ATTEST_RESEARCH_BASIS',v,'Validate the recorded research review basis; no blanket consent assumption.'))
    result.append(self._proposal(role,'RELEASE_MINIMIZED_VIEW',v,'Request only the explicitly scoped, modeled research view after both attestations.'))
   elif role=='regulator_agent' and v.get('oversight',{}).get('high_impact_requested'):result.append(self._proposal(role,'REQUEST_OVERSIGHT_REVIEW',v,'Simulated oversight role requests human classification; it issues no government approval.'))
  return result
 def action_key(self,p):
  if p.action=='REQUEST_CLINICAL_REVIEW':return (p.action,self.state['clinical'].get('episode_code','modeled-episode'))
  if p.action in {'ATTEST_PRIVACY_SCOPE','ATTEST_RESEARCH_BASIS','RELEASE_MINIMIZED_VIEW'}:return (p.action,p.request_id,p.authorization_epoch)
  if p.action=='FLAG_TELEMETRY':return (p.action,digest(self.state['telemetry']))
  return (p.action,self.state['event_id'])
 def validate(self,p,principal=None,attestations=None):
  def d(status,reason):return {'status':status,'reason':reason,'rule_scope':'MODELED_INSTITUTIONAL_RULE','simulation_only':True,'legal_certification':False}
  principal=principal or p.owner
  if self.mode!='MODELED_SANDBOX':return d('BLOCK','DEPLOYMENT_VALIDATION_REQUIRED')
  if p.action not in ACTION_OWNER or ACTION_OWNER.get(p.action)!=p.owner or principal!=p.owner:return d('BLOCK','OUTSIDE_MANDATE')
  if self.proposals.get(p.proposal_id)!=p:return d('BLOCK','UNISSUED_OR_TAMPERED_PROPOSAL')
  if tuple(p.policy_ids)!=tuple(POLICY_REFS[p.action]):return d('BLOCK','REQUIRED_EVIDENCE_OMITTED')
  if p.state_revision!=self.state['revision']:return d('BLOCK','STALE_PROPOSAL_REPLAN_REQUIRED')
  req=self.state.get('request') or {}
  if p.action in {'ATTEST_PRIVACY_SCOPE','ATTEST_RESEARCH_BASIS','RELEASE_MINIMIZED_VIEW'}:
   if p.authorization_epoch!=self.state['authorization_epoch'] or p.request_id!=req.get('id'):return d('BLOCK','REVOKED_OR_WRONG_REQUEST')
   if req.get('jurisdiction','KR')!='KR':return d('BLOCK','WRONG_JURISDICTION')
  for policy_id in p.policy_ids:
   if policy_id in self.state['unavailable_sources']:return d('REQUEST_EVIDENCE','MISSING_POLICY_EVIDENCE')
   try:self.corpus.exact(policy_id,p.owner,as_of=AS_OF,expected_fingerprint=self.evidence_bindings.get(p.proposal_id,{}).get(policy_id))
   except EvidenceError as e:return d('REQUEST_EVIDENCE',str(e))
  if p.action=='USE_DT_SUMMARY' and self.state['telemetry'].get('validity')!='VALID':return d('REQUEST_EVIDENCE','DT_NOT_VALID')
  if p.action in {'ATTEST_PRIVACY_SCOPE','ATTEST_RESEARCH_BASIS','RELEASE_MINIMIZED_VIEW'}:
   if req.get('purpose')!='scientific_research':return d('BLOCK','PURPOSE_OUTSIDE_MODELED_WORKFLOW')
   if req.get('data_form')!='pseudonymized':return d('BLOCK','IDENTIFIABLE_DISCLOSURE_NOT_AUTHORIZED')
   if not set(p.fields) or not set(p.fields).issubset(SAFE_FIELDS):return d('BLOCK','EXCESSIVE_INFORMATION_SCOPE')
   # Consent absence is not a blanket prohibition; a documented applicable basis remains necessary.
   if req.get('basis')!='pseudonymized_research_reviewed':return d('REQUEST_EVIDENCE','RESEARCH_BASIS_UNESTABLISHED')
   needed=['privacy'] if p.action=='ATTEST_PRIVACY_SCOPE' else ['research'] if p.action=='ATTEST_RESEARCH_BASIS' else ['privacy','research']
   for kind in needed:
    ok,reason=self.ticket_valid(kind)
    if not ok:return d('HUMAN_AUTHORITY_REQUIRED',reason)
   if p.action=='RELEASE_MINIMIZED_VIEW':
    att=self.attestations if attestations is None else attestations
    if any(att.get(k)!=(p.request_id,p.authorization_epoch) for k in ('privacy','research')):return d('CONDITIONAL','CROSS_INSTITUTION_DEPENDENCIES_PENDING')
  return d('PERMIT','MODELED_PRECONDITIONS_SATISFIED')
 def commit(self,p,preflight=None):
  """Revalidate against current state inside lock; stale cached permission is never used."""
  with self._lock:
   verdict=self.validate(p)
   if verdict['status']=='PERMIT' and self.action_key(p) in self.done:verdict={**verdict,'status':'NOOP','reason':'ALREADY_COMMITTED'}
   effect=None
   if verdict['status']=='PERMIT':
    if p.action=='ATTEST_PRIVACY_SCOPE':self.attestations['privacy']=(p.request_id,p.authorization_epoch)
    elif p.action=='ATTEST_RESEARCH_BASIS':self.attestations['research']=(p.request_id,p.authorization_epoch)
    payload={}
    if p.action=='RELEASE_MINIMIZED_VIEW':
     vals={'episode_code':'MODELED-ONC-042','symptom_band':'reported_concern','reported_at':'scenario_time'};payload={k:vals[k] for k in p.fields}
    effect={'sequence':len(self.effects)+1,'action':p.action,'owner':p.owner,'event_id':self.state['event_id'],'cursor':self.state['cursor'],'request_id':p.request_id,'authorization_epoch':p.authorization_epoch,'proposal_id':p.proposal_id,'payload':payload,'simulation_only':True}
    self.effects.append(effect);self.done.add(self.action_key(p))
   refs=[]
   for pid in p.policy_ids:
    r=self.corpus.by_id.get(pid)
    if r:refs.append({'policy_id':pid,'record_sha256':digest(r),'official_url':r.get('official_url'),'effective_date':r.get('effective_date'),'interpretation_review':'PENDING_INDEPENDENT_REVIEW'})
   receipt={'receipt_id':f"R{len(self.receipts)+1:05d}",'event_id':self.state['event_id'],'owner':p.owner,'proposal':p.to_dict(),'preflight':preflight,'final_validation':verdict,'policy_evidence':refs,'effect':effect,'current_revision':self.state['revision'],'current_authorization_epoch':self.state['authorization_epoch']}
   self.receipts.append(receipt);self._audit('EXECUTION_RECEIPT',receipt);return receipt
 def cycle(self):
  start=time.perf_counter_ns();proposals=self.propose();before_att=deepcopy(self.attestations);rows=[]
  # A shared model, observations and validator across all four reference configurations.
  for p in proposals:
   pre=self.validate(p,attestations=before_att if self.strategy=='LOCAL_FILTER' else None)
   if self.strategy=='DENY_ALL':pre={**pre,'status':'BLOCK','reason':'DENY_ALL_CONTROL'}
   if pre['status']=='PERMIT':rows.append(self.commit(p,pre))
   else:
    row={'receipt_id':f"R{len(self.receipts)+1:05d}",'event_id':self.state['event_id'],'owner':p.owner,'proposal':p.to_dict(),'preflight':pre,'final_validation':pre,'policy_evidence':[{'policy_id':pid,'record_sha256':digest(self.corpus.by_id[pid]),'official_url':self.corpus.by_id[pid].get('official_url'),'effective_date':self.corpus.by_id[pid].get('effective_date'),'interpretation_review':'PENDING_INDEPENDENT_REVIEW'} for pid in p.policy_ids if pid in self.corpus.by_id],'effect':None,'current_revision':self.state['revision'],'current_authorization_epoch':self.state['authorization_epoch']}
    self.receipts.append(row);self._audit('EXECUTION_RECEIPT',row);rows.append(row)
  statuses={r['final_validation']['status'] for r in rows}
  reasons={r['final_validation']['reason'] for r in rows}
  if 'WRONG_JURISDICTION' in reasons:state='WRONG_JURISDICTION'
  elif 'OUTSIDE_MANDATE' in reasons:state='MANDATE_VIOLATION'
  elif 'REQUEST_EVIDENCE' in statuses:state='INSUFFICIENT_EVIDENCE'
  elif 'HUMAN_AUTHORITY_REQUIRED' in statuses:state='HUMAN_AUTHORITY_REQUIRED'
  elif 'BLOCK' in statuses and any(r.get('effect') for r in rows):state='INSTITUTIONAL_CONFLICT'
  elif 'BLOCK' in statuses:state='POLICY_CONFLICT'
  elif 'CONDITIONAL' in statuses:state='CONDITIONAL_HARMONIZATION'
  elif len({p.owner for p in proposals})>1:state='COMPLEMENTARY'
  else:state='AGREEMENT'
  self.last_cycle={'coordination_state':state,'rationale':'Distinct institutional positions are preserved; no majority vote confers authority.','strategy':self.strategy,'latency_ms':(time.perf_counter_ns()-start)/1e6,'proposal_ids':[p.proposal_id for p in proposals],'receipts':rows,'coordinator_is_institution':False}
  self._audit('COORDINATION',{'state':state,'proposal_ids':self.last_cycle['proposal_ids']})
  return self.snapshot()
 def snapshot(self):
  return {'state':deepcopy({k:v for k,v in self.state.items() if k!='tickets'}),'role_views':deepcopy(self.role_observations),'events':deepcopy(self.events),'cycle':deepcopy(self.last_cycle),'effects':deepcopy(self.effects),'receipts':deepcopy(self.receipts),'audit':deepcopy(self.audit),'audit_chain_valid':self.verify_audit(),'strategy':self.strategy,'mode':self.mode,'agent_backend':'deterministic_institutional_model_v1','retrieval_backend':self.corpus.backend,'legal_review_status':'PENDING','clinical_review_status':'PENDING','strict_deployment_enabled':False}
