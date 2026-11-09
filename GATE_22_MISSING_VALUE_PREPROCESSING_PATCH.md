# Gate 22 Missing-Value Preprocessing Diagnostic Patch

## Observed failure
The first LogisticRegression fit raised:

`ValueError: Input X contains NaN.`

## Classification
Preprocessing / implementation deficiency.

The model had not completed its first fit, so this is not a learned-model
performance failure.

## Root cause
Gate-21A intentionally includes institutional states with unknown values, such
as:
- disclosure authorization unknown
- minimum-necessary status unknown
- purpose declaration unknown

JSON `null` values entered `DictVectorizer` as missing values and ultimately
reached LogisticRegression as NaN.

## Patch
Missing values are now encoded as the explicit categorical sentinel:

`__MISSING__`

This preserves the semantic distinction between:
- known true
- known false
- unknown / insufficient evidence

No row is dropped and no numerical imputation is performed.

## Added diagnostic
Gate 22 now writes:

`outputs/gate22/gate22_preprocessing_diagnostic.json`

and aborts before model fitting if any raw `None` remains after preprocessing.

## Frozen components
Unchanged:
- Gate-21A dataset and split
- Privacy Agent feature fields
- target labels
- multinomial logistic-regression model family
- C ∈ {0.1, 1.0, 10.0}
- dev selection metric
- test split
- PASS thresholds
- policy-shield logic
