# Shared Data Directory

This repository uses one persistent data directory for all diagnostic gates.

Do NOT create gate-specific copies of datasets.

## External public dataset
Place the authoritative NCC CSV once at:

data/external/ncc_cancer_incidence.csv

Gate 1 validates and fingerprints this file.
Later gates reuse the same validated source when needed.

## Reference scenario
The flagship S1 trace is stored at:

data/reference/MVKR-S01.json

## Policy source metadata
Policy manifests are stored at:

data/policy/

Future policy-ingestion gates will add processed/chunked indexes elsewhere,
but the authoritative source metadata remains shared here.
