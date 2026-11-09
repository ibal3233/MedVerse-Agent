# Gate 22B.3 Hyperparameter Selection Table

Selection uses TRAIN/DEV only. Confirmation metrics are deliberately excluded.

| C | Train action F1 | Dev action F1 | Train assessment F1 | Dev assessment F1 | Dev mean F1 | Action iter. | Assessment iter. | Selected |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0.01 | 0.155 | 0.109 | 0.180 | 0.100 | 0.188 | 15 | 12 |  |
| 0.03 | 0.322 | 0.253 | 0.414 | 0.375 | 0.619 | 15 | 12 |  |
| 0.1 | 0.363 | 0.333 | 0.874 | 0.881 | 0.843 | 16 | 16 |  |
| 0.3 | 0.971 | 1.000 | 0.880 | 0.881 | 0.976 | 23 | 21 |  |
| 1 | 0.977 | 1.000 | 1.000 | 1.000 | 1.000 | 30 | 28 | ✓ |
| 3 | 0.987 | 1.000 | 1.000 | 1.000 | 1.000 | 38 | 31 |  |
| 10 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 39 | 32 |  |
