# Team MedVerse — Repository Evidence Audit and Submission Update

**Audit date:** 3 November 2026  
**Purpose:** Supplement the existing final-submission audit with code-level evidence from the two newly supplied archives. Preserve all frozen MedVerse-Agent experiments; do not treat this inspection as a new MedVerse experimental gate.

## 1. Scope, identity, and evidentiary boundaries

The uploaded archives were unpacked and inspected. This review distinguishes source inspection, developer-reported measurements, locally executed pure-function probes, and recommendations.

- **Nakheel Doctor:** ITU identifies this project as the Saudi AI Readiness Hackathon Women's Team Special Prize winner. Its supplied archive is a domain-specific acoustic evidence and policy decision-support prototype.
- **LawThinker:** The supplied README and the authors' February 2026 paper identify it as a legal-agent research project, *LawThinker: A Deep Research Legal Agent in Dynamic Environments*. The official Saudi winners list names SANAD, AI Guardian, SAMAAM, and Nakheel Doctor. No evidence examined establishes LawThinker as one of those winning entries. It is useful as a technical research comparator, not a verified substitute for SANAD's or AI Guardian's code.
- The earlier SAMAAM archive remains a separate reference. These two new archives do not provide the missing SANAD or AI Guardian implementations.

**Executed:** Python syntax parsing; 12 selected policy-function probes; three evidence-integrity probes; four citation-membership probes; a configuration-source probe; four classifier score-boundary probes; corpus and file inventories.

**Not executed:** model training, classifier inference, bundled pickle deserialization, semantic embedding generation/search, hosted/local LLM inference, live apps, full J1-EVAL, or legal-source validation. The pure functions were compiled from inspected AST definitions without importing heavy application modules. These tests characterize the selected functions, not system-wide robustness or scientific benchmark performance.

### Archive fingerprints

| Archive | Files | SHA-256 |
|---|---:|---|
| `LawThinker-agent-main.zip` | 56 | `8edd6ab68fe84e5a1e22c71fd532c107315c54f12e8aa88b5f2992f3563f93d2` |
| `nakheel-doctor-main.zip` | 22 | `5d783315996aaaba9292b8bc348203fcac06610ee81b1481dd22bb566f473c3e` |

These are identities of the uploaded snapshots, not proof that they are exactly the revisions evaluated by the competition judges.

## 2. Nakheel Doctor: implemented strengths and limits

### ND-01 — Small, structured, purpose-specific knowledge base

`knowledge_base.csv` contains **30 unique chunk IDs from eight source references**, with 11 fields: Chunk ID, Source Ref, Source Title, Source Type, Original Source Language, Pages / Section, Y.3172 Node(s), Topic, Chunk Text, Caution / Interpretation, and Source URL.

The source references span research papers, operational guidance, regulations, AI-governance material, and data-sharing guidance. This inspection verifies that the fields and records exist; it does not independently validate every paraphrase against its external source.

**Useful lesson:** explicitly separate what a source states from what the prototype infers or restricts. `Caution / Interpretation` repeatedly identifies scope limits and avoids interpreting broad governance guidance as permission for an integration.

**MedVerse recommendation:** retain authoritative Korean passages, clearly labelled English translations/paraphrases, effective version, applicability, exceptions, internal interpretation, reviewer status, and linked execution rules. Prefer scenario-obligation coverage over corpus-size comparisons. A row is not a whole law, a distinct source, or a validated legal rule.

### ND-02 — Explanatory RAG and policy decisions are separate paths

`app.py:633–735` routes identified policy requests to `evaluate_policy`, attaches fixed supporting chunks, and formats a response. Unsupported recognized policy requests are not passed to the informational LLM as ordinary questions. General informational requests use a separate path.

`informational_rag.py` and `hybrid_search.py` implement source scoping, lexical/semantic retrieval with reciprocal rank fusion, Qwen3 8B generation through a local endpoint, and citation-token checking.

**Boundary:** this does not prove that the natural-language router detects every action request. Semantic routing was not exercised in this audit. It is also decision support; the archive does not establish an operational government-reporting integration.

**MedVerse recommendation:** provide exploratory retrieval for explanations and exact-ID policy dependencies for execution. Apply eligibility, jurisdiction, and access controls to both paths. An agent's narration must not become a side channel for authorization.

### ND-03 — Explicit unknown/false/true authorization handling

`policy_engine.py:13–69` distinguishes reporting integration explicitly present (`ALLOW`), explicitly absent (`BLOCK`), and missing/unknown (`REVIEW_REQUIRED`). It uses identity checks for Boolean values rather than trusting a string such as `"true"`.

`app.py:101–126` takes the integration setting from trusted application configuration. A probe confirmed that a route-supplied `True` is overridden by the archive's configured `False`.

