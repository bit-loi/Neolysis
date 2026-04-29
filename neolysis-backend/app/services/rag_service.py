"""
Neolysis — RAG Service (Qdrant + sentence-transformers)
========================================================
Manages the PubMed paper vector store for Retrieval-Augmented Generation.

Architecture:
    PubMed abstracts → all-MiniLM-L6-v2 embeddings → Qdrant "pubmed_ntd" collection

All heavy embedding work is offloaded to a thread pool via asyncio.to_thread
so the event loop is never blocked.

TODO (BioLLM): Replace all-MiniLM-L6-v2 with BioLinkBERT or PubMedBERT
               for domain-specific embedding quality improvements.
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional
from loguru import logger

from app.config import settings


# ---------------------------------------------------------------------------
# Lazy model/client loading — avoid heavy imports at startup if not configured
# ---------------------------------------------------------------------------

_encoder = None
_qdrant_client = None

COLLECTION_NAME = "pubmed_ntd"
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dim


def _get_encoder():
    """Lazy-load the sentence-transformer model (singleton)."""
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence-transformer: all-MiniLM-L6-v2")
    return _encoder


def _get_qdrant():
    """Lazy-load and return the Qdrant client (singleton)."""
    global _qdrant_client
    if _qdrant_client is None:
        from qdrant_client import QdrantClient
        _qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        logger.info(f"Connected to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    return _qdrant_client


def _ensure_collection() -> None:
    """Create Qdrant collection if it doesn't exist (sync, called in thread)."""
    from qdrant_client.models import Distance, VectorParams

    client = _get_qdrant()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        logger.info(f"Created Qdrant collection '{COLLECTION_NAME}'")


def _embed_text(text: str) -> List[float]:
    """Embed a single text string (sync, runs in thread pool)."""
    model = _get_encoder()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def _search_qdrant(query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
    """Perform similarity search in Qdrant (sync, runs in thread pool)."""
    client = _get_qdrant()
    results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )
    return [
        {
            "title": r.payload.get("title", ""),
            "abstract": r.payload.get("abstract", ""),
            "pmid": r.payload.get("pmid", ""),
            "score": round(r.score, 4),
        }
        for r in results
    ]


def _upsert_paper(title: str, abstract: str, pmid: str) -> None:
    """Embed and upsert a single paper to Qdrant (sync, runs in thread pool)."""
    from qdrant_client.models import PointStruct

    _ensure_collection()
    combined = f"{title}. {abstract}"
    vector = _embed_text(combined)
    point = PointStruct(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"pmid:{pmid}")),
        vector=vector,
        payload={"title": title, "abstract": abstract, "pmid": pmid},
    )
    _get_qdrant().upsert(collection_name=COLLECTION_NAME, points=[point])


def _batch_upsert(papers: List[Dict[str, str]]) -> int:
    """Batch embed and upsert papers (sync, runs in thread pool). Returns count."""
    from qdrant_client.models import PointStruct

    _ensure_collection()
    model = _get_encoder()
    texts = [f"{p['title']}. {p.get('abstract', '')}" for p in papers]
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)

    points = [
        PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"pmid:{p['pmid']}")),
            vector=vec.tolist(),
            payload={"title": p["title"], "abstract": p.get("abstract", ""), "pmid": p["pmid"]},
        )
        for p, vec in zip(papers, vectors)
    ]
    _get_qdrant().upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

class RAGService:
    """
    Async wrapper around the Qdrant vector store for PubMed literature retrieval.

    All I/O-bound ops are run via asyncio.to_thread to avoid blocking the event loop.
    """

    async def ensure_collection(self) -> None:
        """Create the Qdrant collection if it doesn't exist."""
        await asyncio.to_thread(_ensure_collection)

    async def search_relevant_papers(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Embed the query and retrieve the top_k most relevant PubMed papers.

        Args:
            query: Natural language query (e.g. compound + target name)
            top_k: Number of papers to return

        Returns:
            List of {title, abstract, pmid, score} dicts sorted by relevance.
        """
        if not query.strip():
            logger.warning("RAGService: Empty query provided")
            return []

        try:
            query_vector = await asyncio.to_thread(_embed_text, query)
            results = await asyncio.to_thread(_search_qdrant, query_vector, top_k)
            logger.info(f"RAG search returned {len(results)} papers for query: '{query[:60]}...'")
            return results
        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return []

    async def add_paper(self, title: str, abstract: str, pmid: str) -> bool:
        """
        Embed a single paper and upsert it to Qdrant.

        Returns True on success, False on failure.
        """
        try:
            await asyncio.to_thread(_upsert_paper, title, abstract, pmid)
            logger.info(f"Upserted paper PMID={pmid} to Qdrant")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert paper {pmid}: {e}")
            return False

    async def batch_add_papers(self, papers: List[Dict[str, str]]) -> int:
        """
        Batch-embed and upsert a list of papers.

        Args:
            papers: List of {title, abstract, pmid} dicts

        Returns:
            Number of papers successfully upserted.
        """
        if not papers:
            return 0
        try:
            count = await asyncio.to_thread(_batch_upsert, papers)
            logger.info(f"Batch upserted {count} papers to Qdrant")
            return count
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            return 0

    async def health_check(self) -> bool:
        """Check if Qdrant is reachable. Returns True if healthy."""
        try:
            client = await asyncio.to_thread(_get_qdrant)
            client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


rag_service = RAGService()
