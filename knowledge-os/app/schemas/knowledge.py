"""Knowledge schema - Pydantic models for knowledge representation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Entity types for knowledge graph nodes."""

    CONCEPT = "concept"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    TECHNOLOGY = "technology"
    TOOL = "tool"
    METHOD = "method"
    EVENT = "event"
    CLAIM = "claim"


class RelationType(str, Enum):
    """Relation types for knowledge graph edges."""

    USES = "uses"
    ENHANCES = "enhances"
    DEPENDS_ON = "depends_on"
    CONTRASTS = "contrasts"
    IMPLIES = "implies"
    PART_OF = "part_of"
    SIMILAR_TO = "similar_to"
    CAUSES = "causes"
    HAPPENS_BEFORE = "happens_before"


class InsightType(str, Enum):
    """Insight types for extracted insights."""

    IMPLICATION = "implication"
    PREDICTION = "prediction"
    COMPARISON = "comparison"
    PATTERN = "pattern"
    CORRELATION = "correlation"


class Entity(BaseModel):
    """Entity extracted from content."""

    name: str
    type: EntityType
    description: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)

    model_config = {
        "use_enum_values": True,
    }


class Relation(BaseModel):
    """Relation between entities."""

    source: str
    target: str
    type: RelationType
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    evidence: List[str] = Field(default_factory=list)

    model_config = {
        "use_enum_values": True,
    }


class Insight(BaseModel):
    """Insight extracted from content."""

    text: str
    insight_type: InsightType
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    supporting_entities: List[str] = Field(default_factory=list)

    model_config = {
        "use_enum_values": True,
    }


class Knowledge(BaseModel):
    """Complete knowledge representation."""

    id: str
    title: str
    summary: str
    sections: List[str] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
    insights: List[Insight] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source: str
    source_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    canonical_entities: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Knowledge":
        """Create from dictionary."""
        return cls.model_validate(data)


class KnowledgeGraphData(BaseModel):
    """Knowledge graph structure for JSON storage."""

    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
