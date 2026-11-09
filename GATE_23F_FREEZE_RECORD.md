# Gate 23F Freeze Record

Status: PASS
Checks: 8/8

Prospective benchmark:
- protocol: MEDVERSE-G23F-RESEARCH-IRB-COMBINATORIAL-v2
- 48 factorial states
- 4 outer folds
- 12 held-out states per fold
- zero interaction-learnability violations
- benchmark SHA256:
  52112275b302101f7031a66ceffde38d1dc59b69233c750bfc771c29ccefbaba

No repair training occurred before this protocol was frozen.

Gate 23G must use:
- Gate-21A TRAIN + non-held-out factorial folds for fitting;
- Gate-21A DEV only for C selection;
- Gate-21A TEST only for ID evaluation;
- the current outer fold only for prospective combinatorial evaluation;
- Research/IRB precedence representation unchanged;
- complete Research/IRB shield v2 unchanged.
