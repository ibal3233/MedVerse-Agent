# Gate 7A — Multilingual Semantic Retrieval and Translation Provenance

## (1) Question this gate answers
Can MedVerse-Agent retrieve the same authorized policy evidence from semantically equivalent Korean and English queries while preserving policy provenance, institutional access boundaries, and explicit translation status?

This gate does not permit an LLM to make institutional decisions.

## (2) Frozen
- Gates 0-6.
- Gate 6 source provenance.
- Gate 6 agent-specific policy partitions.
- Gate 6 legal-source metadata.

## (3) Changed
Only:
- compact Korean retrieval descriptors
- multilingual sentence embeddings
- cosine-similarity semantic retrieval
- Korean/English query pairs
- cross-lingual ranking diagnostics
- explicit translation-provenance checks

## Embedding model
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

The model supports multilingual sentence similarity and is used only as a retrieval component.

## Important legal-text boundary
The repository does not claim to contain an official English legal translation unless explicitly marked as such.
Current English policy text is tagged:
source-grounded English paraphrase

The Korean fields added here are compact retrieval descriptors, not a reproduced full statute.

## (4) PASS / FAIL / HOLD

### HOLD
If `sentence-transformers` or the embedding model is unavailable, Gate 7A returns HOLD.
This is an environment/dependency condition, not a scientific failure.

Install:
pip install sentence-transformers

On first use the selected model may be downloaded from Hugging Face.

### PASS
Every defined check must pass:
- multilingual record schema valid
- translation provenance explicit
- Korean Hospital query retrieves Medical Service Act seed at Top-1
- English Hospital query retrieves same Top-1
- Korean Cyber query retrieves Security Measures seed at Top-1
- English Cyber query retrieves same Top-1
- Korean/English Top-1 agreement for both agents
- semantic retrieval does not bypass policy partitions
- ranking replay is stable

One failed defined invariant means FAIL.

## (5) Outputs
outputs/gate7a/
- gate7a_semantic_retrieval_trace.csv
- gate7a_checks.csv
- gate7a_status.json

## (6) Next action

### PASS
Freeze semantic retrieval configuration.
Proceed to Gate 7B: bounded LLM reasoning adapter / policy-grounded explanation.

### HOLD
Install the dependency/model only. Do not change retrieval thresholds or queries.

### FAIL: wrong Top-1
Inspect:
1. query wording
2. indexed text
3. semantic score
4. language pair
Do not immediately swap embedding models.

### FAIL: access leakage
Treat as a hard policy-partition regression and restore Gate 6 access semantics before continuing.

### FAIL: cross-lingual disagreement
Run language-pair diagnostics before modifying the corpus or model.
