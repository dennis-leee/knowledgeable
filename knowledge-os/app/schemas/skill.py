"""Skill schema - Pydantic models for skill generation."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Skill(BaseModel):
    """AI-consumable skill representation."""

    name: str
    version: str = "1.0.0"
    description: str
    category: str = "knowledge"
    tags: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    context_refs: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    generated_at: datetime = Field(default_factory=datetime.now)
    source_knowledge_ids: List[str] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create from dictionary."""
        return cls.model_validate(data)

    def to_markdown(self) -> str:
        """Convert to Markdown format with YAML frontmatter."""
        import yaml

        frontmatter = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "compatibility": ["claude", "openai", "gemini"],
            "generated_at": self.generated_at.isoformat(),
        }

        md = "---\n"
        md += yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        md += "---\n\n"

        md += f"# {self.name}\n\n"
        md += f"{self.description}\n\n"

        if self.actions:
            md += "## Actions\n\n"
            for i, action in enumerate(self.actions, 1):
                md += f"### Step {i}: {action.get('description', 'Untitled')}\n"
                md += f"{action.get('instruction', '')}\n\n"

        if self.examples:
            md += "## Examples\n\n"
            for example in self.examples:
                md += f"**Input:** {example.get('input', '')}\n"
                md += f"**Output:** {example.get('output', '')}\n\n"

        if self.context_refs:
            md += "## Related Knowledge\n\n"
            for ref in self.context_refs:
                md += f"- {ref}\n"

        return md


class MCPServerDefinition(BaseModel):
    """MCP Server definition."""

    mcp_version: str = "1.0.0"
    name: str
    description: str
    tools: List[Dict[str, Any]] = Field(default_factory=list)
