"""Relation extraction agent."""

import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.prompts import load_prompt
from app.utils.llm import get_llm_interface


class RelationAgent(BaseAgent):
    """Agent for extracting relations between entities."""

    def __init__(self, config: Dict[str, Any] = None, stream_callback: callable = None):
        """Initialize relation agent."""
        super().__init__(config)
        model = self.config.get("relation", "openrouter/free") if isinstance(self.config, dict) else "openrouter/free"
        self.llm = get_llm_interface(model=model)
        self.max_tokens = self.config.get("max_tokens", 8000) if isinstance(self.config, dict) else 8000
        self.stream_callback = stream_callback

    async def run(self, state: PipelineState) -> PipelineState:
        """Extract relations from content and entities."""
        raw_text = state.get("raw_text")
        entities = state.get("entities", [])
        if not raw_text or not entities:
            state["relations"] = []
            return state

        if self.stream_callback:
            await self.stream_callback("relation", "正在分析实体间关系...\n")

        try:
            entity_names = [e.get("name", "") for e in entities if e.get("name")]
            prompt_template = load_prompt("relation")
            prompt = prompt_template.format(
                entities="\n".join(entity_names),
                content=raw_text[: self.max_tokens],
            )

            response = await self.llm.call(prompt)

            if self.stream_callback:
                await self.stream_callback("relation", "关系分析完成...\n")

            result = json.loads(response.content)
            relations = result.get("relations", [])

            state["relations"] = relations

            if self.stream_callback:
                await self.stream_callback("relation", f"共发现 {len(relations)} 条关系\n")

        except json.JSONDecodeError:
            state["relations"] = self._extract_simple_relations(raw_text, entities)
        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["relations"] = self._extract_simple_relations(raw_text, entities)

        return state

    def _extract_simple_relations(
        self, text: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Simple relation extraction using co-occurrence."""
        import re

        relations = []
        entity_names = [e.get("name", "") for e in entities if e.get("name")]

        action_verbs = ["uses", "depends on", "enhances", "contrasts with", "implies"]

        for verb in action_verbs:
            pattern = rf"(\w+(?:\s+\w+){{0,2}})\s+{re.escape(verb)}\s+(\w+(?:\s+\w+){{0,2}})"
            matches = re.findall(pattern, text, re.IGNORECASE)

            for match in matches[:5]:
                source, target = match
                if any(source.lower() in name.lower() for name in entity_names) or any(
                    target.lower() in name.lower() for name in entity_names
                ):
                    relations.append({
                        "source": source.strip(),
                        "target": target.strip(),
                        "type": verb.replace(" ", "_").lower(),
                        "confidence": 0.5,
                        "evidence": [f"{source} {verb} {target}"],
                    })

        return relations[:10]
