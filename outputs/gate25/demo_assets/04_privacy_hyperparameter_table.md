# Gate 22B.6 Hyperparameter Selection — Action Head Only

Selection uses DEV only. Replication metrics are excluded.

| C | Train action F1 | Dev action F1 | Solver iter. | Selected |
|---:|---:|---:|---:|:---:|
| 0.01 | 0.153 | 0.109 | 12 |  |
| 0.03 | 0.274 | 0.253 | 15 |  |
| 0.1 | 0.512 | 0.467 | 17 |  |
| 0.3 | 1.000 | 1.000 | 23 | ✓ |
| 1 | 1.000 | 1.000 | 34 |  |
| 3 | 1.000 | 1.000 | 42 |  |
| 10 | 1.000 | 1.000 | 35 |  |
