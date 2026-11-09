# Gate 6 — Policy Knowledge-Base Ingestion and Retrieval

## (1) Question this gate answers
Can each institutional agent retrieve the correct policy evidence from a source-grounded, provenance-preserving knowledge base while respecting agent-specific policy access boundaries?

This gate validates retrieval infrastructure, not legal reasoning quality.

## (2) Frozen
- Gates 0-5.
- Institutional roles and observation/action boundaries.
- Gate 5 coordination semantics.
- Initial Korean policy source set for the two-agent slice.

## (3) Changed
Only:
- policy seed record schema
- provenance fields
- agent-specific policy partitions
- deterministic lexical retrieval
- retrieval diagnostics

No embeddings, LLMs, automatic translation, or full legal-text reproduction are introduced yet.

## Policy sources used in Gate 6

### Healthcare Provider Agent
Medical Service Act, Article 21
Current seed version: effective 2026-10-02
Source: National Law Information Center

### Cyber/Network Agent
Personal Information Security Measures Standard
Effective 2026-07-01
Source: National Law Information Center / PIPC

## Important translation decision
Gate 6 stores:
- authoritative Korean-source metadata
- exact official URL
- article/section identifier
- effective date
- English source-grounded paraphrase

It does NOT claim the paraphrase is an official legal translation and does not store full legal text.

Later multilingual ingestion may use:
1. Korean original for retrieval,
2. official English translation where available,
3. machine-assisted translation only when clearly labeled.

## (4) PASS/FAIL criteria
All checks must pass:
- policy records satisfy schema
- every record has authority, source URL, date and article
- hospital partition contains only the hospital seed record
- cyber partition contains only the cyber seed record
- expected query retrieves correct Top-1 chunk
- retrieved hit preserves provenance
- cross-agent policy retrieval is blocked by access partition
- exact deterministic replay

One failure means Gate 6 FAIL.

## (5) Outputs
outputs/gate6/
- gate6_retrieval_trace.csv
- gate6_checks.csv
- gate6_status.json

## (6) Next action by outcome

### PASS
Freeze provenance/access semantics.
Proceed to Gate 7A: multilingual semantic retrieval and translation diagnostics.

### FAIL: wrong Top-1 but access correct
Diagnose tokenization/query vocabulary first. Do not add embeddings immediately.

### FAIL: cross-agent leakage
Treat as policy-access-control failure. Do not proceed to semantic retrieval.

### FAIL: missing provenance
Fix metadata ingestion, not ranking.

### FAIL: replay mismatch
Treat as deterministic retrieval implementation defect.
