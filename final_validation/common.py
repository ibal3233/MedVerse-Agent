from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/final_validation'
OUT=ROOT/'outputs/final_validation'
ROLES=('hospital_agent','cyber_network_agent','privacy_agent','research_irb_agent','regulator_agent')
LABELS=dict(zip(ROLES,('Hospital','Cyber / Network','Privacy','Research / IRB','Regulator')))
AS_OF='2026-11-03'
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def filehash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))
