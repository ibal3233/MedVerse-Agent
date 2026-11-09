# Demo-Day Checklist

## Before opening the room
- Activate the same Anaconda environment used for Gates 7A, 12 and 13.
- Confirm `sentence-transformers` and `streamlit` import successfully.
- Launch the UI once so model weights are already cached.
- Run S1 from Reset to completion once.
- Confirm header says `FULL PGA VALIDATED`.
- Confirm S1 policy cards render.
- Confirm S2, S3 and S4 all complete.
- Keep the Gate 13 console output saved as backup evidence.

## During the demo
- Use **Next Event** for S1. Do not use Auto Run for the first scenario.
- Do not spend time reading every action.
- Emphasize bounded observation, minimum-necessary exchange, coordinator reasoning,
  human escalation, and article-level provenance.
- Use Auto Run only for S2-S4 if time is short.

## Failure-safe response
If semantic policy retrieval fails:
- continue the operational scenario;
- show the explicit “policy retrieval unavailable” state;
- use the saved Gate 13 PASS result as validated evidence;
- do not claim the failing runtime retrieved a policy record.

## Avoid
- calling the system clinically deployed;
- calling the events live hospital data;
- saying an LLM makes the final decision;
- claiming legal certification.
