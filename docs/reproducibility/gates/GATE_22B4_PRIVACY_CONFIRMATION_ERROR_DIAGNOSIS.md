# Gate 22B.4 — Privacy Confirmation Error Diagnosis

## Purpose
Gate 22B.3 passed 12/13 frozen checks but failed minimum per-action recall
because `LIMIT_DISCLOSURE_TO_MINIMUM_NECESSARY` recall was 0.50.

## Diagnostic-only
This gate does not retrain, retune C, alter labels, change the oracle, or change
the model family.

## Questions
1. Which action transitions account for the 21 confirmation errors?
2. Are errors associated with fresh request context, or policy-core precedence?
3. How much combined training support exists for each failing core?
4. Does the result justify changing model family or only training coverage?

## Result to establish
The diagnosis is supported only if:
- all 21 errors are traced;
- they fall into explicit precedence families;
- failing cores show sparse or zero training support;
- the same core error repeats under all three fresh request contexts.

## Consequence
The current 486-record confirmation benchmark is now opened and diagnostic-only.
Any training intervention requires another prospective confirmation benchmark
frozen before repair training.
