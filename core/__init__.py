"""Core utilities: manifest, configuration."""

from core.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_CACHE_DB,
    EMBEDDING_MODEL,
    VECTORSTORE_ROOT,
)
from core.manifest import (
    build_manifest,
    faiss_index_exists,
    get_manifest_path,
    get_store_path,
    hash_pdf_file,
    load_manifest,
    manifest_matches,
    save_manifest,
)

__all__ = [
    "DEFAULT_CHUNK_OVERLAP",
    "DEFAULT_CHUNK_SIZE",
    "EMBEDDING_BATCH_SIZE",
    "EMBEDDING_CACHE_DB",
    "EMBEDDING_MODEL",
    "VECTORSTORE_ROOT",
    "build_manifest",
    "faiss_index_exists",
    "get_manifest_path",
    "get_store_path",
    "hash_pdf_file",
    "load_manifest",
    "manifest_matches",
    "save_manifest",
]