**Boundary:** the `ALLOW` branch checks that configuration Boolean; it does not itself establish a signed human approval, identity binding, delegation chain, or government API authentication. Those would be different controls. A missing rule is also not proof that a real-world action is illegal.

**MedVerse recommendation:** distinguish missing evidence from explicit prohibition. Bind patient-data requests to authenticated institution, purpose, policy version, evidence, and any required human approval. Fail closed for the specific high-impact action while preserving independently authorized work.

### ND-04 — Policy-to-evidence referential integrity

`policy_evidence.py:5–62` checks for empty/duplicate chunk IDs and raises an error if a referenced policy evidence chunk is absent. All **11 distinct chunk IDs** referenced by the deterministic policy engine exist in the uploaded CSV.

The three negative probes—missing chunk, duplicate ID, empty ID—raised the expected `ValueError`.

**Boundary:** presence of a referenced record does not prove that it entails the operational rule, that its interpretation is current, or that it is legally binding.

**MedVerse recommendation:** check both referential integrity and reviewed rule applicability. Record why a clause supports a given obligation; do not merely show a source link.

### ND-05 — Citation membership is not claim support

`informational_rag.py:136–205` validates that at least one citation exists and that every citation belongs to the retrieved source set. It does not compare the answer's claims with the content of the evidence.

A deliberate test statement asserting unlimited disclosure while using an allowed citation token passed this function. Missing citations and an unreturned citation were rejected. This is a characterization of the validator, **not an observed LLM hallucination** and not a claim that the full system produced that answer.

**MedVerse recommendation:** evaluate separately (a) citation existence/membership, (b) source-version fidelity, (c) claim support/applicability, and (d) action authorization. For consequential rules, use reviewed predicates rather than treating another LLM's support score as legal authority.

### ND-06 — Uncertainty remains visible

`classifier.py:46–81` maps scores to low, uncertain, and elevated states. `policy_engine.py:91–159` leaves infestation confirmation subject to review for strong, uncertain, low, and missing evidence states.

The README calls these runtime bands prototype guardrails, not official biological or regulatory thresholds. It reports 95.77% clip-level accuracy, 75.19% leave-one-folder-out balanced accuracy, and five of nine external folders flagged positive, explicitly distinguishing the metrics and limits. **Those reported model results were not reproduced here and are not directly comparable measures of accuracy.**

**MedVerse recommendation:** similarly distinguish DT validity, evidence sufficiency, model uncertainty, and legal permission. Do not imply that a confident model or a valid DT alone authorizes an action. Preserve the existing finite-state/prospective-shift claim limits.

### ND-07 — Selection and confirmation are separated in code, but keep evaluation labels precise

`calibrate_tree_threshold.py:400–617` chooses aggregation strategy and threshold using training-side out-of-folder predictions, then fits the final model and evaluates external folders. This is preferable to selecting using the external results.

However, a score reported on the same out-of-folder predictions used for selecting the threshold is a selection/calibration estimate, not automatically an independent confirmation estimate. The runtime score bands and tree-level aggregation threshold also serve different roles.

**MedVerse recommendation:** retain TRAIN/DEV-only selection, preserve original thresholds, and maintain fresh confirmation cases. Do not imitate numerical thresholds from a different application.

### ND-08 — Scope discipline and reproducibility

The archive includes a saved model and demonstration WAV, while large training data and local LLM/embedding resources remain external. Its README gives launch/training commands and clearly labels missing operational integrations and unestablished policies as limitations.

**MedVerse recommendation:** deliver one documented reproducible local demo with a dependency check, explicit online/offline behavior, and clear degraded-mode messages. A fallback rule mode must not silently masquerade as live LLM execution.

## 3. LawThinker: relevant research mechanisms and boundaries

### LT-01 — Verification is interposed after exploration

`src/agents/law_thinker_agent.py:195–248, 280–321` calls a dedicated `deep_analysis` process after tool results, apart from the explicitly handled empty-memory case. The controller appends tool outputs and verification summaries to the reasoning context.

The associated research framing is Explore–Verify–Memorize, covering knowledge accuracy, fact–law relevance, and procedural compliance.

**MedVerse relevance:** useful evidence need not be applicable evidence. Add a bounded evidence-verification module before an institutional proposal can become executable. This module is not a sixth institutional agent.

### LT-02 — Model-assisted checking is not deterministic authorization

`src/tools/check_tool.py:14–23` retrieves a law and asks a model to analyze relevance. The main orchestration returns verification feedback to the agent; it does not implement MedVerse's institution-specific permit/block execution boundary.

**Do not claim:** that adding this verifier proves legal validity, or that LawThinker's method independently enforces Korean institutional mandates. The tools address a different task and jurisdiction.

**MedVerse recommendation:** a model may suggest applicability or missing evidence; only reviewed rules and authorized human decisions determine consequential permission. Preserve “Learning proposes; policy architecture disposes.”

