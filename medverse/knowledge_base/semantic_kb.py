from __future__ import annotations

from pathlib import Path
import json
from dataclasses import dataclass
from typing import List, Dict, Any

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

@dataclass
class SemanticHit:
    chunk_id: str
    document_id: str
    title: str
    title_ko: str
    article: str
    score: float
    official_url: str
    effective_date: str
    authority: str
    translation_status: str

    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "title": self.title,
            "title_ko": self.title_ko,
            "article": self.article,
            "score": self.score,
            "official_url": self.official_url,
            "effective_date": self.effective_date,
            "authority": self.authority,
            "translation_status": self.translation_status,
        }

class MultilingualPolicyKnowledgeBase:
    def __init__(self, seed_path, model_name=MODEL_NAME):
        self.seed_path = Path(seed_path)
        payload = json.loads(
            self.seed_path.read_text(encoding="utf-8")
        )
        self.kb_version = payload["kb_version"]
        self.records = payload["records"]
        self.model_name = model_name
        self.model = None
        self._embeddings_by_agent = {}

        self._validate_multilingual_fields()

    def _validate_multilingual_fields(self):
        required = {
            "title_ko",
            "article_ko",
            "retrieval_text_ko",
            "text_en",
            "translation_status",
            "official_url",
            "effective_date",
            "authority",
            "agent_access",
        }

        for r in self.records:
            missing = required - set(r.keys())
            if missing:
                raise ValueError(
                    f"{r['chunk_id']} missing multilingual fields: "
                    f"{sorted(missing)}"
                )

    def load_model(self):
        if self.model is not None:
            return self.model

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        self.model = SentenceTransformer(self.model_name)
        return self.model

    def records_for_agent(self, agent_id):
        return [
            r for r in self.records
            if agent_id in r["agent_access"]
        ]

    @staticmethod
    def _document_text(record):
        return " | ".join([
            record["title_ko"],
            record["article_ko"],
            record["retrieval_text_ko"],
            record["title"],
            record["article"],
            " ".join(record["topics"]),
            record["text_en"],
        ])

    def _ensure_index(self, agent_id):
        model = self.load_model()
        records = self.records_for_agent(agent_id)

        texts = [
            self._document_text(r)
            for r in records
        ]

        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        self._embeddings_by_agent[agent_id] = (
            records,
            embeddings,
        )

    def retrieve(self, agent_id, query, top_k=3):
        import numpy as np

        if agent_id not in self._embeddings_by_agent:
            self._ensure_index(agent_id)

        records, doc_embeddings = (
            self._embeddings_by_agent[agent_id]
        )

        if not records:
            return []

        q = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )[0]

        scores = np.dot(doc_embeddings, q)
        order = np.argsort(-scores)

        hits = []
        for idx in order[:top_k]:
            r = records[int(idx)]
            hits.append(
                SemanticHit(
                    chunk_id=r["chunk_id"],
                    document_id=r["document_id"],
                    title=r["title"],
                    title_ko=r["title_ko"],
                    article=r["article"],
                    score=float(scores[int(idx)]),
                    official_url=r["official_url"],
                    effective_date=r["effective_date"],
                    authority=r["authority"],
                    translation_status=r["translation_status"],
                )
            )

        return hits
