import chromadb
from chromadb.config import Settings

from src.rag.loader import Document

COLLECTION_NAME = "prb_documents"
PERSIST_DIRECTORY = ".chroma_db"

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def initialize_store() -> chromadb.Collection:
    global _client, _collection

    if _collection is not None:
        return _collection

    _client = chromadb.Client(
        Settings(
            persist_directory=PERSIST_DIRECTORY,
            anonymized_telemetry=False,
        )
    )

    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    return _collection


def add_documents(docs: list[Document]) -> None:
    if not docs:
        return

    collection = initialize_store()

    ids = [f"doc_{i}_{doc.metadata.get('source', 'unknown')}" for i, doc in enumerate(docs)]
    contents = [doc.content for doc in docs]
    metadatas = [doc.metadata for doc in docs]

    collection.add(
        ids=ids,
        documents=contents,
        metadatas=metadatas,
    )


def search(query: str, k: int = 3) -> list[str]:
    collection = initialize_store()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(k, collection.count()),
    )

    documents = results.get("documents", [[]])
    return documents[0] if documents else []


def clear_store() -> None:
    global _collection, _client

    if _client is not None:
        _client.delete_collection(COLLECTION_NAME)
        _collection = None
