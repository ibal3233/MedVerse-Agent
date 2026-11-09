from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List
import json

import joblib
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


DROP_KEYS = {
    "request_context_index",
    "study_context_index",
    "reg_context_index",
}


MISSING_SENTINEL = "__MISSING__"


def clean_features(features_json: str) -> Dict[str, Any]:
    """
    Convert the structured Privacy Agent state into a DictVectorizer-safe form.

    Missing values are semantically meaningful in this benchmark
    (e.g. unknown disclosure authorization), so they are represented as an
    explicit categorical state rather than dropped or numerically imputed.
    """
    x = json.loads(features_json)

    cleaned = {}
    for k, v in x.items():
        if k in DROP_KEYS:
            continue

        if v is None:
            cleaned[k] = MISSING_SENTINEL
        else:
            cleaned[k] = v

    return cleaned


def make_classifier(C: float) -> Pipeline:
    return Pipeline([
        ("vectorizer", DictVectorizer(sparse=True)),
        ("classifier", LogisticRegression(
            C=C,
            max_iter=2000,
            solver="lbfgs",
        )),
    ])


@dataclass
class PrivacyAgentModelBundle:
    assessment_model: Any
    action_model: Any
    boundary_model: Any
    enforcement_model: Any
    evidence_model: Any
    chosen_C: float

    def predict(self, features: Dict[str, Any]) -> Dict[str, str]:
        X = [features]
        return {
            "assessment": self.assessment_model.predict(X)[0],
            "action": self.action_model.predict(X)[0],
            "boundary_status": self.boundary_model.predict(X)[0],
            "enforcement": self.enforcement_model.predict(X)[0],
            "evidence_request": self.evidence_model.predict(X)[0],
        }


def train_bundle(train_rows: List[Dict[str, Any]], C: float) -> PrivacyAgentModelBundle:
    X = [clean_features(r["features_json"]) for r in train_rows]

    def fit(target):
        model = make_classifier(C)
        y = [r[target] if r[target] != "" else "NONE" for r in train_rows]
        model.fit(X, y)
        return model

    return PrivacyAgentModelBundle(
        assessment_model=fit("target_assessment"),
        action_model=fit("target_action"),
        boundary_model=fit("target_boundary_status"),
        enforcement_model=fit("target_enforcement"),
        evidence_model=fit("target_evidence_request"),
        chosen_C=C,
    )


def save_bundle(bundle: PrivacyAgentModelBundle, path):
    joblib.dump(bundle, path)


def load_bundle(path):
    return joblib.load(path)
