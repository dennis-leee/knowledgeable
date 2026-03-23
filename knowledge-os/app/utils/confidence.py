"""Confidence scoring utilities."""

from typing import Any, Dict, List, Optional


class ConfidenceCalculator:
    """Calculate confidence scores for extracted knowledge."""

    @staticmethod
    def calculate_entity_confidence(entity_data: Dict[str, Any]) -> float:
        """Calculate confidence for an entity based on available data."""
        confidence = 0.5

        if entity_data.get("description"):
            confidence += 0.2

        if entity_data.get("type"):
            confidence += 0.15

        aliases = entity_data.get("aliases", [])
        if aliases and len(aliases) >= 2:
            confidence += 0.1

        return min(confidence, 1.0)

    @staticmethod
    def calculate_relation_confidence(relation_data: Dict[str, Any]) -> float:
        """Calculate confidence for a relation based on evidence."""
        confidence = 0.5

        evidence = relation_data.get("evidence", [])
        if evidence:
            confidence += min(len(evidence) * 0.1, 0.3)

        if relation_data.get("type"):
            confidence += 0.15

        return min(confidence, 1.0)

    @staticmethod
    def calculate_insight_confidence(insight_data: Dict[str, Any]) -> float:
        """Calculate confidence for an insight."""
        confidence = 0.4

        supporting_entities = insight_data.get("supporting_entities", [])
        if supporting_entities:
            confidence += min(len(supporting_entities) * 0.1, 0.3)

        if insight_data.get("insight_type"):
            confidence += 0.15

        if insight_data.get("text"):
            text_length = len(insight_data["text"])
            if text_length > 50:
                confidence += 0.1

        return min(confidence, 1.0)

    @staticmethod
    def calculate_knowledge_confidence(
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]],
        insights: List[Dict[str, Any]],
    ) -> float:
        """Calculate overall confidence for a knowledge entry."""
        if not entities and not relations and not insights:
            return 0.0

        total_confidence = 0.0
        count = 0

        for entity in entities:
            total_confidence += ConfidenceCalculator.calculate_entity_confidence(entity)
            count += 1

        for relation in relations:
            total_confidence += ConfidenceCalculator.calculate_relation_confidence(relation)
            count += 1

        for insight in insights:
            total_confidence += ConfidenceCalculator.calculate_insight_confidence(insight)
            count += 1

        return total_confidence / count if count > 0 else 0.0

    @staticmethod
    def is_low_confidence(
        confidence: float,
        threshold: float = 0.7,
    ) -> bool:
        """Check if confidence is below threshold."""
        return confidence < threshold


def merge_duplicate_entities(
    entities: List[Dict[str, Any]],
    similarity_threshold: float = 0.9,
) -> List[Dict[str, Any]]:
    """Merge duplicate entities based on name similarity."""
    from difflib import SequenceMatcher

    def similarity(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    merged: List[Dict[str, Any]] = []
    used_indices: set = set()

    for i, entity in enumerate(entities):
        if i in used_indices:
            continue

        similar_entities = [entity]
        used_indices.add(i)

        for j, other in enumerate(entities):
            if j in used_indices:
                continue

            if similarity(entity.get("name", ""), other.get("name", "")) >= similarity_threshold:
                similar_entities.append(other)
                used_indices.add(j)

        if len(similar_entities) == 1:
            merged.append(entity)
        else:
            merged_entity = similar_entities[0].copy()
            all_aliases = set()
            for se in similar_entities:
                all_aliases.update(se.get("aliases", []))
                all_aliases.add(se.get("name", ""))
            merged_entity["aliases"] = list(all_aliases)
            merged_entity["name"] = similar_entities[0].get("name", "")
            merged.append(merged_entity)

    return merged
