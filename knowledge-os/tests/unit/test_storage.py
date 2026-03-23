"""Unit tests for storage components."""

import json
import tempfile
from pathlib import Path

import pytest

from app.schemas import Knowledge
from app.storage import GraphStorage, MarkdownStorage, MockVectorStorage


class TestMarkdownStorage:
    """Tests for MarkdownStorage."""

    @pytest.fixture
    def storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield MarkdownStorage(base_path=tmpdir)

    @pytest.fixture
    def sample_knowledge(self):
        """Create sample knowledge."""
        return Knowledge(
            id="test-123",
            title="Test Knowledge Title",
            summary="This is a test summary for the knowledge base.",
            source="test",
            entities=[],
            relations=[],
            insights=[],
            tags=["test", "sample"],
        )

    def test_save_knowledge(self, storage, sample_knowledge):
        """Test saving knowledge to markdown."""
        path = storage.save(sample_knowledge)
        assert path.exists()
        content = path.read_text()
        assert "Test Knowledge Title" in content
        assert "test summary" in content

    def test_list_all(self, storage, sample_knowledge):
        """Test listing all markdown files."""
        storage.save(sample_knowledge)
        files = storage.list_all()
        assert len(files) >= 1


class TestGraphStorage:
    """Tests for GraphStorage."""

    @pytest.fixture
    def storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield GraphStorage(base_path=tmpdir)

    @pytest.fixture
    def sample_knowledge(self):
        """Create sample knowledge."""
        return Knowledge(
            id="graph-test-123",
            title="Graph Test",
            summary="Test summary",
            source="test",
            entities=[],
            relations=[],
            insights=[],
            tags=[],
        )

    def test_add_knowledge(self, storage, sample_knowledge):
        """Test adding knowledge to graph."""
        storage.add_knowledge(sample_knowledge)
        graph = storage.export()
        assert graph["metadata"]["node_count"] >= 1
        assert graph["metadata"]["edge_count"] >= 0

    def test_search(self, storage, sample_knowledge):
        """Test searching nodes."""
        storage.add_knowledge(sample_knowledge)
        results = storage.search("Graph Test")
        assert len(results) >= 1

    def test_get_statistics(self, storage, sample_knowledge):
        """Test getting graph statistics."""
        storage.add_knowledge(sample_knowledge)
        stats = storage.get_statistics()
        assert "node_count" in stats
        assert "edge_count" in stats


class TestMockVectorStorage:
    """Tests for MockVectorStorage."""

    @pytest.fixture
    def storage(self):
        """Create mock storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield MockVectorStorage(persist_path=tmpdir)

    @pytest.fixture
    def sample_knowledge(self):
        """Create sample knowledge."""
        return Knowledge(
            id="vector-test-123",
            title="Vector Test",
            summary="Test summary for vector storage",
            source="test",
            entities=[],
            relations=[],
            insights=[],
            tags=[],
        )

    def test_add_knowledge(self, storage, sample_knowledge):
        """Test adding knowledge."""
        storage.add_knowledge(sample_knowledge)
        assert storage.get_count() == 1

    def test_search(self, storage, sample_knowledge):
        """Test searching."""
        storage.add_knowledge(sample_knowledge)
        results = storage.search("vector")
        assert len(results) >= 1

    def test_delete_knowledge(self, storage, sample_knowledge):
        """Test deleting knowledge."""
        storage.add_knowledge(sample_knowledge)
        storage.delete_knowledge(sample_knowledge.id)
        assert storage.get_count() == 0
