from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import json
import joblib
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier

MISSING_SENTINEL = "__MISSING__"
DROP_KEYS = {"request_context_index", "study_context_index", "reg_context_index"}

def clean_features(features_json: str) -> Dict[str, Any]:
    x = json.loads(features_json)
    out = {}
    for k, v in x.items():
        if k in DROP_KEYS:
            continue
        out[k] = MISSING_SENTINEL if v is None else v
    return out

def make_classifier(C: float, y):
    unique = sorted(set(y))
    if len(unique) == 1:
        return Pipeline([
            ("vectorizer", DictVectorizer(sparse=True)),
            ("classifier", DummyClassifier(strategy="constant", constant=unique[0])),
        ])
    return Pipeline([
        ("vectorizer", DictVectorizer(sparse=True)),
        ("classifier", LogisticRegression(C=C, max_iter=2000, solver="lbfgs")),
    ])

@dataclass
class InstitutionalModelBundle:
    assessment_model: Any
    action_model: Any
    boundary_model: Any
    enforcement_model: Any
    evidence_model: Any
    chosen_C: float

def train_bundle(rows: List[Dict[str, Any]], C: float) -> InstitutionalModelBundle:
    X = [clean_features(r["features_json"]) for r in rows]

    def fit(field):
        y = [r[field] if r[field] != "" else "NONE" for r in rows]
        model = make_classifier(C, y)
        model.fit(X, y)
        return model

    return InstitutionalModelBundle(
        assessment_model=fit("target_assessment"),
        action_model=fit("target_action"),
        boundary_model=fit("target_boundary_status"),
        enforcement_model=fit("target_enforcement"),
        evidence_model=fit("target_evidence_request"),
        chosen_C=C,
    )

def save_bundle(bundle, path):
    joblib.dump(bundle, path)
