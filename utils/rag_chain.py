"""
RAG chain with optional injected vector DB and hybrid engine (no per-query rebuild).
"""

import traceback
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI

from utils.embeddings import get_api_key
from utils.hybrid_search import HybridSearchEngine
from utils.vector_store import search_vector_store

load_dotenv()


class RAGChain:
    """Retrieval-augmented generation with reusable retrieval components."""

    def __init__(
        self,
        use_hybrid_search: bool = True,
        alpha: float = 0.7,
        vector_db: Optional[FAISS] = None,
        hybrid_engine: Optional[HybridSearchEngine] = None,
        store_path: Optional[str] = None,
    ):
        api_key = get_api_key()
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.3,
            google_api_key=api_key,
            top_p=0.9,
            top_k=40,
        )
        self.use_hybrid_search = use_hybrid_search
        self.alpha = alpha
        self.vector_db = vector_db
        self.hybrid_engine = hybrid_engine
        self.store_path = store_path or ""
        self.retrieved_docs: List[Tuple[Document, float]] = []

    def retrieve_documents(
        self,
        question: str,
        k: int = 5,
        use_hybrid: Optional[bool] = None,
    ) -> List[Tuple[Document, float]]:
        hybrid = self.use_hybrid_search if use_hybrid is None else use_hybrid

        try:
            if hybrid and self.hybrid_engine is not None:
                results = self.hybrid_engine.hybrid_search(question, k=k)
            elif hybrid and self.vector_db is not None:
                docs = list(self.vector_db.docstore._dict.values())
                engine = HybridSearchEngine(
                    docs,
                    alpha=self.alpha,
                    vector_db=self.vector_db,
                    store_path=self.store_path,
                )
                results = engine.hybrid_search(question, k=k)
            elif self.vector_db is not None:
                docs = self.vector_db.similarity_search(question, k=k)
                results = [(doc, 1.0) for doc in docs]
            else:
                docs = search_vector_store(
                    question, k=k, store_path=self.store_path, vector_db=self.vector_db
                )
                results = [(doc, 1.0) for doc in docs]

            self.retrieved_docs = results
            print(f"✅ Retrieved {len(results)} documents")
            return results
        except Exception as e:
            print(f"⚠️ Retrieval error: {e}")
            traceback.print_exc()
            return []

    def format_context(
        self, documents: List[Tuple[Document, float]]
    ) -> Tuple[str, List[Dict]]:
        context = ""
        sources = []
        for idx, (doc, score) in enumerate(documents, 1):
            page = doc.metadata.get("page", "Unknown")
            source_name = doc.metadata.get("source", "Unknown")
            context += f"[Document {idx} - Page {page}]\n{doc.page_content}\n\n"
            sources.append(
                {
                    "index": idx,
                    "page": page,
                    "source": source_name,
                    "score": score,
                    "content_preview": doc.page_content[:100],
                }
            )
        return context, sources

    def generate_answer(self, question: str, context: str) -> str:
        prompt = f"""You are an expert financial analyst AI assistant.

Your task: Answer the user's question ONLY using the provided context.
Do NOT make up information.
If the answer is not in the context, say so explicitly.

Be precise, concise, and analytical.
Provide specific numbers when available.
Use professional financial terminology.

RETRIEVED CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""
        response = self.llm.invoke(prompt)
        return response.content

    def get_answer(
        self,
        question: str,
        k: int = 5,
        include_sources: bool = True,
        use_hybrid: Optional[bool] = None,
    ) -> Dict:
        retrieved_docs = self.retrieve_documents(question, k=k, use_hybrid=use_hybrid)

        if not retrieved_docs:
            return {
                "answer": "❌ No relevant documents found. Please upload a PDF first.",
                "sources": [],
                "success": False,
            }

        context, sources = self.format_context(retrieved_docs)
        answer = self.generate_answer(question, context)

        hybrid = self.use_hybrid_search if use_hybrid is None else use_hybrid
        return {
            "answer": answer,
            "sources": sources if include_sources else [],
            "success": True,
            "num_retrieved": len(retrieved_docs),
            "search_type": "Hybrid" if hybrid else "Vector",
        }

    def get_answer_with_context(
        self,
        question: str,
        previous_answer: Optional[str] = None,
        k: int = 5,
        use_hybrid: Optional[bool] = None,
    ) -> Dict:
        if previous_answer:
            enhanced_question = (
                f"Based on this previous answer: {previous_answer[:200]}...\n\n"
                f"Now answer: {question}"
            )
        else:
            enhanced_question = question
        return self.get_answer(enhanced_question, k=k, use_hybrid=use_hybrid)


def get_financial_answer(
    question: str,
    use_hybrid_search: bool = True,
    k: int = 5,
    include_sources: bool = True,
    rag_chain: Optional[RAGChain] = None,
    store_path: Optional[str] = None,
) -> Dict:
    """Answer using an existing RAGChain when provided (preferred)."""
    try:
        chain = rag_chain or RAGChain(use_hybrid_search=use_hybrid_search, store_path=store_path or "")
        return chain.get_answer(
            question,
            k=k,
            include_sources=include_sources,
            use_hybrid=use_hybrid_search,
        )
    except Exception as e:
        traceback.print_exc()
        return {
            "answer": f"❌ Error: {e}",
            "sources": [],
            "success": False,
        }
