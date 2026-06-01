"""Central configuration for ingestion and embeddings."""

EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_BATCH_SIZE = 32
DEFAULT_CHUNK_SIZE = 3000
DEFAULT_CHUNK_OVERLAP = 300
VECTORSTORE_ROOT = "vectorstore"
EMBEDDING_CACHE_DB = "cache/embeddings/cache.sqlite"
MAX_EMBED_RETRIES = 5
RETRY_DELAYS_SECONDS = [2, 4, 8, 16, 32]
MIN_INTERVAL_BETWEEN_BATCHES = 0.5
