from src.rag.loader import Document, load_documents, load_docx, load_pdf
from src.rag.store import add_documents, clear_store, initialize_store, search

__all__ = [
    "Document",
    "load_pdf",
    "load_docx",
    "load_documents",
    "initialize_store",
    "add_documents",
    "search",
    "clear_store",
    "get_context",
]


def get_context(query: str) -> str:
    chunks = search(query, k=3)

    if not chunks:
        return ""

    return "\n\n---\n\n".join(chunks)
