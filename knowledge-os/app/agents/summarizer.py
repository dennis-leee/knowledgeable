"""Summarizer agent - generate knowledge notes from content."""

import json
from typing import Any, Dict, List, Callable

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.prompts import load_prompt
from app.utils.llm import get_llm_interface


class SummarizerAgent(BaseAgent):
    """Agent for generating knowledge notes from content."""

    def __init__(self, config: Dict[str, Any] = None, stream_callback: Callable = None):
        """Initialize summarizer agent."""
        super().__init__(config)
        model = self.config.get("summarizer", "openrouter/free") if isinstance(self.config, dict) else "openrouter/free"
        self.llm = get_llm_interface(model=model)
        self.max_tokens = self.config.get("max_tokens", 16000) if isinstance(self.config, dict) else 16000
        self.stream_callback = stream_callback

    async def run(self, state: PipelineState) -> PipelineState:
        """Generate initial summary from raw content."""
        raw_text = state.get("raw_text", "")
        title = state.get("title", "")

        if not raw_text:
            state["error"] = "No content to summarize"
            return state

        try:
            prompt_template = load_prompt("summarizer")
            prompt = prompt_template.format(
                entities="[]",
                relations="[]",
                insights="[]",
                content=raw_text[: self.max_tokens]
            )

            if self.stream_callback:
                await self.stream_callback("summarizer", "正在分析内容...\n")

            response = await self.llm.call(prompt)

            if self.stream_callback:
                await self.stream_callback("summarizer", "分析完成，正在整理...\n")

            result = json.loads(response.content)

            state["title"] = result.get("title", title) or title
            state["summary"] = result.get("summary", "")
            state["key_points"] = result.get("key_points", [])
            state["important_details"] = result.get("important_details", [])
            state["takeaways"] = result.get("takeaways", [])

        except json.JSONDecodeError as e:
            state["error"] = f"Failed to parse response: {str(e)}"
            state["summary"] = self._generate_simple_summary(raw_text)
            state["key_points"] = []
            state["important_details"] = []
            state["takeaways"] = []
        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["summary"] = self._generate_simple_summary(raw_text)
            state["key_points"] = []
            state["important_details"] = []
            state["takeaways"] = []

        return state

    async def run_with_context(self, state: PipelineState, stream_callback: Callable = None) -> PipelineState:
        """Generate knowledge notes with context from entity/relation/insight agents."""
        raw_text = state.get("raw_text", "")
        entities = state.get("entities", [])
        relations = state.get("relations", [])
        insights = state.get("insights", [])
        title = state.get("title", "")

        if not raw_text:
            return state

        try:
            prompt_template = load_prompt("summarizer")

            entities_text = self._format_entities(entities)
            relations_text = self._format_relations(relations)
            insights_text = self._format_insights(insights)

            if stream_callback:
                await stream_callback("summarizer", "正在基于知识图谱生成人类可读的笔记...\n")

            prompt = prompt_template.format(
                entities=entities_text,
                relations=relations_text,
                insights=insights_text,
                content=raw_text[: self.max_tokens]
            )

            response = await self.llm.call(prompt)

            if stream_callback:
                await stream_callback("summarizer", "笔记生成完成!\n")

            result = json.loads(response.content)

            state["title"] = result.get("title", title) or title
            state["summary"] = result.get("summary", "")
            state["key_points"] = result.get("key_points", [])
            state["important_details"] = result.get("important_details", [])
            state["takeaways"] = result.get("takeaways", [])

            if stream_callback:
                await stream_callback("summarizer", f"生成了 {len(state['key_points'])} 个知识点\n")

        except json.JSONDecodeError as e:
            if stream_callback:
                await stream_callback("summarizer", f"解析失败: {str(e)}\n")
        except Exception as e:
            if stream_callback:
                await stream_callback("summarizer", f"生成失败: {self._get_error_message(e)}\n")

        return state

    def _format_entities(self, entities: List) -> str:
        """Format entities for prompt."""
        if not entities:
            return "无"
        lines = []
        for e in entities[:15]:
            if isinstance(e, dict):
                name = e.get("name", "Unknown")
                entity_type = e.get("type", "concept")
                desc = e.get("description", "")
                lines.append(f"- {name} ({entity_type})")
                if desc:
                    lines.append(f"  说明: {desc}")
            else:
                lines.append(f"- {e.name} ({e.type})")
        return "\n".join(lines) if lines else "无"

    def _format_relations(self, relations: List) -> str:
        """Format relations for prompt."""
        if not relations:
            return "无"
        lines = []
        for r in relations[:10]:
            if isinstance(r, dict):
                source = r.get("source", "?")
                target = r.get("target", "?")
                rel_type = r.get("type", "related")
                lines.append(f"- {source} --[{rel_type}]--> {target}")
            else:
                lines.append(f"- {r.source} --[{r.type}]--> {r.target}")
        return "\n".join(lines) if lines else "无"

    def _format_insights(self, insights: List) -> str:
        """Format insights for prompt."""
        if not insights:
            return "无"
        lines = []
        for i in insights[:10]:
            if isinstance(i, dict):
                insight_type = i.get("insight_type", "insight")
                text = i.get("text", "")
                lines.append(f"- [{insight_type}] {text}")
            else:
                lines.append(f"- [{i.insight_type}] {i.text}")
        return "\n".join(lines) if lines else "无"

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
