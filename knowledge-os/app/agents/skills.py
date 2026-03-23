"""Skills agent - generate AI-consumable skills from knowledge."""

import json
from pathlib import Path
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.schemas import Knowledge, Skill


class SkillsAgent(BaseAgent):
    """Agent for generating AI-consumable skills from knowledge."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize skills agent."""
        super().__init__(config)
        self.output_dir = Path(self.config.get("skills_path", "./data/skills"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, state: PipelineState) -> PipelineState:
        """Generate skills from knowledge."""
        knowledge_data = state.get("knowledge")

        if not knowledge_data:
            state["skills"] = []
            return state

        try:
            knowledge = Knowledge(**knowledge_data)

            skill = self._generate_skill(knowledge)

            skill_path = self._save_skill(skill, knowledge)

            state["skills"] = [skill.model_dump(mode="json")]
            state["skill_path"] = str(skill_path)

        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["skills"] = []

        return state

    def _generate_skill(self, knowledge: Knowledge) -> Skill:
        """Generate a skill from knowledge."""
        skill_name = self._slugify(knowledge.title)

        actions = self._generate_actions(knowledge)

        examples = self._generate_examples(knowledge)

        tags = knowledge.tags[:5] if knowledge.tags else []
        if not tags:
            tags = [knowledge.title.lower().replace(" ", "-")]

        return Skill(
            name=f"knowledge-{skill_name}",
            description=f"Provides knowledge about {knowledge.title}. {knowledge.summary[:200]}",
            category="knowledge",
            tags=tags,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"Query about {knowledge.title}",
                    }
                },
                "required": ["query"],
            },
            actions=actions,
            examples=examples,
            context_refs=[f"knowledge:{knowledge.id}"],
            confidence=knowledge.confidence,
            source_knowledge_ids=[knowledge.id],
        )

    def _generate_actions(self, knowledge: Knowledge) -> List[Dict[str, Any]]:
        """Generate action steps for skill."""
        actions = [
            {
                "step": 1,
                "description": "Recall relevant information",
                "instruction": f"Search memory for '{knowledge.title}' and related concepts.",
            }
        ]

        if knowledge.entities:
            entity_names = [e.name for e in knowledge.entities[:3]]
            actions.append({
                "step": 2,
                "description": "Identify key entities",
                "instruction": f"Focus on: {', '.join(entity_names)}",
            })

        if knowledge.relations:
            actions.append({
                "step": 3,
                "description": "Understand relationships",
                "instruction": f"Key relationships: {len(knowledge.relations)} connections identified.",
            })

        actions.append({
            "step": 4,
            "description": "Synthesize and respond",
            "instruction": "Combine all relevant information to provide a comprehensive answer.",
        })

        return actions

    def _generate_examples(self, knowledge: Knowledge) -> List[Dict[str, Any]]:
        """Generate usage examples."""
        examples = []

        examples.append({
            "input": f"What is {knowledge.title}?",
            "output": knowledge.summary,
        })

        if knowledge.entities:
            entity = knowledge.entities[0]
            examples.append({
                "input": f"Tell me about {entity.name}",
                "output": f"{entity.name} is a {entity.type}. {entity.description or ''}",
            })

        return examples

    def _slugify(self, text: str) -> str:
        """Convert text to kebab-case slug."""
        import re
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text[:50]

    def _save_skill(self, skill: Skill, knowledge: Knowledge) -> Path:
        """Save skill to file."""
        category_dir = self.output_dir / skill.category
        category_dir.mkdir(parents=True, exist_ok=True)

        skill_file = category_dir / f"{skill.name}.json"
        with open(skill_file, "w", encoding="utf-8") as f:
            json.dump(skill.model_dump(mode="json"), f, indent=2, ensure_ascii=False, default=str)

        markdown_file = category_dir / f"{skill.name}.md"
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(skill.to_markdown())

        return skill_file

    def generate_mcp_definition(self, skills: List[Skill]) -> Dict[str, Any]:
        """Generate MCP server definition from skills."""
        tools = []

        for skill in skills:
            tools.append({
                "name": skill.name,
                "description": skill.description,
                "inputSchema": skill.parameters,
            })

        return {
            "mcp_version": "1.0.0",
            "name": "knowledge-graph-mcp",
            "description": "MCP server for knowledge graph access",
            "tools": tools,
        }
