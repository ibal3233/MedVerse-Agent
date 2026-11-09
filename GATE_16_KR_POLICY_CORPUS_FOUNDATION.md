# Gate 16 - Korean Policy Corpus Foundation

## Canonical corpus specification

Korean Policy Corpus
- Statutes
  - Medical Service Act
  - PIPA
  - Bioethics and Safety Act
  - Medical Devices Act
  - Digital Medical Products Act
  - AI Basic Act
- Decrees / Enforcement Rules
  - PIPA Enforcement Decree
  - Digital Medical Products Enforcement Rule
- Official Guidelines
  - Health & Medical Data Utilization Guideline
  - Pseudonymized Information Processing Guideline
- Institutional Governance
  - IRB/DRB procedures
  - security safeguard standards
  - access / audit / consent procedures

## Purpose

This gate creates the source-controlled Korean policy corpus that will be the
jurisdiction-constrained policy foundation for MedVerse-Agent.

It intentionally distinguishes:
- binding statutes/decrees;
- official guidelines;
- institutional governance procedures;
- informational press releases.

A press release can establish provenance that a policy changed, but it is not
accepted as a substitute for the full operative guideline.

## Current dependency

The full 2026.03 Pseudonymized Information Processing Guideline must be placed at:

data/policy/source_documents/Pseudonymized_Information_Processing_Guideline_2026-03.pdf

Official KISA page:
https://www.kisa.or.kr/2060202/form?lang_type=KO&postSeq=138

Until that source is present, Gate 16 should report HOLD rather than scientific FAIL.

## Next gate after PASS

Gate 17 - Jurisdiction-Aware Embedding Index and Policy Boundary Evaluation:
1. semantic chunking of both full guidelines;
2. multilingual MiniLM embeddings;
3. jurisdiction filter;
4. agent-access filter;
5. retrieval accuracy;
6. wrong-jurisdiction rejection;
7. compliant vs out-of-policy action tests.
