from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

@dataclass
class PolicyHit:
    chunk_id: str
    document_id: str
    title: str
    locator: str
    score: float
    jurisdiction: str
    authority: str
    source_type: str
    official_url: str
    agent_access: List[str]
    normative_weight: str

    def to_dict(self):
        return asdict(self)

class JurisdictionAwarePolicyKB:
    """
    Semantic retrieval with hard pre-retrieval constraints.

    Order:
      1. retrieval_eligible
      2. jurisdiction
      3. agent_access
      4. semantic similarity

    Semantic similarity can rank only records that have already passed
    the authority boundary.
    """

    def __init__(self, records_path, deployment_jurisdiction="KR",
                 model_name=MODEL_NAME, extra_records=None):
        self.records_path = Path(records_path)
        payload = json.loads(self.records_path.read_text(encoding="utf-8"))
        self.kb_version = payload.get("kb_version")
        self.records = list(payload["records"])
        if extra_records:
            self.records.extend(extra_records)
        self.deployment_jurisdiction = deployment_jurisdiction
        self.model_name = model_name
        self.model = None
        self._cache = {}

    def load_model(self):
        if self.model is not None:
            return self.model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required. "
                "Install with: pip install sentence-transformers"
            ) from exc
        self.model = SentenceTransformer(self.model_name)
        return self.model

    @staticmethod
    def _locator(r):
        return (
            r.get("article")
            or r.get("section")
            or r.get("source_locator")
            or ""
        )

    @staticmethod
    def _text(r):
        fields = [
            r.get("title_ko", ""),
            r.get("title", ""),
            r.get("article_ko", ""),
            r.get("article", ""),
            r.get("section", ""),
            " ".join(r.get("topics", [])),
            r.get("retrieval_text_ko", ""),
            r.get("text_en", ""),
        ]
        return " | ".join(str(x) for x in fields if x)

    def eligible_records(self, agent_id, jurisdiction=None):
        jurisdiction = jurisdiction or self.deployment_jurisdiction
        return [
            r for r in self.records
            if r.get("retrieval_eligible") is True
            and r.get("jurisdiction") == jurisdiction
            and agent_id in r.get("agent_access", [])
        ]

    def _ensure_index(self, agent_id, jurisdiction=None):
        jurisdiction = jurisdiction or self.deployment_jurisdiction
        key = (agent_id, jurisdiction)
        if key in self._cache:
            return
        model = self.load_model()
        records = self.eligible_records(agent_id, jurisdiction)
        texts = [self._text(r) for r in records]
        if records:
            embeddings = model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
        else:
            import numpy as np
            embeddings = np.empty((0, 384), dtype=float)
        self._cache[key] = (records, embeddings)

    def retrieve(self, agent_id, query, top_k=3, jurisdiction=None):
        import numpy as np
        jurisdiction = jurisdiction or self.deployment_jurisdiction
        self._ensure_index(agent_id, jurisdiction)
        records, doc_embeddings = self._cache[(agent_id, jurisdiction)]
        if not records:
            return []

        q = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]
        scores = np.dot(doc_embeddings, q)
        order = np.argsort(-scores)

        out = []
        for idx in order[:top_k]:
            r = records[int(idx)]
            out.append(PolicyHit(
                chunk_id=r["chunk_id"],
                document_id=r.get("document_id", ""),
                title=r.get("title", ""),
                locator=self._locator(r),
                score=float(scores[int(idx)]),
                jurisdiction=r.get("jurisdiction", ""),
                authority=r.get("authority", ""),
                source_type=r.get("source_type", ""),
                official_url=r.get("official_url", ""),
                agent_access=list(r.get("agent_access", [])),
                normative_weight=r.get("normative_weight", ""),
            ))
        return out
