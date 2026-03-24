"""Ingestion agent - fetch content from URLs."""

import re
from typing import Any, Dict, Optional, Set
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.agents.base import BaseAgent
from app.orchestrator.state import PipelineState
from app.utils.retry import async_retry


WECHAT_NOISE_PATTERNS = [
    r"^https?://", r"^www\.", r"^[\d.]+$",
    r"^doup智能AI", r"^AI$", r"^doup",
    r"^原创$", r"^懂AI", r"^开源AI项目落地",
    r"^在小说阅读器中沉浸阅读",
    r"^视频$", r"^小程序$", r"^赞$", r"^在看$", r"^分享$", r"^留言$", r"^收藏$",
    r"^微信扫一扫.*$", r"^取消$", r"^允许$",
    r"^继续滑动看下一个$", r"^向上滑动看下一个$", r"^轻触阅读原文$",
    r"^知道了$", r"^预览时标签不可点$",
    r"^获得更多技术支持和交流$", r"^与AI时代更靠近一点$",
    r"^扫码加入AI交流群", r"^请注明自己的职业",
    r"^关注.*公众号", r"^微信.*公众号",
    r"^使用完整服务",
    r"^分析$", r"^使用小程序",
    r"^轻点两下取消赞", r"^轻点两下取消在看",
]

WECHAT_NOISE_KEYWORDS: Set[str] = {
    "javascript:", "onclick", "onerror", "onload",
    "data-src", "original-src", "placeholder",
    "lazyload", "data-url",
    "mp-qrcode", "qrcode", "qr_code",
    "appmsg", "weapp", "miniprogram",
    "js_content", "js_name", "js_appid",
}

MIN_CONTENT_LENGTH = 500
MAX_LINE_LENGTH = 500


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

        text = None
        errors = []

        primary_methods = [
            ("httpx", self._fetch_url),
        ]

        fallback_parsers = self.config.get("fallback_parsers", ["jina-reader", "playwright", "readability-lxml"])

        for method_name, fetch_func in primary_methods:
            try:
                text = await fetch_func(url)
                if self._validate_content_quality(text):
                    break
                errors.append(f"{method_name}: content quality too low")
            except Exception as e:
                errors.append(f"{method_name}: {str(e)}")

        if not text or not self._validate_content_quality(text):
            for parser in fallback_parsers:
                try:
                    if parser == "jina-reader":
                        text = await self._fetch_with_jina(url)
                    elif parser == "playwright":
                        text = await self._fetch_with_playwright(url)
                    elif parser == "readability-lxml":
                        from readability import Document
                        import httpx
                        headers = {"User-Agent": "Mozilla/5.0 (compatible; KnowledgeBot/1.0)"}
                        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                            response = await client.get(url, headers=headers)
                            response.raise_for_status()
                            doc = Document(response.text)
                            text = doc.summary()
                    if text and self._validate_content_quality(text):
                        break
                except Exception as e:
                    errors.append(f"{parser}: {str(e)}")

        if text and self._validate_content_quality(text):
            state["raw_text"] = text[: self.max_content_size]
            state["title"] = self._extract_title(text) or url
        else:
            state["error"] = f"Failed to extract quality content. Errors: {'; '.join(errors)}"
            state["raw_text"] = self._get_mock_content(url)
            state["title"] = url

        return state

    def _validate_content_quality(self, text: str) -> bool:
        """Validate if extracted content meets quality thresholds."""
        if not text or len(text) < MIN_CONTENT_LENGTH:
            return False

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if len(lines) < 5:
            return False

        avg_line_length = sum(len(l) for l in lines) / len(lines) if lines else 0
        if avg_line_length < 10:
            return False

        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)
        if total_chars > 0:
            chinese_ratio = chinese_chars / total_chars
            if chinese_ratio < 0.1 and chinese_chars < 100:
                return False

        return True

    async def _fetch_with_jina(self, url: str) -> str:
        """Fetch content using Jina Reader API."""
        import httpx
        jina_url = f"https://r.jina.ai/{url}"
        headers = {
            "Accept": "text/plain",
            "User-Agent": "KnowledgeBot/1.0",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(jina_url, headers=headers)
            response.raise_for_status()
            return response.text

    async def _fetch_with_playwright(self, url: str) -> str:
        """Fetch content using Playwright with stealth mode for WeChat articles."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("playwright not installed")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="network_idle", timeout=self.timeout * 1000)

                await page.wait_for_timeout(3000)

                content = await page.content()

                await browser.close()
                return self._extract_main_content(content)

            except Exception as e:
                await browser.close()
                raise

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

        wechat_content = soup.find("section", {"id": "js_content"})
        if wechat_content:
            text = wechat_content.get_text(separator="\n", strip=True)
        else:
            main_content = soup.find("main") or soup.find("article") or soup.find("body")
            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        text = text.strip()

        text = self._clean_text(text, is_wechat=wechat_content is not None)

        if len(text) < MIN_CONTENT_LENGTH:
            text = self._extract_by_readability(soup)
            text = self._clean_text(text, is_wechat=False)

        return text

    def _clean_text(self, text: str, is_wechat: bool = False) -> str:
        """Clean extracted text by removing noise patterns."""
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if len(line) > MAX_LINE_LENGTH:
                continue

            line_lower = line.lower()
            if any(kw in line_lower for kw in WECHAT_NOISE_KEYWORDS):
                continue

            is_noise = False
            for pattern in WECHAT_NOISE_PATTERNS:
                if re.match(pattern, line, re.IGNORECASE):
                    is_noise = True
                    break

            if is_noise:
                continue

            if len(line) < 3:
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _extract_by_readability(self, soup: BeautifulSoup) -> str:
        """Fallback extraction using readability-like algorithm."""
        from bs4 import Comment

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        candidates = []
        for tag in soup.find_all(["div", "section", "article"]):
            text = tag.get_text(strip=True)
            score = len(text)
            for cls in ["content", "article", "post", "entry", "main", "text"]:
                if cls in (tag.get("class") or []) or cls in (tag.get("id") or "").lower():
                    score *= 2
            candidates.append((score, tag))

        if candidates:
            best = max(candidates, key=lambda x: x[0])[1]
            return best.get_text(separator="\n", strip=True)

        return soup.get_text(separator="\n", strip=True)

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title from text."""
        lines = text.split("\n")
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 5 and len(line) < 200 and not line.startswith(("微信", "赞", "在看", "分享", "收藏", "评论")):
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
