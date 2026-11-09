# Gate 32 measured interpretation — retained gains and losses

## Question resolved
The new runtime can postpone only affected proposals, perform permitted non-disclosing preparation, stop waiting at a declared bound, revalidate at commitment, and produce identical decisions on identical released histories. This is a tested engineering capability, not an optimal online policy theorem.

## Result
Eager: 14/32 branches (14/21 hindsight-feasible). Bounded stateful and MedVerse: 15/32 (15/21). Clinical deadline performance is 28/30 versus 29/30 where the full-information reference can meet that obligation. Waiting is measured in proposal-event opportunities (38 steps over 32 branches), NOT clinical time. Fair and MedVerse tie on all 32 branch comparisons.

Four gains: P01/PROMPT, P02/PROMPT, P03/PROMPT and P03/LATE. Three losses: P04/NO_REPLACEMENT, P04/PENDING_REPLACEMENT and P04/EVIDENCE_NOT_AUTHORITY. Other outcomes tie. Gains and losses were retained; no confirmation-driven repair was made.

## Why the losses matter
At P04 event 1 the original research action has genuine modeled permission. The scope review is visible but advisory for timing; it is not a statutory prohibition. Eager commitment uses that opportunity. At event 2 the grant is revoked. A bounded waiter has not disclosed yet and correctly refuses the now-denied action, but misses an opportunity that was valid earlier. Clinical review proceeds independently at event 1 in all three methods. The study does not classify earlier authorized disclosure as unsafe or imply that revocation can retract it.

## Old C01/C02 are not silently repaired
The original cases do not provide a pending review/commitment window. With no observable reason to wait, the new controller behaves like the old system. All 432 prior event comparisons match. Adding new scope contracts to old cases would change the problem definition; this release instead uses separately versioned cases with explicit declarations.

## Per-role evidence
`agent_behavior.csv` reports proposal-event opportunities, WAIT/PREPARE/BLOCK/ESCALATE counts and actual commits for each institutional role. Counts measure modeled contract handling, not neural-agent accuracy. Repeated pending proposals are not new examples. An unused role is not assigned a perfect score. A release-only compact aggregation is also included as `agent_scorecard.csv` in the presentation run.

## Limitations and next dependency
Same-developer scenario/reference/controller implementations can share mistakes. The first-ever tested continuations are internal confirmation, not unseen-law or external clinical validation. The evaluator's full-information witness is an upper bound, never a runtime input. All clock limits are modeled event steps. The next step is qualified review of commitment contracts, then a versioned clinical-interface integration—not additional tuning on these branches to force perfect results.