### LT-03 — Semantic statute matching must not be mistaken for exact citation validation

`src/tools/law_tool.py:161–175` normalizes a requested law name, uses embedding similarity to choose the top corpus law name, and returns that record. It does not explicitly reject the request merely because the exact claimed citation was absent.

This can be useful for resolving informal references, but it is not equivalent to verifying that an exact article identifier exists.

**MedVerse recommendation:** exact canonical identifier/version matching for claimed legal citations; semantic suggestions remain separately labelled candidates. A nonexistent or outdated citation should not be silently replaced and called verified.

### LT-04 — The source corpus is not a ready-made Korean governance database

The supplied `law.json` contains **55,348 string-key/string-value entries**, and the charge mapping contains **346 entries**. The paper/code comment refers to 55,347 law provisions; the count above is the literal count in this archive, not a conclusion about legally distinct current provisions.

The law JSON is not organized as MedVerse's required reviewed Korean source/version/authority/applicability/access registry. Its Chinese-law content should not be imported into the Korean execution corpus merely because it is large.

### LT-05 — Memory requires revocation and scoping in MedVerse

`src/tools/memory_tool.py:4–26` stores/fetches knowledge and context in lists. That utility does not itself enforce temporal validity, data-access labels, or authorization revocation.

**MedVerse recommendation:** if policy memory/caching is used, bind entries to institution, evidence IDs, policy version, purpose, and validity. A later consent, approval, source-version, or DT-state change should invalidate the affected cached permission. An institution's access to public legal text must remain distinct from its access to patient evidence.

### LT-06 — Full reproduction has additional dependencies

The archive contains launchers, six scenario/evaluation modules, and a demonstration video. Referenced embedding arrays including `law_encodings.npy`, `law_name_encodings.npy`, and crime encodings are absent. The README links external J1-EVAL data; Qwen model services and retrieval models are also required.

Python parsing succeeded for all 40 Python files. This is not a successful end-to-end run. The research paper's numerical improvements were not reproduced in this audit.

## 4. Locally executed observations

| Check | Observed result | Interpretation |
|---|---|---|
| 12 policy action/state probes | 12 matched inspected branch behavior | Narrow functional characterization, not an external benchmark |
| Required evidence IDs | 11/11 present | Referential integrity, not legal validity |
| Missing/duplicate/empty evidence probes | All three rejected | Evidence lookup fails explicitly |
| Missing and unreturned citation tokens | Rejected | Citation membership control works for these probes |
| Unsupported claim with returned citation | Accepted by citation checker | Claim entailment is outside that check |
| Route attempts to supply authorized integration | Configured false retained | Application config overrides route-supplied state |
| Runtime score boundaries | Matched low/uncertain/elevated definitions | Threshold implementation check only |
| Python syntax | 14 Nakheel + 40 LawThinker files parsed | No guarantee of dependency/runtime correctness |

Full probe inputs and outputs, inventories, and SHA-256 file manifests are in `repository_audit_results.json`. Reproduction instructions are in the audit bundle README.

## 5. Implications for MedVerse-Agent's final release

### Preserve the unique object of coordination

The contribution is not “more agents” or “a verifier.” It is coordination among five independently bounded institutions sharing a medical-metaverse/DT context, where valid disagreement can coexist with a feasible authorized workflow.

Keep the coordinator name **MedVerse-Agent — Institutional Harmonization Coordinator**. Do not introduce a Security Coordinator label or make the verifier a sixth peer institution.

### Proposed minimal flow

1. Role-scoped clinical/DT/research events and controlled Korean source retrieval.
2. Source/claim/applicability checking with explicit unknown status.
3. Institution-owned proposal with stable proposal ID.
4. Policy and mandate validation.
5. Harmonization of compatible, conditional, and conflicting institutional positions.
6. Revalidation of every proposed final action, including coordinator-generated alternatives, against current policy/evidence/authority state.
7. Modeled execution and an inspectable decision receipt.

Every action receipt should connect event, owner, proposal, evidence IDs, policy version, applicable conditions, validation, coordination outcome, human approval when required, and resulting side effect. This is a proposed engineering requirement, not a claim that the current release already implements every field.

### Two integration limitations remain higher priority than adding new models

Reinspection of the cumulative MedVerse archive confirms:

- `medverse/integration/gate19_grounded_pipeline.py:117` validates `case["boundary_action"][agent_id]`, while the trace separately records actual recommendations. Add a new adapter for actual proposal lineage rather than modifying frozen fixture tests.
- `medverse/gates/gate26b_architectural_baseline_comparison.py:55` stores `executed_actions` as a sorted set. Existing exact-workflow scores do not establish action ordering, approval-before-release, or revocation between proposal and execution.

