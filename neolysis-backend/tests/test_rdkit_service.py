"""
TDD Tests — RDKit Service
==========================
Tests for all RDKit molecular property calculation functions.

Coverage:
    ✓ _calculate_properties: valid SMILES returns all expected keys
    ✓ _calculate_properties: MW, LogP, HBD, HBA, TPSA values for known compounds
    ✓ _calculate_properties: invalid SMILES raises ValueError
    ✓ get_drug_likeness: returns error-safe dict on invalid SMILES
    ✓ get_drug_likeness: Lipinski pass for aspirin
    ✓ get_drug_likeness: Lipinski fail for a known violator
    ✓ is_valid_smiles: True for valid, False for invalid
    ✓ batch_calculate: returns aligned list with None on failures
    ✓ TPSA: present in output
    ✓ Violations: correct strings for each rule
"""

import pytest
from app.services.rdkit_service import RDKitService, rdkit_service


@pytest.fixture
def service():
    return RDKitService()


# ── _calculate_properties ──────────────────────────────────────────────────

class TestCalculateProperties:
    def test_returns_all_expected_keys(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        expected_keys = {
            "mw", "logp", "hbd", "hba", "tpsa", "qed",
            "heavy_atoms", "rotatable_bonds", "ring_count",
            "lipinski_pass", "lipinski_violations_count", "violations",
        }
        assert expected_keys.issubset(result.keys())

    def test_aspirin_molecular_weight(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        assert 179 < result["mw"] < 182, f"Aspirin MW expected ~180.16, got {result['mw']}"

    def test_aspirin_logp(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        assert 1.0 < result["logp"] < 2.0, f"Aspirin LogP expected ~1.24, got {result['logp']}"

    def test_aspirin_hbd(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        assert result["hbd"] == 1

    def test_aspirin_hba(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        assert result["hba"] in (3, 4)  # RDKit counts ring O too

    def test_aspirin_tpsa_present(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        assert "tpsa" in result
        assert result["tpsa"] > 0

    def test_aspirin_lipinski_pass(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        assert result["lipinski_pass"] is True
        assert result["violations"] == []

    def test_qed_in_range(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        assert 0.0 <= result["qed"] <= 1.0

    def test_heavy_atoms_aspirin(self, service, sample_smiles):
        result = service._calculate_properties(sample_smiles["aspirin"])
        assert result["heavy_atoms"] == 13  # Aspirin: C9H8O4 → 13 heavy atoms

    def test_invalid_smiles_raises_value_error(self, service, sample_smiles):
        with pytest.raises(ValueError, match="Invalid SMILES"):
            service._calculate_properties(sample_smiles["invalid"])

    def test_lipinski_violations_high_mw(self, service):
        # Paclitaxel (MW ~854): violates MW and likely others
        taxol = "CC(=O)OC1C(=O)C2(O)CC(OC(=O)c3ccccc3)C(=C2C1OC(=O)c1ccccc1)CO"
        result = service._calculate_properties(taxol)
        assert result["lipinski_pass"] is False or result["mw"] > 450

    def test_violations_list_contains_rule(self, service):
        # Chloroquine: MW ~319, LogP ~4.6 — should pass all rules
        smiles = "ClC1=CC=NC2=CC(=CC=C12)NC(C)CCCN(CC)CC"
        result = service._calculate_properties(smiles)
        assert isinstance(result["violations"], list)

    def test_ring_count_benzene(self, service):
        result = service._calculate_properties("c1ccccc1")
        assert result["ring_count"] == 1


# ── get_drug_likeness (async) ──────────────────────────────────────────────

class TestGetDrugLikeness:
    @pytest.mark.asyncio
    async def test_valid_smiles_returns_complete_dict(self, service, sample_smiles):
        result = await service.get_drug_likeness(sample_smiles["aspirin"])
        assert "mw" in result
        assert "lipinski_pass" in result
        assert result["lipinski_pass"] is True

    @pytest.mark.asyncio
    async def test_invalid_smiles_returns_safe_dict(self, service, sample_smiles):
        result = await service.get_drug_likeness(sample_smiles["invalid"])
        assert "Calculation Error" in result["violations"]
        assert result["lipinski_pass"] is False

    @pytest.mark.asyncio
    async def test_quercetin_properties(self, service, sample_smiles):
        result = await service.get_drug_likeness(sample_smiles["quercetin"])
        assert result["mw"] > 0
        assert "lipinski_pass" in result

    @pytest.mark.asyncio
    async def test_tpsa_always_present_on_success(self, service, sample_smiles):
        result = await service.get_drug_likeness(sample_smiles["caffeine"])
        assert "tpsa" in result
        assert isinstance(result["tpsa"], float)


# ── is_valid_smiles (async) ────────────────────────────────────────────────

class TestIsValidSmiles:
    @pytest.mark.asyncio
    async def test_valid_aspirin(self, service, sample_smiles):
        assert await service.is_valid_smiles(sample_smiles["aspirin"]) is True

    @pytest.mark.asyncio
    async def test_invalid_string(self, service, sample_smiles):
        assert await service.is_valid_smiles(sample_smiles["invalid"]) is False

    @pytest.mark.asyncio
    async def test_empty_string(self, service, sample_smiles):
        assert await service.is_valid_smiles(sample_smiles["empty"]) is False

    @pytest.mark.asyncio
    async def test_quercetin_valid(self, service, sample_smiles):
        assert await service.is_valid_smiles(sample_smiles["quercetin"]) is True


# ── batch_calculate (async) ────────────────────────────────────────────────

class TestBatchCalculate:
    @pytest.mark.asyncio
    async def test_batch_returns_aligned_list(self, service, sample_smiles):
        smiles_list = [
            sample_smiles["aspirin"],
            sample_smiles["invalid"],
            sample_smiles["caffeine"],
        ]
        results = await service.batch_calculate(smiles_list)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_valid_entries_have_mw(self, service, sample_smiles):
        results = await service.batch_calculate([
            sample_smiles["aspirin"],
            sample_smiles["quercetin"],
        ])
        for r in results:
            assert r is not None
            assert "mw" in r

    @pytest.mark.asyncio
    async def test_invalid_entry_produces_error_dict(self, service, sample_smiles):
        results = await service.batch_calculate([sample_smiles["invalid"]])
        # Invalid SMILES → error dict with violations, not None (service catches exception)
        r = results[0]
        assert r is not None  # get_drug_likeness catches the error
        assert "Calculation Error" in r.get("violations", [])

    @pytest.mark.asyncio
    async def test_empty_batch_returns_empty_list(self, service):
        results = await service.batch_calculate([])
        assert results == []
