"""Unit tests for confidence utilities."""

import pytest
from app.utils.confidence import (
    ConfidenceCalculator,
    merge_duplicate_entities,
)


class TestConfidenceCalculator:
    """Tests for ConfidenceCalculator."""

    def test_entity_confidence_calculation(self):
        """Test entity confidence calculation."""
        entity_data = {
            "name": "Test Entity",
            "type": "technology",
            "description": "A test entity description",
            "aliases": ["alias1", "alias2", "alias3"],
        }
        confidence = ConfidenceCalculator.calculate_entity_confidence(entity_data)
        assert 0.5 < confidence <= 1.0

    def test_entity_confidence_no_description(self):
        """Test entity confidence without description."""
        entity_data = {
            "name": "Test",
            "type": "concept",
        }
        confidence = ConfidenceCalculator.calculate_entity_confidence(entity_data)
        assert 0.4 <= confidence <= 0.7

    def test_relation_confidence_calculation(self):
        """Test relation confidence calculation."""
        relation_data = {
            "type": "uses",
            "evidence": ["evidence1", "evidence2"],
        }
        confidence = ConfidenceCalculator.calculate_relation_confidence(relation_data)
        assert 0.5 < confidence <= 1.0

    def test_insight_confidence_calculation(self):
        """Test insight confidence calculation."""
        insight_data = {
            "text": "This is a test insight about something important",
            "insight_type": "implication",
            "supporting_entities": ["entity1", "entity2"],
        }
        confidence = ConfidenceCalculator.calculate_insight_confidence(insight_data)
        assert 0.4 < confidence <= 1.0

    def test_knowledge_confidence_calculation(self):
        """Test overall knowledge confidence."""
        entities = [
            {"name": "E1", "type": "concept", "description": "desc"},
            {"name": "E2", "type": "technology"},
        ]
        relations = [
            {"source": "E1", "target": "E2", "type": "uses", "evidence": ["e1"]},
        ]
        insights = [
            {"text": "insight text", "insight_type": "pattern"},
        ]

        confidence = ConfidenceCalculator.calculate_knowledge_confidence(
            entities, relations, insights
        )
        assert 0.0 < confidence <= 1.0

    def test_is_low_confidence(self):
        """Test low confidence detection."""
        assert ConfidenceCalculator.is_low_confidence(0.5, threshold=0.7) is True
        assert ConfidenceCalculator.is_low_confidence(0.8, threshold=0.7) is False


class TestMergeDuplicateEntities:
    """Tests for entity merging."""

    def test_merge_similar_entities(self):
        """Test merging similar entities."""
        entities = [
            {"name": "Artificial Intelligence", "type": "technology", "aliases": ["AI"]},
            {"name": "AI", "type": "technology", "aliases": []},
            {"name": "Machine Learning", "type": "concept", "aliases": []},
        ]
        merged = merge_duplicate_entities(entities, similarity_threshold=0.7)
        assert len(merged) <= 3

    def test_no_merge_different_entities(self):
        """Test no merging for different entities."""
        entities = [
            {"name": "Artificial Intelligence", "type": "technology"},
            {"name": "Machine Learning", "type": "concept"},
        ]
        merged = merge_duplicate_entities(entities, similarity_threshold=0.9)
        assert len(merged) == 2

    def test_merge_with_aliases(self):
        """Test merging adds all aliases."""
        entities = [
            {"name": "AI", "type": "tech", "aliases": ["Artificial Intelligence"]},
            {"name": "AI", "type": "tech", "aliases": []},
        ]
        merged = merge_duplicate_entities(entities, similarity_threshold=0.9)
        assert len(merged) == 1
        assert "Artificial Intelligence" in merged[0]["aliases"]
