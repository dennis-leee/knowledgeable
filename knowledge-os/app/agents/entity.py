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

    def __init__(self, config: Dict[str, Any] = None, stream_callback: callable = None):
        """Initialize entity agent."""
        super().__init__(config)
        model = self.config.get("entity", "openrouter/free") if isinstance(self.config, dict) else "openrouter/free"
        self.llm = get_llm_interface(model=model)
        self.max_tokens = self.config.get("max_tokens", 8000) if isinstance(self.config, dict) else 8000
        self.stream_callback = stream_callback

    async def run(self, state: PipelineState) -> PipelineState:
        """Extract entities from content."""
        raw_text = state.get("raw_text")
        title = state.get("title", "")
        if not raw_text:
            state["entities"] = []
            return state

        if self.stream_callback:
            await self.stream_callback("entity", "正在识别文本中的实体...\n")

        try:
            prompt_template = load_prompt("entity")
            prompt = prompt_template.format(
                title=title,
                content=raw_text[: self.max_tokens]
            )

            response = await self.llm.call(prompt)

            if self.stream_callback:
                await self.stream_callback("entity", "实体识别完成，正在去噪...\n")

            result = json.loads(response.content)
            entities = result.get("entities", [])

            entities = self._denoise_entities(entities, title)
            entities = merge_duplicate_entities(entities)

            state["entities"] = entities

            if self.stream_callback:
                await self.stream_callback("entity", f"共识别出 {len(entities)} 个有效实体\n")

        except json.JSONDecodeError:
            state["entities"] = self._extract_simple_entities(raw_text)
        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["entities"] = self._extract_simple_entities(raw_text)

        return state

    def _denoise_entities(self, entities: list, title: str = "") -> list:
        """Remove noise entities that are likely navigation or generic words."""
        title_lower = title.lower()

        generic_words = {
            "project", "solution", "ai", "data", "info", "news", "article",
            "post", "page", "content", "home", "about", "contact", "help",
            "menu", "nav", "header", "footer", "sidebar", "widget",
            "login", "signin", "signup", "register", "password", "username",
            "search", "filter", "sort", "view", "edit", "delete", "add",
            "save", "cancel", "ok", "yes", "no", "confirm", "submit",
            "next", "previous", "back", "forward", "close", "open",
            "loading", "error", "success", "warning", "message", "alert",
            "copyright", "terms", "privacy", "policy", "disclaimer",
            "comments", "replies", "likes", "shares", "views",
            "follow", "followers", "following", "share", "tweet", "retweet",
        }

        filtered = []
        for entity in entities:
            name = entity.get("name", "")
            name_lower = name.lower()

            if len(name) < 2:
                continue

            if name_lower in generic_words:
                continue

            if name_lower in title_lower:
                continue

            if name.count(' ') > 4:
                continue

            filtered.append(entity)

        return filtered

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
