# Final validation: protocol and reporting record

Version v1.0; source snapshot date 3 November 2026. Dataset and code hashes were frozen after
DEV execution and before confirmation. This report was assembled after execution. It is not
external preregistration. All cases/oracles were authored in this task; no independent legal
or clinical reviewer participated. No model or threshold was selected using confirmation.

## FINAL-KB-01 — Evidence construction, retrieval and boundaries

1. **Question:** Can the candidate Korean corpus return the specified source while enforcing eligibility,
   jurisdiction, role access and recorded temporal boundaries? Does an exact citation fail explicitly when absent?
2. **Frozen assumptions:** The original 44-record corpus is a candidate reference collection, not a complete
   regulatory database. 42 are internally eligible. Source text includes labelled paraphrases. All executable
   interpretations remain unapproved for clinical deployment.
3. **Changed component:** Add a separate exact-ID/date/record-fingerprint evidence service and explicit lexical
   bilingual BM25 reference backend. Original multilingual dense code is not changed or claimed reproduced.
4. **Dataset/provenance:** 40 developer-authored intent families, eight per institution, each EN+KO.
   Underlying sources are the supplied Korean corpus; no patient-derived records are used.
5. **Split:** 20 DEV families / 20 confirmation families. Language variants stay together. Policy-source overlap
   is expected and is not claimed as unseen-law generalization.
6. **Leakage audit:** No training. Query text/target IDs are not loaded by the runtime ranker. Separate runner
   reads the oracle. Exact duplicates and intent-family overlap across partitions are audited. Reused source
   concepts are disclosed. This is not evidence of semantic independence of every legal principle.
7. **Oracle:** Frozen target-source sets specified before confirmation. Some guidance may also support an
   answer; alternative-source relevance remains a diagnosis item rather than post-hoc relabelling.
8. **Metrics:** Target-source top-1 and Recall@3 per language, both-language family success, exact-ID and
   prefilter boundary probes, explicit dependency status. Claim-code tests cover a finite registered vocabulary,
   not arbitrary-language entailment or complete legal applicability.
9. **Pass/fail:** No wrong-role/jurisdiction/future/expired exact lookup in the designated hard-boundary tests;
   unknown exact ID and missing evidence must fail. Retrieval accuracy is reported descriptively with no
   post-hoc perfect-score threshold. Clinical/legal completeness remains unestablished.
10. **Raw outputs:** `retrieval_queries.csv`, `retrieval_summary.json`, integrity-check records and source reviews.
11. **Interpretation:** 85% required-source Recall@3 in each confirmation language; six query-level misses
   retained. A mixture of rank and oracle-coverage issues is possible. Dense reproduction is blocked by dependency.
12. **Claim boundary:** Finite source-reference retrieval tests and application-layer filtering, not database
   isolation, legal advice, independent source completeness or healthcare deployment validity.
13. **Next dependency:** Run the dense helper in the original environment; independently review candidate
   targets, exact Korean passages, effective snapshots and institutional interpretations before any clinical use.

## FINAL-WF-01 — Progressive institutional workflow and action lineage

1. **Question:** Can clinical review continue while research disclosure is independently held, conditionally
   released, or blocked as evidence, scope, jurisdiction and authorization change?
2. **Frozen assumptions:** Five asymmetric roles; no sixth institution; local scenario publisher and mock ticket
   signer trusted; no real network or device actions; all proposed permissions are modeled institutional rules.
3. **Changed component:** New versioned runtime extension with actual proposal IDs, allowlisted observations,
   modeled human-review tickets, final revalidation, idempotent commits and audit linkage. Historical Gate19/26
   fixture-oriented code and thresholds remain unchanged.
4. **Dataset/provenance:** 12 authored sequence families, two to six progressively released events, including
   oncology symptoms, unreliable telemetry, secondary research and revocation. These are scenario-based models.
5. **Split:** Four DEV and eight confirmation sequence families. Known policy primitives are recombined;
   no claim of independent clinical observations or wholly unseen legal cores.
6. **Leakage audit:** Input event stream and expected obligations are stored separately. Runtime/server never
   import the oracle. Agents receive only the released allowlisted state. No future event payload reaches agents.
7. **Oracle:** Positive/negative action obligations and deadlines in a separate JSON. Prerequisite order and
   minimum-field payload checked independently of coordination-state string. Developer-authored, not expert adjudicated.
8. **Metrics:** Workflow obligations met, clinical-review completion, forbidden commits, payload scope errors,
   prerequisite-order errors, audit validity and local coordination time. Full local-event time additionally measured
   over 30 repetitions after two warmups, randomizing configuration/family order.
