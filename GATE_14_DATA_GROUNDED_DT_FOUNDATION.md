# Gate 14 — Data-Grounded Digital-Twin Agent Foundation

## Scientific question
Can MedVerse-Agent construct a provenance-aware digital twin, derive explicit
quality metadata, and expose only authorized state/context to each institution?

## Digital-twin formulation

\[
\mathcal{DT}_t =
(\hat{\mathbf x}_t,\mathbf q_t,\mathcal P_t,\mathcal C_t)
\]

with state:

\[
\hat{\mathbf x}_t =
[x_t^{clinical},x_t^{patient},x_t^{network},x_t^{security},
x_t^{consent},x_t^{research},x_t^{AI}]
\]

and quality metadata:

\[
\mathbf q_t =
[q_t^{freshness},q_t^{integrity},q_t^{completeness},
q_t^{provenance},q_t^{uncertainty}]
\]

`VALID / DEGRADED / UNVERIFIED` is a derived display state, not the entire DT.

## Open cancer data boundary
The Korean National Cancer Center CSV is population-level epidemiological
context. It is explicitly prohibited from being represented as an individual
diagnosis, prognosis, or patient-level disease probability.

Expected shared path:

`data/external/ncc_cancer_incidence.csv`

If it is absent, NCC-dependent checks are HOLD, not FAIL.

## Agent evidence partitions

- Hospital: clinical + patient context + DT quality
- Cyber/Network: network + security + DT quality
- Privacy: consent + DT quality
- Research/IRB: consent + research + patient context + DT quality
- Regulator: AI state + DT quality

Population epidemiological context is exposed only to Hospital and Research/IRB.

## What is deliberately not added yet
- no patient-level cancer prediction
- no learned digital-twin estimator
- no LLM authority
- no autonomous treatment recommendation

## Next gate after PASS
Gate 15 — Data/Policy-Grounded Agent Reasoning:
combine authorized DT view + open-data context + policy evidence into
structured Evidence Bundles and test whether agent conclusions are attributable
to the correct evidence sources.
