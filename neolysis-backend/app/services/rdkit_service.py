"""
Neolysis — RDKit Molecular Property Service (Enhanced)
=======================================================
Calculates drug-likeness and molecular properties from SMILES strings.

All RDKit operations are CPU-bound and run in a thread pool via
asyncio.to_thread to never block the async event loop.

Properties computed:
    - MW        : Molecular weight (Da)
    - LogP      : Wildman-Crippen partition coefficient
    - HBD       : H-bond donor count
    - HBA       : H-bond acceptor count
    - TPSA      : Topological polar surface area (Å²)
    - QED       : Quantitative Estimate of Drug-likeness (0–1)
    - Lipinski  : Boolean pass/fail + violation list
    - Heavy atoms: Count for ligand efficiency calculation
"""

import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger


class RDKitService:
    """Async wrapper around RDKit molecular property calculations."""

    def _calculate_properties(self, smiles: str) -> Dict[str, Any]:
        """
        Synchronous RDKit calculations — runs in thread pool.

        Args:
            smiles: SMILES string to analyse

        Returns:
            Dict with all computed molecular properties

        Raises:
            ValueError: If SMILES string is invalid
        """
        from rdkit import Chem
        from rdkit.Chem import Descriptors, QED

        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            raise ValueError(f"Invalid SMILES string: '{smiles[:100]}'")

        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        tpsa = Descriptors.TPSA(mol)
        qed_score = QED.qed(mol)
        heavy_atoms = mol.GetNumHeavyAtoms()
        rotatable_bonds = Descriptors.NumRotatableBonds(mol)
        ring_count = mol.GetRingInfo().NumRings()

        # Lipinski Rule of Five violations
        violations: List[str] = []
        if mw > 500:
            violations.append(f"MW > 500 ({mw:.1f} Da)")
        if logp > 5:
            violations.append(f"LogP > 5 ({logp:.2f})")
        if hbd > 5:
            violations.append(f"HBD > 5 ({hbd})")
        if hba > 10:
            violations.append(f"HBA > 10 ({hba})")

        return {
            "mw": round(mw, 2),
            "logp": round(logp, 2),
            "hbd": hbd,
            "hba": hba,
            "tpsa": round(tpsa, 2),
            "qed": round(qed_score, 4),
            "heavy_atoms": heavy_atoms,
            "rotatable_bonds": rotatable_bonds,
            "ring_count": ring_count,
            "lipinski_pass": len(violations) == 0,
            "lipinski_violations_count": len(violations),
            "violations": violations,
        }

    def _validate_smiles(self, smiles: str) -> bool:
        """Return True if SMILES is parseable by RDKit (sync)."""
        from rdkit import Chem
        return Chem.MolFromSmiles(smiles) is not None

    async def get_drug_likeness(self, smiles: str) -> Dict[str, Any]:
        """
        Compute all drug-likeness properties for a SMILES string.

        Args:
            smiles: SMILES string to analyse

        Returns:
            Dict of molecular properties. On error, returns a safe dict
            with `violations: ["Calculation Error"]`.
        """
        try:
            return await asyncio.to_thread(self._calculate_properties, smiles)
        except ValueError as e:
            logger.warning(f"RDKit: Invalid SMILES: {e}")
            return {
                "lipinski_pass": False,
                "qed": 0.0,
                "violations": ["Calculation Error"],
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"RDKit calculation failed for SMILES (len={len(smiles)}): {e}")
            return {
                "lipinski_pass": False,
                "qed": 0.0,
                "violations": ["Calculation Error"],
                "error": "Unexpected error during property calculation",
            }

    async def is_valid_smiles(self, smiles: str) -> bool:
        """
        Async SMILES validity check.

        Returns True if RDKit can parse the SMILES, False otherwise.
        """
        try:
            return await asyncio.to_thread(self._validate_smiles, smiles)
        except Exception:
            return False

    async def batch_calculate(
        self,
        smiles_list: List[str],
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Calculate properties for a batch of SMILES strings concurrently.

        Returns a list aligned with the input; None entries indicate failed calculations.
        """
        tasks = [self.get_drug_likeness(s) for s in smiles_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r if not isinstance(r, Exception) else None
            for r in results
        ]


rdkit_service = RDKitService()
