"""
PDF manifest: hash validation and per-index metadata for FAISS stores.
"""

import hashlib
import json
import os
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from core.config import VECTORSTORE_ROOT


def hash_pdf_file(pdf_path: str) -> str:
    """Return SHA-256 hex digest of raw PDF bytes."""
    sha = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def get_store_path(pdf_hash: str) -> str:
    """Per-PDF FAISS directory: vectorstore/<pdf_hash>/"""
    return os.path.join(VECTORSTORE_ROOT, pdf_hash)


def get_manifest_path(pdf_hash: str) -> str:
    return os.path.join(get_store_path(pdf_hash), "manifest.json")


def build_manifest(
    pdf_hash: str,
    filename: str,
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
    chunk_count: int,
) -> Dict[str, Any]:
    return {
        "pdf_hash": pdf_hash,
        "filename": filename,
        "embedding_model": embedding_model,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "chunk_count": chunk_count,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def save_manifest(pdf_hash: str, manifest: Dict[str, Any]) -> None:
    path = get_manifest_path(pdf_hash)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_manifest(pdf_hash: str) -> Optional[Dict[str, Any]]:
    path = get_manifest_path(pdf_hash)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        print("⚠️ Failed to load manifest:")
        traceback.print_exc()
        return None


def faiss_index_exists(store_path: str) -> bool:
    """FAISS local save uses index.faiss and index.pkl."""
    return (
        os.path.isdir(store_path)
        and os.path.isfile(os.path.join(store_path, "index.faiss"))
        and os.path.isfile(os.path.join(store_path, "index.pkl"))
    )


def manifest_matches(
    manifest: Dict[str, Any],
    pdf_hash: str,
    filename: str,
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
    chunk_count: int,
) -> bool:
    if not manifest:
        return False
    return (
        manifest.get("pdf_hash") == pdf_hash
        and manifest.get("filename") == filename
        and manifest.get("embedding_model") == embedding_model
        and manifest.get("chunk_size") == chunk_size
        and manifest.get("chunk_overlap") == chunk_overlap
        and manifest.get("chunk_count") == chunk_count
    )


def can_load_cached_index(
    pdf_hash: str,
    filename: str,
    embedding_model: str,
    chunk_size: int,
    chunk_overlap: int,
    chunk_count: int,
) -> bool:
    """True when manifest and FAISS files are valid for this PDF configuration."""
    store_path = get_store_path(pdf_hash)
    manifest = load_manifest(pdf_hash)
    if not manifest_matches(
        manifest, pdf_hash, filename, embedding_model, chunk_size, chunk_overlap, chunk_count
    ):
        return False
    if not faiss_index_exists(store_path):
        print(f"⚠️ Manifest OK but FAISS index missing at {store_path}")
        return False
    return True
