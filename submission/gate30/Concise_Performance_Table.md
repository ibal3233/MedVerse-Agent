# Gate 30 - compact performance table

| Configuration | Snapshot feasible complete | Progressive final complete (same 10) | Per-step reference agreement | Invalid new commits | HTTP median ms | HTTP p95 ms |
|---|---|---|---|---|---|---|
| Requested path only | 1/10 | 1/10 | 75/84 | 0 | 7.27 | 14.45 |
| Fair stateful selector | 10/10 | 8/10 | 84/84 | 0 | 7.34 | 15.9 |
| Independent constraint planner | 10/10 | 8/10 | 84/84 | 0 | 7.37 | 15.74 |
| MedVerse harmonizer | 10/10 | 8/10 | 84/84 | 0 | 7.55 | 16.06 |

Fourteen known families, ten snapshot-feasible. Progressive completion is 8/10 for all capable methods. Four families are appropriately partial/held; C01/C02 additionally lose complete solutions after irreversible earlier commitments. Per-step agreement is conditional on the committed prefix, not globally optimal foresight. No independent clinical/legal validity or strict algorithmic superiority is established.
