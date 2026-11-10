# Team MedVerse — Final GitHub Publication Guide

Repository: https://github.com/ibal3233/MedVerse-Agent

## 1. Work only from the final repository folder

```powershell
cd "D:\experiments\hackathon\Team_MedVerse_Final_Sandbox_Submission_v1.0\MedVerse-Agent"
python verify_final_submission.py
```

The verifier should report all required checks as passing. The optional NCC CSV may remain absent.

## 2. Review the changes before committing

```powershell
git status
git add .
git status
```

Confirm that no `.env`, credentials, virtual environments, caches, private data, or the 508 MB demo MOV are staged.

## 3. Commit and push the final source tree

```powershell
git commit -m "Finalize Team MedVerse hackathon submission"
git push origin main
```

If the repository is private during editing, keep it private until the final review is complete. Before ITU submission, change the repository visibility to **Public**.

## 4. Tag the exact submitted source revision

```powershell
git tag -a v1.0-hackathon -m "ITU AI for Good Sandbox Hackathon submission"
git push origin v1.0-hackathon
```

If the tag already exists and points to an older commit, do not overwrite it silently. Delete/recreate it only after confirming the final commit that should be submitted.

## 5. Create the GitHub Release and upload the final demo

On GitHub: **Releases → Draft a new release → choose `v1.0-hackathon`**.

Release title:

`Team MedVerse — ITU AI for Good Sandbox Hackathon Submission`

Upload the final video as the release asset:

`Team_MedVerse_Demo.mov`

The video is approximately 508 MB, so it should **not** be committed to the normal Git repository.

## 6. Final links for the ITU submission

- Repository: https://github.com/ibal3233/MedVerse-Agent
- Final report: https://github.com/ibal3233/MedVerse-Agent/blob/main/submission/Team_MedVerse_Final_Report_FINAL_CROSS_REFERENCED.pdf
- Knowledge Base overview: https://github.com/ibal3233/MedVerse-Agent/blob/main/docs/knowledge_base/KOREAN_POLICY_KB.md
- Machine-readable KB: https://github.com/ibal3233/MedVerse-Agent/tree/main/data/policy/candidate_v0.4
- Demo release: https://github.com/ibal3233/MedVerse-Agent/releases/tag/v1.0-hackathon

## 7. Final pre-submission check

1. GitHub repository is Public.
2. README renders figures correctly.
3. Final report link opens.
4. KB overview and JSON records open.
5. Demo release asset downloads/plays.
6. `python verify_final_submission.py` passes from a clean local clone.
7. No placeholder links remain in judge-facing documents.
