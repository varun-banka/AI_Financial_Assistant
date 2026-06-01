"""
AI Financial Research Assistant — Streamlit frontend (P0: cache, manifest, reuse).
"""

import logging
import os
import sys
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from core.config import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from core.manifest import get_store_path, hash_pdf_file
from utils.conversation_memory import ConversationMemory
from utils.embeddings import get_embeddings
from utils.financial_extractor import extract_metrics_from_documents
from utils.hybrid_search import HybridSearchEngine
from utils.pdf_loader import load_pdf
from utils.rag_chain import RAGChain
from utils.ratio_calculator import FinancialRatioCalculator
from utils.risk_analyzer import SentimentRiskAnalyzer, generate_risk_report
from utils.summary_generator import ExecutiveSummaryGenerator
from utils.text_splitter import split_documents
from utils.vector_store import create_or_load_vector_store, load_vector_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="AI Financial Research Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive {color: #27AE60;}
    .negative {color: #E74C3C;}
    .neutral {color: #3498DB;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ========== SESSION STATE ==========
_DEFAULTS = {
    "conversation_memory": None,
    "uploaded_files": {},
    "rag_chain": None,
    "hybrid_engine": None,
    "vector_db": None,
    "documents": None,
    "metrics": {},
    "ratios": {},
    "pdf_hash": None,
    "store_path": None,
    "is_processing": False,
    "last_processed_filename": None,
}

for key, default in _DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default if not isinstance(default, dict) else dict(default)

if st.session_state.conversation_memory is None:
    st.session_state.conversation_memory = ConversationMemory()


# ========== CACHED RESOURCES (survive Streamlit reruns) ==========
@st.cache_resource(show_spinner=False)
def get_cached_embeddings():
    return get_embeddings()


@st.cache_resource(show_spinner="Loading FAISS index...")
def get_cached_vector_db(store_path: str):
    return load_vector_store(store_path, get_cached_embeddings())


@st.cache_resource(show_spinner="Building BM25 index...")
def get_cached_hybrid_engine(pdf_hash: str, store_path: str, alpha: float = 0.7):
    db = get_cached_vector_db(store_path)
    docs = list(db.docstore._dict.values())
    return HybridSearchEngine(
        docs,
        alpha=alpha,
        vector_db=db,
        store_path=store_path,
        embeddings=get_cached_embeddings(),
    )


def build_rag_chain(pdf_hash: str, store_path: str) -> RAGChain:
    db = get_cached_vector_db(store_path)
    hybrid = get_cached_hybrid_engine(pdf_hash, store_path)
    return RAGChain(
        use_hybrid_search=True,
        alpha=0.7,
        vector_db=db,
        hybrid_engine=hybrid,
        store_path=store_path,
    )


# ========== HELPERS ==========
def process_pdf(pdf_path: str, filename: str) -> bool:
    """Ingest PDF: hash → split → cached FAISS → metrics → reusable RAG."""
    if st.session_state.is_processing:
        st.warning("⏳ PDF already being processed. Please wait.")
        return False

    st.session_state.is_processing = True
    chunk_size = DEFAULT_CHUNK_SIZE
    chunk_overlap = DEFAULT_CHUNK_OVERLAP

    try:
        safe_name = os.path.basename(filename)
        pdf_hash = hash_pdf_file(pdf_path)
        store_path = get_store_path(pdf_hash)

        with st.spinner(f"Processing {safe_name}..."):
            documents = load_pdf(pdf_path)
            chunks = split_documents(
                documents, chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )

            embeddings = get_cached_embeddings()
            vector_db, from_cache = create_or_load_vector_store(
                chunks=chunks,
                pdf_hash=pdf_hash,
                filename=safe_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                embeddings=embeddings,
            )

            metrics = extract_metrics_from_documents(chunks)
            ratios = FinancialRatioCalculator(metrics).calculate_all_ratios()

            st.session_state.pdf_hash = pdf_hash
            st.session_state.store_path = store_path
            st.session_state.documents = chunks
            st.session_state.metrics[safe_name] = metrics
            st.session_state.ratios[safe_name] = ratios
            st.session_state.vector_db = vector_db
            st.session_state.uploaded_files[safe_name] = pdf_path
            st.session_state.last_processed_filename = safe_name

            st.session_state.rag_chain = build_rag_chain(pdf_hash, store_path)
            st.session_state.hybrid_engine = get_cached_hybrid_engine(pdf_hash, store_path)

            if from_cache:
                st.success(
                    f"✅ Loaded cached index for {safe_name} "
                    f"(hash {pdf_hash[:12]}…) — no re-embedding"
                )
            else:
                st.success(
                    f"✅ Indexed {safe_name} ({len(chunks)} chunks) "
                    f"at {store_path}"
                )
            return True
    except Exception as e:
        st.error(f"❌ Error processing PDF: {e}")
        logging.exception("process_pdf failed")
        return False
    finally:
        st.session_state.is_processing = False


def display_metrics(metrics, ratios, company_name="Company"):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if metrics.get("Revenue"):
            st.metric("Revenue", f"₹{metrics['Revenue']:,.0f} Cr", delta="Annual")
        else:
            st.metric("Revenue", "N/A")

    with col2:
        if metrics.get("Net_Profit"):
            st.metric("Net Profit", f"₹{metrics['Net_Profit']:,.0f} Cr", delta="Annual")
        else:
            st.metric("Net Profit", "N/A")

    with col3:
        if ratios.get("Profit_Margin_Percent"):
            margin = ratios["Profit_Margin_Percent"]
            st.metric(
                "Profit Margin",
                f"{margin:.2f}%",
                delta="Good" if margin > 10 else "Fair",
            )
        else:
            st.metric("Profit Margin", "N/A")

    with col4:
        if ratios.get("ROE_Percent"):
            roe = ratios["ROE_Percent"]
            st.metric(
                "ROE",
                f"{roe:.2f}%",
                delta="Strong" if roe > 15 else "Moderate",
            )
        else:
            st.metric("ROE", "N/A")


def create_charts(metrics, ratios):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Profitability Ratios")
        ratios_to_show = {
            "Profit Margin %": ratios.get("Profit_Margin_Percent"),
            "ROE %": ratios.get("ROE_Percent"),
            "ROA %": ratios.get("ROA_Percent"),
            "EBITDA Margin %": ratios.get("EBITDA_Margin_Percent"),
        }
        ratios_clean = {k: v for k, v in ratios_to_show.items() if v is not None}
        if ratios_clean:
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=list(ratios_clean.keys()),
                        y=list(ratios_clean.values()),
                        marker_color=[
                            "#27AE60" if v > 10 else "#F39C12"
                            for v in ratios_clean.values()
                        ],
                    )
                ]
            )
            fig.update_layout(
                title="Profitability Analysis",
                yaxis_title="Percentage (%)",
                xaxis_title="Ratio",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("⚙️ Leverage Ratios")
        leverage_ratios = {
            "Debt-to-Equity": ratios.get("Debt_to_Equity"),
            "Debt-to-Assets %": ratios.get("Debt_to_Assets"),
            "Equity Ratio %": ratios.get("Equity_Ratio"),
        }
        leverage_clean = {k: v for k, v in leverage_ratios.items() if v is not None}
        if leverage_clean:
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=list(leverage_clean.keys()),
                        y=list(leverage_clean.values()),
                        marker_color=[
                            "#E74C3C" if k.startswith("Debt") else "#27AE60"
                            for k in leverage_clean.keys()
                        ],
                    )
                ]
            )
            fig.update_layout(
                title="Leverage Analysis",
                yaxis_title="Ratio / Percentage",
                xaxis_title="Metric",
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)


