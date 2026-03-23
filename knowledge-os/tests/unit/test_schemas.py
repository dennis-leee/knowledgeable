"""Unit tests for schemas."""

import pytest
from datetime import datetime

from app.schemas import (
    Entity,
    EntityType,
    Insight,
    InsightType,
    Knowledge,
    Relation,
    RelationType,
    Skill,
)


class TestEntity:
    """Tests for Entity model."""

    def test_entity_creation(self):
        """Test basic entity creation."""
        entity = Entity(
            name="Test Entity",
            type=EntityType.CONCEPT,
            description="A test entity",
        )
        assert entity.name == "Test Entity"
        assert entity.type == "concept"
        assert entity.description == "A test entity"

    def test_entity_with_aliases(self):
        """Test entity with aliases."""
        entity = Entity(
            name="AI",
            type=EntityType.TECHNOLOGY,
            aliases=["Artificial Intelligence", "Machine Intelligence"],
        )
        assert len(entity.aliases) == 2

    def test_entity_defaults(self):
        """Test entity default values."""
        entity = Entity(name="Test", type=EntityType.CONCEPT)
        assert entity.description is None
        assert entity.aliases == []
        assert entity.confidence == 0.8


class TestRelation:
    """Tests for Relation model."""

    def test_relation_creation(self):
        """Test basic relation creation."""
        relation = Relation(
            source="Entity A",
            target="Entity B",
            type=RelationType.USES,
            confidence=0.9,
        )
        assert relation.source == "Entity A"
        assert relation.target == "Entity B"
        assert relation.type == "uses"

    def test_relation_with_evidence(self):
        """Test relation with evidence."""
        relation = Relation(
            source="A",
            target="B",
            type=RelationType.CAUSES,
            evidence=["A leads to B", "A enables B"],
        )
        assert len(relation.evidence) == 2


class TestInsight:
    """Tests for Insight model."""

    def test_insight_creation(self):
        """Test basic insight creation."""
        insight = Insight(
            text="This implies that X is true",
            insight_type=InsightType.IMPLICATION,
        )
        assert insight.insight_type == "implication"
        assert insight.confidence == 0.7


class TestKnowledge:
    """Tests for Knowledge model."""

    def test_knowledge_creation(self):
        """Test basic knowledge creation."""
        knowledge = Knowledge(
            id="test-123",
            title="Test Knowledge",
            summary="A test summary",
            source="test",
        )
        assert knowledge.id == "test-123"
        assert knowledge.title == "Test Knowledge"
        assert knowledge.confidence == 0.7

    def test_knowledge_to_dict(self):
        """Test knowledge serialization."""
        knowledge = Knowledge(
            id="test-456",
            title="Test",
            summary="Summary",
            source="source",
        )
        data = knowledge.to_dict()
        assert data["id"] == "test-456"
        assert isinstance(data["created_at"], str)

    def test_knowledge_from_dict(self):
        """Test knowledge deserialization."""
        data = {
            "id": "test-789",
            "title": "From Dict",
            "summary": "Summary",
            "source": "test",
            "entities": [],
            "relations": [],
            "insights": [],
            "tags": [],
        }
        knowledge = Knowledge.from_dict(data)
        assert knowledge.id == "test-789"


class TestSkill:
    """Tests for Skill model."""

    def test_skill_creation(self):
        """Test basic skill creation."""
        skill = Skill(
            name="test-skill",
            description="A test skill",
        )
        assert skill.name == "test-skill"
        assert skill.version == "1.0.0"

    def test_skill_to_markdown(self):
        """Test skill markdown generation."""
        skill = Skill(
            name="knowledge-test",
            description="Test knowledge skill",
            actions=[
                {"step": 1, "description": "Test step", "instruction": "Do test"}
            ],
        )
        md = skill.to_markdown()
        assert "---" in md
        assert "knowledge-test" in md
        assert "Test step" in md
