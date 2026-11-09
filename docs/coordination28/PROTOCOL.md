# Gate 28 — Coordination mechanism discrimination

**Team MedVerse | MedVerse-Agent | Protocol v1.0.0**

This is an additive experimental branch. Original Gates 1–27, policies, thresholds, model artifacts, source files and saved outputs remain unchanged. No new LLM, classifier, clinical rule or Korean legal interpretation is introduced. The dependency scheduler is an experimental candidate, not silently installed into the v1 web interface.

## 1. Question

Does the existing apparent coordination advantage reflect sequential scheduling rather than a distinct institutional harmonization mechanism? With exactly the same actual proposals and execution validator, does explicit dependency ordering improve completion under varied proposal arrival order, and does it improve completion or merely reduce revalidation work relative to a fair fixed-point scheduler?

## 2. Frozen assumptions

Republic of Korea remains the configured modeled jurisdiction. Five institution-owned proposers, role observations, approvals, policy evidence, the final action validator and event chronology are frozen. Both Privacy and Research attestations are required for the modeled restricted research release. This dependency is an engineered sandbox rule, not a newly asserted universal legal requirement. The coordinator cannot mint approvals, invent missing evidence, change purposes, change owners, or override the validator. The local operator and execution process remain trusted. All actions and payloads are modeled.

## 3. Changed component

Only proposal scheduling changes. All strategies receive the same proposals, current state and available dependency specification. SNAPSHOT_ONCE validates against the pre-cycle attestation snapshot. SEQUENTIAL_ONCE performs one live-state pass in arrival order. STATEFUL_FIXED_POINT fairly retries dependency-pending proposals after progress until completion or quiescence, with at most n+1 rounds for n proposals. DEPENDENCY_ORDERED uses stable topological ordering of the declared prerequisite graph, then one live-state pass. DEPENDENCY_EDGES_REMOVED uses the same graph-ordering implementation with only its edge set removed. Every commit invokes the unchanged final revalidation.

The graph is a fixed specification of prerequisites already enforced by the validator. It is not inferred from expected outcomes. The strong stateful baseline is not denied retries, information, evidence, or authority. Its equality with the graph method must be retained.

## 4. Dataset and provenance

Use the original twelve workflow families for native-label equivalence auditing. For order experiments use the eight existing WF05–WF12 families historically labelled CONFIRMATION. These are previously observed, developer-authored institutional modeling cases, not new patient observations or independent confirmation. Generate all 120 permutations of five role-delivery positions and both Research-proposal orders (240 schedule templates per family). Collapse templates with identical actual owner/action delivery order at every event before executing any comparator. Preserve the source family IDs and the unchanged event sequence. No future event is released early.

The schedule bank is constructed from input-only proposal batches; no oracle label or outcome is read. All methods run the identical bank. Scenario–schedule pairs are correlated perturbations, not independent clinical cases. Report per-family results and macro-family completion to avoid giving the longest scenario disproportionate weight.

## 5. Split and selection

No training or tuning occurs. Small integrity checks use DEV-like administrative primitives. The historical confirmation family label is retained solely as provenance: this gate is a new structural perturbation analysis of already seen families. No scientific claim of fresh clinical, policy, or structural generalization is made. A later independently authored workflow-composition benchmark will require its own freeze and fresh confirmation. No method, threshold, dependency edge, deadline or oracle may be changed after this gate's results are observed without a new version and preserved failure record.

## 6. Leakage audit

The scheduler never reads the oracle, family ID, expected outcome, requested deadline, historical scores, or future events. Runtime inputs are released observations and actual proposals. Identical schedules are deduplicated before results. Known semantic overlap is disclosed, not mislabelled leakage-free generalization. Lexical retrieval is unchanged and not evaluated here; no selection uses the existing 40 confirmation queries. Grouping does not turn repeated schedules into independent observations. Developer-defined rules and oracles share conceptual assumptions and are not independent expert adjudication.

## 7. Oracle

The unchanged workflow_oracle.json specifies required clinical review, telemetry flags, the modeled deadline cursor for a permitted research release, and forbidden research/DT use. A separate scorer checks the final side effects. Additional structural invariants inspect owner identity, payload fields, prerequisite ordering within the correct request/authorization epoch, duplicate releases, actual proposal lineage, and audit-chain integrity. This is not a clinical or legal oracle. No exact wording or coordination-label matching is used to manufacture differences between semantically equivalent workflows.

## 8. Metrics

Report: (a) normalized native MEDVERSE/STATEFUL_FILTER behavior equality; (b) completed schedules per family; (c) macro-family completion; (d) families successful under every effective schedule; (e) violated execution invariants by type; (f) validator calls including preflight and final commit revalidation; (g) rounds; (h) paired effect-set equality. A set includes action, owner, event, request and authorization epoch; independent safe action order is not penalized. Single-run wall times are retained only as descriptive traces, not a latency superiority claim. No p-values or clinical population inference are planned.

## 9. Pass/fail and hypotheses

Engineering integrity requires unchanged frozen artifacts, all deterministic instrumentation/boundary checks, complete raw outputs, and identical inputs for the comparisons. Integrity PASS is independent of which method wins. Safety or functional failures must be reported; they do not authorize retrospective threshold changes.

- H1: dependency ordering improves order-robust completion over single-pass live validation.
- H2: dependency ordering strictly improves completion over fair fixed-point validation. A tie means this strict hypothesis is NOT SUPPORTED.
- H3: at equal completion, dependency ordering reduces validator-call count versus fixed-point validation. This is an operation-count result, not automatic runtime speedup.
- H4: removing only dependency edges reproduces single-pass behavior.

A gate with unsupported comparative hypotheses can still be a valid completed experiment. No requirement says MedVerse must win.

## 10. Raw outputs

Each invocation writes a new timestamped directory, never overwriting an earlier run. Save manifest, environment, native normalized traces, deterministic checks, the schedule bank, per-schedule and per-family CSVs, paired comparisons, compressed per-proposal attempt ledger, representative full traces, summary JSON and interpretation. Record every attempted validation and every modeled side effect. UI and historical outputs are not rewritten.

## 11. Interpretation

An improvement over snapshot or single-pass filtering but a tie with fixed-point validation localizes the benefit to dependency scheduling. It does not establish a uniquely superior multi-agent system. Lower validator calls support a bounded coordination-efficiency claim under the current finite graph. Robustness to delivery order is not robustness to unknown law, malicious policy text, model errors, alternative-workflow selection, or arbitrary agent compromise.

## 12. Claim boundary

Deterministic administrative workflow models; fixed policies and known dependency primitives; developer-authored oracle; eight known semantic families. No independent Korean legal review, clinical validation, production deployment, dense-embedding reproduction, LLM capability, or saved-model generalization is established. Native MEDVERSE and STATEFUL_FILTER are equivalence controls, not independent architectures. The dependency scheduler is a new experimental add-on; the sandbox UI still uses frozen v1 scheduling.

## 13. Next dependency

If the stateful baseline ties, preserve the tie. A distinct harmonization claim then requires a new mechanism for selecting among institution-owned alternatives under incompatible goals, scope changes or authority dependencies—not merely more reordering examples. Specify alternative actions, feasible workflow sets, cost/priority rules and an equally capable stateful planner before building that benchmark. Obtain independent clinical and policy review. Model replay must use the saved environment (scikit-learn 1.8.0 and its recorded dependencies); the user's 1.9.0 warning is separate from coordination and must not be suppressed.
