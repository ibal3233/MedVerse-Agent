# Gate 22B Freeze Record

Status: PASS
Checks: 5/5

Diagnosis:
compositional_generalization_and_rule_precedence_limitation

Observed:
- ID action accuracy = 1.0
- OOD action accuracy = 0.5
- OOD action macro-F1 = 0.2941
- unsafe executions after policy shield = 0

Gate 22B changed no learner. Gate 22C may modify only the diagnosed
compositional-coverage component before considering model-family changes.
