# Gate 17 — Jurisdiction-Aware Embedding Retrieval and Policy-Boundary Evaluation

## Scientific question

Can MedVerse-Agent use the validated Korean policy corpus as an operational
knowledge substrate while preserving jurisdiction, institutional access, and
explicit policy-action boundaries?

## Frozen inputs

- Gates 0–16
- deployment jurisdiction = Republic of Korea (`KR`)
- Korean Policy Corpus v0.4 foundation
- five institutional agents and their frozen mandates
- multilingual embedding model:
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

## Retrieval pipeline

\[
K^{KR}_i =
\{k : J(k)=KR,\; i\in access(k),\; eligible(k)=1\}
\]

Only after the hard filter is applied:

\[
e_q=f_	heta(q), \qquad
e_k=f_	heta(k)
\]

\[
score(q,k)=e_q^	op e_k
\]

The embedding model therefore ranks only jurisdiction-valid,
agent-authorized records.

## Gate 17 additions

The full March 2026 Pseudonymized Information Processing Guideline contributes
structured operational records covering:

- special-purpose pseudonymized-data use;
- third-party provision;
- inter-controller data combination;
- safeguards and separation;
- re-identification prohibition;
- five-stage pseudonymization workflow;
- AI/scientific-research treatment;
- expandable AI research purposes;
- low/medium/high risk classification;
- risk-based adequacy review;
- unstructured healthcare/AI data.

## Explicit boundary states

- `COMPLIANT`
- `OUT_OF_POLICY`
- `WRONG_JURISDICTION`
- `OUTSIDE_MANDATE`
- `INSUFFICIENT_EVIDENCE`

The validator is deterministic. It does not replace legal, regulatory,
clinical, IRB, or privacy authority.

## Key tests

1. multilingual semantic retrieval;
2. authorized Korean source in Top-3;
3. cross-lingual thematic agreement;
4. wrong-jurisdiction decoy rejected before semantic ranking;
5. agent-access partition preserved;
6. compliant action permitted;
7. out-of-policy action blocked;
8. outside-mandate action blocked;
9. insufficient-evidence action escalated;
10. replay stability.

## Metrics

- Semantic Top-3 Retrieval Accuracy
- Policy Boundary Accuracy
- Wrong-Jurisdiction Acceptance Rate (target 0)
- Agent-Partition Leakage Rate (target 0)

## Next gate after PASS

Gate 18 — MedVerse-Agent Policy-Aware Harmonization.

Gate 18 should consume validated institutional assessments and Gate-17
boundary decisions to produce:

- AGREEMENT
- COMPLEMENTARY
- CONDITIONAL_HARMONIZATION
- INSTITUTIONAL_CONFLICT
- POLICY_CONFLICT
- INSUFFICIENT_EVIDENCE
- HUMAN_AUTHORITY_REQUIRED

and then generate a harmonized plan, policy block, evidence request,
or escalation.
