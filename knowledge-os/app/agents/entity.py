"""Entity extraction agent."""

import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.prompts import load_prompt
from app.utils.confidence import merge_duplicate_entities
from app.utils.llm import get_llm_interface


class EntityAgent(BaseAgent):
    """Agent for extracting entities from content."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize entity agent."""
        super().__init__(config)
        self.llm = get_llm_interface(model=self.config.get("model", "gpt-4o"))
        self.max_tokens = self.config.get("max_tokens", 8000)

    async def run(self, state: PipelineState) -> PipelineState:
        """Extract entities from content."""
        raw_text = state.get("raw_text")
        if not raw_text:
            state["entities"] = []
            return state

        try:
            prompt_template = load_prompt("entity")
            prompt = prompt_template.format(content=raw_text[: self.max_tokens])

            response = await self.llm.call(prompt)

            result = json.loads(response.content)
            entities = result.get("entities", [])

            entities = merge_duplicate_entities(entities)

            state["entities"] = entities

        except json.JSONDecodeError:
            state["entities"] = self._extract_simple_entities(raw_text)
        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["entities"] = self._extract_simple_entities(raw_text)

        return state

    def _extract_simple_entities(self, text: str) -> List[Dict[str, Any]]:
        """Simple entity extraction using patterns."""
        import re

        entities = []

        capitalized_words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        seen = set()
        for word in capitalized_words[:20]:
            if word not in seen and len(word) > 2:
                seen.add(word)
                entities.append({
                    "name": word,
                    "type": "concept",
                    "description": "",
                    "aliases": [],
                    "confidence": 0.5,
                })

        tech_patterns = [
            r"\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*(?:\s+[A-Z][a-z]+)*)\b",
        ]
        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            for match in matches[:10]:
                if match not in seen and len(match) > 3:
                    seen.add(match)
                    entities.append({
                        "name": match,
                        "type": "technology",
                        "description": "",
                        "aliases": [],
                        "confidence": 0.5,
                    })

        return entities
