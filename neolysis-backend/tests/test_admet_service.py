"""
TDD Tests — ADMET Service
==========================
Tests for the ADMET prediction service risk normalization and pipeline.
"""

import pytest
from app.services.admet_service import ADMETService, _get_risk


@pytest.fixture
def service():
    return ADMETService()


class TestGetRisk:
    def test_caco2_low(self): assert _get_risk("caco2", -5.0) == "low"
    def test_caco2_medium(self): assert _get_risk("caco2", -5.5) == "medium"
    def test_caco2_high(self): assert _get_risk("caco2", -6.5) == "high"
    def test_herg_low(self): assert _get_risk("herg", 15.0) == "low"
    def test_herg_medium(self): assert _get_risk("herg", 5.0) == "medium"
    def test_herg_high(self): assert _get_risk("herg", 0.5) == "high"
    def test_dili_low(self): assert _get_risk("dili", 0.1) == "low"
    def test_dili_medium(self): assert _get_risk("dili", 0.45) == "medium"
    def test_dili_high(self): assert _get_risk("dili", 0.8) == "high"
    def test_bbb_low(self): assert _get_risk("bbb", 0.2) == "low"
    def test_bbb_high(self): assert _get_risk("bbb", 0.9) == "high"
    def test_lipophilicity_low(self): assert _get_risk("lipophilicity", 2.0) == "low"
    def test_lipophilicity_medium(self): assert _get_risk("lipophilicity", 4.0) == "medium"
    def test_lipophilicity_high(self): assert _get_risk("lipophilicity", 6.0) == "high"

    def test_all_return_valid_strings(self):
        for prop, val in [("caco2", -5.0), ("herg", 10.0), ("dili", 0.1), ("bbb", 0.2), ("lipophilicity", 2.0)]:
            assert _get_risk(prop, val) in ("low", "medium", "high")


class TestADMETPredict:
    @pytest.mark.asyncio
    async def test_returns_five_properties(self, service, sample_smiles):
        result = await service.predict(sample_smiles["aspirin"])
        for prop in ("caco2", "herg", "dili", "bbb", "lipophilicity"):
            assert prop in result

    @pytest.mark.asyncio
    async def test_each_property_has_required_keys(self, service, sample_smiles):
        result = await service.predict(sample_smiles["aspirin"])
        for prop in ("caco2", "herg", "dili", "bbb", "lipophilicity"):
            assert "value" in result[prop]
            assert "risk_level" in result[prop]
            assert "description" in result[prop]

    @pytest.mark.asyncio
    async def test_risk_levels_valid(self, service, sample_smiles):
        result = await service.predict(sample_smiles["aspirin"])
        for prop in ("caco2", "herg", "dili", "bbb", "lipophilicity"):
            assert result[prop]["risk_level"] in ("low", "medium", "high")

    @pytest.mark.asyncio
    async def test_includes_drug_likeness(self, service, sample_smiles):
        result = await service.predict(sample_smiles["aspirin"])
        assert "drug_likeness" in result
        assert "mw" in result["drug_likeness"]

    @pytest.mark.asyncio
    async def test_invalid_smiles_raises(self, service, sample_smiles):
        with pytest.raises(Exception):
            await service.predict(sample_smiles["invalid"])

    @pytest.mark.asyncio
    async def test_values_are_floats(self, service, sample_smiles):
        result = await service.predict(sample_smiles["caffeine"])
        for prop in ("caco2", "herg", "dili", "bbb", "lipophilicity"):
            assert isinstance(result[prop]["value"], float)

    @pytest.mark.asyncio
    async def test_fallback_warning_present_when_tdc_unavailable(self, service, sample_smiles):
        result = await service.predict(sample_smiles["aspirin"])
        if result.get("_fallback_used"):
            assert "_warning" in result
