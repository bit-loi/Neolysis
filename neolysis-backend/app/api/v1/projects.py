from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.db.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectOut
from app.models.user import User
from app.core.rate_limit import limiter

router = APIRouter()

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_project(
    request: Request,
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new saved project for the authenticated user.
    """
    repo = ProjectRepository(db)
    project = await repo.create(current_user.id, project_in)
    return project

@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all projects owned by the authenticated user.
    Enforces IDOR by strictly isolating queries to the user's ID.
    """
    repo = ProjectRepository(db)
    return await repo.get_by_user(current_user.id)

@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific project. Enforces IDOR by checking ownership.
    """
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # IDOR Protection check
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions"
        )
        
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific project. Enforces IDOR by checking ownership before delete.
    """
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # IDOR Protection check
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions"
        )
        
    await repo.delete(project_id)
