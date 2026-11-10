# Team MedVerse — Final Results Gallery

This gallery uses the **cropped figures embedded in the final cross-referenced report**. Explanatory notes beneath each plot are retained inside the image so that a reviewer can interpret the evidence while scrolling. The figures summarize scenario-based institutional decision-modeling studies; they are not independent patient cohorts or clinical efficacy measurements.

## Institutional component validation

### Cyber / Network action classification

![Cyber action confusion matrix](final_report_figures/cyber_action_confusion.png)

*All 72 modeled prospective action records lie on the diagonal of the supplied confusion matrix.*

### Prospective stability across groups

![Cyber prospective stability](final_report_figures/cyber_group_stability.png)

*Action and assessment accuracy remain 1.000 across the frozen g5–g8 groups.*

### Development-only model selection

![Cyber hyperparameter selection](final_report_figures/cyber_hyperparameter_selection.png)

*The regularization value was selected on development data before prospective evaluation.*

### Solver diagnostics

![Cyber solver iterations](final_report_figures/cyber_solver_iterations.png)

*LBFGS iteration counts describe solver effort across fitted models, not neural-network epochs.*

---

## Multi-agent architectural comparison

### Coordination quality and exact workflow matching

![Architectural coordination quality](final_report_figures/architectural_coordination_quality.png)

*The main bounded observation is B4→B5: policy filtering alone does not reconstruct the complete encoded cross-institution workflow.*

### Safety and governance behavior

![Architectural safety and governance](final_report_figures/architectural_safety_governance.png)

*Low violation rates must be read together with useful workflow completion; deny-all behavior is not credited as coordination success.*

### Exact workflow match by archetype

![Workflow exact match by archetype](final_report_figures/workflow_by_archetype.png)

*B5 matches all seven encoded archetypes; the ten variants per archetype are contextual variants, not independent institutional problems.*

---

## Workflow coordination mechanisms

### Proposal-order robustness

![Proposal-order robustness](final_report_figures/scheduling_order_robustness.png)

*Fair stateful retry and dependency ordering both complete every tested schedule; the strong-comparator tie is retained.*

### Validation effort at equal completion

![Validation calls at equal completion](final_report_figures/scheduling_validator_calls.png)

*Dependency ordering saves 126 validation calls (1.03%) relative to fair retry at identical completion; this is not an end-to-end speed claim.*

### Authorized workflow selection

![Authorized workflow selection](final_report_figures/workflow_selection_completion.png)

*The requested-path-only control completes 1/10 feasible workflows; all three capable selectors complete 10/10.*

### Complete and permissible partial outcomes

![Workflow selection partial outcomes](final_report_figures/workflow_selection_partial_outcomes.png)

*The capable methods agree on all 14 acceptable complete or partial dispositions within the finite action library.*

### Policy-context handoff tests

![Policy context handoff](final_report_figures/policy_context_handoff.png)

*Valid context exchanges are accepted and altered or incomplete context is rejected by both local adapters; this is not full remote interoperability certification.*

### Snapshot versus progressive execution

![Snapshot to progressive outcomes](final_report_figures/snapshot_progressive_outcomes.png)

*Snapshot correctness does not guarantee online completion: early irreversible choices leave two progressive cases incomplete.*

---

## Digital Twin and policy evidence

### Field-specific Digital Twin freshness

![Digital Twin freshness](final_report_figures/digital_twin_freshness.png)

*An unrelated metadata update must not make older telemetry appear fresh.*

### Institution-specific evidence scope

![Role evidence scope](final_report_figures/role_evidence_scope.png)

*Configured record counts describe role-scoped retrieval access, not corpus completeness or agent accuracy.*

### Korean / English policy retrieval

![Bilingual retrieval](final_report_figures/bilingual_retrieval.png)

*Equal aggregate Recall@3 does not imply identical query-level behavior across Korean and English.*

---

## Progressive execution and commitment timing

### Clinical work before research disclosure

![Progressive clinical trace](final_report_figures/progressive_clinical_trace.png)

*The modeled clinical review proceeds before the restricted research view is authorized.*

### Local progressive-workflow response distribution

![HTTP response distribution](final_report_figures/http_response_ecdf.png)

*Loopback HTTP measurements exclude external-network, model-inference and human-review latency.*

### Completion by commitment family

![Commitment outcomes by family](final_report_figures/commitment_family_outcomes.png)

*The full-information column is a noncausal evaluation bound rather than a deployable controller.*

### Completion–waiting trade-off

![Commitment tradeoff](final_report_figures/commitment_tradeoff.png)

*Bounded waiting yields four gains and three losses versus eager commitment and ties the capable bounded-wait comparator.*

### Inspectable commitment timeline

![Commitment timeline](final_report_figures/commitment_timeline.png)

*WAIT, PREPARE and COMMIT are explicit dispositions; preparation is not clinical completion, disclosure or approval.*

### Institution-specific contributions

![Agent contributions](final_report_figures/agent_contributions.png)

*Counts are correlated decision opportunities and modeled effects, not learned-agent accuracy scores.*

### Operator-response distribution

![Workspace response distribution](final_report_figures/workspace_response_distribution.png)

*The integrated workspace faithfully replays the frozen controller; no speed-superiority claim is made.*

---

## Evidence navigation

- [Research questions](RESEARCH_QUESTIONS.md)
- [Korean policy knowledge base](../knowledge_base/KOREAN_POLICY_KB.md)
- [ITU and AI Readiness mapping](../standards/ITU_AND_READINESS_MAPPING.md)
- [Technical report](../../submission/TECHNICAL-REPORT.md)
- [Final report and annex](../../submission/Team_MedVerse_Final_Report_FINAL_CROSS_REFERENCED.pdf)
