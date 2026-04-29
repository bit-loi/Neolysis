"""
Neolysis — ADMET Prediction Service
=====================================
Predicts ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity)
properties for drug candidate molecules using Therapeutics Data Commons (TDC)
pretrained models.

Properties predicted:
    - Caco-2     : Intestinal membrane permeability (absorption)
    - hERG       : Cardiac ion channel toxicity (safety)
    - DILI       : Drug-induced liver injury (hepatotoxicity)
    - BBB_Martini: Blood-brain barrier permeability
    - Lipophilicity: logD (distribution)

Each property is normalised into:
    { "value": float, "risk_level": "low" | "medium" | "high" }

TODO (BioLLM): Replace individual TDC models with a multi-task BioLLM
               (e.g. Uni-Mol or ChemBERTa) fine-tuned on the full TDC benchmark suite.
"""

import asyncio
from typing import Dict, Any
from loguru import logger

from app.services.rdkit_service import rdkit_service


# ---------------------------------------------------------------------------
# Risk thresholds — tuned from TDC benchmark literature
# ---------------------------------------------------------------------------

RISK_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "caco2": {
        # Caco-2 permeability: log Papp (cm/s)
        # > -5.15 = high permeability (low risk); < -6.0 = low permeability (high risk)
        "low": -5.15,
        "medium": -6.0,
    },
    "herg": {
        # hERG IC50 (µM): > 10 = low risk; 1–10 = medium; < 1 = high
        "low": 10.0,
        "medium": 1.0,
    },
    "dili": {
        # DILI: binary classifier output probability: < 0.3 low; 0.3–0.6 medium; > 0.6 high
        "low": 0.3,
        "medium": 0.6,
    },
    "bbb": {
        # BBB: positive (1) = penetrates BBB; negative (0) = doesn't
        # For NTDs (non-CNS targets), penetrating BBB is usually NOT wanted
        "low": 0.4,   # < 0.4 prob of penetration = low risk
        "medium": 0.7,
    },
    "lipophilicity": {
        # LogD: 0–3 = optimal; > 5 = high (poor selectivity/toxicity)
        "low": 3.0,
        "medium": 5.0,
    },
}


def _get_risk(prop: str, value: float) -> str:
    """
    Map a numeric ADMET value to a risk level string.

    For most properties, HIGHER values = worse (hERG, DILI, BBB, Lipophilicity).
    For Caco-2, LOWER values = worse (less permeable).
    """
    t = RISK_THRESHOLDS[prop]

    if prop == "caco2":
        # Inverted: higher (less negative) is better
        if value >= t["low"]:
            return "low"
        elif value >= t["medium"]:
            return "medium"
        return "high"

    elif prop == "herg":
        # Higher IC50 = less potent = safer
        if value >= t["low"]:
            return "low"
        elif value >= t["medium"]:
            return "medium"
        return "high"

    else:
        # DILI, BBB, Lipophilicity: lower = safer
        if value < t["low"]:
            return "low"
        elif value < t["medium"]:
            return "medium"
        return "high"


# ---------------------------------------------------------------------------
# TDC model loading (lazy, cached in-process)
# ---------------------------------------------------------------------------

_tdc_models: Dict[str, Any] = {}


def _load_tdc_model(name: str) -> Any:
    """
    Load and cache a TDC pretrained model by dataset name.
    Falls back gracefully if PyTDC or DeepPurpose is not installed.
    """
    if name in _tdc_models:
        return _tdc_models[name]
    try:
        from tdc.single_pred import ADME, Tox
        from DeepPurpose import utils, CompoundPred
        # TDC returns pre-split datasets; we just need the pretrained predictor
        # For hackathon: use TDC's built-in oracle/pretrained interface
        from tdc import Oracle
        oracle = Oracle(name=name)
        _tdc_models[name] = oracle
        logger.info(f"Loaded TDC oracle: {name}")
        return oracle
    except Exception as e:
        logger.warning(f"Could not load TDC oracle '{name}': {e} — using RDKit fallback")
        return None


def _predict_with_tdc(smiles: str, model_name: str) -> float:
    """Run TDC oracle prediction (sync)."""
    oracle = _load_tdc_model(model_name)
    if oracle is None:
        raise RuntimeError(f"TDC model {model_name} unavailable")
    result = oracle(smiles)
    # Oracle returns float directly for most models
    if isinstance(result, (int, float)):
        return float(result)
    # Some return dict
    if isinstance(result, dict):
        return float(list(result.values())[0])
    return float(result)


def _rdkit_lipophilicity_fallback(smiles: str) -> float:
    """Estimate logP as a lipophilicity proxy using RDKit (sync)."""
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        raise ValueError(f"Invalid SMILES: {smiles}")
    return float(Descriptors.MolLogP(mol))


def _rdkit_tpsa_fallback(smiles: str) -> float:
    """Estimate TPSA using RDKit (sync, used as BBB proxy)."""
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        raise ValueError(f"Invalid SMILES: {smiles}")
    tpsa = Descriptors.TPSA(mol)
    # Map TPSA to BBB probability proxy: < 60 Å² → high BBB, > 140 Å² → low
    # Return as a probability-like score
    if tpsa < 60:
        return 0.8
    elif tpsa < 90:
        return 0.5
    elif tpsa < 140:
        return 0.3
    return 0.1


