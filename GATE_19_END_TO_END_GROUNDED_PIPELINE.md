# Gate 19 — End-to-End Grounded MedVerse Pipeline

## 1. Scientific question

Can the previously validated modules operate as one complete system across S1-S4
without violating data, jurisdiction, mandate, or policy boundaries?

## 2. Frozen components

- Patient Digital Twin semantics from Gate 14
- evidence-bundle access partitions from Gate 15
- Korean Policy Corpus from Gate 16
- MiniLM + jurisdiction/agent filters + policy boundary from Gate 17
- MedVerse policy-aware harmonization from Gate 18
- NCC population-data safety boundary

## 3. New dataset

`data/evaluation/gate19_end_to_end_cases.json`

Four controlled system-state cases:
- S1: clinical alarm + network degradation + security anomaly
- S2: care allowed + research consent withdrawn
- S3: high-impact AI + unverified Digital Twin
- S4: excessive disclosure + urgent care context

These are evaluation fixtures, not patient diagnosis records.

## 4. Agents exercised

- S1: Hospital, Cyber/Network
- S2: Privacy, Research/IRB
- S3: Regulator
- S4: Hospital, Privacy

All five institutional agents are therefore exercised.

## 5. New integration file

`medverse/integration/gate19_grounded_pipeline.py`

Connects:
1. PatientDigitalTwin
2. EvidenceBundleBuilder
3. DataPolicyGroundedAgent
4. JurisdictionAwarePolicyKB
5. PolicyBoundaryValidator
6. MedVersePolicyAwareCoordinator
7. judge-facing trace

## 6. Important interface change

Older grounded agents may propose multiple operational actions.
Gate 17 validates one proposed action at a time.

Gate 19 therefore selects one representative policy-boundary action per agent
for validation, while preserving the original full recommendation list in the
audit trace.

This is an adapter only; it does not alter agent reasoning or Gate-17 logic.

## 7. NCC data use

The real NCC CSV is used, when present, only through `NCCCancerContext`.

It remains:
- population-level;
- descriptive;
- accessible only to Hospital and Research/IRB through EvidenceBundleBuilder;
- prohibited from becoming patient-level diagnosis/risk probability.

## 8. Expected scenario outcomes

- S1 -> COMPLEMENTARY_RISK
- S2 -> CARE_CONTINUES_RESEARCH_RESTRICTED
- S3 -> EVIDENCE_INSUFFICIENT_HIGH_IMPACT_AI_BLOCKED
- S4 -> DISCLOSURE_BLOCKED

## 9. Gate outputs

`outputs/gate19/`
- `gate19_status.json`
- `gate19_checks.json`
- `gate19_full_results.json`
- `gate19_judge_trace.csv`

## 10. PASS conditions

- all S1-S4 expected outcomes correct
- all five institutional agents exercised
- selected institutional actions policy-compliant
- policy evidence present
- zero unauthorized evidence use
- zero patient-level inference from population data
- complete judge-facing trace
- deterministic replay

## 11. Next gate after PASS

Gate 20 should integrate this validated end-to-end trace into the Streamlit
competition interface and make the following visible to judges:

Digital Twin state -> institutional assessments -> retrieved Korean policy ->
policy compliance boundary -> MedVerse-Agent coordination -> final outcome.

Gate 20 is therefore presentation/integration validation, not another change to
the scientific decision logic.
