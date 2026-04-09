"""
SimLab RAG — Simulation Design Knowledge Base

Retrieves grounded knowledge for simulation spec design:
- Agent-based modeling theory and calibration
- Social simulation dynamics (opinion, cascade, echo chamber)
- Platform behavior benchmarks (action ratios, engagement patterns)
- Domain-specific patterns (corporate, market, geopolitical)
"""
import json
import uuid
import requests
from typing import List, Dict, Any, Optional

QDRANT_URL = "http://localhost:6333"
OLLAMA_URL = "http://localhost:11434"
COLLECTION = "rag-simlab"
EMBED_MODEL = "nomic-embed-text-v2-moe"
VECTOR_DIM = 768


class SimLabRAG:
    def __init__(self, qdrant_url: str = QDRANT_URL, ollama_url: str = OLLAMA_URL):
        self.qdrant_url = qdrant_url
        self.ollama_url = ollama_url
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        r = requests.get(f"{self.qdrant_url}/collections/{COLLECTION}")
        if r.status_code == 404:
            requests.put(f"{self.qdrant_url}/collections/{COLLECTION}", json={
                "vectors": {"size": VECTOR_DIM, "distance": "Cosine"}
            })

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Embed texts via Ollama"""
        r = requests.post(f"{self.ollama_url}/api/embed", json={
            "model": EMBED_MODEL,
            "input": texts
        })
        r.raise_for_status()
        return r.json()["embeddings"]

    def search(self, query: str, limit: int = 10, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """Search the SimLab collection"""
        vectors = self._embed([query])
        r = requests.post(f"{self.qdrant_url}/collections/{COLLECTION}/points/search", json={
            "vector": vectors[0],
            "limit": limit,
            "with_payload": True,
            "score_threshold": min_score,
        })
        r.raise_for_status()
        results = r.json().get("result", [])
        return [{"text": p["payload"]["text"], "category": p["payload"].get("category", ""), "source": p["payload"].get("source", ""), "score": p["score"]} for p in results]

    def retrieve_for_spec(self, domain: str, description: str = "", archetypes: List[str] = None) -> Dict[str, List[str]]:
        """
        Retrieve simulation design knowledge relevant to a spec.
        Returns categorized recommendations.
        """
        queries = [
            f"agent-based simulation {domain} calibration parameters",
            f"social simulation {domain} agent archetypes behavior",
        ]
        if description:
            queries.append(f"simulation design {description[:200]}")
        if archetypes:
            queries.append(f"agent roles {' '.join(archetypes)} interaction dynamics")

        # Deduplicate results across queries
        seen_texts = set()
        categorized = {}

        for q in queries:
            results = self.search(q, limit=5)
            for r in results:
                if r["text"] not in seen_texts:
                    seen_texts.add(r["text"])
                    cat = r.get("category", "general")
                    if cat not in categorized:
                        categorized[cat] = []
                    categorized[cat].append(r["text"])

        return categorized

    def upsert_chunks(self, chunks: List[Dict[str, str]]) -> int:
        """
        Upsert text chunks into the collection.
        Each chunk: {"text": str, "category": str, "source": str}
        """
        if not chunks:
            return 0

        batch_size = 50
        total = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c["text"] for c in batch]
            vectors = self._embed(texts)

            points = []
            for j, (chunk, vector) in enumerate(zip(batch, vectors)):
                points.append({
                    "id": str(uuid.uuid4()),
                    "vector": vector,
                    "payload": {
                        "text": chunk["text"],
                        "category": chunk.get("category", "general"),
                        "source": chunk.get("source", "unknown"),
                    }
                })

            r = requests.put(
                f"{self.qdrant_url}/collections/{COLLECTION}/points",
                json={"points": points}
            )
            r.raise_for_status()
            total += len(points)

        return total
