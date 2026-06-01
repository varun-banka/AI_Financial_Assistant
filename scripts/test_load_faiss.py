"""Load a per-PDF FAISS index (pass pdf_hash as first CLI arg)."""

import sys
import traceback

from langchain_community.vectorstores import FAISS

from core.manifest import get_store_path
from utils.embeddings import get_embeddings


def main():
    pdf_hash = sys.argv[1] if len(sys.argv) > 1 else None
    if not pdf_hash:
        print("Usage: python scripts/test_load_faiss.py <pdf_hash>")
        sys.exit(1)

    store_path = get_store_path(pdf_hash)
    try:
        emb = get_embeddings()
        print("Embeddings initialized")
        v = FAISS.load_local(store_path, emb, allow_dangerous_deserialization=True)
        n = len(v.docstore._dict) if hasattr(v, "docstore") else "?"
        print(f"Loaded OK from {store_path}, documents={n}")
    except Exception:
        print("Exception while loading FAISS:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
