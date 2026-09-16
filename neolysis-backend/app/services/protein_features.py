import hashlib
from collections import Counter
from typing import Dict, Optional

from app.schemas.sequence import ProteinFeatureResult


AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
IONIZABLE_RESIDUES = "DEHKR"

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
    def extract(self, sequence: str, target_ph: float = 7.0) -> ProteinFeatureResult:
        # Canonical form: uppercase only. Callers are expected to already have run this
        # through sequence_validation_service, which strips whitespace/non-letters; the
        # uppercase() here just guards this method against being called directly with an
        # already-cleaned-but-not-yet-uppercased sequence, so the SHA-256 below is always
        # computed from the same canonical representation regardless of call path.
        sequence = sequence.upper()
        warnings: list[str] = []
        counts = Counter(sequence)
        length = len(sequence)
        composition: Dict[str, int] = {aa: counts.get(aa, 0) for aa in AMINO_ACIDS}
        percentages = {
            aa: round((composition[aa] / length) * 100, 3) if length else 0.0
            for aa in AMINO_ACIDS
        }
        sequence_sha256 = hashlib.sha256(sequence.encode("utf-8")).hexdigest()
        ionizable_counts = {aa: counts.get(aa, 0) for aa in IONIZABLE_RESIDUES}
        ionizable_fractions = {
            aa: round(ionizable_counts[aa] / length, 6) if length else 0.0
            for aa in IONIZABLE_RESIDUES
        }

        try:
            from Bio.SeqUtils.ProtParam import ProteinAnalysis

            analysis = ProteinAnalysis(sequence)
            charge_at_target_ph = self._safe_charge_at_ph(analysis, target_ph, warnings)
            return ProteinFeatureResult(
                sequence_length=length,
                amino_acid_composition=composition,
                amino_acid_percent=percentages,
                molecular_weight=round(float(analysis.molecular_weight()), 3),
                gravy=round(float(analysis.gravy()), 3),
                aromaticity=round(float(analysis.aromaticity()), 3),
                instability_index=round(float(analysis.instability_index()), 3),
                isoelectric_point=round(float(analysis.isoelectric_point()), 3),
                sequence_sha256=sequence_sha256,
                target_ph=target_ph,
                charge_at_target_ph=charge_at_target_ph,
                ionizable_residue_counts=ionizable_counts,
                ionizable_residue_fractions=ionizable_fractions,
                method="biopython_protparam",
                warnings=warnings,
            )
        except Exception:
            # Preserve existing fallback behavior. The `method` field below is the
            # observable signal that this branch was used instead of Biopython —
            # callers must not treat these two methods as scientifically equivalent.
            warnings.append("Biopython ProtParam was unavailable; fallback sequence descriptors were used.")

        water_loss = max(length - 1, 0) * 18.015
        molecular_weight = sum(RESIDUE_MASS.get(aa, 0.0) for aa in sequence) - water_loss
        gravy = sum(KYTE_DOOLITTLE.get(aa, 0.0) for aa in sequence) / length if length else 0.0
        aromaticity = sum(composition[aa] for aa in "FWY") / length if length else 0.0
        # No validated charge-at-pH model exists in the fallback path (it depends on
        # Biopython's pKa tables). Report it as unavailable rather than approximating,
        # so the fallback method is never silently presented as equivalent to
        # biopython_protparam.
        if length:
            warnings.append("charge_at_target_ph is unavailable without Biopython; no fallback estimate was substituted.")

        return ProteinFeatureResult(
            sequence_length=length,
            amino_acid_composition=composition,
            amino_acid_percent=percentages,
            molecular_weight=round(molecular_weight, 3),
            gravy=round(gravy, 3),
            aromaticity=round(aromaticity, 3),
            instability_index=None,
            isoelectric_point=None,
            sequence_sha256=sequence_sha256,
            target_ph=target_ph,
            charge_at_target_ph=None,
            ionizable_residue_counts=ionizable_counts,
            ionizable_residue_fractions=ionizable_fractions,
            method="fallback_sequence_descriptors",
            warnings=warnings,
        )

    @staticmethod
    def _safe_charge_at_ph(analysis, target_ph: float, warnings: list[str]) -> Optional[float]:
        try:
            return round(float(analysis.charge_at_pH(target_ph)), 3)
        except Exception as exc:
            warnings.append(f"charge_at_target_ph could not be computed: {type(exc).__name__}.")
            return None


protein_feature_service = ProteinFeatureService()
