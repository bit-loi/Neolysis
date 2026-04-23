from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.db.session import get_db
from app.models.paper import Paper
from app.schemas.paper import PaperCreate, PaperOut

router = APIRouter()


@router.get("/", response_model=List[PaperOut])
async def list_papers(
    target_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all research papers. Optionally filter by target_id.
    Per spec: papers table (RAG layer).
    """
    query = select(Paper)
    if target_id is not None:
        query = query.where(Paper.target_id == target_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PaperOut, status_code=status.HTTP_201_CREATED)
async def create_paper(paper_in: PaperCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a research paper entry (admin / seed use-case).
    """
    paper = Paper(**paper_in.model_dump())
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return paper
