import shutil
import subprocess
from pathlib import Path

from app.schemas.docking import LigandPreparationResult


class LigandPreparationService:
    def prepare_from_smiles(self, smiles: str, workdir: Path) -> LigandPreparationResult:
        workdir.mkdir(parents=True, exist_ok=True)
        warnings: list[str] = []

        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem
        except ImportError:
            return LigandPreparationResult(
                success=False,
                warnings=warnings,
                error_message="RDKit is required for ligand preparation but is not installed.",
            )

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return LigandPreparationResult(
                success=False,
                warnings=warnings,
                error_message="Invalid SMILES; RDKit could not parse the substrate ligand.",
            )

        mol = Chem.AddHs(mol)
        embed_status = AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        if embed_status != 0:
            return LigandPreparationResult(
                success=False,
                warnings=warnings,
                error_message="RDKit conformer generation failed for the substrate ligand.",
            )

        if AllChem.MMFFHasAllMoleculeParams(mol):
            AllChem.MMFFOptimizeMolecule(mol)
        else:
            warnings.append("MMFF parameters unavailable; used UFF optimization for ligand geometry.")
            AllChem.UFFOptimizeMolecule(mol)

        sdf_path = workdir / "ligand.sdf"
        writer = Chem.SDWriter(str(sdf_path))
        writer.write(mol)
        writer.close()

        pdbqt_path = workdir / "ligand.pdbqt"
        conversion_error = self._convert_sdf_to_pdbqt(sdf_path, pdbqt_path)
        if conversion_error:
            return LigandPreparationResult(
                ligand_sdf_path=str(sdf_path),
                success=False,
                warnings=warnings,
                error_message=conversion_error,
            )

        return LigandPreparationResult(
            ligand_sdf_path=str(sdf_path),
            ligand_pdbqt_path=str(pdbqt_path),
            warnings=warnings,
            success=True,
        )

    def _convert_sdf_to_pdbqt(self, sdf_path: Path, pdbqt_path: Path) -> str | None:
        obabel = shutil.which("obabel")
        if obabel:
            completed = subprocess.run(
                [obabel, str(sdf_path), "-O", str(pdbqt_path)],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if completed.returncode == 0 and pdbqt_path.exists():
                return None
            return completed.stderr or completed.stdout or "OpenBabel ligand PDBQT conversion failed."

        return (
            "Ligand PDBQT conversion requires OpenBabel (`obabel`) or a future Meeko adapter. "
            "Install OpenBabel or provide a ligand PDBQT path; Neolysis will not fake docking inputs."
        )
