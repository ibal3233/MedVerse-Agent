# Team MedVerse — Gate 33: live commitment workspace

## Release purpose

Expose the tested Gate 32 commitment controller in a separate, progressive operator interface. No controller, selector, policy, deadline, observation, scenario or earlier outcome is changed. The entire 1,328-file cumulative Gate 32 predecessor is preserved byte-for-byte.

The original clinical / Digital Twin workspace remains available at `/foundation` on the same local host, with its earlier coordination behavior. These are separate modeled sessions, not a newly unified patient-state model. Timing contracts are experimental and review-pending; waiting has NOT been enabled globally in the original workflow. No approval, clinical intervention or research disclosure is real.

## Recommended installation

To preserve local dense-retrieval and other saved results, merge the complete `MedVerse-Agent` directory from the Gate 33 add-on into the existing cumulative Gate 32 project. No existing files are replaced by this add-on. Alternatively, extract the complete cumulative Gate 33 package to a new directory.

A freeze check rejects modified or missing earlier source/evidence files instead of silently accepting them. Additional timestamped local runs are allowed. Keep your successful local Gate 31 dense output; this package does not substitute an archived blocked run for it.

## Launch the operator interface

Inside `MedVerse-Agent`:

```bash
python -B run_commitment_sandbox.py --open --backend dense
```

For a first explicit model download on an internet-connected machine:

```bash
python -m pip install -r requirements-gate31.txt
python -B run_commitment_sandbox.py --open --backend dense --allow-download
```

Use the working evidence environment from your successful Gate 31 run. Do not upgrade the saved-classifier environment just to run this interface. The evidence service is lazy: the dense model loads only when a dense query is requested. There is no automatic fallback to BM25.

An explicitly lexical demonstration:

```bash
python -B run_commitment_sandbox.py --open --backend bm25
```

Spyder:

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate32/MedVerse-Agent/run_commitment_sandbox.py --wdir
```

Adjust the folder if using the new cumulative package. Open `http://127.0.0.1:8765`. Stop an old server on that port first or use `--port 8766`. Restart the kernel when switching project copies to avoid cached imports from a different release.

## Suggested inspection sequence

1. Keep P01 / PROMPT / MedVerse commitment selected. Release E1. Inspect the visible review reason, wait expiry and actual PREPARE receipt. COMMIT proposals awaiting prerequisites have **NO EFFECT**.
2. Release E2. Observe the alternative clinical-review route and containment effects. Inspect Hospital and Cyber role panels.
3. Open Decisions & receipts; export the actual released trace. The export excludes future fixture events.
4. Start P04 / NO_REPLACEMENT. Compare eager and MedVerse in separate sessions. Waiting can lose an earlier valid research opportunity when authorization is revoked. No historical disclosure is retroactively labelled invalid.
5. Start P07 / APPROVAL to inspect the Regulator-owned oversight contract. Missing human authority remains pending; preparation cannot manufacture approval.
6. Start P01 again, enable pause-before-commit, release E1, revoke modeled authority and attempt commitment. Inspect the rejected receipt. Cancellation cancels only an uncommitted plan, not past effects.
7. Search policy evidence in Korean and English. The displayed backend and score type are explicit; unknown exact identifiers are not replaced by similar articles.
8. Open the original DT/clinical workspace through its link. It remains a separate scenario session with the original `PatientDigitalTwin` adapter. The commitment workspace does not invent physiological measurements from proposal contracts.

Operator continuation labels configure the test fixture; they never enter the controller. Role panels are operator inspections, not peer-to-peer sharing or proof of real multi-tenant identity security.

## One-command evaluation and automatic plots

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate32/MedVerse-Agent/medverse/gates/gate33_commitment_workspace.py --wdir
```

Or:

```bash
python -B medverse/gates/gate33_commitment_workspace.py
```

The SAME script verifies the freeze, performs actual loopback HTTP replays, saves CSV/JSON, exports a compact table and PDF/300-dpi PNG figures, then displays figures. Python 3.10+; Matplotlib for figures. Embeddings and saved classifiers are not required for the main integration evaluation; a separate dense endpoint probe reports its status honestly.

```bash
# No interactive display
python -B medverse/gates/gate33_commitment_workspace.py --no-show
# Evaluation only
python -B medverse/gates/gate33_commitment_workspace.py --no-plots
# Existing measured run, no experiment rerun
python -B medverse/gates/gate33_commitment_workspace.py --plot-only --run RUN_ID
# Optional frontend test: Playwright + installed Chromium required
python -B medverse/gates/gate33_commitment_workspace.py --browser --no-show
```

Native Windows/Spyder execution was not independently tested here. For inline plots, `%matplotlib inline` is available; the shared plotting helper also handles Agg inside IPython.

## Measured primary evidence

Primary run: `20261104T035439_172645Z`.

- 47/47 HTTP/projection/integration checks.
- 120 controller replays; 720/720 identical online event states and 120/120 identical full traces versus direct frozen-engine execution.
- 177/177 same-history checks.
- 72/72 nonvacuous change-before-commit probes without new effects.
- 432/432 original clinical/DT event outcomes preserved.
- Historical summary unchanged: eager 14/32; fair bounded wait and MedVerse 15/32. Four gains / three losses and the capable-control tie remain.
- Frontend: 30/30 checks using actual assets and real HTTP backend through a documented test fetch bridge. Managed Chromium blocked native localhost navigation. Actual export Blob content was checked, but native browser download dispatch and Windows behavior remain untested.
- Dense endpoint: blocked in this execution environment; your successful local Gate 31 dense measurements remain separate evidence. No new dense ranking scores are claimed.

Outputs: `outputs/gate33_workspace/<RUN_ID>/`. Inspect `status.json`, `checks.json`, `http_exports.json`, event/trace comparisons, per-role counts, authority probes, original-path regression, browser validation and figures. The browser script is a test harness: it does not alter the runtime or fabricate backend results. The first environment-related browser failure is retained.

## Interpret carefully

This is known-case integration regression, not new confirmation. Agent counts describe proposal-event opportunities and actual effects, not learned predictive accuracy. Clinical and Korean legal review remain pending. No claim of universal language support, unique algorithm superiority, remote institutional authenticity, production security, or ITU certification is made.

A presentation-only amendment archived the prior figure/CSS/freeze files. It changed axis labels, a log-scale latency display, a goal line break, and the illustrative timeline's stop-at-achievement rule; measurements and scientific modules did not change. All raw unselected-proposal decisions remain available.

Next: verify the selected release on your Windows browser, obtain qualified review of the active timing/source interpretations, and consolidate the five-page submission and updated video from this exact release. Do not start another tuning cycle on these known scenarios.
