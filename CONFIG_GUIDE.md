# ⚙️ Configuration & Customization Guide

This guide shows how to adjust the system for different use cases and requirements.

---

## 🔧 Configuration File Reference

### Text Chunking (`utils/text_splitter.py`)

```python
# Current settings
chunk_size = 1000      # Size of each chunk in characters
chunk_overlap = 200    # Overlap to prevent context loss

# For large documents (annual reports > 100 pages):
chunk_size = 1500      # Larger chunks preserve context better
chunk_overlap = 300    # More overlap for better continuity

# For short documents (press releases, quarterlies):
chunk_size = 500       # Smaller chunks for faster retrieval
chunk_overlap = 100    # Less overlap needed

# For legal documents (contracts, terms):
chunk_size = 2000      # Large chunks maintain legal context
chunk_overlap = 500    # Significant overlap for continuity
```

**Impact**: Larger chunks = better context, slower search

---

### Embeddings Configuration (`utils/embeddings.py`)

```python
# Current model
model = "models/embedding-001"    # Gemini's embedding model
task_type = "SEMANTIC_SIMILARITY"  # Task type for embeddings

# Alternative task types:
# "SEMANTIC_SIMILARITY"     - Default (what we use)
# "RETRIEVAL_DOCUMENT"      - For document retrieval
# "RETRIEVAL_QUERY"         - For query embedding
# "CLASSIFICATION"          - For classification tasks
# "CLUSTERING"              - For clustering tasks
```

**Note**: Different task types yield different embeddings. Use consistency!

---

### Vector Store Configuration (`utils/vector_store.py`)

```python
# Current: FAISS (Facebook AI Similarity Search)
# Pros: Fast, in-memory, free
# Cons: Can't scale beyond RAM

# Alternatives for production:
# 1. Milvus (distributed vector DB)
# 2. Pinecone (managed, cloud-based)
# 3. Weaviate (open-source, scalable)
# 4. Qdrant (high-performance)
# 5. Elasticsearch (built-in vector search)
```

**When to switch**:
- FAISS: < 1M vectors, single machine
- Milvus: > 1M vectors, distributed setup
- Pinecone: Want managed, don't want ops

---

### Hybrid Search Configuration (`utils/hybrid_search.py`)

```python
# Current weighting
alpha = 0.7     # Weight for Vector Search
# (1-alpha) = 0.3 weight for BM25

# Final Score = 0.7 × Vector_Score + 0.3 × BM25_Score

# For different scenarios:
alpha = 0.9     # Semantic-heavy (conceptual questions)
alpha = 0.5     # Balanced (most use cases) ← Good default
alpha = 0.2     # Keyword-heavy (exact matches matter)

# Example tuning based on results:
if answer_quality < 0.8:
    alpha = 0.8  # Try more semantic weight
if exact_keywords_missed:
    alpha = 0.3  # Try more keyword weight
```

**Testing**: A/B test with your actual queries

---

### LLM Configuration (`utils/rag_chain.py`)

```python
# Current settings
model = "gemini-1.5-pro"      # Latest, most powerful
temperature = 0.3             # Lower = more factual
top_p = 0.9                   # Nucleus sampling
top_k = 40                    # Top tokens to consider

# Model options:
"gemini-pro"              # Faster, cheaper, good for simple tasks
"gemini-1.5-pro"          # Latest, most capable (current)
"gemini-1.5-flash"        # Fastest, cheapest (new in 2024)

# Temperature tuning:
temperature = 0.0    # Deterministic, best for finance (risky: repetitive)
temperature = 0.2    # Very factual (good for finance)
temperature = 0.3    # Factual with variation (current setting)
temperature = 0.5    # Balanced (neutral)
temperature = 1.0    # Creative, inconsistent (bad for finance)

# Cost implications:
# gemini-pro: $0.00035 per 1K input, $0.00053 per 1K output
# gemini-1.5-pro: $0.00175 per 1K input, $0.00525 per 1K output
# gemini-1.5-flash: $0.0000375 per 1K input, $0.00015 per 1K output
```

