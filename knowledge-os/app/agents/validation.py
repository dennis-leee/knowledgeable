"""Validation agent - validate and repair knowledge objects."""

import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.schemas import Entity, Insight, Knowledge, Relation


class ValidationAgent(BaseAgent):
    """Agent for validating and quality-checking knowledge objects."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize validation agent."""
        super().__init__(config)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)

    async def run(self, state: PipelineState) -> PipelineState:
        """Validate the assembled knowledge object."""
        knowledge_data = state.get("knowledge")

        if not knowledge_data:
            state["validated"] = False
            state["validation_errors"] = ["No knowledge object to validate"]
            return state

        errors: List[str] = []
        knowledge = None

        try:
            knowledge = Knowledge(**knowledge_data)
        except Exception as e:
            errors.append(f"Knowledge validation error: {str(e)}")

        if knowledge:
            if not knowledge.title or len(knowledge.title) < 3:
                errors.append("Title is too short or missing")

            if not knowledge.summary or len(knowledge.summary) < 10:
                errors.append("Summary is too short or missing")

            if knowledge.confidence < self.confidence_threshold:
                errors.append(
                    f"Confidence ({knowledge.confidence:.2f}) below threshold ({self.confidence_threshold})"
                )

            if not knowledge.entities:
                errors.append("No entities extracted")

            for i, entity in enumerate(knowledge.entities[:3]):
                if not (entity.name if hasattr(entity, 'name') else entity.get("name", "")):
                    errors.append(f"Entity {i} missing name")

        state["validated"] = len(errors) == 0
        state["validation_errors"] = errors
        state["retry_count"] = state.get("retry_count", 0)

        return state

    def validate_json_schema(self, data: Dict[str, Any], schema_name: str) -> tuple:
        """Validate data against expected schema."""
        required_fields = {
            "knowledge": ["id", "title", "summary", "entities", "relations"],
            "entity": ["name", "type"],
            "relation": ["source", "target", "type"],
            "insight": ["text", "insight_type"],
        }

        required = required_fields.get(schema_name, [])
        missing = [f for f in required if f not in data or data[f] is None]

        return len(missing) == 0, missing
