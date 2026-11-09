"""Fixed release schedule, not a predictor or a new clinical protocol.

Every source family is already known from Gate 29. These releases test integration,
not new-law generalization. The schedule does not depend on reference outcomes.
"""
from copy import deepcopy
from .common import ROLES
TITLE={1:'Clinical concern registered',2:'Clinical–cyber responsibilities released',3:'Original research request received',4:'Digital Twin context transferred',5:'Institution-owned alternatives and scoped reviews',6:'Research authority records released'}
EXPLANATION={1:'Only the Hospital observation is visible. No unreleased workflow contracts or authority records are supplied to the selector.',2:'Released clinical and technical contracts are evaluated. Containment cannot assume clinical authority.',3:'The original research purpose, requested scope and corresponding records become available. Clinical work is not research permission.',4:'Receiving-side Digital Twin checks assess the transferred context; a valid-looking label alone is insufficient.',5:'Alternative proposals are released by their owning institutions. Privacy and non-research authority records are available; research attestations may still be pending.',6:'The remaining modeled research-authority records are released. Their original APPROVED, DENIED or PENDING state is retained.'}
def action_phase(a):
 if a['priority']=='ALTERNATIVE':return 5
 if a['kind'] in {'CLINICAL_REVIEW','QUARANTINE_STREAM','HANDOFF_ACK'}:return 2
 if a['kind'] in {'PRIVACY_ATTEST','RESEARCH_ATTEST','RESEARCH_VIEW'}:return 3
 return 4

def released_input(source,phase):
 """No private observations, family labels, future records or reference scores enter selection."""
 keys=('jurisdiction','policy_snapshot','epoch','freshness_events','initial_tokens','field_constraints')
 c={k:deepcopy(source[k]) for k in keys}
 c['cursor']=phase
 c.update(actions=[],goals=[],task_purposes=[],adequacy={},facts={},authority_register={},authority_register_hashes={},evidence_register={},envelopes={},trusted_envelope_hashes=[])
 if phase==0:return c
 acts=[deepcopy(a) for a in source['actions'] if action_phase(a)<=phase]
 c['actions']=acts
 if phase>=2:c['facts']=deepcopy(source['facts'])
 # A goal becomes known when one of its owning proposals is released, not by reading future proposals.
 provided={t for a in acts for t in a['provides']}
 c['goals']=[g for g in source['goals'] if g in provided]
 c['task_purposes']=sorted({a['purpose'] for a in acts})
 c['adequacy']={a['task']:deepcopy(source['adequacy'][a['task']]) for a in acts}
 for a in acts:
  for e in a['evidence']:
   if e in source['evidence_register']:c['evidence_register'][e]=deepcopy(source['evidence_register'][e])
  for g in a['grant_ids']:
   # Alternative research review/dispatch is not supplied before the final event.
   release=max(action_phase(a),6 if a['priority']=='ALTERNATIVE' and a['owner']=='research_irb_agent' else 0)
   if release<=phase and g in source['authority_register']:
    c['authority_register'][g]=deepcopy(source['authority_register'][g])
    if g in source['authority_register_hashes']:c['authority_register_hashes'][g]=source['authority_register_hashes'][g]
  e=a['envelope_id']
  if e and e in source['envelopes']:
   c['envelopes'][e]=deepcopy(source['envelopes'][e])
 # Published trusted hashes only for currently released envelope records.
 from .common import digest
 c['trusted_envelope_hashes']=[digest(e) for e in c['envelopes'].values() if digest(e) in source['trusted_envelope_hashes']]
 # Contract constraints are public task metadata, not clinical observations; they are
 # released only when a matching recipient and relevant fields enter the visible task.
 recipients={a['recipient'] for a in acts}
 c['field_constraints']=[r for r in c['field_constraints'] if r['recipient'] in recipients]
 return c

def role_view(source,phase,role,receipts):
 if role not in ROLES:raise ValueError('UNKNOWN_INSTITUTION')
 first={'hospital_agent':1,'cyber_network_agent':2,'privacy_agent':3,'research_irb_agent':3,'regulator_agent':4}[role]
 observation=deepcopy(source.get('operator_private_views',{}).get(role,{})) if phase>=first else {}
 released=released_input(source,phase)
 actions=[a for a in released['actions'] if a['owner']==role]
 refs=sorted({e for a in actions for e in a['evidence']})
 # Local operator inspection is NOT a production peer identity system.
 return {'role':role,'label':ROLES[role],'released_event':phase,'observation':observation,'own_proposals':actions,'candidate_evidence_ids':refs,'own_receipts':[r for r in receipts if r['owner']==role],
         'access_boundary':'Operator-inspected institutional projection. No real authentication or peer transport claim.'}