def _compute_admet_sync(smiles: str) -> Dict[str, Any]:
    """
    Compute all ADMET properties synchronously.
    Uses TDC oracles where available; falls back to RDKit heuristics.
    """
    results: Dict[str, Any] = {}
    fallback_used = False

    # ── Caco-2 (log Papp) ──────────────────────────────────────────────────
    try:
        caco2_val = _predict_with_tdc(smiles, "Caco2_Wang")
    except Exception:
        # Fallback: estimate from TPSA & MW (rough heuristic)
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            tpsa = Descriptors.TPSA(mol)
            mw = Descriptors.MolWt(mol)
            # Rough correlation: better permeability with lower TPSA and MW
            caco2_val = -5.0 - (tpsa / 200.0) - (mw / 2000.0)
        else:
            caco2_val = -6.5
        fallback_used = True

    results["caco2"] = {
        "value": round(caco2_val, 4),
        "risk_level": _get_risk("caco2", caco2_val),
        "unit": "log Papp (cm/s)",
        "description": "Intestinal membrane permeability (Caco-2 cell line)",
    }

    # ── hERG Cardiac Toxicity ─────────────────────────────────────────────
    try:
        herg_val = _predict_with_tdc(smiles, "hERG")
    except Exception:
        # Fallback: use logP as rough proxy (high logP → more likely hERG binder)
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        mol = Chem.MolFromSmiles(smiles)
        logp = Descriptors.MolLogP(mol) if mol else 3.0
        herg_val = max(0.1, 10.0 - max(0, logp - 1) * 1.5)
        fallback_used = True

    results["herg"] = {
        "value": round(herg_val, 4),
        "risk_level": _get_risk("herg", herg_val),
        "unit": "IC50 (µM)",
        "description": "hERG potassium channel inhibition (cardiac toxicity risk)",
    }

    # ── DILI (Drug-Induced Liver Injury) ──────────────────────────────────
    try:
        dili_val = _predict_with_tdc(smiles, "DILI")
    except Exception:
        # Fallback: use logP + MW as rough hepatotoxicity proxy
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            logp = Descriptors.MolLogP(mol)
            mw = Descriptors.MolWt(mol)
            dili_val = min(0.95, max(0.05, (logp / 10.0) + (mw / 3000.0)))
        else:
            dili_val = 0.5
        fallback_used = True

    results["dili"] = {
        "value": round(dili_val, 4),
        "risk_level": _get_risk("dili", dili_val),
        "unit": "probability (0–1)",
        "description": "Drug-induced liver injury probability",
    }

    # ── Blood-Brain Barrier ───────────────────────────────────────────────
    try:
        bbb_val = _predict_with_tdc(smiles, "BBB_Martini")
    except Exception:
        bbb_val = _rdkit_tpsa_fallback(smiles)
        fallback_used = True

    results["bbb"] = {
        "value": round(bbb_val, 4),
        "risk_level": _get_risk("bbb", bbb_val),
        "unit": "probability (0–1)",
        "description": "Blood-brain barrier penetration probability",
    }

    # ── Lipophilicity (logD) ──────────────────────────────────────────────
    try:
        lipo_val = _predict_with_tdc(smiles, "Lipophilicity_AstraZeneca")
    except Exception:
        lipo_val = _rdkit_lipophilicity_fallback(smiles)
        fallback_used = True

    results["lipophilicity"] = {
        "value": round(lipo_val, 4),
        "risk_level": _get_risk("lipophilicity", lipo_val),
        "unit": "logD",
        "description": "Lipophilicity (distribution coefficient at pH 7.4)",
    }

    results["_fallback_used"] = fallback_used
    if fallback_used:
        results["_warning"] = (
            "TDC pretrained models unavailable — RDKit heuristic estimates used. "
            "Install PyTDC and DeepPurpose for research-grade predictions."
        )

    return results


class ADMETService:
    """
    Async ADMET prediction service.

    Wraps TDC pretrained models (Caco-2, hERG, DILI, BBB, Lipophilicity)
    with an RDKit fallback and normalises outputs to risk levels.
    """

    async def predict(self, smiles: str) -> Dict[str, Any]:
        """
        Predict ADMET properties for a SMILES string.

        Args:
            smiles: Valid SMILES string (validated by RDKit before calling this)

        Returns:
            Dict with one key per ADMET property, each containing:
                { "value": float, "risk_level": "low"|"medium"|"high",
                  "unit": str, "description": str }
        """
        # Validate SMILES first
        props = await rdkit_service.get_drug_likeness(smiles)
        if "Calculation Error" in props.get("violations", []):
            raise ValueError(f"Invalid SMILES: {smiles}")

        # Run ADMET prediction in thread pool (CPU-bound)
        result = await asyncio.to_thread(_compute_admet_sync, smiles)

        # Attach drug-likeness summary
        result["drug_likeness"] = {
            "mw": props.get("mw"),
            "logp": props.get("logp"),
            "hbd": props.get("hbd"),
            "hba": props.get("hba"),
            "tpsa": props.get("tpsa"),
            "qed": props.get("qed"),
            "lipinski_pass": props.get("lipinski_pass"),
            "violations": props.get("violations", []),
        }

        logger.info(f"ADMET prediction complete for SMILES (len={len(smiles)})")
        return result


admet_service = ADMETService()
