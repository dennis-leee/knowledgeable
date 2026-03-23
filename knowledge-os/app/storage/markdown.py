"""Markdown storage adapter."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas import Knowledge


class MarkdownStorage:
    """Storage adapter for Markdown files."""

    def __init__(self, base_path: str = "./data/md"):
        """Initialize Markdown storage."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _slugify(self, text: str) -> str:
        """Convert text to URL-safe slug."""
        import re
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text[:50]

    def _generate_filename(self, knowledge: Knowledge) -> str:
        """Generate filename for knowledge entry."""
        slug = self._slugify(knowledge.title)
        date = knowledge.created_at.strftime("%Y%m%d")
        return f"{date}-{slug}.md"

    def save(self, knowledge: Knowledge) -> Path:
        """Save knowledge as Markdown file."""
        filename = self._generate_filename(knowledge)
        filepath = self.base_path / filename

        content = self._generate_markdown(knowledge)
        filepath.write_text(content, encoding="utf-8")

        return filepath

    def _generate_markdown(self, knowledge: Knowledge) -> str:
        """Generate Markdown content from knowledge."""
        lines = [
            f"# {knowledge.title}",
            "",
            f"**ID:** `{knowledge.id}`",
            f"**Source:** {knowledge.source}",
            f"**Created:** {knowledge.created_at.isoformat()}",
            f"**Confidence:** {knowledge.confidence:.2f}",
            "",
            "## Summary",
            "",
            knowledge.summary,
            "",
        ]

        if knowledge.sections:
            lines.append("## Key Sections")
            for i, section in enumerate(knowledge.sections, 1):
                lines.append(f"{i}. {section}")
            lines.append("")

        if knowledge.entities:
            lines.append("## Entities")
            for entity in knowledge.entities:
                lines.append(f"- **{entity.name}** ({entity.type})")
                if entity.description:
                    lines.append(f"  - {entity.description}")
            lines.append("")

        if knowledge.relations:
            lines.append("## Relations")
            for relation in knowledge.relations:
                lines.append(f"- {relation.source} --[{relation.type}]--> {relation.target}")
            lines.append("")

        if knowledge.insights:
            lines.append("## Insights")
            for insight in knowledge.insights:
                lines.append(f"- [{insight.insight_type}] {insight.text}")
            lines.append("")

        if knowledge.tags:
            lines.append("## Tags")
            lines.append(", ".join(f"`{tag}`" for tag in knowledge.tags))

        return "\n".join(lines)

    def load(self, filepath: Path) -> Optional[Knowledge]:
        """Load knowledge from Markdown file."""
        if not filepath.exists():
            return None

        content = filepath.read_text(encoding="utf-8")
        return self._parse_markdown(content, filepath)

    def _parse_markdown(self, content: str, filepath: Path) -> Knowledge:
        """Parse Markdown content back to Knowledge."""
        lines = content.split("\n")
        knowledge_data: Dict[str, Any] = {
            "entities": [],
            "relations": [],
            "insights": [],
            "tags": [],
            "sections": [],
        }

        current_section = None
        body_lines = []

        for line in lines:
            if line.startswith("# "):
                knowledge_data["title"] = line[2:].strip()
            elif line.startswith("**ID:**"):
                knowledge_data["id"] = line.split("`")[1] if "`" in line else ""
            elif line.startswith("**Source:**"):
                knowledge_data["source"] = line.split("**Source:**")[1].strip()
            elif line.startswith("**Created:**"):
                created_str = line.split("**Created:**")[1].strip()
                try:
                    knowledge_data["created_at"] = datetime.fromisoformat(created_str)
                except ValueError:
                    knowledge_data["created_at"] = datetime.now()
            elif line.startswith("**Confidence:**"):
                try:
                    knowledge_data["confidence"] = float(line.split(":")[1].strip())
                except (ValueError, IndexError):
                    knowledge_data["confidence"] = 0.7
            elif line.startswith("## "):
                current_section = line[3:].strip().lower()
            elif current_section == "summary":
                if line.strip() and not line.startswith("#"):
                    body_lines.append(line)
            elif current_section == "entities":
                if line.startswith("- **"):
                    parts = line[4:].split("**")
                    if len(parts) >= 2:
                        knowledge_data["entities"].append({
                            "name": parts[0].strip(),
                            "type": parts[1].strip(" ()") if len(parts) > 1 else "concept",
                            "description": "",
                            "aliases": [],
                        })
            elif current_section == "tags":
                if "`" in line:
                    tags_str = line.replace("`", "").strip()
                    if "," in tags_str:
                        knowledge_data["tags"].extend([t.strip() for t in tags_str.split(",")])

        knowledge_data["summary"] = "\n".join(body_lines).strip()

        knowledge_data["id"] = knowledge_data.get("id", hashlib.md5(content.encode()).hexdigest())
        knowledge_data["source"] = knowledge_data.get("source", str(filepath))

        return Knowledge(**knowledge_data)

    def list_all(self) -> List[Path]:
        """List all Markdown files."""
        return sorted(self.base_path.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
