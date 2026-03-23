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

    async def run(self, url: str) -> "PipelineState":
        """Run the complete pipeline for a URL."""
        from app.orchestrator.state import PipelineState

        state: "PipelineState" = {
            "url": url,
            "raw_text": "",
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

        state = await self.ingestion_agent.run(state)
        if state.get("error") and not state.get("raw_text"):
            return state

        state = await self.summarizer_agent.run(state)
        state = await self.entity_agent.run(state)
        state = await self.relation_agent.run(state)
        state = await self.insight_agent.run(state)
        state = await self.structuring_agent.run(state)
        state = await self.validation_agent.run(state)

        max_retries = self.config.get("pipeline", {}).get("retry_limit", 3)
        while not state.get("validated") and state.get("retry_count", 0) < max_retries:
            state = await self.repair_agent.run(state)
            state = await self.validation_agent.run(state)

        if state.get("validated"):
            state = await self.memory_agent.run(state)
            if state.get("stored"):
                state = await self.skills_agent.run(state)

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