**For Finance**: Use `temperature=0.2` or `0.3`, `gemini-1.5-pro`

---

### Conversation Memory Configuration (`utils/conversation_memory.py`)

```python
# Current settings
memory_file = "data/conversation_memory.json"

# Production alternatives:
# PostgreSQL: Scalable, supports complex queries
# MongoDB: Flexible schema, good for document storage
# Redis: Fast, in-memory (good for active sessions)
# DynamoDB: Serverless, AWS-native

# Session management:
max_history_turns = 100        # Keep last 100 turns
auto_save = True               # Save after each turn
export_format = "json"         # Can be "json", "csv", "txt"
```

---

### Risk Analyzer Configuration (`utils/risk_analyzer.py`)

```python
# Risk categories (customizable by domain)
risk_levels = ["HIGH", "MEDIUM", "LOW"]

# Financial-specific risk types:
BUSINESS_RISKS = [
    "Market Risk",
    "Regulatory Risk",
    "Operational Risk",
    "Financial Risk",
    "Liquidity Risk",
    "Cybersecurity Risk"
]

# Customize for your industry:
# Healthcare: Add "Compliance Risk", "Product Liability"
# Tech: Add "IP Risk", "Competition Risk"
# Energy: Add "Environmental Risk", "Commodity Risk"
```

---

## 🎯 Use Case Configurations

### 📋 Use Case 1: Quick Financial Summary (Speed Optimized)

```python
# Prioritize speed over perfect accuracy

# Text splitting
chunk_size = 500
chunk_overlap = 50

# Retrieval
k = 3  # Fewer documents
use_hybrid_search = False  # Vector only (faster)

# LLM
model = "gemini-1.5-flash"  # Faster, cheaper
temperature = 0.2

# Result: 1-2 seconds per query, good for dashboards
```

### 📈 Use Case 2: Detailed Financial Analysis (Accuracy Optimized)

```python
# Prioritize accuracy over speed

# Text splitting
chunk_size = 1500
chunk_overlap = 300

# Retrieval
k = 10  # More documents
use_hybrid_search = True
alpha = 0.6  # Balanced

# LLM
model = "gemini-1.5-pro"  # Most capable
temperature = 0.2

# Memory
keep_full_history = True
export_detailed = True

# Result: 5-10 seconds per query, high-quality analysis
```

### 🔒 Use Case 3: Secure Enterprise Deployment

```python
# Prioritize security and compliance

# Storage
vectorstore = "on-premise milvus"
memory_storage = "postgresql with encryption"

# Embeddings
model = "local/open-source model"  # No external API
encrypt_vectors = True

# LLM
local_model = "llama-2"  # Run locally
no_external_api = True

# Logging
audit_log = "postgresql"
log_all_queries = True
user_tracking = "enabled"

# Result: Fully controlled, compliant, slower
```

### 🌍 Use Case 4: Multi-Language Support

```python
# Add language detection and translation

from langchain.chat_models import ChatOpenAI
from langchain.agents import tool

@tool
def translate_query(query, target_language):
    """Translate query before embedding"""
    # Translate to English for embedding
    return translate(query, target_language, "en")

# Modify rag_chain.py to detect language
if detect_language(question) != "en":
    question = translate_query(question, "en")
    
# Generate answer in English
# Translate back to original language before returning

# Result: Works with multiple languages
```

---

## 🚀 Performance Tuning

### Benchmark Your Current Setup

```python
import time

def benchmark_retrieval(query, iterations=10):
    times = []
    for _ in range(iterations):
        start = time.time()
        results = search_vector_store(query, k=5)
        times.append(time.time() - start)
    
    return {
        "mean": sum(times) / len(times),
        "min": min(times),
        "max": max(times)
    }

# Run benchmark
results = benchmark_retrieval("What is revenue?")
print(f"Average retrieval time: {results['mean']*1000:.0f}ms")
```

### Optimization Strategies

| Problem | Solution | Trade-off |
|---------|----------|-----------|
| Slow embedding | Batch 10 queries together | Higher latency initially |
| Slow retrieval | Reduce chunk size | Potential context loss |
| Slow LLM | Use gemini-1.5-flash | Slightly lower quality |
| High cost | Cache frequent queries | Need caching layer |
| High memory | Stream responses | Slower response display |

