# Team MedVerse final sandbox release manifest

Release: **v1.0-hackathon candidate**  
Prepared: **5 November 2026**  
Project files in package: **1492**  
Working-tree size: **234M**

## Key artifact hashes

| Artifact | SHA-256 |
|---|---|
| Final report PDF | `f2bc52796f446c4c440568ef4b49a14f28b687960b1963720bbaed725fe6095c` |
| GitHub technical report | `a770cbb86b8f432988a71a609b8a205e0d9f3c2b47716c7cea2dfa27e939076f` |
| Demo video | `feaff5f6757c487311c9cde0f8121e6bf00220d65d1cd520702248c64b9b74dc` |

## Public entry points

- `README.md` — repository landing page
- `submission/TECHNICAL-REPORT.md` — detailed GitHub technical report
- `submission/Team_MedVerse_Final_Report_RC4.pdf` — official report + annex
- `submission/demo/Team_MedVerse_Demo.mp4` — 6:45 demo
- `docs/knowledge_base/` — Korean policy-KB documentation
- `docs/standards/` — Y.3172 / readiness / standards mapping
- `docs/evaluation/` — selected presentation evidence
- `verify_final_submission.py` — release package verifier

## Evidence policy

Historical gate files and output directories are retained for reproducibility. Public documentation refers to experiments by scientific function rather than requiring readers to understand internal gate numbering.

## Remaining manual release steps

1. Push the exact verified tree to the final GitHub repository.
2. Insert the resulting GitHub URL into any report header that still contains a placeholder and regenerate that report artifact.
3. Verify the clean public checkout and native browser downloads.
4. Confirm redistribution rights for external primary-source files and optional NCC CSV.
5. Tag the release `v1.0-hackathon`.
