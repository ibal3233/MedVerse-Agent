# Final submission checklist

## Ready in this package

- [x] Runnable sandbox and historical reproducibility evidence
- [x] Final five-page technical report followed by annex
- [x] GitHub-style `submission/TECHNICAL-REPORT.md`
- [x] 6:45 demo video and captions
- [x] Korean policy-KB documentation
- [x] Y.3172 / AI Readiness / standards mapping
- [x] Digital Twin, retrieval and coordination figures
- [x] NCC population-context documentation
- [x] Final release verification script

## Manual steps before public submission

- [ ] Create/push the public GitHub repository.
- [ ] Insert the final GitHub URL into any report header that still contains a placeholder and regenerate that PDF/DOCX.
- [ ] Verify `python verify_final_submission.py` on the exact public checkout.
- [ ] Verify `python -B run_presenter_sandbox.py --open --backend bm25` in a clean environment.
- [ ] Verify dense mode separately if it will be shown in the final video/demo.
- [ ] Test trace export/download in the native browser used for judging.
- [ ] Confirm source redistribution rights; do not publish primary-source files or NCC CSV unless permitted.
- [ ] Create Git tag/release `v1.0-hackathon` and attach final report/video/results as appropriate.
- [ ] Verify every external link in README and report.

Do not tune frozen experimental results during release preparation. Any defect correction must be versioned and regression-tested.
