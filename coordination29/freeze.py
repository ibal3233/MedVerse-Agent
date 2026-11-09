"""Administrative one-time freeze; not invoked by the experiment runner."""
from __future__ import annotations
from datetime import datetime,timezone
from .common import ROOT,DATA,save,filehash,load


def freeze():
    target=DATA/'freeze_manifest.json'
    if target.exists():raise FileExistsError('Freeze already exists; do not overwrite after outcomes.')
    files=[]
    for folder in ('coordination29','docs/coordination29','data/coordination29'):
        files += [p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    files += [ROOT/'medverse/gates/gate29_institutional_workflow_choice.py',ROOT/'GATE29_START_HERE.md',
              ROOT/'data/policy/candidate_v0.4/policy_records_v0.4_candidate.json']
    groups=load(DATA/'scenario_families.json')['families']
    save(target,{'version':'1.0.0','gate':'GATE_29_INSTITUTIONAL_WORKFLOW_CHOICE',
                 'frozen_utc':datetime.now(timezone.utc).isoformat(),
                 'confirmation_outcomes_seen':False,'training':False,
                 'splits':{s:sum(c['split']==s for c in groups) for s in ('DEVELOPMENT','CONFIRMATION')},
                 'interpretation_review':'PENDING','files':{str(p.relative_to(ROOT)):filehash(p) for p in sorted(files)}})
    return load(target)

if __name__=='__main__':
    x=freeze();print('Frozen',len(x['files']),'files before confirmation.')
