# Gate 24B — Prospective Cyber / Network Confirmation Benchmark Freeze

Gate 24B extends the exact frozen Gate-21A Cyber generator to future groups g5-g8.

No training occurs in this gate.

Future Gate 24C must:
- train only on g0-g2;
- tune only on g3;
- keep g4 diagnostic-only;
- use TRAIN-fitted numeric standardization;
- encode missing `session_origin` explicitly;
- retain training-history diagnostics;
- evaluate once on frozen g5-g8.

Frozen confirmation thresholds:
- action accuracy >= 0.90
- action macro-F1 >= 0.85
- assessment accuracy >= 0.90
- assessment macro-F1 >= 0.80
- every action-class recall >= 0.80
