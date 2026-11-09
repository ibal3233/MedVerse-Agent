# MedVerse-Agent — 3-Minute Judge Demo Script

## 0:00–0:20 — Problem
“Medical Metaverse systems can fail when the patient, the digital twin, the network,
the AI system, and institutional policy tell different stories. MedVerse-Agent does
not collapse those institutions into one omniscient model. It coordinates bounded agents.”

## 0:20–1:20 — S1: Digital Twin Cannot Be Trusted
Start S1 and press **Next Event** three times.

1. Clinical alarm arrives.
   - Hospital Agent sees clinical evidence.
   - Cyber Agent does not see raw clinical values.

2. Network degradation arrives.
   - Cyber Agent marks telemetry trust as degraded.
   - The digital twin trust state deteriorates.

3. Identity/integrity anomaly arrives.
   - DT becomes UNVERIFIED.
   - Coordinator identifies complementary risk.
   - Human review is required.

Point out the minimum-necessary inter-agent messages:
- TELEMETRY_TRUST_STATUS = UNVERIFIED
- CLINICAL_PRIORITY = URGENT

## 1:20–2:10 — Governance scenarios
Switch rapidly through:
- **S2** — care continues, research use is restricted after consent withdrawal.
- **S3** — stale/unverified DT blocks high-impact automated action and requires human oversight.
- **S4** — excessive cross-institution disclosure is denied.

## 2:10–2:40 — Policy grounding
Point to the policy/provenance cards.

Say:
“Policy grounding is article-level and access-partitioned. The final campaign achieved
PGA = 1.0 across all six frozen grounding cases. If retrieval is unavailable at demo
time, the interface explicitly reports that and never fabricates a citation.”

## 2:40–3:00 — Evidence
Point to:
- 5 bounded institutional agents
- 240 deterministic operational benchmark rows
- S1–S4 complete operational coverage
- complete policy-grounding coverage
- full Gate 10 experimental matrix complete

Close:
“MedVerse-Agent is a coordination and governance layer around Medical Metaverse AI,
not another clinical chatbot.”
