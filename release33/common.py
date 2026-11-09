from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/release33'
OUT=ROOT/'outputs/gate33_workspace'
WEB=ROOT/'release33/web'
ROLES=('hospital_agent','cyber_network_agent','privacy_agent','research_irb_agent','regulator_agent')
ROLE_NAMES=dict(zip(ROLES,('Hospital','Cyber / Network','Privacy','Research / IRB','Regulator')))
STRATEGIES={'EAGER':'Eager commitment','FAIR_BOUNDED_WAIT':'Fair bounded wait','MEDVERSE_COMMITMENT':'MedVerse commitment'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def filehash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def families():return read(ROOT/'data/commitment32/prefix_families.json')['families']
def verify_freeze():
 from commitment32.evaluate import verify_freeze as verify32
 verify32()
 m=read(DATA/'freeze.json')
 for path,h in m['files'].items():
  if not (ROOT/path).is_file() or filehash(ROOT/path)!=h:raise RuntimeError('GATE33_FROZEN_FILE_MISMATCH: '+path)
 prior=read(DATA/'predecessor_manifest.json')
 for path,h in prior.items():
  if not (ROOT/path).is_file() or filehash(ROOT/path)!=h:raise RuntimeError('PREDECESSOR_FILE_CHANGED: '+path)
 return m,len(prior)
