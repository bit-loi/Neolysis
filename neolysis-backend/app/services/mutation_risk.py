import re
from typing import Iterable, Optional

from app.schemas.variant import MutationRiskResult


MUTATION_RE = re.compile(r"^([A-Z])([1-9][0-9]*)([A-Z])$")


class MutationRiskService:
    def apply_mutations(self, wild_type: str, mutations: Iterable[str]) -> tuple[Optional[str], list[str]]:
        sequence = list(wild_type.upper())
        warnings: list[str] = []
        for mutation in mutations:
            match = MUTATION_RE.match(mutation.strip().upper())
            if not match:
                warnings.append(f"Could not parse mutation notation: {mutation}")
                continue
            original, position_text, replacement = match.groups()
            position = int(position_text)
            index = position - 1
            if index < 0 or index >= len(sequence):
                warnings.append(f"Mutation {mutation} is outside the sequence length.")
                continue
            if sequence[index] != original:
                warnings.append(
                    f"Mutation {mutation} expected {original} at position {position}, found {sequence[index]}."
                )
                continue
            sequence[index] = replacement
        return "".join(sequence), warnings

    def analyze(
        self,
        wild_type: str,
        variant_sequence: Optional[str] = None,
        mutations: Optional[Iterable[str]] = None,
        active_site_positions: Optional[Iterable[int]] = None,
        conserved_regions: Optional[Iterable[str]] = None,
    ) -> MutationRiskResult:
        wild_type = wild_type.upper()
        warnings: list[str] = []
        if variant_sequence:
            variant = variant_sequence.upper()
        else:
            variant, warnings = self.apply_mutations(wild_type, mutations or [])

        risk_flags_stability: list[str] = []
        risk_flags_function: list[str] = []

        if len(variant) != len(wild_type):
            risk_flags_function.append("Variant length differs from wild type; alignment-aware review is required.")

        mutation_positions = [
            index + 1
            for index, (wt, var) in enumerate(zip(wild_type, variant))
            if wt != var
        ]
        mutation_count = len(mutation_positions) + abs(len(variant) - len(wild_type))
        denominator = max(len(wild_type), 1)
        risk_score = min(1.0, mutation_count / denominator * 8.0)

        for position in mutation_positions:
            wt = wild_type[position - 1]
            var = variant[position - 1]
            if wt in "CPG" or var in "CPG":
                risk_flags_stability.append(
                    f"Mutation {wt}{position}{var} changes cysteine, proline, or glycine and may affect folding."
                )
            if wt in "DEKRH" and var not in "DEKRH":
                risk_flags_function.append(
                    f"Mutation {wt}{position}{var} removes a charged residue that may affect local interactions."
                )

        active_positions = set(active_site_positions or [])
        active_hits = sorted(active_positions.intersection(mutation_positions))
        active_warning = None
        if active_hits:
            active_warning = f"Mutations overlap supplied active-site positions: {active_hits}."
            risk_score = min(1.0, risk_score + 0.25)

        conserved_warning = None
        for motif in conserved_regions or []:
            motif = motif.upper()
            start = wild_type.find(motif)
            if start == -1:
                continue
            motif_positions = set(range(start + 1, start + len(motif) + 1))
            hits = sorted(motif_positions.intersection(mutation_positions))
            if hits:
                conserved_warning = f"Mutations overlap supplied conserved motif '{motif}' at positions {hits}."
                risk_score = min(1.0, risk_score + 0.2)
                break

        if warnings:
            risk_flags_function.extend(warnings)
            risk_score = min(1.0, risk_score + 0.1)

        if risk_score >= 0.7:
            risk_level = "high"
        elif risk_score >= 0.35:
            risk_level = "medium"
        else:
            risk_level = "low"

        return MutationRiskResult(
            risk_level=risk_level,
            risk_score=round(risk_score, 3),
            potential_stability_risk=risk_flags_stability,
            potential_function_risk=risk_flags_function,
            conserved_region_warning=conserved_warning,
            active_site_warning=active_warning,
            confidence=0.34,
            limitations=[
                "Mutation risk is estimated from sequence-level heuristics only.",
                "Structure, conservation alignment, and activity assay data are required for reliable engineering decisions.",
            ],
        )

    def summarize_mutations(self, wild_type: str, variant_sequence: str) -> str:
        changes = [
            f"{wt}{index + 1}{var}"
            for index, (wt, var) in enumerate(zip(wild_type.upper(), variant_sequence.upper()))
            if wt != var
        ]
        length_delta = len(variant_sequence) - len(wild_type)
        if length_delta:
            changes.append(f"length_delta={length_delta:+d}")
        return ", ".join(changes) if changes else "No sequence changes detected"


mutation_risk_service = MutationRiskService()
