# Gate 22B — Privacy Agent OOD Error Decomposition & Publication Plots

## Scientific purpose
Diagnose the Gate-22A OOD failure before changing the learner.

## Frozen
- Gate-21A benchmark
- Gate-22 Privacy Agent model family
- C = 1.0
- preprocessing
- policy shield
- OOD benchmark
- Gate-22A PASS/FAIL thresholds

## New capability
Only diagnostic decomposition and publication-quality plotting.

## Diagnostic families
- wrong-jurisdiction precedence
- missing-evidence precedence
- multiple simultaneous policy violations
- audit + policy-violation interactions
- simple vs multi-condition states

## Dataset methodology
The gate writes a machine-readable rationale explaining:
- why the benchmark is synthetic;
- how features are derived;
- how oracle labels are produced;
- why agents receive separate observations;
- why group-aware splitting is used;
- why OOD combinations are needed;
- why learned competence and hard execution safety are measured separately.

## Figures
- ID vs OOD accuracy
- OOD action accuracy by diagnostic family
- decision errors vs shielded safety
- OOD action confusion matrix

Both PNG and PDF versions are generated.

## Next dependency
Only after diagnosis should Gate 22C modify one diagnosed component.
