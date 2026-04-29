"""
Neolysis Models Package
========================
Imports all ORM models to ensure SQLAlchemy metadata is populated
before Alembic migrations or table creation.
"""

from app.models.user import User
from app.models.compound import Compound
from app.models.target import Target
from app.models.docking import DockingResult
from app.models.paper import Paper
from app.models.project import SavedProject
from app.models.disease import Disease
from app.models.protein import Protein
from app.models.knowledge_graph import KnowledgeGraph

__all__ = [
    "User",
    "Compound",
    "Target",
    "DockingResult",
    "Paper",
    "SavedProject",
    "Disease",
    "Protein",
    "KnowledgeGraph",
]