def main():
    st.title("📊 AI Financial Research Assistant")
    st.markdown("### Analyze Annual Reports with Advanced RAG & Financial Metrics")

    st.sidebar.title("🔧 Navigation")
    app_mode = st.sidebar.radio(
        "Select Mode",
        [
            "📤 Upload & Process",
            "❓ Ask Questions",
            "📈 Financial Analysis",
            "💡 Risk Assessment",
            "📋 Executive Summary",
            "💬 Conversation History",
        ],
    )

    if st.session_state.store_path:
        st.sidebar.caption(
            f"Index: `{st.session_state.store_path}`"
        )
        if st.session_state.pdf_hash:
            st.sidebar.caption(f"PDF hash: `{st.session_state.pdf_hash[:16]}…`")

    # ========== UPLOAD & PROCESS ==========
    if app_mode == "📤 Upload & Process":
        st.header("📤 Upload Annual Reports")

        uploaded_file = st.file_uploader(
            "Upload PDF (Annual Report)",
            type=["pdf"],
            help="Upload financial documents for analysis",
        )

        if uploaded_file:
            filename = os.path.basename(uploaded_file.name)
            os.makedirs("uploads", exist_ok=True)
            file_path = os.path.join("uploads", filename)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.info(f"📁 File saved: {filename}")

            if st.session_state.is_processing:
                st.warning("⏳ PDF already being processed…")

            if st.button(
                "🚀 Process PDF",
                use_container_width=True,
                disabled=st.session_state.is_processing,
            ):
                process_pdf(file_path, filename)

    # ========== ASK QUESTIONS ==========
    elif app_mode == "❓ Ask Questions":
        st.header("❓ Ask Financial Questions")

        if not st.session_state.documents or st.session_state.rag_chain is None:
            st.warning("⚠️ Please upload and process a PDF first")
        else:
            st.success("✅ Vector store ready for Q&A (cached index)")

            question = st.text_input(
                "Ask a financial question:",
                placeholder="e.g., What was the revenue growth?",
            )

            col1, col2 = st.columns(2)
            with col1:
                search_mode = st.radio(
                    "Search Mode",
                    ["Hybrid (Recommended)", "Vector Only"],
                )
            with col2:
                k = st.slider("Documents to retrieve", 1, 10, 5)

            if question:
                use_hybrid = search_mode == "Hybrid (Recommended)"
                memory = st.session_state.conversation_memory

                if memory.is_follow_up_question(question):
                    st.info("💡 This appears to be a follow-up question")

                chain: RAGChain = st.session_state.rag_chain

                with st.spinner("🔍 Searching and generating answer..."):
                    if memory.is_follow_up_question(question) and memory.get_full_history():
                        prev = memory.get_full_history()[-1]["answer"]
                        result = chain.get_answer_with_context(
                            question,
                            previous_answer=prev,
                            k=k,
                            use_hybrid=use_hybrid,
                        )
                    else:
                        result = chain.get_answer(
                            question, k=k, use_hybrid=use_hybrid
                        )

                if result["success"]:
                    st.subheader("💬 Answer")
                    st.write(result["answer"])

                    with st.expander("📚 Sources"):
                        for source in result["sources"]:
                            st.write(
                                f"**Document {source['index']} - Page {source['page']}**"
                            )
                            st.write(f"Relevance Score: {source['score']:.2f}")
                            st.write(
                                f"Preview: {source['content_preview'][:100]}..."
                            )

                    memory.add_turn(
                        question,
                        result["answer"],
                        metadata={
                            "num_sources": len(result["sources"]),
                            "search_type": result["search_type"],
                        },
                    )
                    st.success("✅ Answer saved to conversation memory")
                else:
                    st.error(result["answer"])

    # ========== FINANCIAL ANALYSIS ==========
    elif app_mode == "📈 Financial Analysis":
        st.header("📈 Financial Analysis")

        if not st.session_state.metrics:
            st.warning("⚠️ Please upload and process a PDF first")
        else:
            for filename, metrics in st.session_state.metrics.items():
                st.subheader(f"📊 {filename}")
                ratios = st.session_state.ratios.get(filename, {})
                display_metrics(metrics, ratios, filename)
                create_charts(metrics, ratios)

                st.subheader("📋 Detailed Metrics")
                st.dataframe(
                    pd.DataFrame(
                        {"Metric": list(metrics.keys()), "Value": list(metrics.values())}
                    ),
                    use_container_width=True,
                )

                st.subheader("📐 Financial Ratios")
                st.dataframe(
                    pd.DataFrame(
                        {"Ratio": list(ratios.keys()), "Value": list(ratios.values())}
                    ),
                    use_container_width=True,
                )

    # ========== RISK ASSESSMENT ==========
    elif app_mode == "💡 Risk Assessment":
        st.header("💡 Risk & Sentiment Analysis")

        if not st.session_state.documents:
            st.warning("⚠️ Please upload and process a PDF first")
        else:
            if st.button("🔍 Analyze Risks & Sentiment", use_container_width=True):
                with st.spinner("Analyzing document for risks and opportunities..."):
                    try:
                        analyzer = SentimentRiskAnalyzer()
                        report = generate_risk_report(
                            st.session_state.documents, analyzer
                        )
                        st.write(report)
                    except Exception as e:
                        st.error(f"❌ Error generating risk report: {e}")

    # ========== EXECUTIVE SUMMARY ==========
    elif app_mode == "📋 Executive Summary":
        st.header("📋 Executive Summary")

        if not st.session_state.documents:
            st.warning("⚠️ Please upload and process a PDF first")
        else:
            if st.button("📝 Generate Executive Summary", use_container_width=True):
                with st.spinner("Generating comprehensive executive summary..."):
                    try:
                        generator = ExecutiveSummaryGenerator()
                        uploaded_files = list(st.session_state.uploaded_files.keys())
                        company_name = (
                            uploaded_files[0].replace(".pdf", "")
                            if uploaded_files
                            else "Company"
                        )
                        metrics = (
                            list(st.session_state.metrics.values())[0]
                            if st.session_state.metrics
                            else {}
                        )
                        ratios = (
                            list(st.session_state.ratios.values())[0]
                            if st.session_state.ratios
                            else {}
                        )
                        report = generator.generate_full_report(
                            st.session_state.documents,
                            metrics,
                            ratios,
                            company_name,
                        )
                        st.write(report)

                        if st.button("💾 Export Report"):
                            export_file = (
                                f"exports/report_"
                                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                            )
                            os.makedirs("exports", exist_ok=True)
                            with open(export_file, "w", encoding="utf-8") as f:
                                f.write(report)
                            st.success(f"✅ Report exported to {export_file}")
                    except Exception as e:
                        st.error(f"❌ Error generating summary: {e}")

    # ========== CONVERSATION HISTORY ==========
    elif app_mode == "💬 Conversation History":
        st.header("💬 Conversation History")
        memory = st.session_state.conversation_memory
        history = memory.get_full_history()

        if not history:
            st.info("No conversation history yet")
        else:
            summary = memory.get_summary()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Turns", summary["total_turns"])
            with col2:
                st.metric("Total Characters", summary["total_characters"])
            with col3:
                st.metric("Session ID", summary["session_id"][:12] + "...")

            st.subheader("Conversation Transcript")
            for turn in history:
                with st.expander(
                    f"Turn {turn['turn_number']}: {turn['question'][:50]}..."
                ):
                    st.write(f"**Q:** {turn['question']}")
                    st.write(f"**A:** {turn['answer']}")
                    st.caption(f"Time: {turn['timestamp']}")

            if st.button("💾 Export Conversation"):
                export_file = (
                    f"exports/conversation_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                )
                os.makedirs("exports", exist_ok=True)
                memory.export_history(export_file)
                st.success("✅ Conversation exported")

            if st.button("🗑️ Clear History"):
                memory.clear_history()
                st.rerun()


if __name__ == "__main__":
    main()
