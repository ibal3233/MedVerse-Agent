# External Public Data

Gate 1B uses the National Cancer Center public cancer-incidence CSV.

Authoritative record:
https://www.data.go.kr/data/3039563/fileData.do

Current portal metadata checked in October 2026:
- file name: 국립암센터_암발생 통계 정보_20260120
- 37,050 rows
- years 1999–2023
- CSV
- columns:
  발생연도, 성별, 국제질병분류, 암종, 연령군, 발생자수, 조발생률
- use scope: no restriction

Download the authoritative CSV and save it as:

data/external/ncc_cancer_incidence.csv

Do not rename columns manually. Gate 1B validates the original schema first.
