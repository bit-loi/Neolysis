import hashlib

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


# ── Milestone 1: normalization ────────────────────────────────────────────────

def test_validate_accepts_raw_sequence():
    result = sequence_validation_service.validate("MKTAA")

    assert result.valid is True
    assert result.detected_format == "raw"
    assert result.cleaned_sequence == "MKTAA"


def test_validate_accepts_multiline_fasta():
    result = sequence_validation_service.validate(">protein\nMKT\nAA")

    assert result.valid is True
    assert result.cleaned_sequence == "MKTAA"


def test_validate_normalizes_lowercase_sequence():
    result = sequence_validation_service.validate("mktaa")

    assert result.valid is True
    assert result.cleaned_sequence == "MKTAA"


def test_validate_strips_whitespace_between_residues():
    result = sequence_validation_service.validate("m k t a a")

    assert result.valid is True
    assert result.cleaned_sequence == "MKTAA"


def test_validate_empty_sequence_is_invalid():
    result = sequence_validation_service.validate("")

    assert result.valid is False
    assert result.sequence_length == 0
    assert "No amino acid sequence could be extracted." in result.warnings


# ── Milestone 1: SHA-256 provenance ───────────────────────────────────────────

def test_sequence_sha256_is_present_and_correct():
    features = protein_feature_service.extract("MKTAA")

    expected = hashlib.sha256("MKTAA".encode("utf-8")).hexdigest()
    assert features.sequence_sha256 == expected


def test_sha256_reproducible_for_identical_input():
    first = protein_feature_service.extract("MKTAA")
    second = protein_feature_service.extract("MKTAA")

    assert first.sequence_sha256 == second.sequence_sha256


def test_canonical_hash_matches_across_equivalent_representations():
    """
    >protein / MKTAA, 'm k t a a', and 'MKTAA' all represent the same protein and
    must resolve to the same sequence_sha256 once run through sequence normalization.
    """
    fasta_form = sequence_validation_service.validate(">protein\nMKTAA")
    lowercase_spaced_form = sequence_validation_service.validate("m k t a a")
    raw_form = sequence_validation_service.validate("MKTAA")

    assert fasta_form.cleaned_sequence == lowercase_spaced_form.cleaned_sequence == raw_form.cleaned_sequence

    hashes = {
        protein_feature_service.extract(fasta_form.cleaned_sequence).sequence_sha256,
        protein_feature_service.extract(lowercase_spaced_form.cleaned_sequence).sequence_sha256,
        protein_feature_service.extract(raw_form.cleaned_sequence).sequence_sha256,
    }
    assert len(hashes) == 1


# ── Milestone 1: charge_at_target_ph / target_ph ──────────────────────────────

def test_default_target_ph_is_neutral():
    features = protein_feature_service.extract("MKTAADDVKEEHHRR")

    assert features.target_ph == 7.0
    assert features.charge_at_target_ph is not None


def test_charge_changes_with_target_ph():
    sequence = "MKTAADDVKEEHHRR"  # mix of acidic (D/E) and basic (K/R/H) residues
    low_ph = protein_feature_service.extract(sequence, target_ph=2.0)
    high_ph = protein_feature_service.extract(sequence, target_ph=12.0)

    assert low_ph.charge_at_target_ph is not None
    assert high_ph.charge_at_target_ph is not None
    # At low pH the sequence should carry a more positive net charge than at high pH.
    assert low_ph.charge_at_target_ph > high_ph.charge_at_target_ph


# ── Milestone 1: ionizable residue counts/fractions ───────────────────────────

def test_ionizable_residue_counts_and_fractions():
    sequence = "DDEEHHKKRRAAAA"  # 2 each of D,E,H,K,R + 4 non-ionizable
    features = protein_feature_service.extract(sequence)

    assert features.ionizable_residue_counts == {"D": 2, "E": 2, "H": 2, "K": 2, "R": 2}
    length = len(sequence)
    for aa in "DEHKR":
        assert features.ionizable_residue_fractions[aa] == round(2 / length, 6)


# ── Milestone 1: fallback observability ───────────────────────────────────────

def test_method_field_reports_biopython_when_available():
    features = protein_feature_service.extract("MKTAADDVKEEHHRR")

    # Biopython is a declared dependency and is installed in this environment,
    # so the primary branch is expected to run and must be labeled accordingly.
    assert features.method == "biopython_protparam"
    assert features.instability_index is not None
    assert features.isoelectric_point is not None


def test_method_field_distinguishes_biopython_from_fallback(monkeypatch):
    """
    The fallback path must never claim to be biopython_protparam, and must not
    silently fabricate a charge_at_target_ph value it cannot actually compute.
    Forcing `sys.modules["Bio.SeqUtils.ProtParam"] = None` makes Python raise
    ImportError for that specific import without touching global import machinery.
    """
    import sys

    monkeypatch.setitem(sys.modules, "Bio.SeqUtils.ProtParam", None)

    features = protein_feature_service.extract("MKTAADDVKEEHHRR")

    assert features.method == "fallback_sequence_descriptors"
    assert features.instability_index is None
    assert features.isoelectric_point is None
    assert features.charge_at_target_ph is None
    assert any("fallback" in warning.lower() for warning in features.warnings)
