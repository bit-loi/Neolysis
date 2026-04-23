import httpx
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.core.cache import cache
from loguru import logger

class PubChemService:
    def __init__(self):
        self.base_url = settings.PUBCHEM_BASE_URL
        self.client = httpx.AsyncClient(timeout=10.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def search_similar_compounds(self, smiles: str, threshold: float = 0.7, limit: int = 20) -> List[int]:
        """
        Search for compounds similar to the given SMILES.
        Returns a list of PubChem CIDs.
        """
        cache_key = f"pubchem:sim:{smiles}:{threshold}:{limit}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        # PubChem PUG REST similarity search involves two steps: initiating search and polling
        # Simplified here: assuming direct search if possible or using a standard endpoint
        url = f"{self.base_url}/compound/fastsimilarity_2d/smiles/{smiles}/cids/JSON?Threshold={int(threshold*100)}&MaxRecords={limit}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            cids = data.get("IdentifierList", {}).get("CID", [])
            
            await cache.set(cache_key, cids, ttl=3600)
            return cids
        except Exception as e:
            logger.error(f"PubChem similarity search failed: {e}")
            return []

    async def get_compound_details(self, cid: int) -> Optional[Dict[str, Any]]:
        cache_key = f"pubchem:cid:{cid}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        url = f"{self.base_url}/compound/cid/{cid}/property/CanonicalSMILES,MolecularWeight,IUPACName,XLogP/JSON"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            prop = data["PropertyTable"]["Properties"][0]
            
            result = {
                "pubchem_cid": cid,
                "name": prop.get("IUPACName"),
                "smiles": prop.get("CanonicalSMILES"),
                "mw": prop.get("MolecularWeight"),
                "logp": prop.get("XLogP")
            }
            
            await cache.set(cache_key, result, ttl=86400)
            return result
        except Exception as e:
            logger.error(f"PubChem details fetch failed for CID {cid}: {e}")
            return None

pubchem_service = PubChemService()
