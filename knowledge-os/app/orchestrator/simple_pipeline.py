"""Simplified knowledge extraction pipeline with full agent support."""

from typing import Dict, Any, Optional, Callable
import asyncio


class SimplePipeline:
    """Simplified pipeline with streaming support and all agents."""

    def __init__(self, config: Dict[str, Any] = None):
        from app.config import load_config
        self.config = config or load_config().model_dump()

    async def run(
        self,
        url: str = None,
        text: str = None,
        progress_callback: Callable = None,
        stream_callback: Callable = None,
        agent_models: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Run the complete pipeline with all agents."""
        agent_models = agent_models or {}
        state = {
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
            "stored": False,
            "markdown_path": None,
            "skill_path": None,
            "key_points": [],
            "important_details": [],
            "takeaways": [],
        }

        async def update_progress(stage: str, progress: int, message: str = ""):
            if progress_callback:
                await progress_callback(stage, progress, message)

        await update_progress("ingestion", 10, "正在获取页面内容...")

        if text:
            state["raw_text"] = text
            state["title"] = self._extract_title(text)
            await update_progress("ingestion", 15, "直接使用粘贴的文本")
        else:
            from app.agents.ingestion import IngestionAgent
            ingestion = IngestionAgent(config=self.config.get("pipeline", {}))
            state = await ingestion.run(state)

        if state.get("error") and not state.get("raw_text"):
            return state

        summarizer_model = agent_models.get("summarizer", "openrouter/free")
        entity_model = agent_models.get("entity", "openrouter/free")
        relation_model = agent_models.get("relation", "openrouter/free")
        insight_model = agent_models.get("insight", "openrouter/free")
        skills_model = agent_models.get("skills", "openrouter/free")

        await update_progress("entity", 20, "正在提取实体...")
        if stream_callback:
            await stream_callback("entity", "开始识别实体...\n")

        from app.agents.entity import EntityAgent
        entity_agent = EntityAgent(config={"entity": entity_model}, stream_callback=stream_callback)
        state = await entity_agent.run(state)
        await update_progress("entity", 30, f"提取到 {len(state.get('entities', []))} 个实体")

        await update_progress("relation", 35, "正在分析关系...")
        from app.agents.relation import RelationAgent
        relation_agent = RelationAgent(config={"relation": relation_model}, stream_callback=stream_callback)
        state = await relation_agent.run(state)
        await update_progress("relation", 40, f"分析出 {len(state.get('relations', []))} 个关系")

        await update_progress("insight", 45, "正在提取洞察...")
        from app.agents.insight import InsightAgent
        insight_agent = InsightAgent(config={"insight": insight_model}, stream_callback=stream_callback)
        state = await insight_agent.run(state)
        await update_progress("insight", 50, f"提取到 {len(state.get('insights', []))} 个洞察")

        await update_progress("summarizer", 55, "正在生成人类可读的知识点...")
        from app.agents.summarizer import SummarizerAgent
        summarizer = SummarizerAgent(config={"summarizer": summarizer_model}, stream_callback=stream_callback)
        state = await summarizer.run_with_context(state, stream_callback=stream_callback)
        await update_progress("summarizer", 65, "知识点生成完成")

        await update_progress("structuring", 70, "正在构建知识结构...")
        from app.agents.structuring import StructuringAgent
        structuring_agent = StructuringAgent()
        state = await structuring_agent.run(state)
        await update_progress("structuring", 75, "知识结构构建完成")

        await update_progress("validation", 80, "正在进行质量验证...")
        from app.agents.validation import ValidationAgent
        validator = ValidationAgent(config=self.config.get("confidence", {}))
        state = await validator.run(state)
        await update_progress("validation", 85, "验证完成" if state.get("validated") else "验证未通过")

        if state.get("validated"):
            await update_progress("memory", 90, "正在保存...")
            from app.agents.memory import MemoryAgent
            memory = MemoryAgent(config=self.config.get("storage", {}))
            state = await memory.run(state)
            await update_progress("memory", 95, "保存完成")

        if state.get("stored"):
            await update_progress("skills", 98, "正在生成 Skills...")
            from app.agents.skills import SkillsAgent
            skills_agent = SkillsAgent(config={"skills": skills_model}, stream_callback=stream_callback)
            state = await skills_agent.run(state)
            await update_progress("skills", 100, "Skills 生成完成")
        else:
            await update_progress("skills", 100, "跳过 Skills 生成")

        return state

    def _extract_title(self, text: str) -> str:
        """Extract title from text."""
        lines = text.split("\n")
        for line in lines[:20]:
            line = line.strip()
            if len(line) > 5 and len(line) < 200:
                return line
        return "Untitled"
