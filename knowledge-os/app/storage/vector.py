"""Vector storage adapter using ChromaDB."""

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.schemas import Knowledge


class VectorStorage:
    """Vector storage adapter using ChromaDB for embeddings."""

    def __init__(self, persist_path: str = "./data/vectors"):
        """Initialize vector storage."""
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._client = None
        self._collection = None

    def _get_client(self):
        """Get or create ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                self._client = chromadb.PersistentClient(
                    path=str(self.persist_path),
                    settings=Settings(anonymized_telemetry=False),
                )
            except ImportError:
                return None
        return self._client

    def _get_collection(self):
        """Get or create collection."""
        if self._collection is None:
            client = self._get_client()
            if client is None:
                return None
            try:
                self._collection = client.get_or_create_collection(
                    name="knowledge_embeddings",
                    metadata={"description": "Knowledge graph embeddings"},
                )
            except Exception:
                return None
        return self._collection

    def add_knowledge(self, knowledge: Knowledge) -> None:
        """Add knowledge embeddings."""
        collection = self._get_collection()
        if collection is None:
            return

        knowledge_id = knowledge.id or str(uuid.uuid4())

        texts_to_add = []
        ids_to_add = []
        metadatas_to_add = []

        summary_text = f"{knowledge.title}. {knowledge.summary}"
        texts_to_add.append(summary_text)
        ids_to_add.append(f"{knowledge_id}:summary")
        metadatas_to_add.append({
            "knowledge_id": knowledge_id,
            "type": "summary",
            "source": knowledge.source,
        })

        for i, insight in enumerate(knowledge.insights):
            texts_to_add.append(f"Insight: {insight.text}")
            ids_to_add.append(f"{knowledge_id}:insight:{i}")
            metadatas_to_add.append({
                "knowledge_id": knowledge_id,
                "type": "insight",
                "insight_type": insight.insight_type,
            })

        if texts_to_add:
            try:
                collection.add(
                    documents=texts_to_add,
                    ids=ids_to_add,
                    metadatas=metadatas_to_add,
                )
            except Exception:
                pass

    def search(
        self,
        query: str,
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar knowledge."""
        collection = self._get_collection()
        if collection is None:
            return []

        try:
            results = collection.query(
                query_texts=[query],
                n_results=limit,
                where=filter_metadata,
            )

            search_results = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"]):
                    if results.get("metadatas") and i < len(results["metadatas"]):
                        search_results.append({
                            "text": doc,
                            "metadata": results["metadatas"][i],
                            "distance": results.get("distances", [[]])[0][i] if results.get("distances") else 0.0,
                        })

            return search_results

        except Exception:
            return []

    def delete_knowledge(self, knowledge_id: str) -> None:
        """Delete knowledge embeddings."""
        collection = self._get_collection()
        if collection is None:
            return

        try:
            collection.delete(where={"knowledge_id": knowledge_id})
        except Exception:
            pass

    def get_count(self) -> int:
        """Get total number of embeddings."""
        collection = self._get_collection()
        if collection is None:
            return 0

        try:
            return collection.count()
        except Exception:
            return 0


class MockVectorStorage:
    """Mock vector storage for testing without ChromaDB."""

    def __init__(self, persist_path: str = "./data/vectors"):
        """Initialize mock vector storage."""
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._embeddings: Dict[str, Dict[str, Any]] = {}

    def add_knowledge(self, knowledge: Knowledge) -> None:
        """Add knowledge (mock)."""
        knowledge_id = knowledge.id or str(uuid.uuid4())
        self._embeddings[knowledge_id] = {
            "knowledge_id": knowledge_id,
            "title": knowledge.title,
            "summary": knowledge.summary,
            "source": knowledge.source,
        }

    def search(
        self,
        query: str,
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search (mock - simple text match)."""
        query_lower = query.lower()
        results = []

        for emb in self._embeddings.values():
            text = f"{emb.get('title', '')} {emb.get('summary', '')}".lower()
            if query_lower in text:
                results.append({
                    "text": emb.get("summary", ""),
                    "metadata": {"knowledge_id": emb["knowledge_id"], "source": emb.get("source", "")},
                    "distance": 0.0,
                })

            if len(results) >= limit:
                break

        return results

    def delete_knowledge(self, knowledge_id: str) -> None:
        """Delete knowledge (mock)."""
        self._embeddings.pop(knowledge_id, None)

    def get_count(self) -> int:
        """Get count (mock)."""
        return len(self._embeddings)


def get_vector_storage(persist_path: str = "./data/vectors") -> VectorStorage:
    """Get vector storage instance."""
    try:
        import chromadb
        return VectorStorage(persist_path=persist_path)
    except ImportError:
        return MockVectorStorage(persist_path=persist_path)
