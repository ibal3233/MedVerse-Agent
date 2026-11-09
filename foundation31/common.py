from __future__ import annotations
from pathlib import Path
import hashlib, json
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/foundation31'
OUT = ROOT / 'outputs/gate31_foundation'
MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
REVISION = 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
AS_OF = '2026-11-03'
CORPUS = ROOT / 'data/policy/candidate_v0.4/policy_records_v0.4_candidate.json'
ROLES = ('hospital_agent','cyber_network_agent','privacy_agent','research_irb_agent','regulator_agent')
def canonical(x): return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()
def filehash(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
