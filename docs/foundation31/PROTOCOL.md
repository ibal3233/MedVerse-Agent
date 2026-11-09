# Gate 31 — Original Digital Twin and evidence-retrieval integration

**Version:** 1.0.0. Additive foundation checkpoint. No old experiment is reopened.

## Scientific status
The original `medverse.digital_twin` and multilingual retrieval representation are imported through new adapters. Gate 30's action contracts, selector and validator are unchanged. This checkpoint does NOT repair eager commitment, evaluate a new learning model, or establish current-law applicability. C01/C02 and capable-comparator ties remain.

## Thirteen reporting elements
1. **Question:** Can the original DT state class and constrained dense-retrieval interface be connected without inventing observations, bypassing source boundaries, or changing the prior workflow effects?
2. **Frozen assumptions:** Five roles, KR deployment, current archived 44-record candidate corpus, original 384-dimensional multilingual MiniLM model family, top-k=3. Pin revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` for this release; older runs did not pin revisions, so identical historical weights are not established. Recorded effective dates are metadata, not legal verification.
3. **Changed component:** Per-session observational DT bridge and optional evidence backend. Previous action selection, commitment and authority validation are held fixed. The bridge is not an inference-to-action integration of learned agents.
4. **Data and provenance:** Original 18 scenario families, 40 bilingual query intents, original policy records, and explicitly modeled S1 development fixtures. No patient-derived data. Source documents have not been reinterpreted or re-verified for this checkpoint.
5. **Split:** Prior DEV/CONFIRMATION labels retained only for historical comparability. All are now known regression inputs, NOT fresh confirmation data. No parameter selection is performed.
6. **Leakage audit:** The DT bridge receives released snapshots, never the future scenario. Zero initial vital-sign values. Role projections retain own-domain provenance. Exact policy lookup and ranked search share boundary checks. Deterministic test vectors are labelled engineering fixtures, never LM measurements.
7. **Reference specification:** Hand-specified source boundary and DT field expectations; compare normalized original/new workflow effects at every event; compare known query targets without editing labels. Engineering review only, not independent expert clinical/legal review.
8. **Metrics:** Development check count; unchanged event transitions; receipt-chain validity; HTTP checks; per-role eligible-source counts; target-source top-1 and Recall@3 by backend/language; paired hit counts; recorded vector normalization/truncation metadata when the real model runs. Missing dense measurements are N/A, never zero.
9. **Acceptance:** All engineering checks and noninterference comparisons pass. Dense reproduction has a separate EXECUTED/BLOCKED status. Engineering success does not imply dense readiness or legal/clinical validity. No target retrieval score is required and no thresholds are retuned.
10. **Raw outputs:** Per-query source results, scores, model/revision/versions, recorded filter reasons, original-file hashes, role coverage, DT trajectory and provenance, integration rows, HTTP trace, run-specific JSON/CSV, PDF/PNG figures.
11. **Interpretation:** A diagnostic fix to a view is not improved clinical outcome. Lexical and dense backends are separately identified; no surrogate vector score is published as semantic performance. Known-input regression is not generalization. Relevant alternative guidance may be missed by the frozen target-source labels; labels remain unchanged.
12. **Claim boundary:** Local modeled governance prototype, original DT class with additive observation accounting, optional pinned semantic retrieval. Not a third-party DT SDK, clinical twin, external database-isolation proof, legal permission, or a commitment-timing improvement.
13. **Next dependency:** Run the pinned dense model on an environment with the dependency and weights, review the results without tuning to them, then implement the separate Gate 32 commitment-control design with new grouped families and fresh confirmation.

## DT diagnostic semantics
- Original defaults are explicitly cleared at construction. Each field requires its own released source record.
- Missing S1 core observations leave the adapter's core validity UNVERIFIED, even when original defaults or native diagnostic rules would suggest otherwise.
- The native rule computes freshness using the latest global observation. The additive observation-aware diagnostic uses the oldest required observed field so a consent update cannot freshen telemetry.
- The native exponential time constant is 300 modeled seconds with a 0.5 freshness threshold. These unchanged values are not clinical standards. The native comment calls it a half-life; mathematically, 300 is the exponential time constant. No underlying code or threshold is altered.
- The bridge's 60 seconds per released event is a labelled display clock. It does not replace the receiving validator's separate event-step freshness conditions.
- Incoming envelopes identify fields and authority conditions, not actual field values. No vitals are reconstructed from their metadata or from population statistics.

## Retrieval design
Source eligibility and recorded date checks → KR jurisdiction → institutional access → ranking.
Dense indexing imports the original `_text` representation and normalized embedding logic, with a pinned model loader and deterministic ID tie break. Scores are cosine-equivalent unit-vector dot products, not authority or confidence values. Exact identifiers bypass ranking, not permissions. Required action-rule references are resolved separately and completely; top-three ranking is not a completeness guarantee for legal reasoning.

BM25 is an explicitly selected baseline. Dense loading failure returns an empty BLOCKED result; it never silently falls back. Both services retain pending interpretation status. The integrated action proposals remain frozen contracts; search results do not silently rewrite the execution rules.

## Primary software references (consulted for model/API identity)
- Model card: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- Model API and revision: https://huggingface.co/api/models/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- SentenceTransformer API: https://sbert.net/docs/package_reference/sentence_transformer/model.html

## Development correction log
One test initially supplied `observed_seconds=0` for a consent update while expecting an observation at 300. The fixture was corrected to explicitly supply 300 BEFORE the freeze and integration regression. No code threshold, query target, or experiment output was changed. The raw development outputs are archived in `docs/foundation31/development/`.