9. **Pass/fail:** Defined finite safety boundaries and positive MedVerse workflow obligations must hold. B5 beating
   every control is not a PASS criterion. Deny-all cannot pass positive clinical-review obligations.
10. **Raw outputs:** Case CSV, per-configuration traces, proposal/receipt IDs, source hashes, tickets' scoped validity
    decisions, event cursors and modeled effect order. Tickets are not real human credentials.
11. **Interpretation:** MedVerse 8/8; independent snapshot filtering 6/8; stateful equivalence control 8/8; deny-all
    0/8. No unsafe commits observed on these families. The stateful control shares the same ordered execution kernel:
    the result is consistency evidence, not independently established algorithmic superiority.
12. **Claim boundary:** In-memory model execution. No clinical diagnosis, no patient-level inference from population
    statistics, no autonomous therapy, no regulatory approval, no live LLM or trained-classifier proposal path in this UI.
13. **Next dependency:** Independent workflow and policy review; actual deployment identity and approval mechanisms;
    separately frozen integration of trained agents if pursued. Do not reuse present scores for those extensions.

## FINAL-REL-01 — Fault response, packaging and auditability

1. **Question:** Can the advertised local demonstration run without optional services, retain source/action lineage,
   and reject defined faults without silently upgrading to an authorized action?
2. **Frozen assumptions:** One release; original archive files preserved; no credentials or real patient data;
   original trained models replayed without fit() or hyperparameter selection.
3. **Changed component:** New local HTTP/UI packaging and explicit interface test harness; no scientific threshold changes.
4. **Dataset/provenance:** 30 engineered integrity probes; exhaustive 2^9 authorization-state table (one satisfying
   conjunction, 511 negatives); 18 browser/API probes; six clean-runtime checks; legacy regression and saved-model replay.
5. **Split:** New finite checks are not patient samples. Clean venv has no pip/third-party packages. Browser tests use
   the actual interface code and running HTTP backend through an explicit test transport.
6. **Leakage audit:** No oracle input to agents. Raw measurements and traces retained. No unpublished clinical data.
   Replay and concurrent-commit tests check idempotency. Original artifact byte hashes rechecked at packaging.
7. **Oracle:** Explicit engineered invariants, reference file hashes, API responses and trace field requirements.
   Cryptographic identity, unbounded adversarial resistance and arbitrary claim entailment are outside this oracle.
8. **Metrics:** Probe pass/fail, finite state-table correctness, regression passes/skips, model P/R/F1/support and
   stored LBFGS iteration counts, clean-launch status, JS errors, responsive overflow and artifact preservation.
9. **Pass/fail:** All finite integrity/authorization assertions pass; environmental skips remain labelled skips.
   Deployment readiness stays HOLD regardless of engineering checks. Native-browser network restrictions cannot be
   relabelled as a full production-browser pass.
10. **Raw outputs:** JSON/CSV tests, command logs, environment record, PNG captures, source/model/data hashes,
    model class reports, dependency failure log and clean-runtime log.
11. **Interpretation:** 30/30, 512/512, 18/18 and 6/6 finite checks; legacy 27 passed/9 skipped; stored-model replay
    reproduced Privacy/Cyber class results. Managed Chromium blocked direct localhost navigation: test rendering
    used offline actual assets with a Python HTTP fetch bridge; native download dispatch was intercepted, Blob tested.
12. **Claim boundary:** Linux/Python 3.13.5 and managed headless Chromium smoke checks. No Windows execution,
    accessibility certification, production penetration test, regulatory certificate or externally anchored audit.
13. **Next dependency:** User-side normal browser and original dense model environment; independent clinical/legal
    review; final five-page competition document and ITU KB integration confirmation.

## Error taxonomy used

- Row-level leakage: exact duplicate records across partitions; audited separately.
- Semantic/template leakage: shared policy primitives and context variants; disclosed, not called novel legal coverage.
- Oracle underspecification: possible alternative relevant guidance for a required-source miss; preserved for review.
- Coverage gap: missing policy/SOP/source-date/clinical review; never filled with fabricated law.
- Representation failure: possible lexical rank limitation; not automatically model-capacity failure.
- Model-capacity / optimization failure: not inferred from an unavailable embedding package or from frozen inference replay.
- Environmental/dependency failure: original dense backend unavailable; browser localhost transport restricted.

No threshold was changed after confirmation. No failed retrieval record was dropped or relabelled. All superiority
hypotheses remain separate from implementation integrity.
