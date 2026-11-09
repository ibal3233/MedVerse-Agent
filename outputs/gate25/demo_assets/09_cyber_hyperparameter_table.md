# Gate 24C Hyperparameter Selection Table

Selection uses Gate-21A TRAIN/DEV only. Gate-24B prospective metrics are excluded.

| C | Train Action F1 | Dev Action F1 | Train Assessment F1 | Dev Assessment F1 | Dev Mean F1 | Action Iter. | Assessment Iter. | Selected |
|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0.01 | 0.314 | 0.314 | 0.222 | 0.222 | 0.268 | 12 | 10 |  |
| 0.03 | 0.533 | 0.533 | 0.472 | 0.472 | 0.503 | 13 | 12 |  |
| 0.1 | 1.000 | 1.000 | 0.619 | 0.619 | 0.810 | 14 | 14 |  |
| 0.3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 19 | 18 | ✓ |
| 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 21 | 26 |  |
| 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 21 | 27 |  |
| 10 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 23 | 27 |  |
