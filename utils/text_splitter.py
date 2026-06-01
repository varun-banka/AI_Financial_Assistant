"""
Phase 1: Text Splitter Module
Splits documents into manageable chunks for embedding
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Optional
from langchain_core.documents import Document


def split_documents(documents: List[Document], chunk_size: int = 3000, chunk_overlap: int = 300, max_chunks: Optional[int] = None) -> List[Document]:
    """
    Splits documents into chunks using RecursiveCharacterTextSplitter.
    
    Args:
        documents (List[Document]): List of documents to split
        chunk_size (int): Size of each chunk in characters
        chunk_overlap (int): Overlap between chunks for continuity
        
    Returns:
        List[Document]: List of chunk documents with metadata preserved
        
    Why Chunking?
        - LLMs have context windows (e.g., Gemini 1.5 Pro: 2M tokens)
        - Semantic chunking preserves meaning better than random splits
        - Overlapping chunks maintain context across boundaries
        
    Example:
        >>> chunks = split_documents(documents, chunk_size=1000, chunk_overlap=200)
        >>> print(f"Created {len(chunks)} chunks")
    """
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_documents(documents)
        original_count = len(chunks)

        if max_chunks is not None and max_chunks > 0:
            chunks = chunks[:max_chunks]
            print(f"⚠️  Limiting chunks for testing: using {len(chunks)}/{original_count} chunks")
        else:
            print(f"✅ Split into {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")

        return chunks
    except Exception as e:
        raise Exception(f"Error splitting documents: {str(e)}")
