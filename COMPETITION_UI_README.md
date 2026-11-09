# MedVerse-Agent Competition UI

## Purpose
Competition-facing real-time command center for the MedVerse-Agent Medical Metaverse demonstrator.

## Run

From Anaconda Prompt:

```bash
cd D:\experiments\hackathon\MedVerse-Agent-Competition-UI\MedVerse-Agent
pip install -r requirements-competition-ui.txt
streamlit run demo\competition_app.py
```

Or double-click:

`RUN_COMPETITION_UI.bat`

## Demonstration controls

- **Scenario selector** — S1 to S4
- **Next Event** — release one event at a time
- **Auto Run** — run the scenario as a short real-time sequence
- **Reset** — restore initial state

## What is live in the UI

The UI calls the actual project components:
- deterministic S1 Medical Metaverse pipeline
- Privacy / Research-IRB / Regulator agents
- institutional routing and mandates
- S2-S4 policy coordinator
- multilingual semantic policy retrieval
- actual policy seed metadata

The event timing is simulated for demonstration. The system is not connected to a live hospital.

## Judge demo sequence

Recommended:
1. Start with S1.
2. Click **Next Event** once: clinical deterioration appears.
3. Click again: network degradation appears and DT becomes degraded.
4. Click again: identity anomaly appears and DT becomes unverified.
5. Point out the minimum-necessary message exchange.
6. Point out the coordinator response and human review.
7. Open S2 to demonstrate care vs research scope.
8. Open S3 to demonstrate stale-DT / high-impact AI control.
9. Open S4 to demonstrate disclosure blocking.
10. Point to policy provenance and official article metadata.

## Important Gate 13 behavior

The header checks for:
`outputs/gate13/gate13_status.json`

If Gate 13 has not passed, it displays:
`PGA FINAL VALIDATION PENDING`

After Gate 13 PASS, it automatically displays:
`FULL PGA VALIDATED`

This prevents the interface from claiming evidence that has not yet been generated.
