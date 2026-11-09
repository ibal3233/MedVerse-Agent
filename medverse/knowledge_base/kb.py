from __future__ import annotations

from pathlib import Path
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any

REQUIRED_FIELDS = {
    "chunk_id",
    "document_id",
    "title",
    "jurisdiction",
    "authority",
    "source_language",
    "article",
    "effective_date",
    "official_url",
    "agent_access",
    "topics",
    "text_en",
    "translation_status",
    "full_text_stored",
}

@dataclass
class RetrievalHit:
    chunk_id: str
    document_id: str
    title: str
    article: str
    score: float
    text_en: str
    official_url: str
    effective_date: str
    authority: str
    translation_status: str

    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "title": self.title,
            "article": self.article,
            "score": self.score,
            "text_en": self.text_en,
            "official_url": self.official_url,
            "effective_date": self.effective_date,
            "authority": self.authority,
            "translation_status": self.translation_status,
        }

def _tokens(text: str) -> set[str]:
    return set(
        re.findall(
            r"[a-z0-9_]+",
            text.lower().replace("-", "_"),
        )
    )

class PolicyKnowledgeBase:
    def __init__(self, seed_path):
        self.seed_path = Path(seed_path)
        payload = json.loads(
            self.seed_path.read_text(encoding="utf-8")
        )
        self.kb_version = payload["kb_version"]
        self.records = payload["records"]
        self.validate()

    def validate(self):
        if not self.records:
            raise ValueError("Policy KB contains no records.")

        ids = [r["chunk_id"] for r in self.records]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate policy chunk_id detected.")

        for r in self.records:
            missing = REQUIRED_FIELDS - set(r.keys())
            if missing:
                raise ValueError(
                    f"{r.get('chunk_id')} missing fields: {sorted(missing)}"
                )

            if r["jurisdiction"] != "KR":
                raise ValueError(
                    f"Unexpected jurisdiction for {r['chunk_id']}"
                )

            if not r["official_url"].startswith("https://"):
                raise ValueError(
                    f"Non-HTTPS source URL for {r['chunk_id']}"
                )

            if not r["agent_access"]:
                raise ValueError(
                    f"No agent_access for {r['chunk_id']}"
                )

            if r["full_text_stored"] is not False:
                raise ValueError(
                    "Gate 6 seed records must not claim full legal text storage."
                )

    def records_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        return [
            r for r in self.records
            if agent_id in r["agent_access"]
        ]

    def retrieve(self, agent_id: str, query: str, top_k: int = 3):
        candidates = self.records_for_agent(agent_id)
        q = _tokens(query)

        hits = []
        for r in candidates:
            searchable = " ".join(
                [
                    r["title"],
                    r["article"],
                    " ".join(r["topics"]),
                    r["text_en"],
                ]
            )
            d = _tokens(searchable)

            overlap = q.intersection(d)
            union = q.union(d)

            # Deterministic lexical Jaccard score.
            score = 0.0 if not union else len(overlap) / len(union)

            if score > 0:
                hits.append(
                    RetrievalHit(
                        chunk_id=r["chunk_id"],
                        document_id=r["document_id"],
                        title=r["title"],
                        article=r["article"],
                        score=score,
                        text_en=r["text_en"],
                        official_url=r["official_url"],
                        effective_date=r["effective_date"],
                        authority=r["authority"],
                        translation_status=r["translation_status"],
                    )
                )

        hits.sort(
            key=lambda h: (-h.score, h.chunk_id)
        )

        return hits[:top_k]
