"""Quick embedding smoke test (uses production model + GOOGLE_API_KEY_1)."""

import os
import traceback

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from core.config import EMBEDDING_MODEL
from utils.embeddings import CachedBatchEmbeddings, get_primary_api_key

load_dotenv()


def main():
    api_key = get_primary_api_key()
    print("API Key Loaded:", (api_key[:10] + "...") if api_key else "None")

    base = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key,
        task_type="SEMANTIC_SIMILARITY",
    )
    embeddings = CachedBatchEmbeddings(base)

    try:
        result = embeddings.embed_query("Hello World")
        print("Embedding Length:", len(result))
        print("SUCCESS")
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
