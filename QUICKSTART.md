# 🚀 Quick Start Guide

## 1️⃣ Prerequisites

- Python 3.9+
- Gemini API Key (free at https://aistudio.google.com/app/apikey)
- ~2GB disk space
- Windows/Mac/Linux

---

## 2️⃣ Installation (5 minutes)

### Step 1: Install Dependencies

```bash
cd AI_Financial_Assistant
pip install -r requirements.txt
```

### Step 2: Setup API Key

Edit `.env` file:

```
GOOGLE_API_KEY=your_gemini_api_key_here
```

Replace `your_gemini_api_key_here` with your actual API key.

### Step 3: Verify Installation

```bash
python -c "from langchain_google_genai import ChatGoogleGenerativeAI; print('✅ All imports successful')"
```

---

## 3️⃣ Running the Application

### Start Streamlit App

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`

---

## 4️⃣ First-Time Usage

### Step 1: Upload a PDF
1. Go to **📤 Upload & Process** tab
2. Click "Upload Annual Report"
3. Select a financial PDF (e.g., annual report, 10-K, prospectus)
4. Click **🚀 Process PDF**
5. Wait for completion message ✅

### Step 2: Ask Questions
1. Go to **❓ Ask Questions** tab
2. Type your question: "What was the revenue?"
3. Click Enter or button
4. See answer with source citations

### Step 3: View Analysis
1. Go to **📈 Financial Analysis** tab
2. See extracted metrics and ratios
3. View interactive charts

### Step 4: Generate Summary
1. Go to **📋 Executive Summary** tab
2. Click "📝 Generate Executive Summary"
3. Export as text file

---

## 5️⃣ Sample Questions to Try

```
1. What was the total revenue?
2. How much did profit grow?
3. What's the debt-to-equity ratio?
4. What are the main business risks?
5. What new opportunities are mentioned?
6. How does profitability compare?
7. What's the current ratio?
8. How did operating cash flow change?
9. What's the ROE?
10. Compare this to the previous year
```

---

## 6️⃣ Project Structure

```
AI_Financial_Assistant/
├── app.py                     # Main UI application
├── requirements.txt           # Dependencies
├── .env                       # Your API key
├── README.md                  # Full documentation
├── INTERVIEW_GUIDE.md        # Interview Q&A
│
├── utils/
│   ├── pdf_loader.py          # Load PDFs
│   ├── text_splitter.py       # Split into chunks
│   ├── embeddings.py          # Generate embeddings
│   ├── vector_store.py        # FAISS storage
│   ├── rag_chain.py           # Main RAG pipeline
│   ├── financial_extractor.py # Extract metrics
│   ├── ratio_calculator.py    # Calculate ratios
│   ├── hybrid_search.py       # Vector + BM25
│   ├── conversation_memory.py # Multi-turn dialogue
│   ├── risk_analyzer.py       # Risk analysis
│   └── summary_generator.py   # Generate summaries
│
├── uploads/                   # Uploaded PDFs
├── vectorstore/               # FAISS database
└── exports/                   # Generated reports
```

---

## 7️⃣ Troubleshooting

### Problem: "GOOGLE_API_KEY not set"
**Solution**: 
- Check `.env` file exists in project root
- Verify key is entered correctly (no spaces)
- Restart app: `streamlit run app.py`

### Problem: "No vector store found"
**Solution**: 
- Upload a PDF first in **📤 Upload & Process** tab
- Wait for "✅ Successfully processed" message

### Problem: "Streamlit not found"
**Solution**: 
- Reinstall: `pip install streamlit==1.28.1`
- Check Python version: `python --version` (need 3.9+)

### Problem: "Low answer quality"
**Solution**: 
- Try different question phrasing
- Increase "Documents to retrieve" to 7-10
- Ensure PDF is text (not scanned image)
- Try searching for different keywords

### Problem: "Slow processing"
**Solution**: 
- Reduce chunk size in `utils/text_splitter.py` (line ~18)
- Use "Vector Only" search instead of "Hybrid"
- Close other applications using RAM

---

## 8️⃣ Understanding Each Module

### 📄 pdf_loader.py
```python
from utils.pdf_loader import load_pdf
documents = load_pdf("uploads/annual_report.pdf")
# Returns: [Document(page_content="...", metadata={"page": 0}), ...]
```
- Loads PDF using PyPDFLoader
- Preserves page numbers
- Handles multi-page documents

### ✂️ text_splitter.py
```python
from utils.text_splitter import split_documents
chunks = split_documents(documents, chunk_size=1000, chunk_overlap=200)
# Returns: Chunked documents for embedding
```
- Splits large documents into manageable pieces
- Maintains semantic continuity with overlap
- Prevents questions from spanning boundaries

### 🧠 embeddings.py
```python
from utils.embeddings import get_embeddings
embeddings = get_embeddings()
# Returns: GoogleGenerativeAIEmbeddings instance
```
- Converts text to 768-dimensional vectors
- Captures semantic meaning
- Powers similarity search

### 🔍 vector_store.py
```python
from utils.vector_store import create_vector_store, load_vector_store
db = create_vector_store(chunks)  # Save to disk
db = load_vector_store()           # Load from disk
docs = db.similarity_search("What is revenue?", k=5)
```
- FAISS vector database for fast retrieval
- O(log n) search complexity
- Persistent storage

### 💬 rag_chain.py
```python
from utils.rag_chain import get_financial_answer
result = get_financial_answer("What's the profit?")
# Returns: {"answer": "...", "sources": [...], "success": True}
```
- Main RAG pipeline
- Retrieves documents → generates answers
- Includes source citations

### 💰 financial_extractor.py
```python
from utils.financial_extractor import extract_metrics_from_documents
metrics = extract_metrics_from_documents(chunks)
# Returns: {"Revenue": 50000, "Net_Profit": 5000, ...}
```
- Extracts financial metrics using regex
- Finds Revenue, Profit, Assets, Liabilities, etc.
- Enables automatic financial analysis

### 📊 ratio_calculator.py
```python
from utils.ratio_calculator import calculate_ratios
ratios = calculate_ratios(metrics)
# Returns: {"Profit_Margin_Percent": 10.0, "ROE_Percent": 15.5, ...}
```
- Calculates 10+ financial ratios
- Provides ratio interpretations
- Powers financial dashboard

### 🔄 hybrid_search.py
```python
from utils.hybrid_search import HybridSearchEngine
engine = HybridSearchEngine(documents, alpha=0.7)
results = engine.hybrid_search("What's the revenue?", k=5)
# Combines Vector Search (70%) + BM25 (30%)
```
- Hybrid retrieval: Semantic + Keyword
- Better than pure vector search
- Configurable weighting

### 💭 conversation_memory.py
```python
from utils.conversation_memory import ConversationMemory
memory = ConversationMemory()
memory.add_turn("What's revenue?", "Revenue is 50K Cr", {})
context = memory.get_context(max_turns=5)
```
- Tracks multi-turn conversations
- Enables follow-up questions
- Exportable history

### ⚠️ risk_analyzer.py
```python
from utils.risk_analyzer import generate_risk_report
report = generate_risk_report(documents)
# Returns: Business risks, sentiment analysis, opportunities
```
- Analyzes document sentiment
- Identifies business risks
- Finds growth opportunities

### 📋 summary_generator.py
```python
from utils.summary_generator import ExecutiveSummaryGenerator
generator = ExecutiveSummaryGenerator()
report = generator.generate_full_report(documents, metrics, ratios)
# Returns: Comprehensive executive summary
```
- Generates professional summaries
- Investment recommendations
- Exportable reports

---

## 9️⃣ Tips & Tricks

### Tip 1: Use Hybrid Search for Better Results
- Default is Hybrid (Recommended) - use it!
- Pure Vector for conceptual questions
- Pure BM25 for exact matches

### Tip 2: Increase Retrieved Documents for Complex Questions
- Simple question: k=3
- Complex analysis: k=7-10
- Comparison across documents: k=10

### Tip 3: Export Everything
- **Conversation**: 💾 Export button in Conversation History
- **Executive Summary**: 💾 Export Report button
- **Metrics**: Copy from dataframe

### Tip 4: Understand What RAG Can't Do
- ❌ Predict future prices
- ❌ Make investment recommendations (it will analyze but shouldn't decide)
- ❌ Handle confidential data (runs locally but still risky)
- ✅ Summarize documents
- ✅ Extract metrics
- ✅ Answer questions from documents

### Tip 5: Optimize for Your Use Case
- **Speed**: Reduce chunk size, fewer docs retrieved
- **Accuracy**: Increase chunk size, more docs retrieved
- **Cost**: Use hybrid search, cache results

---

## 🔟 Next Steps (After Learning)

1. **Upload Your Own PDFs**: Use real financial reports
2. **Explore Financial Analysis**: Check extracted metrics vs manual review
3. **Customize Prompts**: Edit prompts in `utils/rag_chain.py` for your needs
4. **Add More Ratios**: Extend `ratio_calculator.py`
5. **Deploy**: Use Streamlit Cloud for free hosting
6. **Interview**: Explain architecture to interviewers!

---

## 📞 Support

### Common Issues

| Issue | Fix |
|-------|-----|
| Slow embedding | Use batch API or reduce chunk size |
| Poor answers | Try different question phrasing |
| Memory error | Reduce document retrieval count (k) |
| API errors | Check GOOGLE_API_KEY is valid |
| PDF not processing | Ensure it's text-based (not scanned) |

### Resources

- **LangChain Docs**: https://python.langchain.com/
- **Gemini API**: https://aistudio.google.com/
- **Streamlit**: https://docs.streamlit.io/
- **FAISS**: https://github.com/facebookresearch/faiss

---

## 🎓 Learning Path

1. **Week 1**: Get app running, upload PDFs, ask questions
2. **Week 2**: Read README.md, understand architecture
3. **Week 3**: Read INTERVIEW_GUIDE.md, prepare answers
4. **Week 4**: Modify code, add your own features
5. **Week 5**: Build portfolio, practice interviews

---

Happy Analyzing! 📊🚀

