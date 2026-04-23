from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.project import SavedProject
from app.schemas.project import ProjectCreate

class IProjectRepository(ABC):
    @abstractmethod
    async def get_by_id(self, project_id: int) -> Optional[SavedProject]:
        pass

    @abstractmethod
    async def get_by_user(self, user_id: int) -> List[SavedProject]:
        pass

    @abstractmethod
    async def create(self, user_id: int, project_in: ProjectCreate) -> SavedProject:
        pass

    @abstractmethod
    async def delete(self, project_id: int) -> bool:
        pass

class ProjectRepository(IProjectRepository):
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def get_by_id(self, project_id: int) -> Optional[SavedProject]:
        return await self.db.get(SavedProject, project_id)

    async def get_by_user(self, user_id: int) -> List[SavedProject]:
        result = await self.db.execute(select(SavedProject).where(SavedProject.user_id == user_id))
        return list(result.scalars().all())

    async def create(self, user_id: int, project_in: ProjectCreate) -> SavedProject:
        project = SavedProject(
            user_id=user_id,
            title=project_in.title,
            description=project_in.description,
            target_id=project_in.target_id
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete(self, project_id: int) -> bool:
        project = await self.get_by_id(project_id)
        if not project:
            return False
        await self.db.delete(project)
        await self.db.commit()
        return True
