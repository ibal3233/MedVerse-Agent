from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
import pandas as pd

EXPECTED_COLUMNS = [
    "발생연도",
    "성별",
    "국제질병분류",
    "암종",
    "연령군",
    "발생자수",
    "조발생률",
]

class NCCCancerContext:
    """
    Descriptive epidemiological context adapter.

    IMPORTANT:
    Output is population-level context only.
    It must not be interpreted as an individual diagnosis, prognosis,
    or patient-level cancer probability.
    """

    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(self.csv_path)

        self.df = self._load()
        self._validate()

    def _load(self):
        errors = []
        for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
            try:
                return pd.read_csv(self.csv_path, encoding=enc)
            except UnicodeDecodeError as exc:
                errors.append((enc, str(exc)))
        raise ValueError(f"Could not decode NCC CSV: {errors}")

    def _validate(self):
        missing = [c for c in EXPECTED_COLUMNS if c not in self.df.columns]
        if missing:
            raise ValueError(
                f"NCC CSV missing expected columns: {missing}"
            )

    def query(
        self,
        *,
        cancer_type: Optional[str] = None,
        sex: Optional[str] = None,
        age_group: Optional[str] = None,
        year: Optional[int] = None,
    ) -> Dict:
        q = self.df

        if cancer_type is not None:
            q = q[q["암종"].astype(str) == str(cancer_type)]
        if sex is not None:
            q = q[q["성별"].astype(str) == str(sex)]
        if age_group is not None:
            q = q[q["연령군"].astype(str) == str(age_group)]
        if year is not None:
            q = q[q["발생연도"].astype(int) == int(year)]

        rows = int(len(q))

        incidence_count_sum = (
            float(pd.to_numeric(q["발생자수"], errors="coerce").fillna(0).sum())
            if rows else 0.0
        )

        crude_rate_mean = (
            float(pd.to_numeric(q["조발생률"], errors="coerce").dropna().mean())
            if rows else None
        )

        return {
            "scope": "population_epidemiological_context",
            "source": "Korean National Cancer Center open cancer-incidence data",
            "filters": {
                "cancer_type": cancer_type,
                "sex": sex,
                "age_group": age_group,
                "year": year,
            },
            "matched_rows": rows,
            "incidence_count_sum": incidence_count_sum,
            "mean_crude_incidence_rate": crude_rate_mean,
            "patient_level_probability": None,
            "clinical_inference_permitted": False,
            "warning": (
                "Population-level descriptive context only; "
                "not an individual diagnosis or risk probability."
            ),
        }
