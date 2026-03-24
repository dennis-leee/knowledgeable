"""Pipeline state for LangGraph orchestration."""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class PipelineState(TypedDict, total=False):
    """State passed through the pipeline."""

    url: str
    raw_text: str
    title: str
    summary: str
    sections: List[str]
    entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    insights: List[Dict[str, Any]]
    knowledge: Optional[Dict[str, Any]]
    validated: bool
    validation_errors: List[str]
    retry_count: int
    error: Optional[str]
    approved: bool
    approved_by: Optional[str]
    pending_review: bool
    review_notes: Optional[str]
    stored: bool
    markdown_path: Optional[str]
    skill_path: Optional[str]
    key_points: List[Dict[str, Any]]
    important_details: List[str]
    takeaways: List[str]
