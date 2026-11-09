"""Shared data and canonical serialization. No model or external network is required."""
from __future__ import annotations
import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/commitment32'
OUT=ROOT/'outputs/gate32_commitment'
STRATEGIES=('EAGER','FAIR_BOUNDED_WAIT','MEDVERSE_COMMITMENT')
LABELS={'EAGER':'Eager commit','FAIR_BOUNDED_WAIT':'Fair bounded wait','MEDVERSE_COMMITMENT':'MedVerse commitment'}
ROLES=('hospital_agent','cyber_network_agent','privacy_agent','research_irb_agent','regulator_agent')
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def digest(x):return hashlib.sha256(canonical(x).encode('utf-8')).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,x):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def hashfile(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def fresh_case():
 return {'jurisdiction':'KR','policy_snapshot':'G32-MODELED-1','epoch':1,'cursor':0,'freshness_events':2,
 'initial_tokens':[],'actions':[],'goals':[],'task_purposes':[],'adequacy':{},'facts':{},
 'authority_register':{},'authority_register_hashes':{},'evidence_register':{},'field_constraints':[],
 'envelopes':{},'trusted_envelope_hashes':[]}
