"""Insight extraction agent."""

import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.prompts import load_prompt
from app.utils.llm import get_llm_interface


class InsightAgent(BaseAgent):
    """Agent for extracting non-obvious insights."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize insight agent."""
        super().__init__(config)
        self.llm = get_llm_interface(model=self.config.get("model", "gpt-4o"))
        self.max_tokens = self.config.get("max_tokens", 8000)

    async def run(self, state: PipelineState) -> PipelineState:
        """Extract insights from content and entities."""
        raw_text = state.get("raw_text")
        entities = state.get("entities", [])
        if not raw_text:
            state["insights"] = []
            return state

        try:
            entity_names = [e.get("name", "") for e in entities if e.get("name")]
            prompt_template = load_prompt("insight")
            prompt = prompt_template.format(
                entities="\n".join(entity_names[:10]),
                content=raw_text[: self.max_tokens],
            )

            response = await self.llm.call(prompt)

            result = json.loads(response.content)
            insights = result.get("insights", [])

            state["insights"] = insights

        except json.JSONDecodeError:
            state["insights"] = self._extract_simple_insights(raw_text, entities)
        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["insights"] = self._extract_simple_insights(raw_text, entities)

        return state

    def _extract_simple_insights(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Simple insight extraction."""
        insights = []
        entity_names = [e.get("name", "") for e in entities if e.get("name")]

        sentences = text.split(".")
        for sentence in sentences[:10]:
            sentence = sentence.strip()
            if len(sentence) > 50 and any(word in sentence.lower() for word in ["therefore", "thus", "consequently", "suggests", "implies"]):
                insights.append({
                    "text": sentence,
                    "insight_type": "implication",
                    "confidence": 0.6,
                    "supporting_entities": [],
                })

        if len(entities) > 3:
            insights.append({
                "text": f"The document discusses {len(entities)} distinct entities, suggesting a complex interconnected topic.",
                "insight_type": "pattern",
                "confidence": 0.5,
                "supporting_entities": entity_names[:5],
            })

        return insights[:5]
