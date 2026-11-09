# Korean National Cancer Center population context

MedVerse-Agent supports the Republic of Korea **National Cancer Center Cancer Incidence Statistics** dataset as optional population-level oncology context.

- Dataset: `국립암센터_암발생 통계 정보_20260120`
- Public catalogue: https://www.data.go.kr/data/3039563/fileData.do
- Expected local filename: `ncc_cancer_incidence.csv`
- Expected path: `data/external/ncc_cancer_incidence.csv`
- Project manifest: `config/data_manifest.json`

## Important boundary

This dataset contains population-level incidence statistics. It is **not** patient telemetry and must never be used to infer a patient's diagnosis, fill a missing patient measurement, or authorize an institutional action.

The historical data-grounding modules load the CSV only when it is present. The final coordination demonstration can run without the CSV; population context is optional and is kept separate from the patient Digital Twin and from policy evidence.

## Reproducible setup

1. Download the CSV from the public catalogue above.
2. Preserve the source filename and provenance information.
3. Place the validated CSV at `data/external/ncc_cancer_incidence.csv`.
4. Run the data-loading / grounding checks before using it for descriptive context.

Redistribution rights should be checked before committing the source CSV to a public GitHub repository.
