# Gate 0 — Frozen System and Experimental Contract

## Question answered
Can we define the Medical Metaverse coordination problem precisely enough that later code, learning, and evaluation have a stable reference?

## Frozen system model
World state:
S_t = {x_clinical, x_DT, x_network, x_security, x_consent, x_research}

Institutional agent i receives only:
o_i,t = H_i(S_t)

Agent assessment:
d_i,t = pi_i(o_i,t, M_i, K_i)

Coordinator:
a*_t = Pi(d_1,t, ..., d_N,t)

## Frozen initial agents
1. Healthcare Provider Agent
2. Cyber/Network Agent

Later agents (not yet implemented):
3. Privacy Agent
4. Research/IRB Agent
5. Health/AI Regulator Agent

## Frozen flagship scenario
MVKR-S01 — When the Digital Twin Cannot Be Trusted

Progressive events:
- E1 clinical alarm
- E2 network degradation
- E3 device authentication anomaly

## Frozen experimental question
Does explicit mandate-aware institutional coordination improve safe, policy-grounded behavior over simpler single-agent or unconstrained multi-agent designs under partial and asynchronously arriving information?

## Frozen constraints
- Agents cannot access observations outside their visibility boundary.
- Agents cannot execute actions outside their mandate.
- Inter-agent disclosure must be explicit and logged.
- High-risk clinical resolution can require human review.
- Policy claims must be tied to authentic public sources.
- No confidential patient data are required for the demonstrator.

## Frozen primary metrics
- Agent Routing Accuracy (ARA)
- Mandate Compliance Rate (MCR)
- Coordination Success Rate (CSR)
- Conflict/Complementarity Detection Rate (CDR)
- Escalation Accuracy Rate (EAR)
- Policy Grounding Accuracy (PGA)
- Information Leakage Rate (ILR)

## Development rule
No learning/LLM/coordination optimization is introduced until deterministic environment and data gates pass.

## Gate progression
Gate 0: system contract
Gate 1: data loading and schema validation
Gate 2: deterministic environment/state transitions
Gate 3: routing and observation boundaries
Gate 4: two-agent deterministic assessments
Gate 5: deterministic coordinator
Gate 6: policy KB retrieval
Gate 7: optional LLM reasoning adapter
Gate 8: dashboard/demo integration
Gate 9: evaluation harness/baselines
Gate 10: multi-seed/final campaign and standards-gap evidence
