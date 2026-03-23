"""Structuring agent - assemble knowledge object."""

import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.schemas import Knowledge
from app.utils.confidence import ConfidenceCalculator


class StructuringAgent(BaseAgent):
    """Agent for assembling Knowledge objects from extracted data."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize structuring agent."""
        super().__init__(config)
        self.confidence_calculator = ConfidenceCalculator()

    async def run(self, state: PipelineState) -> PipelineState:
        """Assemble knowledge object from extracted components."""
        try:
            title = state.get("title", "Untitled")
            summary = state.get("summary", "")
            sections = state.get("sections", [])
            entities = state.get("entities", [])
            relations = state.get("relations", [])
            insights = state.get("insights", [])
            url = state.get("url", "")

            confidence = self.confidence_calculator.calculate_knowledge_confidence(
                entities, relations, insights
            )

            knowledge_id = self._generate_id(title, url)

            knowledge_data = {
                "id": knowledge_id,
                "title": title,
                "summary": summary,
                "sections": sections,
                "entities": entities,
                "relations": relations,
                "insights": insights,
                "tags": self._extract_tags(title, summary, entities),
                "source": url or "unknown",
                "source_url": url,
                "confidence": confidence,
                "canonical_entities": self._build_canonical_map(entities),
                "created_at": datetime.now(),
            }

            state["knowledge"] = knowledge_data

        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["knowledge"] = None

        return state

    def _generate_id(self, title: str, url: str) -> str:
        """Generate unique ID for knowledge entry."""
        content = f"{title}:{url}:{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _extract_tags(
        self, title: str, summary: str, entities: list
    ) -> list:
        """Extract tags from content."""
        tags = set()

        words = (title + " " + summary).lower().split()
        important_words = [w for w in words if len(w) > 4][:5]
        tags.update(important_words)

        for entity in entities[:5]:
            entity_type = entity.get("type", "")
            if entity_type in ["technology", "method", "concept"]:
                name = entity.get("name", "").lower().replace(" ", "-")
                if name:
                    tags.add(name)

        return list(tags)[:10]

    def _build_canonical_map(self, entities: list) -> Dict[str, str]:
        """Build canonical entity mapping."""
        canonical_map = {}
        canonical_id = 1

        for entity in entities:
            entity_id = f"entity_{canonical_id}"
            canonical_map[entity.get("name", "")] = entity_id
            canonical_id += 1

        return canonical_map
