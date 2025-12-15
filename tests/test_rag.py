import tempfile

import pytest

from src.rag import Document, get_context
from src.rag.loader import _chunk_text, load_documents
from src.rag.store import add_documents, clear_store, initialize_store, search


class TestChunking:
    def test_chunk_text_empty_string(self):
        result = _chunk_text("")
        assert result == []

    def test_chunk_text_short_string(self):
        text = "Short text"
        result = _chunk_text(text, chunk_size=500, overlap=50)
        assert len(result) == 1
        assert result[0] == "Short text"

    def test_chunk_text_long_string(self):
        text = "a" * 1000
        result = _chunk_text(text, chunk_size=500, overlap=50)
        assert len(result) >= 2

    def test_chunk_text_with_overlap(self):
        text = "a" * 600
        result = _chunk_text(text, chunk_size=500, overlap=100)
        assert len(result) == 2


class TestLoadDocuments:
    def test_load_documents_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_documents(tmpdir)
            assert result == []

    def test_load_documents_nonexistent_dir(self):
        result = load_documents("/nonexistent/path")
        assert result == []


class TestVectorStore:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        initialize_store()
        yield
        clear_store()

    def test_initialize_store(self):
        collection = initialize_store()
        assert collection is not None
        assert collection.name == "prb_documents"

    def test_add_and_search_documents(self):
        docs = [
            Document(
                content="PRB guidelines for project management",
                metadata={"source": "test.pdf"},
            ),
            Document(
                content="How to submit expense reports",
                metadata={"source": "test.pdf"},
            ),
            Document(
                content="Company vacation policy details",
                metadata={"source": "test.pdf"},
            ),
        ]
        add_documents(docs)

        results = search("project management", k=2)
        assert len(results) <= 2
        assert any("project" in r.lower() for r in results)

    def test_search_empty_store(self):
        clear_store()
        initialize_store()
        results = search("any query")
        assert results == []

    def test_add_empty_documents(self):
        add_documents([])


class TestGetContext:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        initialize_store()
        yield
        clear_store()

    def test_get_context_with_documents(self):
        docs = [
            Document(content="First document about testing", metadata={"source": "doc1.pdf"}),
            Document(content="Second document about deployment", metadata={"source": "doc2.pdf"}),
        ]
        add_documents(docs)

        context = get_context("testing")
        assert context != ""
        assert "---" in context or "testing" in context.lower()

    def test_get_context_empty_store(self):
        clear_store()
        initialize_store()
        context = get_context("any query")
        assert context == ""
