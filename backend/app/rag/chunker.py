"""Text chunking strategies optimized for clinical trial documents."""
from typing import List
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings


# Clinical-trial-specific separators
# Chinese and English sentence/paragraph boundaries
CLINICAL_SEPARATORS = [
    "\n\n",     # paragraph break
    "\n",       # line break
    "。",       # Chinese period
    "；",       # Chinese semicolon
    "；",       # Chinese semicolon (fullwidth)
    ". ",       # English period + space
    "; ",       # English semicolon
    "，",       # Chinese comma
    ", ",       # English comma
    " ",        # word boundary (last resort)
    "",         # character level (last resort)
]


def get_text_splitter(
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> RecursiveCharacterTextSplitter:
    """Get a RecursiveCharacterTextSplitter tuned for clinical documents."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size or settings.CHUNK_SIZE,
        chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP,
        separators=CLINICAL_SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )


def split_documents(docs: List[Document]) -> List[Document]:
    """Split loaded documents into chunks optimized for RAG retrieval."""
    splitter = get_text_splitter()
    chunks = splitter.split_documents(docs)

    # Enrich metadata with chunk index
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["total_chunks"] = len(chunks)

    return chunks
