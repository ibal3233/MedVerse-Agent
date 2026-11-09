"""One-time administrative freeze; never called automatically by the runner."""
from datetime import datetime,timezone
from .common import ROOT,DATA,load,save,filehash
FILES=['coordination30/common.py','coordination30/schedule.py','coordination30/engine.py','coordination30/evidence.py','coordination30/server.py','coordination30/client.py','coordination30/tests.py','coordination30/evaluate.py','docs/coordination30/PROTOCOL.md','run_integrated_sandbox.py']
def create():
 path=DATA/'freeze_manifest.json'
 if path.exists():raise FileExistsError('Freeze already exists. No outcome-driven re-freeze.')
 # UI is a separate presentation surface; implementation errors must remain versioned.
 save(path,{'gate':'GATE_30_INTEGRATED_RELEASE','frozen_utc':datetime.now(timezone.utc).isoformat(),'known_data_regression':True,'evaluation_executed':False,'files':{p:filehash(ROOT/p) for p in FILES},'prior_gate29_manifest_sha256':filehash(ROOT/'data/coordination29/freeze_manifest.json')})
def verify():
 m=load(DATA/'freeze_manifest.json');bad=[p for p,h in m['files'].items() if not (ROOT/p).is_file() or filehash(ROOT/p)!=h]
 if bad:raise RuntimeError('Frozen integration files changed: '+', '.join(bad))
 from coordination29.evaluate import verify_freeze
 verify_freeze()
 return m
