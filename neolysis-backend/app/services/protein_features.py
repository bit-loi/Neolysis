from collections import Counter
from typing import Dict

from app.schemas.sequence import ProteinFeatureResult


AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"

RESIDUE_MASS = {
    "A": 89.09,
    "C": 121.16,
    "D": 133.10,
    "E": 147.13,
    "F": 165.19,
    "G": 75.07,
    "H": 155.16,
    "I": 131.18,
    "K": 146.19,
    "L": 131.18,
    "M": 149.21,
    "N": 132.12,
    "P": 115.13,
    "Q": 146.15,
    "R": 174.20,
    "S": 105.09,
    "T": 119.12,
    "V": 117.15,
    "W": 204.23,
    "Y": 181.19,
}

KYTE_DOOLITTLE = {
    "A": 1.8,
    "C": 2.5,
    "D": -3.5,
    "E": -3.5,
    "F": 2.8,
    "G": -0.4,
    "H": -3.2,
    "I": 4.5,
    "K": -3.9,
    "L": 3.8,
    "M": 1.9,
    "N": -3.5,
    "P": -1.6,
    "Q": -3.5,
    "R": -4.5,
    "S": -0.8,
    "T": -0.7,
    "V": 4.2,
    "W": -0.9,
    "Y": -1.3,
}


class ProteinFeatureService:
    def extract(self, sequence: str) -> ProteinFeatureResult:
        sequence = sequence.upper()
        warnings: list[str] = []
        counts = Counter(sequence)
        length = len(sequence)
        composition: Dict[str, int] = {aa: counts.get(aa, 0) for aa in AMINO_ACIDS}
        percentages = {
            aa: round((composition[aa] / length) * 100, 3) if length else 0.0
            for aa in AMINO_ACIDS
        }

        try:
            from Bio.SeqUtils.ProtParam import ProteinAnalysis

            analysis = ProteinAnalysis(sequence)
            return ProteinFeatureResult(
                sequence_length=length,
                amino_acid_composition=composition,
                amino_acid_percent=percentages,
                molecular_weight=round(float(analysis.molecular_weight()), 3),
                gravy=round(float(analysis.gravy()), 3),
                aromaticity=round(float(analysis.aromaticity()), 3),
                instability_index=round(float(analysis.instability_index()), 3),
                isoelectric_point=round(float(analysis.isoelectric_point()), 3),
                method="biopython_protparam",
                warnings=warnings,
            )
        except Exception:
            warnings.append("Biopython ProtParam was unavailable; fallback sequence descriptors were used.")

        water_loss = max(length - 1, 0) * 18.015
        molecular_weight = sum(RESIDUE_MASS.get(aa, 0.0) for aa in sequence) - water_loss
        gravy = sum(KYTE_DOOLITTLE.get(aa, 0.0) for aa in sequence) / length if length else 0.0
        aromaticity = sum(composition[aa] for aa in "FWY") / length if length else 0.0

        return ProteinFeatureResult(
            sequence_length=length,
            amino_acid_composition=composition,
            amino_acid_percent=percentages,
            molecular_weight=round(molecular_weight, 3),
            gravy=round(gravy, 3),
            aromaticity=round(aromaticity, 3),
            instability_index=None,
            isoelectric_point=None,
            method="fallback_sequence_descriptors",
            warnings=warnings,
        )


protein_feature_service = ProteinFeatureService()
