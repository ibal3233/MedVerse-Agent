# Gate 15 — Data/Policy-Grounded Agent Reasoning

## Scientific question
Can each MedVerse institutional agent produce an attributable assessment using
only its authorized Digital-Twin view, authorized policy records, permitted
population context, and provenance?

## Evidence bundle

For agent \(i\):

\[
\mathcal B_{i,t} =
\left[
O_i(\mathcal{DT}_t),
K_i^{policy},
D_i^{open},
P_{i,t}
\right]
\]

and the deterministic institutional reasoner is:

\[
d_{i,t}=g_i(\mathcal B_{i,t},M_i)
\]

where \(M_i\) is the frozen institutional mandate.

## Evidence layers
1. authorized Digital-Twin view
2. authorized policy records
3. open population context where permitted
4. provenance references

## Open-data safety boundary
Korean NCC cancer-incidence data may be attached as descriptive context to:
- Hospital
- Research/IRB

It is not exposed to:
- Cyber/Network
- Privacy
- Regulator

No assessment may derive an individual diagnosis, prognosis, or cancer probability
from the NCC population dataset.

## PASS criteria
- S1 Hospital assessment grounded correctly
- S1 Cyber assessment grounded correctly
- S2 Privacy assessment grounded correctly
- S2 Research/IRB assessment grounded correctly
- S3 Regulator assessment grounded correctly
- S4 Privacy assessment grounded correctly
- policy attribution present
- DT provenance attribution present
- no unauthorized evidence use
- no patient-level inference from population statistics

## What remains frozen
- Gates 0-14
- S1-S4 coordination semantics
- policy KB v0.3
- Gate 14 Digital-Twin quality semantics
- population-data interpretation boundary

## Next step after PASS
Gate 16 should connect these grounded assessments to the coordinator and compare:
- legacy event-payload path
- grounded Evidence-Bundle path

The required result is semantic equivalence on S1-S4 while gaining explicit
data/policy/provenance attribution.
