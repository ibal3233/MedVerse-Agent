# MedVerse-Agent

Diagnostic-gated development repository for the ITU AI for Good Sandbox Hackathon.

## Repository design

This is ONE persistent project.

Do not create or maintain separate working folders such as:
- MedVerse-Agent-Gated-v0.1
- MedVerse-Agent-Gated-v0.2
- MedVerse-Agent-Gated-v0.3

Those labels are only release snapshots.

Your actual development folder should remain:

MedVerse-Agent/

## Shared data

Place the validated NCC dataset once at:

data/external/ncc_cancer_incidence.csv

All current and future gates share this data directory.

## Current gates

### Gate 0
Frozen system model, assumptions, experimental question, constraints and metrics.

### Gate 1
Data loading, source provenance, schema checks and dataset fingerprinting.

Run:
python -m medverse.gates.gate1_data_loading

### Gate 2
Deterministic Medical Metaverse state-transition environment.

Run:
python -m medverse.gates.gate2_environment

## Next gate

Gate 3 will add:
- event routing
- institutional observation boundaries
- explicit asymmetric visibility

No agent reasoning or coordination optimization will be added until Gate 3 passes.

See:
- GATE_0_FROZEN_SPEC.md
- GATE_1_DATA_LOADING.md
- GATE_2_DETERMINISTIC_ENVIRONMENT.md
- WORKFLOW.md
