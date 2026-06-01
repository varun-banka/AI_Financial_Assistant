"""
Gemini embeddings with persistent cache, batching, rate-limit retries, and throttling.
"""

import logging
import time
import traceback
from typing import List, Optional

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core.config import (
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
    MAX_EMBED_RETRIES,
    MIN_INTERVAL_BETWEEN_BATCHES,
    RETRY_DELAYS_SECONDS,
)
from utils.embedding_cache import EmbeddingCache

load_dotenv()

logger = logging.getLogger(__name__)

_key_rotation_counter = 0
_last_batch_time = 0.0
_embeddings_singleton: Optional["CachedBatchEmbeddings"] = None


def _is_rate_limit_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    name = type(exc).__name__.lower()
    return (
        "429" in msg
        or "resource_exhausted" in msg
        or "quota" in msg
        or "rate" in msg
        or "resourceexhausted" in name
    )


def _rate_limit_batch() -> None:
    global _last_batch_time
    elapsed = time.time() - _last_batch_time
    if elapsed < MIN_INTERVAL_BETWEEN_BATCHES:
        delay = MIN_INTERVAL_BETWEEN_BATCHES - elapsed
        time.sleep(delay)
    _last_batch_time = time.time()


def get_api_key() -> str:
    """Round-robin API key selection (LLM calls); embeddings use primary key."""
    global _key_rotation_counter

    api_keys = []
    for i in range(1, 6):
        key = __import__("os").getenv(f"GOOGLE_API_KEY_{i}")
        if key and key != f"YOUR_API_KEY_{i}_HERE" and not key.startswith("YOUR_"):
            api_keys.append(key)

    if not api_keys:
        raise ValueError(
            "No valid GOOGLE_API_KEY configured. "
            "Set GOOGLE_API_KEY_1 through GOOGLE_API_KEY_5 in .env"
        )

    selected_key = api_keys[_key_rotation_counter % len(api_keys)]
    _key_rotation_counter += 1
    key_number = api_keys.index(selected_key) + 1
    logger.info("Using API Key %s/%s", key_number, len(api_keys))
    return selected_key


def get_primary_api_key() -> str:
    """Stable key for embedding ingest (avoids cache invalidation from key rotation)."""
    import os

    for i in range(1, 6):
        key = os.getenv(f"GOOGLE_API_KEY_{i}")
        if key and key != f"YOUR_API_KEY_{i}_HERE" and not key.startswith("YOUR_"):
            return key
    raise ValueError("No valid GOOGLE_API_KEY_1 configured in .env")


def _call_with_retry(operation_name: str, fn):
    """Exponential backoff: 2s, 4s, 8s, 16s, 32s (5 attempts)."""
    last_exc = None
    for attempt in range(MAX_EMBED_RETRIES):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if not _is_rate_limit_error(exc) or attempt >= MAX_EMBED_RETRIES - 1:
                logger.error("%s failed (non-retryable or max retries): %s", operation_name, exc)
                traceback.print_exc()
                raise
            delay = RETRY_DELAYS_SECONDS[attempt]
            logger.warning(
                "Retry %s/%s for %s after %ss (%s)",
                attempt + 1,
                MAX_EMBED_RETRIES,
                operation_name,
                delay,
                exc,
            )
            print(f"⏳ Retry {attempt + 1}/{MAX_EMBED_RETRIES} for {operation_name} after {delay}s")
            time.sleep(delay)
    raise last_exc


class CachedBatchEmbeddings:
    """
    LangChain-compatible embeddings: SQLite cache + batched API calls + retries.
    """

    def __init__(
        self,
        base: GoogleGenerativeAIEmbeddings,
        model_name: str = EMBEDDING_MODEL,
        batch_size: int = EMBEDDING_BATCH_SIZE,
    ):
        self.base = base
        self.model_name = model_name
        self.batch_size = batch_size
        self.cache = EmbeddingCache()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        results: List[Optional[List[float]]] = [None] * len(texts)
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []
        cache_hits = 0

        for i, text in enumerate(texts):
            cached = self.cache.get(text, self.model_name)
            if cached is not None:
                results[i] = cached
                cache_hits += 1
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if cache_hits:
            print(f"♻️  Embedding cache: {cache_hits}/{len(texts)} hits, {len(uncached_texts)} API batches needed")

        if uncached_texts:
            api_calls = (len(uncached_texts) + self.batch_size - 1) // self.batch_size
            print(f"📡 Embedding {len(uncached_texts)} chunks in {api_calls} batch(es) (size={self.batch_size})")

            for batch_start in range(0, len(uncached_texts), self.batch_size):
                batch_texts = uncached_texts[batch_start : batch_start + self.batch_size]
                batch_indices = uncached_indices[batch_start : batch_start + self.batch_size]
                _rate_limit_batch()

                def _embed_batch(bt=batch_texts):
                    return self.base.embed_documents(bt)

                batch_vectors = _call_with_retry("embed_documents", _embed_batch)

                for idx, text, vec in zip(batch_indices, batch_texts, batch_vectors):
                    results[idx] = vec
                    self.cache.set(text, self.model_name, vec)

                done = min(batch_start + self.batch_size, len(uncached_texts))
                print(f"  📄 Embedded {done}/{len(uncached_texts)} new chunks...")

        return results  # type: ignore[return-value]

    def embed_query(self, text: str) -> List[float]:
        cached = self.cache.get(text, self.model_name)
        if cached is not None:
            return cached

        _rate_limit_batch()

        def _embed():
            return self.base.embed_query(text)

        vec = _call_with_retry("embed_query", _embed)
        self.cache.set(text, self.model_name, vec)
        return vec

    def __getattr__(self, name):
        return getattr(self.base, name)


def get_embeddings(force_new: bool = False) -> CachedBatchEmbeddings:
    """
    Return shared CachedBatchEmbeddings instance (primary API key for stability).
    """
    global _embeddings_singleton
    if _embeddings_singleton is not None and not force_new:
        return _embeddings_singleton

    api_key = get_primary_api_key()
    try:
        base = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=api_key,
            task_type="SEMANTIC_SIMILARITY",
        )
        _embeddings_singleton = CachedBatchEmbeddings(base)
        print("✅ Embeddings initialized (cached, batched, retry-enabled)")
        return _embeddings_singleton
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Error initializing embeddings: {e}") from e
