"""LangGraph pipeline orchestration."""

from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.base import BaseAgent
    from app.orchestrator.state import PipelineState


class KnowledgePipeline:
    """Main pipeline orchestrator using LangGraph-like pattern."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize pipeline with agents."""
        from app.config import load_config
        from app.agents import (
            IngestionAgent,
            SummarizerAgent,
            EntityAgent,
            InsightAgent,
            RelationAgent,
            StructuringAgent,
            ValidationAgent,
            RepairAgent,
            MemoryAgent,
            SkillsAgent,
        )

        self.config = config or load_config().model_dump()

        model_config = self.config.get("model", {})
        pipeline_config = self.config.get("pipeline", {})
        confidence_config = self.config.get("confidence", {})
        storage_config = self.config.get("storage", {})

        self.ingestion_agent = IngestionAgent(config=pipeline_config)
        self.summarizer_agent = SummarizerAgent(config=model_config)
        self.entity_agent = EntityAgent(config=model_config)
        self.relation_agent = RelationAgent(config=model_config)
        self.insight_agent = InsightAgent(config=model_config)
        self.structuring_agent = StructuringAgent()
        self.validation_agent = ValidationAgent(config=confidence_config)
        self.repair_agent = RepairAgent(config=model_config)
        self.memory_agent = MemoryAgent(config=storage_config)
        self.skills_agent = SkillsAgent(config=storage_config)

    async def run(self, url: str = None, text: str = None, progress_callback=None) -> "PipelineState":
        """Run the complete pipeline for a URL or text."""
        from app.orchestrator.state import PipelineState

        state: "PipelineState" = {
            "url": url or "",
            "raw_text": text or "",
            "title": "",
            "summary": "",
            "sections": [],
            "entities": [],
            "relations": [],
            "insights": [],
            "knowledge": None,
            "validated": False,
            "validation_errors": [],
            "retry_count": 0,
            "error": None,
            "approved": False,
            "approved_by": None,
            "pending_review": False,
            "review_notes": None,
        }

        def update_progress(stage: str, progress: int):
            if progress_callback:
                progress_callback(stage, progress)

        update_progress("ingestion", 10)

        if text:
            state["raw_text"] = text
            state["title"] = self._extract_title_from_text(text)
        else:
            state = await self.ingestion_agent.run(state)

        if state.get("error") and not state.get("raw_text"):
            return state

        update_progress("entity", 20)
        state = await self.entity_agent.run(state)

        update_progress("relation", 35)
        state = await self.relation_agent.run(state)

        update_progress("insight", 50)
        state = await self.insight_agent.run(state)

        update_progress("summarizer", 65)
        state = await self.summarizer_agent.run(state)

        update_progress("structuring", 75)
        state = await self.structuring_agent.run(state)

        update_progress("validation", 80)
        state = await self.validation_agent.run(state)

        max_retries = self.config.get("pipeline", {}).get("retry_limit", 3)
        retry_count = 0
        while not state.get("validated") and retry_count < max_retries:
            update_progress("repair", 85)
            state = await self.repair_agent.run(state)
            state = await self.validation_agent.run(state)
            retry_count += 1

        if state.get("validated"):
            update_progress("memory", 92)
            state = await self.memory_agent.run(state)
            if state.get("stored"):
                update_progress("skills", 100)
                state = await self.skills_agent.run(state)
        else:
            update_progress("validation", 100)

        return state

    def get_agent(self, name: str) -> "BaseAgent":
        """Get agent by name."""
        from app.agents.base import BaseAgent
        
        agents: Dict[str, BaseAgent] = {
            "ingestion": self.ingestion_agent,
            "summarizer": self.summarizer_agent,
            "entity": self.entity_agent,
            "relation": self.relation_agent,
            "insight": self.insight_agent,
            "structuring": self.structuring_agent,
            "validation": self.validation_agent,
            "repair": self.repair_agent,
            "memory": self.memory_agent,
            "skills": self.skills_agent,
        }
        return agents.get(name)

    def _extract_title_from_text(self, text: str) -> str:
        """Extract title from text content."""
        lines = text.split("\n")
        for line in lines[:20]:
            line = line.strip()
            if len(line) > 5 and len(line) < 200:
                return line
        return "Untitled"
