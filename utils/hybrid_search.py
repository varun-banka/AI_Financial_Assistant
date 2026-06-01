"""
Hybrid search: FAISS vector + BM25 (reuses injected vector DB — no reload per query).
"""

import traceback
from typing import List, Optional, Tuple

import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from utils.embeddings import CachedBatchEmbeddings
from utils.vector_store import load_vector_store


class HybridSearchEngine:
    """Vector + BM25 hybrid retrieval with optional pre-loaded FAISS index."""

    def __init__(
        self,
        documents: List[Document],
        alpha: float = 0.7,
        vector_db: Optional[FAISS] = None,
        store_path: Optional[str] = None,
        embeddings: Optional[CachedBatchEmbeddings] = None,
    ):
        self.documents = documents
        self.alpha = alpha
        self.vector_db = vector_db
        self.store_path = store_path or ""
        self.embeddings = embeddings
        self.bm25 = None
        self.corpus = None
        self._initialize_bm25()

    def _initialize_bm25(self) -> None:
        self.corpus = [doc.page_content for doc in self.documents]
        tokenized_corpus = [doc.lower().split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"✅ BM25 index initialized with {len(self.corpus)} documents")

    def bm25_search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        top_indices = np.argsort(bm25_scores)[::-1][:k]
        return [
            (self.documents[idx], bm25_scores[idx])
            for idx in top_indices
            if bm25_scores[idx] > 0
        ]

    def vector_search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        try:
            db = self.vector_db
            if db is None:
                if not self.store_path:
                    raise ValueError("No vector_db or store_path for vector search")
                db = load_vector_store(self.store_path, self.embeddings)

            return db.similarity_search_with_relevance_scores(query, k=k)
        except Exception as e:
            print(f"⚠️ Vector search failed: {e}")
            traceback.print_exc()
            return []

    def normalize_scores(self, scores: List[float]) -> List[float]:
        if not scores or max(scores) == 0:
            return [0.0] * len(scores)
        max_score = max(scores)
        return [s / max_score for s in scores]

    def hybrid_search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        vector_results = self.vector_search(query, k=k * 2)
        bm25_results = self.bm25_search(query, k=k * 2)

        hybrid_scores = {}

        vector_scores_list = [score for _, score in vector_results]
        vector_scores_normalized = self.normalize_scores(vector_scores_list)
        for (doc, _), normalized_score in zip(vector_results, vector_scores_normalized):
            doc_id = doc.page_content[:50]
            hybrid_scores[doc_id] = self.alpha * normalized_score

        bm25_scores_list = [score for _, score in bm25_results]
        bm25_scores_normalized = self.normalize_scores(bm25_scores_list)
        for (doc, _), normalized_score in zip(bm25_results, bm25_scores_normalized):
            doc_id = doc.page_content[:50]
            if doc_id in hybrid_scores:
                hybrid_scores[doc_id] += (1 - self.alpha) * normalized_score
            else:
                hybrid_scores[doc_id] = (1 - self.alpha) * normalized_score

        final_results = []
        all_docs_dict = {doc.page_content[:50]: doc for doc in self.documents}
        sorted_scores = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)

        for doc_id, score in sorted_scores[:k]:
            if doc_id in all_docs_dict:
                final_results.append((all_docs_dict[doc_id], score))

        print(f"✅ Hybrid search completed (α={self.alpha}) — {len(final_results)} documents")
        return final_results


def perform_hybrid_search(
    query: str,
    documents: List[Document],
    k: int = 5,
    alpha: float = 0.7,
    vector_db: Optional[FAISS] = None,
    store_path: Optional[str] = None,
) -> List[Tuple[Document, float]]:
    engine = HybridSearchEngine(
        documents, alpha=alpha, vector_db=vector_db, store_path=store_path
    )
    return engine.hybrid_search(query, k=k)
