from app.schemas.property import TargetConditions
from app.schemas.variant import VariantCandidate
from app.services.variant_ranking import variant_ranking_service


WILD_TYPE = (
    "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGEENFKALVLIAFAQYLQQCPFEDH"
    "VKLVNEVTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFL"
)


def test_ranked_variants_are_sorted_and_have_sequential_rank():
    result = variant_ranking_service.rank(
        wild_type_sequence=WILD_TYPE,
        variants=[
            VariantCandidate(variant_id="V1", mutations=["M1A"]),
            VariantCandidate(variant_id="V2", mutations=["K2R"]),
        ],
        target_conditions=TargetConditions(temperature_c=60, ph=10),
    )

    ranks = [item.rank for item in result.ranked_variants]
    assert ranks == list(range(1, len(ranks) + 1))
    scores = [item.predicted_fit_score for item in result.ranked_variants]
    assert scores == sorted(scores, reverse=True)


def test_signals_include_deltas_relative_to_wild_type():
    result = variant_ranking_service.rank(
        wild_type_sequence=WILD_TYPE,
        variants=[VariantCandidate(variant_id="V1", mutations=["M1A"])],
        target_conditions=TargetConditions(temperature_c=60, ph=10),
    )

    variant = result.ranked_variants[0]
    assert variant.signals is not None
    assert variant.signals.thermostability_delta is not None
    assert variant.signals.solubility_delta is not None
    assert variant.signals.ph_fit_delta is not None


def test_structure_dependent_signals_are_explicitly_unavailable_without_structure_context():
    """
    This endpoint receives no structure/backbone context, so active-site
    distance, ProteinMPNN compatibility, and structure prediction confidence
    must stay None with an explicit status rather than a fabricated value.
    """
    result = variant_ranking_service.rank(
        wild_type_sequence=WILD_TYPE,
        variants=[VariantCandidate(variant_id="V1", mutations=["M1A"])],
        target_conditions=TargetConditions(temperature_c=60, ph=10),
    )

    signals = result.ranked_variants[0].signals
    assert signals.active_site_distance_angstrom is None
    assert signals.proteinmpnn_compatibility is None
    assert signals.proteinmpnn_status == "not_available"
    assert signals.structure_prediction_confidence is None


def test_proteinmpnn_compatibility_field_is_never_called_ddg():
    """Guard against regressing the ProteinMPNN != \u0394\u0394G scientific correction."""
    from app.schemas.variant import VariantSignals

    fields = VariantSignals.model_fields.keys()
    assert "ddg" not in fields
    assert "predicted_ddg" not in fields
    assert "proteinmpnn_compatibility" in fields


def test_reasoning_mentions_active_site_overlap_when_supplied():
    result = variant_ranking_service.rank(
        wild_type_sequence=WILD_TYPE,
        variants=[VariantCandidate(variant_id="V1", mutations=["M1A"])],
        target_conditions=TargetConditions(temperature_c=60, ph=10),
        active_site_positions=[1],
    )

    variant = result.ranked_variants[0]
    assert any("active-site" in note.lower() for note in variant.reasoning)


def test_priority_label_does_not_claim_experimental_success():
    result = variant_ranking_service.rank(
        wild_type_sequence=WILD_TYPE,
        variants=[VariantCandidate(variant_id="V1", mutations=["M1A"])],
        target_conditions=TargetConditions(temperature_c=60, ph=10),
    )

    variant = result.ranked_variants[0]
    assert variant.wet_lab_priority in {"high", "medium", "low"}
    assert "prioritization scaffold" in variant.explanation
    assert "requires experimental validation" in variant.explanation


def test_limitations_disclose_missing_structure_signals():
    result = variant_ranking_service.rank(
        wild_type_sequence=WILD_TYPE,
        variants=[VariantCandidate(variant_id="V1", mutations=["M1A"])],
        target_conditions=TargetConditions(temperature_c=60, ph=10),
    )

    assert any("structure-dependent signals" in limitation.lower() for limitation in result.limitations)
