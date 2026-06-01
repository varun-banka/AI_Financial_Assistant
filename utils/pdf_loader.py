"""
Phase 1: PDF Loader Module
Loads PDF documents using PyPDFLoader
"""

from langchain_community.document_loaders import PyPDFLoader
from typing import List
from langchain_core.documents import Document
import os


def load_pdf(pdf_path: str) -> List[Document]:
    """
    Loads PDF and returns documents with metadata.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        List[Document]: List of documents with page content and metadata
        
    Example:
        >>> documents = load_pdf("reports/annual_report.pdf")
        >>> print(documents[0].page_content)
        >>> print(documents[0].metadata)
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"✅ Loaded {len(documents)} pages from {pdf_path}")
        return documents
    except Exception as e:
        raise Exception(f"Error loading PDF: {str(e)}")
