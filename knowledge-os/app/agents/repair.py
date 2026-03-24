"""Repair agent - fix invalid data using LLM."""

import json
from datetime import datetime
from typing import Any, Dict

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.prompts import load_prompt
from app.utils.llm import get_llm_interface


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class RepairAgent(BaseAgent):
    """Agent for repairing invalid or incomplete data using LLM."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize repair agent."""
        super().__init__(config)
        self.llm = get_llm_interface(model=self.config.get("model", "gpt-4o-mini"))
        self.max_retries = self.config.get("max_retries", 3)

    async def run(self, state: PipelineState) -> PipelineState:
        """Attempt to repair invalid knowledge data."""
        retry_count = state.get("retry_count", 0)

        if retry_count >= self.max_retries:
            state["pending_review"] = True
            state["error"] = "Max repair retries exceeded"
            return state

        knowledge_data = state.get("knowledge")
        validation_errors = state.get("validation_errors", [])

        if not knowledge_data or not validation_errors:
            state["validated"] = True
            return state

        try:
            prompt_template = load_prompt("repair")
            prompt = prompt_template.format(
                error="\n".join(validation_errors),
                invalid_data=json.dumps(knowledge_data, ensure_ascii=False, indent=2, cls=DateTimeEncoder),
            )

            response = await self.llm.call(prompt)

            repaired_data = json.loads(response.content)

            state["knowledge"] = repaired_data
            state["retry_count"] = retry_count + 1
            state["validated"] = False
            state["validation_errors"] = []

        except json.JSONDecodeError:
            state["error"] = "Failed to parse repair response"
            state["retry_count"] = retry_count + 1
        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["retry_count"] = retry_count + 1

        return state

    def _fill_defaults(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fill missing fields with defaults."""
        defaults = {
            "entities": [],
            "relations": [],
            "insights": [],
            "tags": [],
            "confidence": 0.5,
            "sections": [],
        }

        for key, default_value in defaults.items():
            if key not in data or data[key] is None:
                data[key] = default_value

        if not data.get("id"):
            import uuid
            data["id"] = str(uuid.uuid4())[:16]

        if "title" not in data or not data["title"]:
            data["title"] = "Untitled Knowledge Entry"

        if "summary" not in data or not data["summary"]:
            data["summary"] = "No summary available"

        return data
