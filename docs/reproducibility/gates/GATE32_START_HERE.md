# Team MedVerse — Gate 32: bounded commitment control

## What this release does

Implements an additive causal commitment experiment: COMMIT, bounded WAIT, authorized PREPARE, or BLOCK/ESCALATE for actual institution-owned proposals. The original Gate 29 selector and authorization validator are imported unchanged. All effects are modeled. It does not replace the final clinical interface, old gates, or the original DT/dense retrieval components.

The cumulative release starts from Gate 31 PLUS the previously supplied runtime compatibility fix. All 1,244 files of that patched predecessor are preserved byte-for-byte. Your local dense results are separate evidence: this gate does not reload embeddings and does not substitute an archived blocked run for your successful local run.

## Install

Preferred: extract `Team_MedVerse_Cumulative_Gate32.zip` into a new directory.

Small update: merge the ENTIRE `MedVerse-Agent` folder from `Team_MedVerse_Gate32_AddOn.zip` into your Gate 31 project. It includes the same previously supplied Gate 31 compatibility patch. Do not copy only the gate entry file: frozen modules/data/manifests are required. The update contains no replacement Gate 31 output files; your local successful run is preserved. Back up local source modifications first; modified frozen source is correctly rejected rather than silently accepted.

## One command

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate32/MedVerse-Agent/medverse/gates/gate32_commitment_control.py --wdir
```

Terminal, inside `MedVerse-Agent`:

```bash
python -B medverse/gates/gate32_commitment_control.py
```

Python 3.10+; the experiment uses the standard library. Matplotlib is required for PNG/PDF plots and the four-page report. No training, classifier loading, LLM API, network call, or embedding download is performed.

The SAME entry point verifies frozen evidence, executes, saves, exports figures and compact table, then displays using the active backend. In Spyder, figures appear in Plots; `%matplotlib inline` is optional if an earlier session changed its backend. Headless runs save without pretending to open a window.

```bash
# Save all outputs without opening plots
python -B medverse/gates/gate32_commitment_control.py --no-show
# Replot a saved run, without changing measurements
python -B medverse/gates/gate32_commitment_control.py --plot-only --run RUN_ID
# Evaluation only, explicitly omit plotting
python -B medverse/gates/gate32_commitment_control.py --no-plots
```

Outputs: `outputs/gate32_commitment/<RUN_ID>/`.
Core files: `status.json`, `case_metrics.csv`, `strategy_summary.csv`, `paired_comparisons.csv`, `agent_behavior.csv`, `same_history_checks.csv`, `temporal_revalidation.csv`, `reference_outcomes.json`, `raw_traces.json`, `legacy_regression.csv`, `split_audit.json`, environment and freeze. Figures and report: `figures/display_<TIMESTAMP>/`.

## Measured primary result

Four development prefix families / 8 branches; eight internal confirmation prefix families / 32 branches. Three controllers, 120 total runs, 720 events. Branches are correlated, not independent clinical patients.

| Controller | All continuation branches completed | Among 21 offline-feasible branches | Clinical obligation on time when reference-feasible | Mean proposal-wait steps | Invalid commits |
|---|---:|---:|---:|---:|---:|
| Eager | 14/32 | 14/21 | 28/30 | 0.00 | 0 |
| Fair bounded wait | 15/32 | 15/21 | 29/30 | 1.19 | 0 |
| MedVerse commitment | 15/32 | 15/21 | 29/30 | 1.19 | 0 |

MedVerse gains four branches and loses three versus eager commitment. All three losses occur when a currently valid authorization is revoked before the delayed action, without a usable replacement. An earlier valid action is NOT retroactively classified as illegal. Fair bounded wait ties on 32/32 branches. Full-information feasibility is a NONCAUSAL diagnostic bound, not information available to the controllers.

52/52 development checks; 177/177 same-history comparisons; 72/72 nonvacuous change-before-commit probes without effects; 432/432 historical event comparisons unchanged. No unsafe-commit claim outside these modeled tests. Native Windows/Spyder execution remains to be checked locally.

## What is NOT repaired or claimed

- C01/C02 lack visible timing/review contracts. They remain unchanged, not relabelled successful.
- No removal of old effects, implicit rollback, artificial early release of future proposals, or invented approval.
- PREPARE records an authorized local operation, not completed clinical review or released research data.
- Review dates/deadlines are event-model assumptions, not clinical recommendations.
- No unique superiority over a capable stateful timing policy.
- No external clinical/Korean legal interpretation review or production deployment validity.

## Practical decision

Do not turn bounded waiting on globally in the main clinical sandbox. First review which actions can safely be deferred, what observed review condition justifies it, and what authority sets the expiry/urgency. Integrate only the approved experimental profile in a separately evaluated version. Keep the original default path and results reproducible.
