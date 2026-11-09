# Team MedVerse — Gate 31 DT / evidence bridge

This additive checkpoint reconnects the original project-local Digital Twin class and exposes explicit dense/BM25 retrieval. It does not change the Gate 30 selector or repair its C01/C02 commitment failures.

## Run the experiment with automatic PDF/PNG figures
```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate31/MedVerse-Agent/medverse/gates/gate31_dt_retrieval_bridge.py --wdir
```
Adjust the extraction path. By default the dense loader uses only cached model files: unavailable dependencies or weights produce an explicit BLOCKED result, not lexical substitution.

To download the pinned public model on an internet-connected machine:
```bash
python -B medverse/gates/gate31_dt_retrieval_bridge.py --allow-download
```
Spyder accepts script arguments using its run configuration, or:
```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate31/MedVerse-Agent/medverse/gates/gate31_dt_retrieval_bridge.py --args "--allow-download" --wdir
```
Use a separate environment for evidence reproduction rather than upgrading the saved-classifier environment. Python 3.10+ is expected; Python 3.11 is a practical isolated-environment choice. Optional dependencies are in `requirements-gate31.txt`; package installation and native Windows/Spyder behavior were not tested in the build container. Every successful run records actual package versions.
```bash
python -m pip install -r requirements-gate31.txt
```
The original model ID is `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. This release pins model revision `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Original historical runs were unpinned, so identical historical weights cannot be asserted. The model weights are NOT included in the ZIP.

## Launch the integrated evidence workspace
```bash
python -B run_foundation_sandbox.py --open --backend dense --allow-download
```
For the explicitly labelled dependency-free lexical baseline:
```bash
python -B run_foundation_sandbox.py --open --backend bm25
```
Default localhost port: 8765; choose `--port 8766` if the previous sandbox is running. Run old and new launchers in separate processes. Backend selection is visible in the policy page and can be changed explicitly per search. Dense loading failure never silently switches backends. Exact IDs work independently of an embedding dependency, subject to all boundaries.

## What to inspect
1. Start C12; no patient vital signs appear by default.
2. Release events individually. The new DT card shows only released role observations, their provenance, and unestablished S1 telemetry status when no S1 measurements were supplied.
3. Switch role views: the DT's own-domain projections must not show another institution's observations.
4. Keep receiving-workspace metadata separate from actual observations. A context marked valid does not create temperature, SpO2 or other values.
5. Search Korean/English policy queries and inspect the ACTUAL backend, score type, source ID, official link and pending interpretation status.
6. Search `KR-NONEXISTENT-999`: no substitution. Dense nonavailability is not permission to return invented semantic evidence.
7. Export the actual trace; the DT bridge is included. Prior modeled commitment outcomes remain unchanged.

## Outputs and integrity
`outputs/gate31_foundation/<RUN_ID>/` holds tests, original-file integrity, query traces, source scores, environment, blocked-dense status when relevant, DT trajectory, HTTP trace and integration regression. Figures/report are under its `figures/display_<TIMESTAMP>/`.

The main gate saves and displays plots automatically. `--no-show` saves without displaying; `--plot-only --run RUN_ID` regenerates presentation only. No automatic freeze regeneration is provided.

## Boundaries
- The DT is our imported project-local `PatientDigitalTwin`, not a third-party SDK or validated physiological twin.
- All 18 workflows and 40 bilingual intents are known regression material, not new confirmation.
- Deterministic vectors used in one unit test test indexing mathematics only; they are not LM outputs or semantic evaluation.
- Source dates are recorded metadata. Interpretation/current-law and clinical review remain pending.
- Live proposals are existing institution-owned contracts. This release does not add live learned proposal generation.
- `docs/foundation31/NEXT_COMMITMENT_DESIGN_v1.md` freezes the next design only. Its controller and new datasets are not yet implemented/frozen/evaluated.

## Packaged execution evidence
Primary run: `20261103T132213_435523Z`.
- 42/42 engineering fixtures; 11/11 real loopback HTTP checks.
- 432/432 unchanged event outcomes across 18 known families and four methods.
- 31/31 browser checks using actual assets and backend via the documented test-only fetch bridge; managed Chromium blocked direct localhost navigation. Native browser navigation/download dispatch remains unverified.
- An isolated Python invocation reproduced the deterministic summaries. This is not a new installed dependency environment.
- Dense reproduction is BLOCKED here: sentence-transformers was absent and pip failed DNS resolution. No dense scores are manufactured. Optional requirements and explicit download commands are supplied for local execution.

Optional browser regression (requires Playwright and Chromium):
```bash
python -B -m foundation31.browser_check
```
The browser-check module is a supplementary test, not part of the scientific comparison. A code-hash manifest of all added files accompanies the release.
