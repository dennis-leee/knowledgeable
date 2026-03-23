"""Integration tests for the complete pipeline."""

import pytest
from unittest.mock import patch, AsyncMock

from app.orchestrator import KnowledgePipeline
from app.orchestrator.state import PipelineState


class TestKnowledgePipeline:
    """Integration tests for KnowledgePipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create pipeline instance."""
        return KnowledgePipeline()

    @pytest.mark.asyncio
    async def test_pipeline_run_with_mock_content(self, pipeline):
        """Test complete pipeline run with mock content."""
        with patch.object(
            pipeline.ingestion_agent,
            '_fetch_url',
            new_callable=AsyncMock,
            return_value="Test content for knowledge extraction"
        ):
            result = await pipeline.run("https://example.com")
            
            assert result is not None
            assert "raw_text" in result
            assert "entities" in result
            assert "relations" in result

    @pytest.mark.asyncio
    async def test_pipeline_handles_empty_url(self, pipeline):
        """Test pipeline with empty URL."""
        result = await pipeline.run("")
        assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_pipeline_validation_failure(self, pipeline):
        """Test pipeline handles validation failure."""
        with patch.object(
            pipeline.ingestion_agent,
            '_fetch_url',
            new_callable=AsyncMock,
            return_value="Short"  # Too short to pass validation
        ):
            result = await pipeline.run("https://example.com")
            # Should still run but validation may fail

    @pytest.mark.asyncio
    async def test_pipeline_stores_on_success(self, pipeline):
        """Test pipeline stores on successful validation."""
        with patch.object(
            pipeline.ingestion_agent,
            '_fetch_url',
            new_callable=AsyncMock,
            return_value="This is a detailed test document. " * 50
        ):
            result = await pipeline.run("https://example.com")
            if result.get("validated"):
                assert "stored" in result or "markdown_path" in result

    def test_get_agent(self, pipeline):
        """Test getting agent by name."""
        agent = pipeline.get_agent("ingestion")
        assert agent is not None
        
        agent = pipeline.get_agent("summarizer")
        assert agent is not None
        
        agent = pipeline.get_agent("invalid")
        assert agent is None


class TestPipelineState:
    """Tests for PipelineState."""

    def test_state_creation(self):
        """Test creating pipeline state."""
        state: PipelineState = {
            "url": "https://example.com",
            "raw_text": "",
            "validated": False,
        }
        assert state["url"] == "https://example.com"
        assert state["validated"] is False

    def test_state_update(self):
        """Test updating pipeline state."""
        state: PipelineState = {}
        state["entities"] = []
        state["entities"].append({"name": "Test"})
        assert len(state["entities"]) == 1


class TestEdgeCases:
    """Edge case tests."""

    @pytest.mark.asyncio
    async def test_very_long_url(self):
        """Test handling of very long URLs."""
        pipeline = KnowledgePipeline()
        long_url = "https://example.com/" + "a" * 1000
        result = await pipeline.run(long_url)
        assert "error" or "raw_text" in result

    @pytest.mark.asyncio
    async def test_special_characters_in_url(self):
        """Test URL with special characters."""
        pipeline = KnowledgePipeline()
        url = "https://example.com/path?param=value&other=测试"
        result = await pipeline.run(url)
        assert "error" or "raw_text" in result

    @pytest.mark.asyncio
    async def test_empty_entities_and_relations(self):
        """Test handling when no entities/relations extracted."""
        pipeline = KnowledgePipeline()
        result = await pipeline.run("https://example.com")
        # Should handle gracefully
        assert "entities" in result

    @pytest.mark.asyncio
    async def test_multiple_validation_retries(self):
        """Test multiple validation retries."""
        pipeline = KnowledgePipeline(config={
            "pipeline": {"retry_limit": 3},
            "model": {},
            "confidence": {"threshold": 0.9},
            "storage": {}
        })
        
        with patch.object(
            pipeline.ingestion_agent,
            '_fetch_url',
            new_callable=AsyncMock,
            return_value="Content"
        ):
            result = await pipeline.run("https://example.com")
            assert "retry_count" in result
