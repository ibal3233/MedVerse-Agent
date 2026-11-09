# Gate 11C — Final Operational Benchmark Campaign for S2-S4

## Purpose
Generate reproducible final operational evidence for the three scenario
families validated in Gate 11B.

## Frozen
- Gates 0-11B
- S2-S4 deterministic semantics
- B1/B2/B3
- 10 deterministic repetitions
- Gate 10 reporting rules

## Metrics scored
- ARA
- MCR
- CSR
- CDR
- EAR
- ILR

## PGA boundary
PGA is deliberately NOT scored for S2-S4 in Gate 11C.

Reason:
the current authoritative policy knowledge base was validated only for the
Hospital and Cyber/Network agents. Privacy, Research/IRB and Regulator policy
records have not yet undergone source/provenance/retrieval validation.

Reporting `PGA=1` for S2-S4 at this stage would fabricate evidence.

## Campaign size
3 scenario variants x 10 repetitions x 3 systems = 90 raw rows.

## PASS criteria
- 90 raw rows
- deterministic replay exact
- MedVerse ARA=1
- MedVerse MCR=1
- MedVerse CSR=1
- MedVerse CDR=1
- MedVerse EAR=1
- MedVerse ILR=0
- MedVerse PGA=None by design

## Interpretation after PASS
Operational final evidence covers S1-S4.

Policy-grounding final evidence:
- S1 complete
- S2-S4 incomplete

The next gate should expand and validate the authoritative policy KB for the
new agents before making the complete policy-grounding claim from Gate 10.
