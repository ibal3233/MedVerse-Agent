# Reproduction helpers

Run from the project root with `python -B`. These scripts write NEW observations to the existing new-release output paths: copy the original report/results before rerunning. They do not touch Gate 1–26 artifacts.

- `python -B tools/final_validation/clean_runtime_validation.py`: creates a temporary isolated venv without third-party packages, launches the local runtime on port 8766, performs six API checks, then stops it. That port must be free.
- `python -B tools/final_validation/browser_validation.py`: requires Playwright and an installed Chromium, plus the sandbox running on port 8765. The recorded test rendered actual UI assets with a test-only fetch bridge because this environment prohibited direct browser navigation to localhost. This does not establish native browser navigation/download compatibility. Set `MEDVERSE_CHROMIUM` to a Chromium executable and `MEDVERSE_TEST_BASE` to an alternate local server URL when needed. The script saves real screenshots and test results. Native browser use is via `run_final_sandbox.py --open`.

The browser script captures the full operator dashboard. The scenario data are modeled and contain no actual patient information. Do not point these scripts at a production clinical service. Windows-specific behavior is not claimed as tested.
