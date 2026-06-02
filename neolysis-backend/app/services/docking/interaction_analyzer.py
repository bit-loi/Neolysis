from pathlib import Path
from typing import Any


class InteractionAnalyzer:
    def analyze_contacts(
        self,
        receptor_pdb_path: str,
        ligand_pose_path: str,
        cutoff_angstrom: float = 4.0,
    ) -> dict[str, Any]:
        receptor_atoms = self._parse_receptor_atoms(Path(receptor_pdb_path))
        ligand_atoms = self._parse_ligand_atoms(Path(ligand_pose_path))
        contacts: dict[tuple[str, str, int], dict[str, Any]] = {}

        for protein_atom in receptor_atoms:
            for ligand_atom in ligand_atoms:
                distance = self._distance(protein_atom, ligand_atom)
                if distance > cutoff_angstrom:
                    continue
                key = (
                    protein_atom["chain"],
                    protein_atom["residue_name"],
                    protein_atom["residue_number"],
                )
                label = self._label(protein_atom)
                existing = contacts.get(key)
                if existing is None or distance < existing["min_distance"]:
                    contacts[key] = {
                        "chain": protein_atom["chain"],
                        "residue_name": protein_atom["residue_name"],
                        "residue_number": protein_atom["residue_number"],
                        "label": label,
                        "min_distance": round(distance, 3),
                    }

        return {
            "cutoff_angstrom": cutoff_angstrom,
            "residues": sorted(contacts.values(), key=lambda item: item["min_distance"]),
            "method": "distance_based_contacts",
            "limitations": [
                "Contacts are distance-based from docked coordinates and are binding hypotheses, not confirmed interactions."
            ],
        }

    def _parse_receptor_atoms(self, path: Path) -> list[dict[str, Any]]:
        atoms: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("ATOM"):
                continue
            try:
                atoms.append(
                    {
                        "chain": line[21].strip(),
                        "residue_name": line[17:20].strip(),
                        "residue_number": int(line[22:26].strip()),
                        "x": float(line[30:38].strip()),
                        "y": float(line[38:46].strip()),
                        "z": float(line[46:54].strip()),
                    }
                )
            except ValueError:
                continue
        return atoms

    def _parse_ligand_atoms(self, path: Path) -> list[dict[str, float]]:
        atoms: list[dict[str, float]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith(("ATOM", "HETATM")):
                continue
            parsed = self._parse_pdbqt_atom(line)
            if parsed:
                atoms.append(parsed)
        return atoms

    @staticmethod
    def _parse_pdbqt_atom(line: str) -> dict[str, float] | None:
        try:
            return {
                "x": float(line[30:38].strip()),
                "y": float(line[38:46].strip()),
                "z": float(line[46:54].strip()),
            }
        except ValueError:
            parts = line.split()
            for idx in range(len(parts) - 2):
                try:
                    return {
                        "x": float(parts[idx]),
                        "y": float(parts[idx + 1]),
                        "z": float(parts[idx + 2]),
                    }
                except ValueError:
                    continue
        return None

    @staticmethod
    def _distance(a: dict[str, float], b: dict[str, float]) -> float:
        return ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 + (a["z"] - b["z"]) ** 2) ** 0.5

    @staticmethod
    def _label(atom: dict[str, Any]) -> str:
        chain = atom["chain"]
        residue_name = atom["residue_name"]
        residue_number = atom["residue_number"]
        return f"{chain}:{residue_name}{residue_number}" if chain else f"{residue_name}{residue_number}"
