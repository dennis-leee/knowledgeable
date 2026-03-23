"""Unit tests for LLM utilities."""

import pytest
from unittest.mock import patch, AsyncMock

from app.utils.llm import LLMInterface, LLMError


class TestLLMInterface:
    """Tests for LLMInterface."""

    @pytest.fixture
    def llm(self):
        """Create LLM interface instance."""
        return LLMInterface(model="gpt-4o-mini")

    @pytest.mark.asyncio
    async def test_call_without_api_key(self, llm):
        """Test LLM call without API key returns mock response."""
        with patch.object(llm, '_get_api_key', return_value=None):
            response = await llm.call("Test prompt")
            assert response.content is not None
            assert response.mock is True

    @pytest.mark.asyncio
    async def test_call_with_schema(self, llm):
        """Test LLM call with schema returns structured response."""
        from pydantic import BaseModel

        class TestSchema(BaseModel):
            name: str
            value: int

        with patch.object(llm, '_get_api_key', return_value=None):
            response = await llm.call("Test prompt", schema=TestSchema)
            assert response.content is not None

    def test_get_api_key_from_env(self, llm):
        """Test getting API key from environment."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            api_key = llm._get_api_key()
            assert api_key == 'test-key'

    def test_generate_mock_data(self, llm):
        """Test mock data generation."""
        from pydantic import BaseModel

        class MockSchema(BaseModel):
            name: str
            description: str = "a description"
            confidence: float = 0.5

        mock_data = llm._generate_mock_data(MockSchema)
        assert "name" in mock_data
        assert "description" in mock_data


class TestLLMError:
    """Tests for LLMError."""

    def test_error_creation(self):
        """Test error creation."""
        error = LLMError("Test error")
        assert str(error) == "Test error"
