from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/coordination30'
OUT=ROOT/'outputs/gate30_integration'
ROLES={'hospital_agent':'Hospital','cyber_network_agent':'Cyber / Network','privacy_agent':'Privacy','research_irb_agent':'Research / IRB','regulator_agent':'Regulator'}
STRATEGIES=('REQUEST_ONLY','FAIR_STATEFUL_SELECTOR','INDEPENDENT_CONSTRAINT_PLANNER','MEDVERSE_HARMONIZER')
LABELS={'REQUEST_ONLY':'Requested path only','FAIR_STATEFUL_SELECTOR':'Fair stateful selector','INDEPENDENT_CONSTRAINT_PLANNER':'Independent constraint planner','MEDVERSE_HARMONIZER':'MedVerse harmonizer'}
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def canonical(o):return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(o):return hashlib.sha256(canonical(o).encode()).hexdigest()
def filehash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_cases():return load(ROOT/'data/coordination29/scenario_families.json')['families']
