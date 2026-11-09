# Gate 3 — Event Routing and Asymmetric Observations

## (1) Question this gate answers
Does the system enforce the institutional information asymmetry required by the MedVerse-Agent formulation?

Specifically:
- Is each event routed only to its authorized institutional agent?
- Is unauthorized observation rejected?
- Does each delivered observation contain only the domain information required by that agent?

This gate does not test agent reasoning, policy retrieval, coordination, LLMs, or learning.

## (2) Frozen
- Gate 0 system model and experimental question.
- Gate 1 data semantics and validated source version.
- Gate 2 deterministic environment and DT-validity semantics.
- S1 event types and `visible_to` declarations.
- Initial agents:
  - hospital_agent
  - cyber_network_agent

## (3) Changed in this gate
Only:
- routing policy
- observation projection
- unauthorized-access guards
- routing/observation diagnostics

No agent assessment logic is introduced.

## (4) PASS/FAIL criteria
Every check must pass:
- E1 routes only to hospital_agent.
- E2 routes only to cyber_network_agent.
- E3 routes only to cyber_network_agent.
- Hospital E1 payload contains only SpO2 and heart_rate.
- Cyber E2 payload contains only packet_loss, rtt_ms, jitter_ms.
- Cyber E3 payload contains only certificate_status and session_origin.
- Hospital access to E2/E3 is rejected.
- Cyber access to E1 is rejected.
- No cross-domain fields leak into authorized observations.
- Scenario `visible_to` metadata exactly matches routing policy.

One failed invariant means Gate 3 FAIL.

## (5) Required outputs
outputs/gate3/
- gate3_routing_trace.csv
- gate3_observation_trace.csv
- gate3_checks.csv
- gate3_status.json

No plot is required. The raw observation trace is more informative at this gate.

## (6) Next action by outcome

### PASS
Freeze routing and observation boundaries.
Proceed to Gate 4: deterministic institutional assessments for Hospital and Cyber/Network agents.

### FAIL: wrong recipient
Compare the scenario `visible_to` field against ROUTE_POLICY.
Do not alter both at once. Determine which is the frozen source of truth and correct only the inconsistent component.

### FAIL: unauthorized access not rejected
Treat as an access-control implementation defect.
Do not proceed to agent reasoning.

### FAIL: payload leakage
Inspect `build_observation()`.
Confirm that it constructs an event-scoped minimal observation rather than copying the full environment state.

### FAIL: scenario/router mismatch
Do not silently normalize.
Identify whether the scenario metadata or routing policy changed after Gate 0 and restore consistency through a controlled change.
