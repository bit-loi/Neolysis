import asyncio
from typing import Dict, Any, List
from rdkit import Chem
from rdkit.Chem import Descriptors, QED
from loguru import logger

class RDKitService:
    def _calculate_properties(self, smiles: str) -> Dict[str, Any]:
        """Synchronous RDKit calculations."""
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            raise ValueError(f"Invalid SMILES string: {smiles}")

        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        qed_score = QED.qed(mol)

        violations = []
        if mw > 500: violations.append("MW > 500")
        if logp > 5: violations.append("LogP > 5")
        if hbd > 5: violations.append("HBD > 5")
        if hba > 10: violations.append("HBA > 10")

        return {
            "mw": round(mw, 2),
            "logp": round(logp, 2),
            "hbd": hbd,
            "hba": hba,
            "qed": round(qed_score, 4),
            "lipinski_pass": len(violations) == 0,
            "violations": violations
        }

    async def get_drug_likeness(self, smiles: str) -> Dict[str, Any]:
        """Wrap synchronous RDKit call in a thread pool."""
        try:
            return await asyncio.to_thread(self._calculate_properties, smiles)
        except Exception as e:
            logger.error(f"RDKit calculation failed for {smiles}: {e}")
            return {
                "lipinski_pass": False,
                "qed": 0.0,
                "violations": ["Calculation Error"]
            }

rdkit_service = RDKitService()
