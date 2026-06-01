"""
FAISS vector store with per-PDF paths and manifest-validated cache loading.
"""

import logging
import os
import traceback
from typing import List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from core.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE, EMBEDDING_MODEL
from core.manifest import (
    build_manifest,
    can_load_cached_index,
    get_store_path,
    save_manifest,
)
from utils.embeddings import CachedBatchEmbeddings, get_embeddings

logger = logging.getLogger(__name__)


def create_or_load_vector_store(
    chunks: List[Document],
    pdf_hash: str,
    filename: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    embedding_model: str = EMBEDDING_MODEL,
    embeddings: Optional[CachedBatchEmbeddings] = None,
) -> Tuple[FAISS, bool]:
    """
    Load cached FAISS when manifest matches; otherwise build and save.

    Returns:
        (vector_db, loaded_from_cache)
    """
    if not chunks:
        raise ValueError("No chunks provided to create vector store")

    store_path = get_store_path(pdf_hash)
    chunk_count = len(chunks)
    emb = embeddings or get_embeddings()

    if can_load_cached_index(
        pdf_hash, filename, embedding_model, chunk_size, chunk_overlap, chunk_count
    ):
        try:
            vector_db = FAISS.load_local(
                store_path,
                emb,
                allow_dangerous_deserialization=True,
            )
            print(
                f"✅ Loaded cached FAISS index from '{store_path}' "
                f"({chunk_count} chunks) — no re-embedding"
            )
            return vector_db, True
        except Exception:
            print(f"⚠️ Failed to load cached FAISS at '{store_path}', rebuilding...")
            traceback.print_exc()

    try:
        print(f"🔨 Building FAISS index at '{store_path}' ({chunk_count} chunks)...")
        vector_db = FAISS.from_documents(chunks, emb)
        os.makedirs(store_path, exist_ok=True)
        vector_db.save_local(store_path)

        manifest = build_manifest(
            pdf_hash=pdf_hash,
            filename=filename,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunk_count=chunk_count,
        )
        save_manifest(pdf_hash, manifest)

        print(f"✅ Vector store created with {chunk_count} chunks at '{store_path}'")
        return vector_db, False
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Error creating vector store: {e}") from e


def create_vector_store(
    chunks: List[Document],
    pdf_hash: str,
    filename: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> FAISS:
    """Backward-compatible wrapper."""
    db, _ = create_or_load_vector_store(
        chunks, pdf_hash, filename, chunk_size, chunk_overlap
    )
    return db


def load_vector_store(
    store_path: str,
    embeddings: Optional[CachedBatchEmbeddings] = None,
) -> FAISS:
    """Load FAISS from per-PDF path (vectorstore/<pdf_hash>/)."""
    if not os.path.isdir(store_path):
        raise FileNotFoundError(
            f"Vector store not found at '{store_path}'. "
            "Please upload and process a PDF first."
        )

    emb = embeddings or get_embeddings()
    try:
        db = FAISS.load_local(store_path, emb, allow_dangerous_deserialization=True)
        logger.info("Vector store loaded from %s", store_path)
        return db
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Error loading vector store from '{store_path}': {e}") from e


def search_vector_store(
    query: str,
    k: int = 3,
    store_path: str = "",
    embeddings: Optional[CachedBatchEmbeddings] = None,
    vector_db: Optional[FAISS] = None,
) -> List[Document]:
    """Similarity search using an in-memory DB or disk path."""
    try:
        db = vector_db if vector_db is not None else load_vector_store(store_path, embeddings)
        results = db.similarity_search(query, k=k)
        print(f"✅ Retrieved {len(results)} relevant documents")
        return results
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Error searching vector store: {e}") from e
