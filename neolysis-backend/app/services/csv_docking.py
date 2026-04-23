import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.parent / "docking-results"

def read_top10_csv() -> List[Dict[str, Any]]:
    results = []
    file_path = BASE_DIR / "top10_per_pocket.csv"
    
    if not file_path.exists():
        return results
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                "target": row.get("target"),
                "pocket": int(row.get("pocket", 1)),
                "cid": int(row.get("cid")),
                "name": row.get("name"),
                "smiles": row.get("smiles"),
                "mw": float(row.get("mw", 0)),
                "logp": float(row.get("logp", 0)),
                "affinity": float(row.get("affinity", 0)),
                "ligand_eff": float(row.get("ligand_eff", 0)),
                "affinity_rank": float(row.get("affinity_rank", 0)),
                "le_rank": float(row.get("le_rank", 0)),
                "composite": float(row.get("composite", 0)),
                "confidence": float(row.get("confidence", 0)),
                "explanation": row.get("explanation"),
            })
    
    return results


def get_docking_by_target(target_name: str) -> List[Dict[str, Any]]:
    all_results = read_top10_csv()
    
    target_map = {
        "lipl32": "LipL32",
        "lena": "LenA",
        "scac": "ScaC",
        "ompa": "OmpA",
        "bima": "BmaP",
        "bohA": "BohA",
        "ns3_helicase": "NS3_Helicase",
        "ns2b-ns3": "NS3_Helicase",
    }
    
    canonical_name = target_map.get(target_name.lower(), target_name)
    
    return [r for r in all_results if r["target"].lower() == canonical_name.lower()]


def get_docking_by_cid(cid: int) -> List[Dict[str, Any]]:
    all_results = read_top10_csv()
    return [r for r in all_results if r["cid"] == cid]


def get_all_targets() -> List[str]:
    all_results = read_top10_csv()
    targets = set(r["target"] for r in all_results)
    return sorted(list(targets))