"""LLM utilities - unified interface for LLM calls."""

import json
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """LLM response wrapper."""

    content: str
    raw: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class LLMError(Exception):
    """LLM-related error."""

    pass


class LLMInterface:
    """Unified LLM interface for making calls."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None, provider: str = "openai"):
        """Initialize LLM interface."""
        self.model = model
        self.api_key = api_key or self._get_api_key()
        self.provider = provider

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        import os

        if os.environ.get("OPENAI_API_KEY", "").startswith("sk-or-"):
            self.provider = "openrouter"
            return os.environ.get("OPENAI_API_KEY")
        return os.environ.get("OPENAI_API_KEY")

    async def call(
        self,
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Make an LLM call with optional structured output."""
        try:
            import os

            if self.api_key:
                import httpx

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://knowledge-os.local",
                    "X-Title": "Knowledge OS",
                }

                payload = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }

                if schema:
                    payload["response_format"] = {
                        "type": "json_object",
                        "schema": schema.model_json_schema(),
                    }

                async with httpx.AsyncClient() as client:
                    base_url = os.environ.get("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
                    response = await client.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=120.0,
                    )
                    response.raise_for_status()
                    data = response.json()

                content = data["choices"][0]["message"]["content"]

                return LLMResponse(
                    content=content,
                    raw=data,
                    model=data.get("model"),
                    usage=data.get("usage"),
                )
            else:
                return LLMResponse(
                    content=self._mock_response(prompt, schema),
                    raw={"mock": True},
                )

        except Exception as e:
            raise LLMError(f"LLM call failed: {str(e)}") from e

    def _mock_response(self, prompt: str, schema: Optional[Type[BaseModel]] = None) -> str:
        """Generate mock response for testing without API key."""
        if schema:
            mock_data = self._generate_mock_data(schema)
            return json.dumps(mock_data, ensure_ascii=False)
        return "Mock response"

    def _generate_mock_data(self, schema: Type[BaseModel]) -> Dict[str, Any]:
        """Generate mock data matching schema."""
        from pydantic import Field
        import random

        mock = {}
        schema_dict = schema.model_json_schema()

        for field_name, field_info in schema_dict.get("properties", {}).items():
            field_type = field_info.get("type", "string")

            if field_type == "string":
                if "description" in field_info:
                    desc = field_info["description"].lower()
                    if "name" in desc:
                        mock[field_name] = f"Mock {field_name}"
                    elif "summary" in desc or "text" in desc:
                        mock[field_name] = "This is a mock summary for testing purposes."
                    else:
                        mock[field_name] = f"Mock value for {field_name}"
                else:
                    mock[field_name] = f"Mock {field_name}"
            elif field_type == "number" or field_type == "integer":
                mock[field_name] = random.uniform(0.5, 0.95)
            elif field_type == "boolean":
                mock[field_name] = True
            elif field_type == "array":
                mock[field_name] = []
            elif field_type == "object":
                mock[field_name] = {}

        return mock


_llm_interface: Optional[LLMInterface] = None


def get_llm_interface(model: str = "gpt-4o-mini") -> LLMInterface:
    """Get global LLM interface instance."""
    global _llm_interface
    if _llm_interface is None:
        _llm_interface = LLMInterface(model=model)
    return _llm_interface
