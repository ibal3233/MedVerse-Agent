# Korean Policy Knowledge Base

Canonical jurisdiction: **Republic of Korea (KR)**.

The candidate corpus contains 44 curated records; 42 are configured as retrieval-eligible. Records preserve source title/authority, source type, article/section, recorded version/date, jurisdiction, agent access, source locator and provenance hash.

## Corpus layers

| Layer | Representative material | Primary use |
|---|---|---|
| Statutes | Medical Service Act, PIPA, Bioethics and Safety Act, Medical Devices Act, Digital Medical Products Act, AI Basic Act | Legal/authority boundaries and institutional obligations |
| Subordinate instruments | PIPA Enforcement Decree, DMPA Enforcement Rule, security measures standard | Safeguards and implementation requirements |
| Official guidance | Health & Medical Data Utilization Guideline; Pseudonymized Information Processing Guideline | Operational data/research/pseudonymization guidance |
| Institutional governance | IRB/DRB, consent, access, audit and security procedures | Workflow prerequisites and escalation |

## Retrieval rule

`eligibility → jurisdiction → agent access → ranking`

The ranker may be BM25 lexical retrieval or multilingual semantic retrieval. Similarity identifies relevant evidence; it does not determine legal authority or executable permission.

## Institutional evidence scope

Configured eligible records (shared records may serve more than one role): Hospital 6; Cyber/Network 12; Privacy 28; Research/IRB 30; Regulator 8. These are retrieval-scope counts, not completeness scores or agent accuracy.

## Machine-usable processing

1. Preserve official source and provenance.
2. Chunk statutes by article and longer guidance by section/semantic unit.
3. Store Korean authoritative text/descriptor plus official English where available or a labelled source-grounded paraphrase.
4. Generate retrieval representation.
5. Apply jurisdiction and institutional access constraints before ranking.
6. Return top-k source-linked evidence.
7. Validate proposed actions against mandate, purpose, evidence and authority.
8. Pass only validated proposals into institutional harmonization.

See `Korean_Policy_Corpus_Illustration.docx` for the detailed clause-to-agent mapping.
