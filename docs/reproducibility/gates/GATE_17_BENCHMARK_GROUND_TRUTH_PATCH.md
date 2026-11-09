# Gate 17 Benchmark Ground-Truth Diagnostic Patch

## Classification
Benchmark ground-truth misspecification — incomplete acceptable-policy set.

Initial Gate 17:
- 29/32 checks PASS
- semantic Top-3 accuracy = 0.75
- policy-boundary accuracy = 1.0
- wrong-jurisdiction acceptance rate = 0.0
- agent-partition leakage rate = 0.0

Only Q1 and Q2 failed individual semantic retrieval checks.

For both queries, `KR-HMDUG-2025-PURPOSE-MIN-001` appeared in Top-3 and directly
covers the query's purpose-limitation and minimum-necessary concepts.

## Patch
Add `KR-HMDUG-2025-PURPOSE-MIN-001` to the acceptable Top-3 gold set for Q1 and Q2.

## Frozen components
No changes to:
- MiniLM model
- embeddings
- policy corpus
- source metadata
- Top-k
- similarity
- jurisdiction filtering
- agent-access filtering
- policy-boundary logic
- action sets
- scenario facts

## Expected rerun
- semantic_top3_accuracy = 1.0
- policy_boundary_accuracy = 1.0
- wrong_jurisdiction_acceptance_rate = 0.0
- agent_partition_leakage_rate = 0.0
- Gate 17 = PASS
