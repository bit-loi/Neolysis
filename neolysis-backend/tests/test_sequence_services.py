from app.services.protein_features import protein_feature_service
from app.services.sequence_validation import sequence_validation_service


SAMPLE_FASTA = """>alkaline_protease_candidate
MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDHVKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFLSHKDDSPDLPKLKPDPNTLCDEFKADEKKFWGKYLYEIARRHPYFYAPELLYYANKYNGVFQECCQAEDKGACLLPKIETMREKVLASSARQRLR"""


def test_validate_fasta_extracts_clean_sequence():
    result = sequence_validation_service.validate(SAMPLE_FASTA)

    assert result.valid is True
    assert result.detected_format == "fasta"
    assert result.name == "alkaline_protease_candidate"
    assert result.sequence_length > 100
    assert result.invalid_residues == []


def test_validate_rejects_invalid_residues():
    result = sequence_validation_service.validate(">bad\nMKTZZX")

    assert result.valid is False
    assert "X" in result.invalid_residues
    assert "Z" in result.invalid_residues


def test_feature_extraction_returns_core_descriptors():
    validation = sequence_validation_service.validate(SAMPLE_FASTA)
    features = protein_feature_service.extract(validation.cleaned_sequence)

    assert features.sequence_length == validation.sequence_length
    assert features.molecular_weight > 0
    assert "A" in features.amino_acid_composition
    assert features.method in {"biopython_protparam", "fallback_sequence_descriptors"}
