# Gate 21A Import Diagnostic Patch

## Observed failure
Spyder raised:

`KeyError: 'medverse'`

while importing `medverse.learning.gate21a_dataset_builder`.

## Classification
Implementation / Python package-structure error.

The failure occurred before the Gate 21A dataset adequacy checks executed.
It is therefore not a scientific or learning-data FAIL.

## Root cause
`medverse/learning/` did not contain `__init__.py`.
Spyder had already loaded/reloaded earlier MedVerse packages, so Python treated
`medverse.learning` as a namespace package and encountered stale namespace state
when the cumulative project directory changed.

## Patch
1. Add `medverse/learning/__init__.py`.
2. Put the current cumulative project root first on `sys.path`.
3. Invalidate import caches.
4. Remove only stale `medverse.learning` namespace entries before importing the
   Gate-21A dataset builder.

## Unchanged
- Gate 21A dataset design
- record count target
- five agents
- train/dev/test thresholds
- split strategy
- labels and actions
- scientific PASS criteria
- all Gates 0-21
