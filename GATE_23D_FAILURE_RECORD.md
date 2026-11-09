# Gate 23D Failure Record

Status: FAIL
Checks: 7/8

Passed:
- zero generated OOD overlap
- ID action accuracy threshold
- OOD action accuracy threshold
- OOD assessment accuracy threshold
- zero policy-inconsistent execution
- model family unchanged
- publication outputs

Failed:
- OOD action macro-F1 >= 0.75

Observed:
- OOD action accuracy = 0.8333
- OOD action macro-F1 = 0.46875
- OOD action errors = 4
- policy-inconsistent executions = 0

Gate 23E is diagnostic only and does not alter this result.
