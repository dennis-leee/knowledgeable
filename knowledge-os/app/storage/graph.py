"""JSON Graph storage adapter."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas import Knowledge


class GraphStorage:
    """Storage adapter for JSON Graph files."""

    def __init__(self, base_path: str = "./data/graph"):
        """Initialize JSON Graph storage."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.graph_file = self.base_path / "knowledge_graph.json"
        self._ensure_graph_file()

    def _ensure_graph_file(self) -> None:
        """Ensure graph file exists with proper structure."""
        if not self.graph_file.exists():
            self._save_graph({"nodes": [], "edges": [], "metadata": {}})

    def _load_graph(self) -> Dict[str, Any]:
        """Load graph from file."""
        with open(self.graph_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_graph(self, graph: Dict[str, Any]) -> None:
        """Save graph to file."""
        with open(self.graph_file, "w", encoding="utf-8") as f:
            json.dump(graph, f, indent=2, ensure_ascii=False, default=str)

    def add_knowledge(self, knowledge: Knowledge) -> None:
        """Add knowledge entry to graph."""
        graph = self._load_graph()

        knowledge_id = knowledge.id or str(uuid.uuid4())

        node = {
            "id": knowledge_id,
            "type": "knowledge",
            "label": knowledge.title,
            "data": {
                "summary": knowledge.summary,
                "source": knowledge.source,
                "source_url": knowledge.source_url,
                "confidence": knowledge.confidence,
                "tags": knowledge.tags,
                "created_at": knowledge.created_at.isoformat(),
            },
        }

        if not any(n["id"] == knowledge_id for n in graph["nodes"]):
            graph["nodes"].append(node)

        entity_names = set()
        for entity in knowledge.entities:
            entity_id = f"entity:{entity.name}"
            if entity.name not in entity_names:
                entity_names.add(entity.name)
                entity_node = {
                    "id": entity_id,
                    "type": "entity",
                    "label": entity.name,
                    "data": {
                        "entity_type": entity.type,
                        "description": entity.description,
                        "aliases": entity.aliases,
                        "confidence": entity.confidence,
                    },
                }
                if not any(n["id"] == entity_id for n in graph["nodes"]):
                    graph["nodes"].append(entity_node)

                edge = {
                    "id": f"edge:{knowledge_id}:{entity_id}",
                    "source": knowledge_id,
                    "target": entity_id,
                    "type": "contains",
                }
                if not any(e["id"] == edge["id"] for e in graph["edges"]):
                    graph["edges"].append(edge)

        for relation in knowledge.relations:
            source_id = f"entity:{relation.source}"
            target_id = f"entity:{relation.target}"

            edge = {
                "id": f"edge:{source_id}:{target_id}",
                "source": source_id,
                "target": target_id,
                "type": relation.type,
                "data": {
                    "confidence": relation.confidence,
                    "evidence": relation.evidence,
                },
            }

            if not any(e["id"] == edge["id"] for e in graph["edges"]):
                graph["edges"].append(edge)

        graph["metadata"]["updated_at"] = datetime.now().isoformat()
        graph["metadata"]["node_count"] = len(graph["nodes"])
        graph["metadata"]["edge_count"] = len(graph["edges"])

        self._save_graph(graph)

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node by ID."""
        graph = self._load_graph()
        for node in graph["nodes"]:
            if node["id"] == node_id:
                return node
        return None

    def get_neighbors(self, node_id: str, depth: int = 1) -> List[Dict[str, Any]]:
        """Get neighboring nodes."""
        graph = self._load_graph()
        neighbors = []
        visited = {node_id}
        current_level = {node_id}

        for _ in range(depth):
            next_level = set()
            for edge in graph["edges"]:
                if edge["source"] in current_level and edge["target"] not in visited:
                    neighbors.append(self.get_node(edge["target"]))
                    next_level.add(edge["target"])
                    visited.add(edge["target"])
                elif edge["target"] in current_level and edge["source"] not in visited:
                    neighbors.append(self.get_node(edge["source"]))
                    next_level.add(edge["source"])
                    visited.add(edge["source"])
            current_level = next_level

        return [n for n in neighbors if n is not None]

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search nodes by label."""
        graph = self._load_graph()
        query_lower = query.lower()
        results = []

        for node in graph["nodes"]:
            if query_lower in node.get("label", "").lower():
                results.append(node)
            elif query_lower in str(node.get("data", {})).lower():
                results.append(node)

            if len(results) >= limit:
                break

        return results

    def export(self) -> Dict[str, Any]:
        """Export entire graph."""
        return self._load_graph()

    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics."""
        graph = self._load_graph()
        return {
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "node_types": self._count_by_type(graph["nodes"]),
            "edge_types": self._count_by_type(graph["edges"], key="type"),
            "updated_at": graph["metadata"].get("updated_at"),
        }

    def _count_by_type(self, items: List[Dict[str, Any]], key: str = "type") -> Dict[str, int]:
        """Count items by type."""
        counts: Dict[str, int] = {}
        for item in items:
            item_type = item.get(key, "unknown")
            counts[item_type] = counts.get(item_type, 0) + 1
        return counts
