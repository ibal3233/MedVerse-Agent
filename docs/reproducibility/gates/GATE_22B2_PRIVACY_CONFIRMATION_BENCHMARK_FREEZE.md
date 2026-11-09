# Gate 22B.2 — Privacy Precedence-Oracle Adoption & Fresh Confirmation Benchmark Freeze

## Purpose
Gate 22B.1 showed:
- no conflict between Gate-21A's eight observed Privacy templates and Gate-22A;
- but Gate-21A did not define the richer simultaneous-condition precedence
  semantics exercised by Gate-22A.

This gate therefore explicitly versions/adopts those semantics before final
Privacy confirmation.

## Adopted oracle
`KR-PRIVACY-PRECEDENCE-v2`

This is an explicit methodological adoption. It must not be described as a
precedence rule already learned from the original Gate-21A dataset.

## Fresh benchmark
Complete policy-state factorial:

- jurisdiction: 3
- disclosure authorization: 3
- minimum necessary: 3
- purpose declared: 3
- audit required: 2

Core states:

`3 × 3 × 3 × 3 × 2 = 162`

Each state is evaluated under three request-context values that never appeared
in Gate-21A or Gate-22A:

- institutional quality review
- cross-institutional referral
- data-governance audit

Total:

`162 × 3 = 486 records`

## Freshness boundary
Exact model-visible records have zero overlap with:
- Gate-21A;
- Gate-22A;
- Gate-22C augmentation.

Core-state overlap is reported explicitly. This is confirmation of the adopted
precedence semantics and context invariance, not externally novel law.

## Next training gate
Gate 22B.3 must:
- train on Gate-21A TRAIN + Gate-22C augmentation;
- never add the opened Gate-22A OOD cases;
- rerun C selection using DEV only;
- save a hyperparameter results table;
- retain valid non-epoch training-history plots;
- evaluate once on this frozen confirmation benchmark.

## Reporting standard
Hyperparameter-selection table contains TRAIN/DEV only.
TEST/confirmation results appear in a separate evaluation table.
