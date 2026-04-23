from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.csv_docking import get_docking_by_target, get_docking_by_cid, get_all_targets, read_top10_csv
from app.schemas.docking_csv import DockingCSVResult, DockingCSVResponse

router = APIRouter()


@router.get("/target/{target_id}", response_model=DockingCSVResponse)
async def get_docking_by_target_id(target_id: str):
    """
    Get all docking results for a target from CSV.
    Target ID: lipl32, lena, scac, ompa, ns3_helicase, etc.
    """
    results = get_docking_by_target(target_id)
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No docking results found for target: {target_id}")
    
    target_name = results[0]["target"]
    compounds = [DockingCSVResult(**r) for r in results]
    
    return DockingCSVResponse(target=target_name, compounds=compounds)


@router.get("/compound/{cid}", response_model=List[DockingCSVResult])
async def get_docking_by_compound_cid(cid: int):
    """
    Get all docking results for a compound (by PubChem CID).
    """
    results = get_docking_by_cid(cid)
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No docking results found for compound CID: {cid}")
    
    return [DockingCSVResult(**r) for r in results]


@router.get("/targets")
async def list_available_targets():
    """
    List all targets that have docking data.
    """
    targets = get_all_targets()
    return {"targets": targets}


@router.get("/")
async def get_all_docking():
    """
    Get all docking results from CSV.
    """
    results = read_top10_csv()
    return {"docking": results}