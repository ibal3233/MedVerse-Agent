# Gate 31 runtime compatibility and plotting amendment — v1.0.1

This patch addresses the warnings reported for local run `20261104T003737_462827Z`.
It does not retune or repair the retrieval method, alter the modeled policy rules,
change the Digital Twin, or implement the Gate 32 commitment controller.

## Changes

1. Prefer `get_embedding_dimension()`; fall back to the legacy method only when
   the current API is absent. The required output dimension remains 384.
2. Count untruncated document/query token lengths with `verbose=False` ONLY in the
   intentional diagnostic call. The token IDs from that audit never enter model
   inference. The actual `model.encode` calls and their warnings remain unchanged.
   New traces record source IDs, raw token counts, excess tokens, and query lengths.
3. Respect an existing interactive backend. Inside IPython/Spyder, recover from
   non-interactive Agg through `%matplotlib inline`. Record display dispatch in
   the presentation manifest. A genuinely headless process saves files and prints
   a clear message rather than calling an unusable Agg `.show()`.
4. Derive next-dependency text from the recorded dense result. A successful dense
   evaluation is no longer told to execute that path as though it had not run.

No model ID/revision, 128-token limit, retrieval text, corpus, target label, split,
source filter, cosine calculation, normalization, top-k, threshold, authority rule,
or earlier raw result is changed. No global warning suppression is used.

## Install

Extract `Team_MedVerse_Gate31_Runtime_Compatibility_Fix.zip` and merge the included
`MedVerse-Agent` directory into your EXISTING cumulative Gate 31 project. Accept
replacement of the listed patch files. Do not delete the existing project.

The entire patch must be merged: the source is freeze-checked. The replacement
`data/foundation31/freeze.json` is an explicit compatibility amendment. Its
original freeze time is retained. Original source files and the earlier manifest
are archived in `before/`, and old/new SHA-256 values are in
`AMENDMENT_MANIFEST.json`. Do not regenerate or bypass the freeze check.

The original main gate script is unchanged; its imported implementation receives
the update. No new plotting launcher is necessary. No `outputs/` files are shipped
in the patch, so your local successful dense run is not overwritten.

Restart the Spyder kernel after merging to avoid retaining already-imported code.

### Replot the successful local run WITHOUT rerunning its experiment

In Spyder:

```python
%matplotlib inline
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate31/MedVerse-Agent/medverse/gates/gate31_dt_retrieval_bridge.py --wdir --args "--plot-only --run 20261104T003737_462827Z"
```

Terminal equivalent, from `MedVerse-Agent`:

```bash
python -B medverse/gates/gate31_dt_retrieval_bridge.py --plot-only --run 20261104T003737_462827Z
```

Replotting reads existing results. It neither reloads the embedding model nor adds
new token-length measurements. It writes a fresh `figures/display_<timestamp>/`
directory inside the selected run. Dense rank plots are rendered from your actual
`dense_query_metrics.csv`; no per-query ranks are invented from console totals.

### Future full runs

Your usual entry point remains:

```python
%runfile D:/experiments/hackathon/Team_MedVerse_Cumulative_Gate31/MedVerse-Agent/medverse/gates/gate31_dt_retrieval_bridge.py --wdir
```

It evaluates, saves raw results, exports PNG/PDF and the compact table, and shows
figures with the active backend. With cached weights available, no new download
is required. The next full run also records the added token diagnostics.

Spyder normally shows inline figures in its Plots pane. Uncheck **Mute inline
plotting** there to display the figures in the console as well.

## Scientific interpretation of the user's local console

The following figures are transcribed from the supplied console. They are not a
new independent model run and do not replace the user's full raw artifacts.

| Historical confirmation subset | BM25 top-1 | Dense top-1 | BM25 Recall@3 | Dense Recall@3 |
|---|---:|---:|---:|---:|
| English | 16/20 | 13/20 | 17/20 | 19/20 |
| Korean | 14/20 | 10/20 | 17/20 | 15/20 |

Both methods return the frozen target within the top three on 34/40 language-query
records. Both-language success is 16/20 intent families for BM25 and 15/20 for dense.
This is a known-input regression, not fresh confirmation or arbitrary-language
independence. Dense improves English Recall@3 but does not dominate BM25.

The length warning is consistent with the untruncated diagnostic in the archived
code. A completed encoder run is not evidence that every token was represented.
Inspect the original trace's `documents_exceeding_model_limit`, and the new
`document_token_lengths` / `query_token_length` diagnostics after a full rerun.
Do not increase the token limit, reorder bilingual fields, change chunking, or tune
by language after seeing these confirmation outcomes without a separately
specified development/confirmation experiment.

The logged revision is constructor-pinned; `resolved_revision: null` is not a
confirmed mismatch, but the console does not independently identify the loaded
weight files. Retain the environment and cache/artifact provenance.

The 11 HTTP checks in Gate 31 are explicitly BM25 checks. A successful dense
benchmark is not itself proof of a dense live-interface HTTP test. The distinct
causal commitment study remains the next scientific task; C01/C02 are unchanged.

## Validation of this amendment

- 27 runtime/API/diagnostic/display tests passed.
- Original 42 engineering checks and 11 HTTP checks passed.
- 432/432 integration comparisons preserved the original modeled event outcomes.
- BM25 summary matched the archived run exactly.
- A deterministic fixture encoder produced identical ordered IDs and scores before
  and after the patch on all 80 query records. This is a mechanics check, NOT a
  real-model accuracy evaluation.
- The preserved 1,118 predecessor files all verified unchanged.
- PDF/PNG exports rendered successfully; the four-page report was inspected.
- Agg-to-inline recovery was exercised in an actual IPython session. This
  environment reports the canonical alias `inline` after recovery.
- Real SentenceTransformer weights were NOT rerun in the patch environment
  (`sentence_transformers` is unavailable). User-reported Windows dense scores
  remain the evidence for actual model performance.
- Native Windows/Spyder GUI behavior remains locally unverified.

References used for API/display verification:
- https://sbert.net/docs/package_reference/sentence_transformer/model.html
- https://sbert.net/examples/sentence_transformer/applications/computing-embeddings/README.html
- https://huggingface.co/docs/transformers/main_classes/tokenizer
- https://matplotlib.org/stable/users/explain/backends.html
- https://docs.spyder-ide.org/current/panes/plots.html
