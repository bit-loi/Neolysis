import re
from typing import Optional

from app.schemas.sequence import SequenceValidationResult


CANONICAL_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
AMBIGUOUS_OR_RARE = set("BJOUXZ")


class SequenceValidationService:
    def validate(self, sequence_text: str, name: Optional[str] = None) -> SequenceValidationResult:
        detected_format = "fasta" if sequence_text.lstrip().startswith(">") else "raw"
        warnings: list[str] = []
        fasta_names: list[str] = []
        sequence_lines: list[str] = []

        for raw_line in sequence_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(">"):
                fasta_names.append(line[1:].strip())
                continue
            sequence_lines.append(line)

        if detected_format == "fasta" and len(fasta_names) > 1:
            warnings.append("Multiple FASTA records were detected; sequences were concatenated for staging analysis.")

        cleaned = re.sub(r"[^A-Za-z]", "", "".join(sequence_lines if sequence_lines else [sequence_text])).upper()
        invalid = sorted({aa for aa in cleaned if aa not in CANONICAL_AMINO_ACIDS})

        if any(aa in AMBIGUOUS_OR_RARE for aa in invalid):
            warnings.append("Ambiguous or rare residues were detected and marked invalid for baseline scoring.")
        if not cleaned:
            warnings.append("No amino acid sequence could be extracted.")
        if cleaned and len(cleaned) < 30:
            warnings.append("Sequence is short for an enzyme candidate; verify that the full protein sequence was provided.")
        if len(cleaned) > 5000:
            warnings.append("Sequence is long for the staging baseline; feature extraction remains approximate.")

        display_name = name or (fasta_names[0] if fasta_names else None)
        return SequenceValidationResult(
            valid=bool(cleaned) and not invalid,
            name=display_name,
            cleaned_sequence=cleaned,
            sequence_length=len(cleaned),
            invalid_residues=invalid,
            warnings=warnings,
            detected_format=detected_format,
        )


sequence_validation_service = SequenceValidationService()
