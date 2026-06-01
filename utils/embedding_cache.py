"""
Persistent SQLite cache for text embeddings (keyed by SHA-256 of chunk text).
"""

import hashlib
import json
import os
import sqlite3
from typing import List, Optional

from core.config import EMBEDDING_CACHE_DB


class EmbeddingCache:
    """SQLite-backed embedding cache."""

    def __init__(self, db_path: str = EMBEDDING_CACHE_DB):
        self.db_path = db_path
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    text_hash TEXT NOT NULL,
                    model TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    PRIMARY KEY (text_hash, model)
                )
                """
            )
            conn.commit()

    @staticmethod
    def hash_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        text_hash = self.hash_text(text)
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT embedding FROM embeddings WHERE text_hash = ? AND model = ?",
                    (text_hash, model),
                ).fetchone()
            if row:
                return json.loads(row[0])
        except Exception:
            return None
        return None

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        text_hash = self.hash_text(text)
        payload = json.dumps(embedding)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings (text_hash, model, embedding)
                VALUES (?, ?, ?)
                """,
                (text_hash, model, payload),
            )
            conn.commit()

    def get_many(self, texts: List[str], model: str) -> List[Optional[List[float]]]:
        return [self.get(t, model) for t in texts]

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()
        return int(row[0]) if row else 0
