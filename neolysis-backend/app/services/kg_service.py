"""
Neolysis — Knowledge Graph Query Service
==========================================
Queries the KnowledgeGraph table (PostgreSQL via Supabase) for biomedical triples.

Supports three query modes:
    1. Subject-based  : get all triples where subject matches
    2. Relation-based : get all triples of a given relation type
    3. Hybrid         : subject + relation filter combined

TODO (GNN): Replace SQL triple lookup with a Graph Neural Network (e.g. TransE/RotatE)
            for link prediction and entity embedding similarity search.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from loguru import logger

from app.models.knowledge_graph import KnowledgeGraph
from app.schemas.knowledge_graph import KnowledgeGraphOut, KnowledgeGraphCreate


class KGService:
    """
    Service layer for querying and mutating the KnowledgeGraph table.

    All methods are async and accept an `AsyncSession` as injected dependency.
    """

    async def get_relations(
        self,
        db: AsyncSession,
        subject: str,
        limit: int = 50,
    ) -> List[KnowledgeGraphOut]:
        """
        Retrieve all triples where the subject matches (case-insensitive substring).

        Args:
            db:      AsyncSession from dependency injection
            subject: Entity name to search for (e.g. "Dengue NS5")
            limit:   Maximum number of triples to return

        Returns:
            List of KnowledgeGraphOut sorted by confidence desc
        """
        query = (
            select(KnowledgeGraph)
            .where(KnowledgeGraph.subject.ilike(f"%{subject}%"))
            .order_by(KnowledgeGraph.confidence.desc().nullslast())
            .limit(limit)
        )
        result = await db.execute(query)
        rows = result.scalars().all()
        logger.debug(f"KG subject query '{subject}' → {len(rows)} triples")
        return [KnowledgeGraphOut.model_validate(r) for r in rows]

    async def get_by_relation(
        self,
        db: AsyncSession,
        relation: str,
        limit: int = 50,
    ) -> List[KnowledgeGraphOut]:
        """
        Retrieve all triples of a given relation type (exact match, case-insensitive).

        Args:
            db:       AsyncSession
            relation: Relation type (e.g. "inhibited_by", "targets", "associated_with")
            limit:    Maximum results

        Returns:
            List of triples sorted by confidence desc
        """
        query = (
            select(KnowledgeGraph)
            .where(KnowledgeGraph.relation.ilike(relation))
            .order_by(KnowledgeGraph.confidence.desc().nullslast())
            .limit(limit)
        )
        result = await db.execute(query)
        rows = result.scalars().all()
        logger.debug(f"KG relation query '{relation}' → {len(rows)} triples")
        return [KnowledgeGraphOut.model_validate(r) for r in rows]

    async def hybrid_query(
        self,
        db: AsyncSession,
        subject: Optional[str] = None,
        relation: Optional[str] = None,
        object_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[KnowledgeGraphOut]:
        """
        Flexible hybrid query supporting subject + relation + object filters.

        Any combination of the three filters can be applied.
        At least one filter must be provided (caller must validate).

        Args:
            db:            AsyncSession
            subject:       Optional subject filter (substring)
            relation:      Optional relation filter (exact)
            object_filter: Optional object filter (substring)
            limit:         Maximum results

        Returns:
            Filtered and confidence-ranked triples
        """
        query = select(KnowledgeGraph)

        if subject:
            query = query.where(KnowledgeGraph.subject.ilike(f"%{subject}%"))
        if relation:
            query = query.where(KnowledgeGraph.relation.ilike(relation))
        if object_filter:
            query = query.where(KnowledgeGraph.object.ilike(f"%{object_filter}%"))

        query = (
            query
            .order_by(KnowledgeGraph.confidence.desc().nullslast())
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.scalars().all()
        logger.debug(f"KG hybrid query → {len(rows)} triples")
        return [KnowledgeGraphOut.model_validate(r) for r in rows]

    async def create_triple(
        self,
        db: AsyncSession,
        triple_in: KnowledgeGraphCreate,
    ) -> KnowledgeGraphOut:
        """
        Persist a new knowledge graph triple.

        Args:
            db:        AsyncSession
            triple_in: Validated triple data

        Returns:
            Persisted triple as KnowledgeGraphOut
        """
        triple = KnowledgeGraph(**triple_in.model_dump())
        db.add(triple)
        await db.commit()
        await db.refresh(triple)
        logger.info(f"KG triple created: {triple.subject} → {triple.relation} → {triple.object}")
        return KnowledgeGraphOut.model_validate(triple)

    async def get_context_for_prompt(
        self,
        db: AsyncSession,
        subject: str,
        max_triples: int = 10,
    ) -> str:
        """
        Build a human-readable knowledge graph context string for LLM prompts.

        Args:
            db:          AsyncSession
            subject:     Entity to center the context on
            max_triples: Maximum triples to include

        Returns:
            Formatted string of triples for LLM injection
        """
        triples = await self.get_relations(db, subject, limit=max_triples)
        if not triples:
            return f"No knowledge graph data found for '{subject}'."

        lines = [f"Knowledge Graph Context for '{subject}':"]
        for t in triples:
            conf_str = f" (confidence: {t.confidence:.2f})" if t.confidence else ""
            lines.append(f"  • {t.subject} → {t.relation} → {t.object} [{t.source}]{conf_str}")

        return "\n".join(lines)


kg_service = KGService()