Preserve Gate 26 as a frozen reference architecture ablation. Add integrated temporal-action evidence separately.

## 6. Amend the existing final-validation plan; do not expand it indefinitely

The earlier plan defines FINAL-KB-01, FINAL-WF-01, and FINAL-REL-01. Add the following cases within that structure, retaining its proposed grouped splits and independent oracle. Do not select thresholds using confirmation failures.

| Existing validation workstream | Additional targeted test | Evidence to collect |
|---|---|---|
| FINAL-KB-01 | Real source ID with unsupported assertion | Citation membership versus support/applicability labels |
| FINAL-KB-01 | Nonexistent article or outdated version | Exact-reference rejection and explicit candidate alternatives |
| FINAL-KB-01 | Missing required rule evidence | No permission for the affected action; evidence request/escalation |
| FINAL-KB-01 | Exact article query versus paraphrased query | Canonical lookup and optional hybrid retrieval under identical filters |
| FINAL-WF-01 | Request claims that approval exists, but trusted state says otherwise | Application authority cannot be overwritten by narrative text |
| FINAL-WF-01 | Valid evidence but wrong institutional owner | Action blocked without reassigning authority implicitly |
| FINAL-WF-01 | Approval revoked between proposal and commit | Commit-time revalidation denies the affected action |
| FINAL-WF-01 | Research disclosure denied while independent clinical review remains authorized | Legitimate work continues; no global deny-all shortcut |
| FINAL-WF-01 | Future event not yet released | No future information in agent observations or decisions |
| FINAL-REL-01 | Missing embedding/LLM/dependency | Explicit startup/degraded mode; no hidden substitute for advertised model |
| FINAL-REL-01 | Invalid or missing evidence ID in decision receipt | Fail closed for affected action; inspectable failure reason |

### Retrieval experiment: optional, bounded

Do not replace the existing embedding model just to imitate Nakheel. First include exact-ID lookup for exact article requests. Compare the frozen dense retriever against a lexical+dense alternative only if development evidence shows a deficiency. Both arms must use the same source snapshot and eligibility → jurisdiction → agent-access restrictions before ranking. Select on DEV only, then run fresh confirmation once. Report retrieval relevance separately from policy applicability and execution safety.

### New experiment records

Each amended experiment must retain the user's 13-item contract: question; frozen assumptions; changed component; dataset and provenance; split; leakage audit; oracle; metrics; pass/fail criteria; raw outputs; interpretation; claim boundary; next dependency. The tests in this audit are competitor-code characterization, not a replacement for that MedVerse protocol.

## 7. Submission artifacts that directly expose the improvements

- **A versioned Korean policy pack:** source registry, clause-level evidence, interpretation status, agent/task mapping, and required tests. Include only review-ready sources in the consequential execution path.
- **One interactive oncology/DT scenario:** progressively released observations, role-specific views, visibly different but valid institutional responses, and an authorized alternative to blanket rejection.
- **A decision receipt:** event, institution, clause/version, proposed action, validator outcome, prerequisites, coordinator outcome, final action, and escalation. Display structured rationale rather than private model chain-of-thought.
- **One results panel:** separate KB evidence quality, workflow utility/safety, and existing Gate 26 architectural results. Do not compare classification percentages across unrelated tasks.
- **A clean release:** runnable instructions, known dependencies, raw evaluation results, limitation statement, and source/experiment hashes.

These are proposed submission priorities, not official judging weights. They target the call's knowledge-base quality, agent capability, gap identification, auditability, and ITU alignment criteria.

## 8. Competitive claim boundary

The inspected repositories do not establish MedVerse superiority, nor does identifying their limitations predict competition rankings. They identify concrete practices to adopt and checks to strengthen.

A defensible target claim is:

> MedVerse-Agent connects source-traceable Korean policy evidence to institution-owned actions in progressively disclosed medical-metaverse scenarios, preserving legitimate institutional disagreement while coordinating auditable, policy-feasible workflows.

That claim becomes persuasive through the actual scenario and evidence, not by repeating “five agents” or “100%.” No first-place outcome is guaranteed.

## 9. External identity and criteria references

The following primary pages were checked for project identity and competition context. The uploaded archives remain the basis for code findings; live repository revisions can differ.

- ITU Saudi winners: https://aiforgood.itu.int/event/ai-readiness-hackathon-kingdom-of-saudi-arabia/
- ITU winner descriptions: https://aiforgood.itu.int/the-itu-ai-readiness-hackathon-names-four-winning-solutions-in-riyadh/
- ITU UAE call: https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/
- LawThinker primary paper: https://arxiv.org/abs/2602.12056
- LawThinker authors' repository: https://github.com/RUC-NLPIR/LawThinker-agent
- Nakheel Doctor repository: https://github.com/HelhBader/nakheel-doctor