---

## 📊 Financial Ratio Customization

### Add More Ratios (`utils/ratio_calculator.py`)

```python
def quick_ratio_custom(metrics):
    """
    Quick Ratio = (Current Assets - Inventory - Prepaid) / Current Liabilities
    More conservative than current ratio
    """
    numerator = (metrics.get("Current_Assets", 0) - 
                 metrics.get("Inventory", 0) - 
                 metrics.get("Prepaid_Expenses", 0))
    
    denominator = metrics.get("Current_Liabilities", 1)
    
    if denominator > 0:
        return numerator / denominator
    return None

# Add to calculate_all_ratios()
ratios["Quick_Ratio"] = quick_ratio_custom(metrics)
```

### Industry-Specific Metrics

```python
# Banking metrics
def npa_ratio(metrics):
    """Non-Performing Assets ratio"""
    return metrics.get("NPA") / metrics.get("Total_Assets")

# Tech metrics
def cash_burn_rate(metrics, months=12):
    """Monthly cash burn"""
    return metrics.get("Cash_Used") / months

# Retail metrics
def inventory_turnover(metrics):
    """How fast inventory sells"""
    return metrics.get("Revenue") / metrics.get("Inventory")
```

---

## 🔐 Security Customization

### Add Authentication

```python
# Add to app.py
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    credentials={
        "usernames": {
            "analyst@company.com": {
                "name": "John Analyst",
                "password": "hashed_password"
            }
        }
    },
    cookie_name="financial_app",
    key="random_key",
    cookie_expiry_days=1
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.write(f'Welcome *{name}*')
    # Show app
else:
    st.error("Login failed or user not registered")
```

### Add Access Control

```python
# Restrict documents by role
user_permissions = {
    "analyst": ["all"],
    "manager": ["summary_only"],
    "viewer": ["public_reports"]
}

if not user_has_access(user_role, document_id):
    st.error("You don't have access to this document")
    return
```

---

## 📈 Monitoring & Metrics

### Add Observability

```python
import logging
import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename="data/app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Log every query
def log_query(query, answer_length, retrieval_time, user_id):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "answer_length": answer_length,
        "retrieval_time_ms": retrieval_time * 1000,
        "user_id": user_id
    }
    
    logging.info(json.dumps(log_entry))

# Track metrics
class QueryMetrics:
    def __init__(self):
        self.queries = 0
        self.avg_latency = 0
        self.errors = 0
        self.cache_hits = 0
```

---

## 🔄 Deployment Configurations

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

### Environment-Specific `.env`

```bash
# .env.dev
GOOGLE_API_KEY=dev_key
ENVIRONMENT=development
DEBUG=true
CHUNK_SIZE=1000

# .env.prod
GOOGLE_API_KEY=prod_key
ENVIRONMENT=production
DEBUG=false
CHUNK_SIZE=1500
```

---

## 💾 Database Configuration

### PostgreSQL for Production

```python
import psycopg2

class ConversationMemoryDB:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
        self.create_tables()
    
    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR,
                    turn_number INT,
                    question TEXT,
                    answer TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE INDEX idx_session ON conversations(session_id);
            """)
            self.conn.commit()
    
    def add_turn(self, session_id, turn_number, question, answer):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversations (session_id, turn_number, question, answer)
                VALUES (%s, %s, %s, %s)
            """, (session_id, turn_number, question, answer))
            self.conn.commit()
```

---

## ✅ Configuration Checklist

- [ ] Set GOOGLE_API_KEY in .env
- [ ] Choose appropriate chunk_size for your docs
- [ ] Select model based on speed vs quality needs
- [ ] Configure hybrid search weights
- [ ] Set up logging and monitoring
- [ ] Enable caching if needed
- [ ] Configure access control for enterprise
- [ ] Set up database for persistence
- [ ] Test with real financial documents
- [ ] Monitor performance metrics

---

This configuration guide should help you adapt the system for any use case! 🚀

