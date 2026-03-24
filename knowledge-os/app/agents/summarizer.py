"""Summarizer agent - generate summaries from content."""

import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.prompts import load_prompt
from app.utils.llm import get_llm_interface


class SummarizerAgent(BaseAgent):
    """Agent for generating summaries from raw content."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize summarizer agent."""
        super().__init__(config)
        self.llm = get_llm_interface(model=self.config.get("model", "gpt-4o-mini"))
        self.max_tokens = self.config.get("max_tokens", 8000)

    async def run(self, state: PipelineState) -> PipelineState:
        """Generate summary from entities, relations, insights and optionally raw text."""
        entities = state.get("entities", [])
        relations = state.get("relations", [])
        insights = state.get("insights", [])
        raw_text = state.get("raw_text", "")

        if not entities and not raw_text:
            state["error"] = "No content to summarize"
            return state

        try:
            prompt_template = load_prompt("summarizer")

            entities_text = json.dumps(entities, ensure_ascii=False, indent=2)
            relations_text = json.dumps(relations, ensure_ascii=False, indent=2)
            insights_text = json.dumps(insights, ensure_ascii=False, indent=2)

            if entities or relations or insights:
                fallback_content = f"Original content (for reference only):\n{raw_text[:2000]}" if raw_text else ""
                prompt = prompt_template.format(
                    entities=entities_text,
                    relations=relations_text,
                    insights=insights_text,
                    fallback_content=fallback_content
                )
            else:
                prompt = prompt_template.format(
                    entities="[]",
                    relations="[]",
                    insights="[]",
                    fallback_content=f"Content:\n{raw_text[: self.max_tokens]}"
                )

            response = await self.llm.call(prompt)

            result = json.loads(response.content)

            state["summary"] = result.get("summary", "")
            state["sections"] = result.get("sections", [])

        except json.JSONDecodeError:
            state["summary"] = self._generate_simple_summary(raw_text)
            state["sections"] = self._extract_sections(raw_text)
        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["summary"] = self._generate_simple_summary(raw_text)
            state["sections"] = []

        return state

    def _generate_simple_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a simple extractive summary."""
        sentences = text.split(".")
        summary_parts = []
        current_length = 0

        for sentence in sentences[:5]:
            sentence = sentence.strip()
            if current_length + len(sentence) < max_length:
                summary_parts.append(sentence)
                current_length += len(sentence)

        return ". ".join(summary_parts) + "." if summary_parts else text[:max_length]

    def _extract_sections(self, text: str, max_sections: int = 5) -> List[str]:
        """Extract key sections from text."""
        lines = text.split("\n")
        sections = []

        for line in lines:
            line = line.strip()
            if line and len(line) > 20:
                sections.append(line)
            if len(sections) >= max_sections:
                break

        return sections
