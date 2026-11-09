# Team MedVerse - integrated coordination demonstration (Gate 30)

This is an ADDITIVE update. All 1,048 prior files remain unchanged. It connects the
frozen Gate 29 selector to a new progressive HTTP/UI runtime; it does not replace
`run_final_sandbox.py` or any earlier gate.

## Launch the integrated interface
From the extracted `MedVerse-Agent` folder:

```bash
python -B run_integrated_sandbox.py --open
```

Address: `http://127.0.0.1:8765`. Stop any older sandbox using that port first, or use
`--port 8766`. Default scenario: **C12**, strategy: **MedVerse harmonizer**.

Spyder:

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate30/MedVerse-Agent/run_integrated_sandbox.py --wdir
```

The local interface uses Python's standard library. It makes no external clinical
requests. The patient representation, proposals, authority records and effects are modeled.

## Run the integration experiment and plot automatically

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate30/MedVerse-Agent/medverse/gates/gate30_integrated_release.py --wdir
```

Or:

```bash
python -B medverse/gates/gate30_integrated_release.py
```

Default: verify freezes, run actual HTTP evaluation, save raw CSV/JSON, export three
non-bar result figures as PNG/PDF and a compact table, then display the plots. Requires
Python 3.10+; Matplotlib is needed only for figures. No saved classifier or embedding
model is loaded. `--no-show` exports without showing; `--no-plots` explicitly skips plots.
`--plot-only --run RUN_ID` reads an existing run without re-evaluation.

## Six-event C12 demonstration
1. Release a modeled Hospital concern. No future proposals or authority records are visible.
2. Release clinical/cyber contracts. Containment, clinical acknowledgement and review commit.
3. Release the original research request. Its denied authority records prevent disclosure.
4. Release a DT context transfer. Inspect the receiving-side checks and committed modeled view.
5. Release institution-owned alternatives and scoped non-research reviews. Research authority is still missing.
6. Release the remaining modeled research reviews. The restricted research view is committed.

Use institution buttons to inspect **operator-only** role projections. The proposal table
shows pre-selection boundary checks; final verdicts are in Decisions & receipts. The new
receipt includes proposal ID, actual contract, owner, source hashes and modeled effect.
The Korean evidence page uses explicit **lexical bilingual BM25**, not dense embeddings.

For change-before-commit: reset, release event 1, expand the challenge panel, check
"Pause next event before commitment", release event 2, revoke modeled authority, and
commit the pending plan. Rejected actions produce no modeled side effect.

## Presentation outputs
`outputs/gate30_integration/<RUN_ID>/figures/display_<TIMESTAMP>/` contains:
- Paired workflow outcome map (snapshot vs progressive final, case by case).
- Event-to-commitment timeline for the actual C12 HTTP trace.
- Empirical HTTP response-time distribution.
- Compact CSV/Markdown table and an all-figures PDF.

The primary packaged run is `20261103T111811_756965Z`. Its performance brief is in
`submission/gate30/`. Do not mix its latency figures with a later run without labelling it.

## Results to report honestly
The capable methods match on snapshot completion (10/10) and progressive final completion
(8/10 of those same cases). Two previously feasible paths become incomplete after earlier
irreversible actions. Four additional families require partial/held outcomes. The 84/84
per-step agreement is conditional on the committed prefix, not universal workflow success.
Read `docs/coordination30/INTERPRETATION.md` before presenting results.

The interface displays the latest evaluated run. The original v1 interface remains available
through `run_final_sandbox.py`. No new model training or confirmation-set tuning is performed.

## Environment / review boundary
Linux HTTP execution was tested; native Windows/Spyder execution remains to be checked.
Managed Chromium blocked localhost navigation: browser checks used the actual assets and
real backend through a documented test-only bridge. Native download dispatch was not tested.
Optional browser reproduction requires Playwright and Chromium:

```bash
python -B -m coordination30.browser_check
```

Clinical and Korean legal review is still pending. This is a demonstrable modeled governance
prototype, not production-ready clinical software, legal authorization, or ITU certification.
