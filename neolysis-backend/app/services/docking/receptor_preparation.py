import shutil
import subprocess
from pathlib import Path

from app.schemas.docking import ReceptorPreparationResult


class ReceptorPreparationService:
    def prepare_from_pdb_text(
        self,
        pdb_text: str,
        workdir: Path,
        chain_id: str | None = None,
        remove_waters: bool = True,
        remove_non_protein_heteroatoms: bool = True,
    ) -> ReceptorPreparationResult:
        workdir.mkdir(parents=True, exist_ok=True)
        warnings: list[str] = []
        filtered_lines: list[str] = []

        for line in pdb_text.splitlines():
            if not line.startswith(("ATOM", "HETATM", "TER", "END")):
                continue
            if chain_id and line.startswith(("ATOM", "HETATM")) and line[21].strip() != chain_id:
                continue
            residue_name = line[17:20].strip()
            if remove_waters and residue_name in {"HOH", "WAT"}:
                continue
            if remove_non_protein_heteroatoms and line.startswith("HETATM"):
                continue
            filtered_lines.append(line)

        if not any(line.startswith("ATOM") for line in filtered_lines):
            return ReceptorPreparationResult(
                success=False,
                warnings=warnings,
                error_message="No protein ATOM records remained after receptor filtering.",
            )

        receptor_pdb_path = workdir / "receptor.pdb"
        receptor_pdb_path.write_text("\n".join(filtered_lines) + "\n", encoding="utf-8")
        receptor_pdbqt_path = workdir / "receptor.pdbqt"

        conversion_error = self._convert_pdb_to_pdbqt(receptor_pdb_path, receptor_pdbqt_path)
        if conversion_error:
            return ReceptorPreparationResult(
                receptor_pdb_path=str(receptor_pdb_path),
                success=False,
                warnings=warnings,
                error_message=conversion_error,
            )

        return ReceptorPreparationResult(
            receptor_pdb_path=str(receptor_pdb_path),
            receptor_pdbqt_path=str(receptor_pdbqt_path),
            warnings=warnings,
            success=True,
        )

    def _convert_pdb_to_pdbqt(self, pdb_path: Path, pdbqt_path: Path) -> str | None:
        obabel = shutil.which("obabel")
        if obabel:
            completed = subprocess.run(
                [obabel, str(pdb_path), "-O", str(pdbqt_path), "-xr"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if completed.returncode == 0 and pdbqt_path.exists():
                return None
            return completed.stderr or completed.stdout or "OpenBabel receptor PDBQT conversion failed."

        return (
            "Receptor PDBQT conversion requires OpenBabel (`obabel`) or MGLTools/Meeko integration. "
            "Install a converter before running docking; Neolysis will not pretend a receptor was prepared."
        )
