# Gate 30 interpretation - measured integration, not a superiority claim

Primary run: `20261103T111811_756965Z`.

## What was connected
The new local UI and HTTP runtime invoke the unmodified Gate 29 workflow selector.
Each event supplies only released institution-owned action contracts and modeled
source/authority records. Selected proposals are revalidated immediately before
modeled commitment. Receipt IDs refer to the actual proposal, not a scenario substitute.
The runtime retains prior committed effects, detects duplicate plans, and supports
explicit modeled changes between selection and commitment. The old sandbox is untouched.

## Results and denominators
- 41/41 development engineering boundary checks passed.
- 72 HTTP snapshot runs: 18 known families x 4 configurations.
- 72 progressive sessions; 432 event responses: 18 x 4 x 6 releases.
- The comparable 14-family subset contains 10 snapshot-feasible cases. The three
  capable methods each complete 10/10 snapshot-feasible workflows and match the
  reference partial/complete objective on 14/14.
- Progressive final completion is 8/10 of those same feasible cases for all three
  capable methods. Four additional families have no complete snapshot solution and
  appropriately remain partial/held. Do not report 14/14 progressive completion.
- 84/84 per-step reference agreements for each capable method are conditional on
  the already committed prefix. This is NOT optimality with future information.
- 0 observed invalid newly committed actions, 0 duplicate effects, and intact
  receipts across the replay. Tests do not prove universal safety.
- 42/42 separate change-before-commit probes reject all planned actions after an
  authority, purpose or policy-binding change. These are correlated probes.
- Browser: 27/27 functional checks using the real UI assets and running HTTP backend
  via a test-only fetch bridge. Managed Chromium blocked direct local navigation.
  Exported Blob content was verified; native download dispatch was not verified.
- 240 timed event calls across four configurations, 60 each. MedVerse median 7.55 ms,
  p95 16.06 ms on this environment. These are loopback HTTP times, not deployed latency.

## Retained online-coordination limitations
C01: At event 2, the original clinical route is committed under the currently released
contracts. The quarantine action is incompatible with that committed route. The
independent alternative appears later and cannot erase the original commitment.
Clinical review completes, but the joint containment obligation remains incomplete.

C02: At event 2, broad containment is committed. It conflicts with the clinical action.
The narrower containment alternative released later cannot remove the prior effect.
The clinical-review obligation remains incomplete. This shows an availability and
responsibility-handoff limitation, not an unauthorized medical treatment.

All three capable methods share these outcomes through the same eager-commit adapter.
No threshold, constraint, source interpretation, input release timing, or selector was
changed after observing them. The snapshot reference does not model future observations.
The next mechanism question is when to commit, hold for authority, or preserve reversible
options without assuming undisclosed alternatives. Do not "repair" these observations by
silently making future proposals visible earlier or calling a held clinical task complete.

## Publication-ready bounded statement
On a frozen, known-family integration replay, the live HTTP service preserved the
workflow selector's full-information outcomes and rejected the defined changed-authority
probes. The cross-track demonstration completed clinical review at event 2 and restricted
research release at event 6. Progressive arrival exposed two irreversible-choice cases;
no unique advantage over capable planners, clinical validity, legal compliance certification,
or complete ITU conformance is established.

## Evidence locations
`status_measurements.json` preserves the initially measured status. `status.json` adds
presentation and browser status only. Per-case/event CSV and JSON, all HTTP traces,
temporal probes, raw latency observations and browser results are in the run directory.
Figure files are derived from that exact run and carry input/output hash manifests.
