"""Unit tests for agents."""

import pytest

from app.agents import (
    IngestionAgent,
    SummarizerAgent,
    EntityAgent,
    StructuringAgent,
    ValidationAgent,
)
from app.orchestrator.state import PipelineState


class TestIngestionAgent:
    """Tests for IngestionAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return IngestionAgent(config={"timeout": 10})

    @pytest.mark.asyncio
    async def test_run_with_url(self, agent):
        """Test ingestion with URL."""
        state: PipelineState = {"url": "https://example.com"}
        result = await agent.run(state)
        assert "raw_text" in result

    @pytest.mark.asyncio
    async def test_run_without_url(self, agent):
        """Test ingestion without URL."""
        state: PipelineState = {}
        result = await agent.run(state)
        assert "error" in result


class TestSummarizerAgent:
    """Tests for SummarizerAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return SummarizerAgent(config={"max_tokens": 8000})

    @pytest.mark.asyncio
    async def test_run_with_text(self, agent):
        """Test summarization with text."""
        state: PipelineState = {
            "raw_text": "This is a test document. " * 50
        }
        result = await agent.run(state)
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_run_without_text(self, agent):
        """Test summarization without text."""
        state: PipelineState = {}
        result = await agent.run(state)
        assert "summary" in result or "error" in result


class TestEntityAgent:
    """Tests for EntityAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return EntityAgent(config={"max_tokens": 8000})

    @pytest.mark.asyncio
    async def test_run_with_text(self, agent):
        """Test entity extraction with text."""
        state: PipelineState = {
            "raw_text": "Artificial Intelligence and Machine Learning are transforming technology."
        }
        result = await agent.run(state)
        assert "entities" in result

    @pytest.mark.asyncio
    async def test_run_without_text(self, agent):
        """Test entity extraction without text."""
        state: PipelineState = {}
        result = await agent.run(state)
        assert result.get("entities") == []


class TestStructuringAgent:
    """Tests for StructuringAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return StructuringAgent()

    @pytest.mark.asyncio
    async def test_run_with_data(self, agent):
        """Test structuring with complete data."""
        state: PipelineState = {
            "title": "Test Title",
            "summary": "Test summary",
            "sections": ["Section 1", "Section 2"],
            "entities": [{"name": "Entity1", "type": "concept"}],
            "relations": [],
            "insights": [],
            "url": "https://test.com",
        }
        result = await agent.run(state)
        assert "knowledge" in result
        assert result["knowledge"]["title"] == "Test Title"

    @pytest.mark.asyncio
    async def test_run_generates_id(self, agent):
        """Test that ID is generated."""
        state: PipelineState = {
            "title": "Test",
            "summary": "Summary",
            "entities": [],
            "relations": [],
            "insights": [],
        }
        result = await agent.run(state)
        assert "knowledge" in result
        assert "id" in result["knowledge"]


class TestValidationAgent:
    """Tests for ValidationAgent."""

    @pytest.fixture
    def agent(self):
        """Create agent instance."""
        return ValidationAgent(config={"confidence_threshold": 0.5})

    @pytest.mark.asyncio
    async def test_valid_knowledge(self, agent):
        """Test validation of valid knowledge."""
        state: PipelineState = {
            "knowledge": {
                "id": "test-123",
                "title": "Valid Title",
                "summary": "Valid summary text",
                "source": "test",
                "entities": [{"name": "E1", "type": "concept"}],
                "relations": [],
                "insights": [],
                "confidence": 0.8,
            }
        }
        result = await agent.run(state)
        assert result.get("validated") is True

    @pytest.mark.asyncio
    async def test_invalid_knowledge(self, agent):
        """Test validation of invalid knowledge."""
        state: PipelineState = {
            "knowledge": {
                "id": "test-456",
                "title": "T",
                "summary": "Short",
                "entities": [],
                "relations": [],
                "insights": [],
                "confidence": 0.3,
            }
        }
        result = await agent.run(state)
        assert result.get("validated") is False
        assert len(result.get("validation_errors", [])) > 0

    @pytest.mark.asyncio
    async def test_missing_knowledge(self, agent):
        """Test validation with missing knowledge."""
        state: PipelineState = {}
        result = await agent.run(state)
        assert result.get("validated") is False
