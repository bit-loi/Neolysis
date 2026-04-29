"""
Neolysis — Knowledge Graph Router
===================================
Query and manage biomedical knowledge graph triples.

Endpoints:
    GET  /api/v1/knowledge-graph              — Query triples (subject, relation, object filters)
    POST /api/v1/knowledge-graph              — Add a new triple
    GET  /api/v1/knowledge-graph/relations    — List all distinct relation types

Design notes:
    - All three filter params (subject, relation, object) are optional but at least one required
    - Supports partial/substring matching on subject and object
    - Exact case-insensitive match on relation
    - Results ordered by confidence score descending

Example usage:
    GET /api/v1/knowledge-graph?subject=Dengue+NS5
    GET /api/v1/knowledge-graph?relation=inhibited_by
    GET /api/v1/knowledge-graph?subject=NS5&relation=inhibited_by
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct
from loguru import logger

from app.db.session import get_db
from app.models.knowledge_graph import KnowledgeGraph
from app.schemas.knowledge_graph import KnowledgeGraphOut, KnowledgeGraphCreate, KnowledgeGraphListResponse
from app.services.kg_service import kg_service

router = APIRouter()


@router.get(
    "/",
    response_model=KnowledgeGraphListResponse,
    summary="Query knowledge graph triples",
)
async def query_knowledge_graph(
    subject: Optional[str] = Query(None, max_length=255, description="Filter by subject (substring match)"),
    relation: Optional[str] = Query(None, max_length=100, description="Filter by relation type (e.g. 'inhibited_by')"),
    object: Optional[str] = Query(None, max_length=255, alias="object", description="Filter by object (substring match)"),
    limit: int = Query(50, le=200, description="Max results"),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeGraphListResponse:
    """
    Query the knowledge graph with flexible subject + relation + object filters.

    At least one filter parameter must be provided.

    Supports:
    - Subject-only:   `?subject=Dengue+NS5`
    - Relation-only:  `?relation=inhibited_by`
    - Hybrid:         `?subject=NS5&relation=inhibited_by`
    - Object filter:  `?object=Quercetin`
    """
    if not any([subject, relation, object]):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of: subject, relation, or object query parameters.",
        )

    triples = await kg_service.hybrid_query(
        db=db,
        subject=subject,
        relation=relation,
        object_filter=object,
        limit=limit,
    )

    logger.debug(f"KG query returned {len(triples)} triples (subject={subject}, relation={relation})")
    return KnowledgeGraphListResponse(total=len(triples), items=triples)


@router.get(
    "/relations",
    summary="List all distinct relation types in the knowledge graph",
)
async def list_relation_types(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Return all distinct relation types currently stored in the knowledge graph.

    Useful for building filter UIs and discovering available relationship categories.
    Example relation types: inhibited_by, targets, associated_with, causes, treats
    """
    result = await db.execute(
        select(distinct(KnowledgeGraph.relation)).order_by(KnowledgeGraph.relation)
    )
    relations = [row[0] for row in result.all()]
    return {"relations": relations, "total": len(relations)}


@router.post(
    "/",
    response_model=KnowledgeGraphOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new knowledge graph triple",
)
async def create_triple(
    triple_in: KnowledgeGraphCreate,
    db: AsyncSession = Depends(get_db),
) -> KnowledgeGraphOut:
    """
    Persist a new biomedical knowledge graph triple.

    Example:
        {
            "subject": "Dengue NS5",
            "relation": "inhibited_by",
            "object": "Quercetin",
            "source": "DrugBank",
            "confidence": 0.87
        }

    Use for manual curation or automated extraction pipelines.
    """
    return await kg_service.create_triple(db, triple_in)
