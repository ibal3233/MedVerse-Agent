# Gate 12 — Authoritative Policy-KB Expansion

## Purpose
Close the policy-grounding gap identified after Gate 11C for:
- Privacy Agent
- Research/IRB Agent
- Regulator Agent

## Authoritative source families

### Privacy
Personal Information Protection Act:
- Article 17 — third-party provision
- Article 18 — restrictions on use/provision beyond original purpose

### Research/IRB
Bioethics and Safety Act:
- Article 16 — human-subject research consent
- Article 37 — consent scope and withdrawal for human-derived-material research

### Regulator
Digital Medical Products Act / Enforcement Rule:
- Article 2 — regulated digital medical device scope
- Enforcement Rule Article 14 — safety review materials including software verification/validation and cyber-protection evidence

## Important interpretation boundary
The regulator sources support regulated scope, safety evidence, validation, and oversight.

They do NOT literally state the MedVerse sandbox action:
`BLOCK_AUTOMATED_HIGH_IMPACT_ACTION until fresh DT verification`.

That action remains a system-level governance control derived conservatively from
validated evidence/oversight principles and is not represented as a direct statutory quote.

## Retrieval
Multilingual semantic retrieval with:
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

KB version: 0.3

## PASS criteria
- Korean and English queries retrieve an authorized relevant record for each new agent
- Korean/English top-1 agreement for each agent
- no cross-agent partition leakage
- provenance metadata complete
- translation status explicit
- regulator mapping does not overclaim literal statutory requirements
- semantic replay stable

## Next action
PASS -> run final policy-grounding campaign (Gate 13) and compute PGA for S2-S4.
FAIL -> diagnose only policy data/retrieval/provenance; do not alter operational benchmark results.
