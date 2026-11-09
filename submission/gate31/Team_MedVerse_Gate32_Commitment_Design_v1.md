# Gate 32 — bounded commitment control: design specification v1

**Status:** design specification frozen with the Gate 31 release. Controller implementation, scenario files, reference evaluation and experiments are NOT yet frozen or executed. No performance result is claimed.

## Purpose
Decide COMMIT, WAIT, PREPARE or BLOCK/ESCALATE for actual institution-owned action proposals without revealing future proposals. Preserve existing coordination-state names; these are separate execution dispositions. One coordinator is not a sixth institutional authority.

## Hard constraints
- Use only released history, current authority records, authorized contracts and explicitly declared operational limits.
- Required immediate modeled clinical/protective actions cannot be delayed merely to improve final task completion.
- No replay, authorization widening, retroactive erasure, implicit undo of disclosure, or implicit human approval.
- WAIT has an observable reason, responsible institution, expiry/trigger and recorded start. It holds only the affected proposal.
- PREPARE must be an available and authorized institution-owned action contract with no disallowed irreversible effect. It does not count as completed care or released research data.
- All comparators have the same candidate actions, preparations, observations and deadlines. Existing selector and execution validator remain fixed for the primary comparison.
- The original C01/C02 traces remain known diagnostic regressions. Do not add hints to them solely to reveal their future solution.

## Decision contract (proposed fields)
`proposal_id, owner, history_hash, decision, current_reason, known_prerequisites, pending_review_ref, latest_commit_time, wait_expiry, allowed_preparation_ids, final_revalidation_required`.

A locally valid irreversible action need not be committed immediately when an explicitly visible unresolved review affects its permissible scope and delay is allowed. Absence of such evidence does not justify pretending a favorable alternative will arrive. Unknown futures can produce unavoidable trade-offs; no universal hindsight-optimality claim is allowed.

## Experimental plan / thirteen elements
1. **Question:** Does bounded commitment control improve completion without violating modeled clinical/protective limits or authority conditions under partial information?
2. **Frozen assumptions to finalize:** shared clock semantics, visible decision contracts, allowed preparation, urgency/deadline obligations. All limits engineering assumptions pending clinical/legal review.
3. **Changed component:** commitment timing only. Any expanded preparation vocabulary is held common across methods and separately disclosed.
4. **Dataset/provenance:** newly authored information-prefix families with different subsequent event continuations; not patient-derived.
5. **Split:** proposed 4 development and 8 confirmation prefix families; all branches/translations of each family kept together. Freeze files before running confirmation.
6. **Leakage audit:** same-prefix histories must produce the same decisions; inspect actual policy inputs; remove case IDs, full timelines, future grants and reference answers. Coupled seeds when randomized.
7. **Reference outcomes:** permissible current-state actions, deadline obligations and bounded wait reasons; compare final completion separately with an offline full-information upper bound, never as a causal competitor.
8. **Metrics:** authorized completion, obligation completion within modeled limit, avoidable waiting, wait duration, irreversible conflicts, invalid commits, proper escalation, per-role counts and receipt integrity.
9. **Acceptance:** integrity/boundary acceptance separate from comparative superiority; retain ties and failure branches; forbid threshold changes after confirmation without independently justified new version.
10. **Raw outputs:** visible-history hash per step, candidates, reason/expiry, preparation and commits, source/authority references, exact event trace, CSV summaries and plotting manifest.
11. **Interpretation:** separate insufficient information from selector/commit errors; do not imply model-learning gains.
12. **Claim boundary:** finite online modeled coordination; no real clinical timing, disclosure, legal certification, or perfect performance under arbitrary continuations.
13. **Next dependency:** qualified review, then one frozen integrated release and a new video recorded from that release.

## Comparator contracts
- EAGER: unchanged selection and immediate revalidated commit.
- FAIR_BOUNDED_WAIT: stateful competitor with the same visible review conditions, deadlines and available preparations; no artificial handicap.
- MEDVERSE_COMMITMENT: proposed explicit decision contract implementation.
- FULL_INFORMATION_REFERENCE: evaluation-only upper bound, clearly noncausal and unavailable at runtime.

## Mandatory branch families
Alternative arrives promptly / late / never; alternative fails authority; urgent obligation; late revocation; earlier irreversible disclosure; safe preparation unavailable; evidence update without authority; source-version change. Preserve correct partial work and uncertainty states.

## Main entry-point requirement
`medverse/gates/gate32_commitment_control.py` should verify its own new freeze, execute, save raw outputs, export tables and non-bar PNG/PDF figures, and display figures by default. This file is planned, not supplied by Gate 31.
