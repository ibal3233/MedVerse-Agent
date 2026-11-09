# Gate 26 — Architectural Baseline Comparison

## Scientific question
Does MedVerse-Agent's institutional harmonization architecture add measurable
value beyond simpler centralized, unconstrained multi-agent, consensus/debate,
and policy-filter-only designs?

## Baselines
- B1 — Single omniscient policy-aware central agent
- B2 — Role-based but unconstrained MAS
- B3 — Consensus/debate MAS
- B4 — Policy filtering without harmonization
- B5 — MedVerse-Agent

## Isolation principle
Institutional proposals and frozen workflow ground truth are held constant.
Only the coordination, authority, filtering, and information-sharing architecture changes.

This is therefore an architectural ablation, not a comparison of differently
trained institutional classifiers.

## Gate 26A
Freeze:
- 70 cases;
- 7 coordination archetypes, 10 variants each;
- five baseline capability contracts;
- fairness rules;
- metrics;
- benchmark SHA256.

## Gate 26B
Run every baseline once on the frozen benchmark.

A Gate PASS indicates correct execution of the comparison. It does **not**
require B5 to outperform the alternatives.

## Metrics
1. Institutional correctness
2. Policy violation rate
3. Unnecessary escalation rate
4. Information over-exposure rate
5. Unsafe execution rate
6. Reference coordination-logic latency
7. Coordination quality
8. Exact workflow match (additional strict metric)

## Latency boundary
Latency measures only lightweight Python reference coordination logic.
It is not LLM inference latency, network latency, or clinical workflow latency.

## Claim boundary
The benchmark is controlled and synthetic, derived from frozen MedVerse
institutional semantics. Results support architectural interpretation within
this benchmark and must not be generalized to external clinical deployment
without further validation.
