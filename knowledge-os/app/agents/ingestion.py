"""Ingestion agent - fetch content from URLs."""

import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.utils.retry import async_retry


class IngestionAgent(BaseAgent):
    """Agent for fetching and parsing content from URLs."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize ingestion agent."""
        super().__init__(config)
        self.timeout = self.config.get("timeout", 30)
        self.max_content_size = self.config.get("max_content_size", 1048576)

    async def run(self, state: PipelineState) -> PipelineState:
        """Fetch content from URL."""
        url = state.get("url")
        if not url:
            state["error"] = "No URL provided"
            return state

        try:
            text = await self._fetch_url(url)
            title = self._extract_title(text) or url
            state["raw_text"] = text[: self.max_content_size]
            state["title"] = title
        except Exception as e:
            state["error"] = self._get_error_message(e)
            state["raw_text"] = self._get_mock_content(url)

        return state

    @async_retry(max_attempts=3, delay=1.0)
    async def _fetch_url(self, url: str) -> str:
        """Fetch URL content with retry."""
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"
        try:
            import httpx

            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; KnowledgeBot/1.0)",
                "Accept": "text/html,application/xhtml+xml",
            }

            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return self._extract_main_content(response.text)
        except ImportError:
            return self._get_mock_content(url)

    def _extract_main_content(self, html: str) -> str:
        """Extract main content from HTML."""
        soup = BeautifulSoup(html, "lxml")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        main_content = soup.find("main") or soup.find("article") or soup.find("body")

        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()

        return text

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from text."""
        lines = text.split("\n")
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 5 and len(line) < 200:
                return line
        return None

    def _get_mock_content(self, url: str) -> str:
        """Get mock content for testing without network."""
        return f"""
Knowledge Graph Auto-Growth System

This is a sample document about building AI-powered knowledge management systems.

Key Topics:
1. Knowledge Extraction - Automatically extract entities and relationships from content
2. Graph Construction - Build knowledge graphs from extracted information
3. MCP Integration - Export knowledge as MCP-compatible skills

Main Components:
- Ingestion Agent: Fetch content from URLs
- Summarizer Agent: Generate concise summaries
- Entity Agent: Extract named entities
- Relation Agent: Identify relationships between entities
- Insight Agent: Discover non-obvious insights
- Validation Agent: Ensure data quality
- Repair Agent: Fix malformed data
- Memory Agent: Store knowledge persistently
- Skills Agent: Generate AI-consumable skills

Technology Stack:
- LangGraph for orchestration
- Pydantic for data validation
- ChromaDB for vector storage
- JSON files for graph storage

This system enables autonomous knowledge acquisition and organization.
"""
