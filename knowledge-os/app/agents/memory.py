"""Memory agent - persist knowledge to storage."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.schemas import Knowledge
from app.storage import GraphStorage, MarkdownStorage, get_vector_storage


class MemoryAgent(BaseAgent):
    """Agent for persisting knowledge to various storage backends."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize memory agent."""
        super().__init__(config)
        self.markdown_storage = MarkdownStorage(
            base_path=self.config.get("markdown_path", "./data/md")
        )
        self.graph_storage = GraphStorage(
            base_path=self.config.get("graph_path", "./data/graph")
        )
        self.vector_storage = get_vector_storage(
            persist_path=self.config.get("vector_persist", "./data/vectors")
        )
        self.pending_review_dir = Path(
            self.config.get("pending_review_dir", "./pending_review")
        )
        self.pending_review_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, state: PipelineState) -> PipelineState:
        """Persist knowledge to all storage backends."""
        knowledge_data = state.get("knowledge")

        if not knowledge_data:
            state["error"] = "No knowledge to store"
            return state

        try:
            knowledge = Knowledge(**knowledge_data)

            markdown_path = self.markdown_storage.save(knowledge)
            state["markdown_path"] = str(markdown_path)

            self.graph_storage.add_knowledge(knowledge)

            self.vector_storage.add_knowledge(knowledge)

            if state.get("pending_review"):
                await self._save_pending_review(state, knowledge)

            state["stored"] = True

        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["stored"] = False

        return state

    async def _save_pending_review(
        self, state: PipelineState, knowledge: Knowledge
    ) -> None:
        """Save knowledge for pending human review."""
        review_file = self.pending_review_dir / f"{knowledge.id}.json"

        review_data = {
            "knowledge": knowledge.model_dump(mode="json"),
            "validation_errors": state.get("validation_errors", []),
            "retry_count": state.get("retry_count", 0),
            "original_error": state.get("error", ""),
            "created_at": knowledge.created_at.isoformat(),
        }

        with open(review_file, "w", encoding="utf-8") as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False, default=str)

    def load_pending_review(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """Load pending review data."""
        review_file = self.pending_review_dir / f"{knowledge_id}.json"
        if not review_file.exists():
            return None

        with open(review_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def approve_pending_review(self, knowledge_id: str) -> bool:
        """Approve a pending review and store the knowledge."""
        review_data = self.load_pending_review(knowledge_id)
        if not review_data:
            return False

        knowledge = Knowledge(**review_data["knowledge"])

        self.markdown_storage.save(knowledge)
        self.graph_storage.add_knowledge(knowledge)
        self.vector_storage.add_knowledge(knowledge)

        review_file = self.pending_review_dir / f"{knowledge_id}.json"
        review_file.unlink(missing_ok=True)

        return True

    def reject_pending_review(self, knowledge_id: str) -> bool:
        """Reject and discard a pending review."""
        review_file = self.pending_review_dir / f"{knowledge_id}.json"
        if review_file.exists():
            review_file.unlink(missing_ok=True)
            return True
        return False
