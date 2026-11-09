from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List
import json
import joblib

from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier

DROP_KEYS = {"request_context_index", "study_context_index", "reg_context_index"}


def clean_features(features_json: str) -> Dict[str, Any]:
    x = json.loads(features_json)
    out = {}
    for k, v in x.items():
        if k in DROP_KEYS:
            continue
        out[k] = "__MISSING__" if v is None else v
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
        ("classifier", LogisticRegression(
            C=C,
            max_iter=3000,
            solver="lbfgs",
        )),
    ])


@dataclass
class CyberModelBundle:
    assessment_model: Any
    action_model: Any
    chosen_C: float


def train_bundle(rows: List[Dict[str, Any]], C: float) -> CyberModelBundle:
    X = [clean_features(r["features_json"]) for r in rows]

    ya = [r["target_assessment"] for r in rows]
    yact = [r["target_action"] for r in rows]

    ma = make_classifier(C, ya)
    mact = make_classifier(C, yact)

    ma.fit(X, ya)
    mact.fit(X, yact)

    return CyberModelBundle(
        assessment_model=ma,
        action_model=mact,
        chosen_C=C,
    )


def save_bundle(bundle, path):
    joblib.dump(bundle, path)


def solver_iterations(model) -> int:
    clf = model.named_steps["classifier"]
    if hasattr(clf, "n_iter_"):
        return int(max(clf.n_iter_))
    return 0
