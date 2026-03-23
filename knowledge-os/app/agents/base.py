"""Base agent interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.orchestrator.state import PipelineState


class BaseAgent(ABC):
    """Base class for all agents in the pipeline."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize agent with configuration."""
        self.config = config or {}

    @abstractmethod
    async def run(self, state: PipelineState) -> PipelineState:
        """Execute the agent's main function.

        Args:
            state: Current pipeline state

        Returns:
            Updated pipeline state
        """
        pass

    def _update_state(self, state: PipelineState, **kwargs) -> PipelineState:
        """Helper to update state with new values."""
        for key, value in kwargs.items():
            if value is not None:
                state[key] = value
        return state

    def _get_error_message(self, e: Exception) -> str:
        """Get error message from exception."""
        return f"{self.__class__.__name__} error: {str(e)}"
