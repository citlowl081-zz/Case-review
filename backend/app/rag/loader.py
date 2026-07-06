"""Document loader factory — supports PDF, DOCX, TXT, MD, CSV, XLSX."""
import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
)


def load_document(file_path: str, file_type: str) -> List[Document]:
    """Load a document using the appropriate LangChain loader.

    Args:
        file_path: Absolute path to the document
        file_type: File extension without dot (e.g. 'pdf', 'docx')

    Returns:
        List of LangChain Document objects
    """
    ext = file_type.lower().lstrip(".")

    loader_map = {
        "pdf": PyPDFLoader,
        "docx": Docx2txtLoader,
        "doc": Docx2txtLoader,
        "txt": TextLoader,
        "md": UnstructuredMarkdownLoader,
        "csv": CSVLoader,
    }

    loader_cls = loader_map.get(ext)
    if loader_cls is None:
        # Default: try as text
        loader_cls = TextLoader

    # Handle CSV specially for encoding
    if ext == "csv":
        loader = loader_cls(file_path, encoding="utf-8-sig")
    elif ext == "txt":
        loader = loader_cls(file_path, encoding="utf-8")
    else:
        loader = loader_cls(file_path)

    return loader.load()
