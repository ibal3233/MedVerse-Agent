# Implementation and evidence map

- `commitment32/publisher.py`: accepts one released modeled event; rejects future fields, proposal-ID reuse, owner-mismatched timing and deadline redefinition.
- `commitment32/controllers.py`: three timing policies, identical allowed inputs. Bounded methods independently implemented; capable ties expected and retained.
- `commitment32/runtime.py`: original Gate 29 selector and validator, common preparatory handler, append-only receipts, final revalidation. No `reference` or scenario loader import.
- `commitment32/reference.py`: separately coded new-action checks and exhaustive full-information timeline assessment. Evaluation only.
- `commitment32/evaluate.py`: frozen hashes, grouped study, raw traces, same-history checks, intervention probes, historical integration regression.
- `commitment32/tests.py`: development fixtures and negative boundary checks; does not execute confirmation branches.
- `commitment32/figures.py`: measured outcome map, completion/wait trade-off, event trace; automatic PNG/PDF/table/report export and display.
- `data/commitment32/prefix_families.json`: authored scenario-modeling data, grouped split and 40 continuations.
- `data/commitment32/freeze.json`: final methods/data hash freeze created before confirmation, no automatic refreeze.
- `data/commitment32/predecessor_manifest.json`: 1,244 original patched-predecessor file hashes.

The Gate 31 DT and pinned dense evidence bridge are preserved, not reimplemented or reevaluated. The successful Windows dense run reported by the user is not replaced by older archived outputs. This release is an additive commitment laboratory, not a new universal live clinical coordinator.
