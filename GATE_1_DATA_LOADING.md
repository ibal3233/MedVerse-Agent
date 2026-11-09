# Gate 1 — Data Loading and Validation

## (1) Question this gate answers
Can every required input be loaded reproducibly with known provenance, expected schema, physically valid values, explicit institutional visibility, and no silent repair/substitution?

This gate does NOT ask whether the agents or coordinator are intelligent.

## (2) Frozen
- Gate 0 system model and metrics.
- Flagship scenario MVKR-S01.
- Initial two agents.
- Current NCC source version metadata.
- Event/policy manifest schemas for this gate.

## (3) Changed in this gate
Only the data layer:
- source manifest
- file readers
- schema validators
- range/integrity checks
- data fingerprints
- CSV diagnostic outputs

No agent logic, coordinator, LLM, dashboard, or learning is modified.

## Gate 1A — repository-controlled inputs
PASS requires:
- scenario contains events
- event IDs unique
- time strictly increasing
- event schema complete
- every event has an explicit visibility target
- clinical/network/device fields lie in basic physical domains
- policy manifest contains >=2 documents
- policy IDs unique
- manifest fields complete
- policy URLs use HTTPS
- both initial agents have at least one authorized policy source

## Gate 1B — authoritative NCC public dataset
PASS requires:
- seven expected source columns are present
- exact current-version row count = 37,050
- year coverage = 1999–2023
- incidence counts are numeric and nonnegative
- crude incidence rates are nonnegative when present
- missing crude rate occurs only where incidence count is zero
- key categorical fields are non-empty
- exact duplicate rows = 0

If the external file is absent, status is HOLD, not PASS and not FAIL.

## (5) Required outputs
outputs/gate1/
- gate1a_scenario_checks.csv
- gate1a_policy_manifest_checks.csv
- gate1b_ncc_checks.csv (when external CSV exists)
- gate1_status.json

No plot is required in Gate 1 because this is an integrity/schema gate. Plotting data before schema/semantics are validated can hide structural problems.

## (6) Next action by outcome

### Core PASS + External PASS
Promote Gate 1. Freeze file hashes and move to Gate 2: deterministic Medical Metaverse state-transition environment.

### Core PASS + External HOLD
Do not alter code. Download the authoritative NCC CSV, save as:
data/external/ncc_cancer_incidence.csv
Then rerun Gate 1.

### Any FAIL
Do not tune thresholds or modify agent logic.
Read the failed row(s) in the Gate 1 CSV.
Classify the cause:
1. source/version change,
2. encoding/header mismatch,
3. malformed public data,
4. reference-trace construction error,
5. validator implementation error.

Run the smallest targeted diagnostic against that cause. Change only the supported component and rerun the entire Gate 1 regression suite.
