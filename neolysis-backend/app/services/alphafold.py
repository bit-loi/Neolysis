import httpx
from typing import Optional
from app.config import settings
from app.core.cache import cache
from loguru import logger

class AlphaFoldService:
    def __init__(self):
        self.af_base = settings.ALPHAFOLD_BASE_URL
        self.pdb_base = settings.RCSB_PDB_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_structure_url(self, uniprot_id: str = None, pdb_id: str = None) -> Optional[str]:
        """
        Returns a URL to the PDB file.
        Prefer AlphaFold if uniprot_id is provided.
        """
        if uniprot_id:
            # AlphaFold DB naming convention
            af_url = f"{self.af_base}/AF-{uniprot_id}-F1-model_v4.pdb"
            return af_url
        
        if pdb_id:
            pdb_url = f"{self.pdb_base}/{pdb_id.lower()}.pdb"
            return pdb_url
            
        return None

    async def fetch_structure_file(self, url: str) -> Optional[bytes]:
        """Fetch and cache the PDB file content."""
        cache_key = f"pdb_file:{url}"
        cached = await cache.get(cache_key)
        if cached:
            return cached.encode('utf-8') if isinstance(cached, str) else cached

        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                content = response.content
                # Cache for 24 hours (PDBs don't change often)
                await cache.set(cache_key, content.decode('latin-1', errors='ignore'), ttl=86400)
                return content
        except Exception as e:
            logger.error(f"Failed to fetch structure from {url}: {e}")
        
        return None

alphafold_service = AlphaFoldService()
