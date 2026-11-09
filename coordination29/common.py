"""Serialization and experiment schema; no evaluation labels are planner inputs."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/coordination29'
OUT = ROOT / 'outputs/gate29_workflow_choice'
OWNERS = {
    'CLINICAL_REVIEW': 'hospital_agent',
    'QUARANTINE_STREAM': 'cyber_network_agent',
    'HANDOFF_ACK': 'hospital_agent',
    'PRIVACY_ATTEST': 'privacy_agent',
    'RESEARCH_ATTEST': 'research_irb_agent',
    'RESEARCH_VIEW': 'research_irb_agent',
    'DT_RECEIVE': 'hospital_agent',
    'OVERSIGHT_ATTEST': 'regulator_agent',
}
EVIDENCE_IDS = {
    'CLINICAL_REVIEW': [],  # explicitly a modeled care-continuity obligation
    'QUARANTINE_STREAM': ['KR-PIPC-SAFE-2026-001'],
    'HANDOFF_ACK': [],
    'PRIVACY_ATTEST': ['KR-PIPA-ART28-2-PSEUDONYM-001', 'KR-PIPA-ART28-4-SAFEGUARDS-001'],
    'RESEARCH_ATTEST': ['KR-BIOETHICS-ART10-IRB-001'],
    'RESEARCH_VIEW': ['KR-PIPA-ART28-2-PSEUDONYM-001', 'KR-PIPA-ART28-4-SAFEGUARDS-001'],
    'DT_RECEIVE': ['KR-MSA-ART23-EMR-001'],
    'OVERSIGHT_ATTEST': ['KR-AI-ACT-ART34-HIGHIMPACT-DUTIES-001'],
}
STRATEGIES = ('REQUEST_ONLY', 'FAIR_STATEFUL_SELECTOR', 'INDEPENDENT_CONSTRAINT_PLANNER', 'MEDVERSE_HARMONIZER')
LABELS = {
    'REQUEST_ONLY': 'Requested path\nonly',
    'FAIR_STATEFUL_SELECTOR': 'Fair stateful\nselector',
    'INDEPENDENT_CONSTRAINT_PLANNER': 'Independent\nconstraint planner',
    'MEDVERSE_HARMONIZER': 'MedVerse\nharmonizer',
}
ENVELOPE_KEYS = ('dt_ref','data_version','observed_event','provenance_ref','validity','purpose','recipient','fields','policy_snapshot','authority_epoch','expires_event')

def canonical(x: Any) -> str:
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def digest(x: Any) -> str:
    return hashlib.sha256(canonical(x).encode('utf-8')).hexdigest()

def filehash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def save(path: Path, value: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')

def tokens(case: dict, chosen: tuple | frozenset | list) -> set:
    selected = set(chosen)
    return set(case['initial_tokens']).union(*(set(a['provides']) for a in case['actions'] if a['id'] in selected))

def outcome(case: dict, chosen: tuple | list | frozenset) -> tuple:
    """Frozen lexicographic objective. Violations are never utility penalties."""
    achieved = tokens(case, chosen)
    missing = len(set(case['goals']) - achieved)
    # Disclosure units count unique modeled payload fields per recipient, not patient leaks.
    exposed = {(a['recipient'], f) for a in case['actions'] if a['id'] in chosen for f in a['fields']}
    protected_missing = int('clinical_review_done' in case['goals'] and 'clinical_review_done' not in achieved)
    return protected_missing, missing, len(exposed), len(chosen)
