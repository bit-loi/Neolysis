import pytest
from app.schemas.quantum_variant import (
    QuantumVariantRankRequest,
    MutationPosition,
    MutationOption,
    IncompatiblePair,
)
from app.services.quantum_qubo import QuboFormulation
from app.services.quantum_solver import (
    solve_exact_qubo,
    solve_qaoa_qubo,
    verify_qaoa_correctness,
    evaluate_solver_result,
)
from app.services.classical_solver import solve_classical_ilp
from app.services.quantum_ranking_service import quantum_variant_ranking_service


@pytest.fixture
def sample_quantum_request():
    return QuantumVariantRankRequest(
        positions=[
            MutationPosition(
                position_id=1,
                position_name="Pos 142 (Loop Alpha)",
                options=[
                    MutationOption(substitution="WT", score_contribution=0.0, risk_penalty=0.0, is_wildtype=True),
                    MutationOption(substitution="A142V", score_contribution=0.85, risk_penalty=0.15, is_wildtype=False),
                    MutationOption(substitution="A142L", score_contribution=0.60, risk_penalty=0.10, is_wildtype=False),
                ],
            ),
            MutationPosition(
                position_id=2,
                position_name="Pos 205 (H-Bond Domain)",
                options=[
                    MutationOption(substitution="WT", score_contribution=0.0, risk_penalty=0.0, is_wildtype=True),
                    MutationOption(substitution="E205K", score_contribution=0.90, risk_penalty=0.20, is_wildtype=False),
                ],
            ),
            MutationPosition(
                position_id=3,
                position_name="Pos 310 (Hydrophobic Pocket)",
                options=[
                    MutationOption(substitution="WT", score_contribution=0.0, risk_penalty=0.0, is_wildtype=True),
                    MutationOption(substitution="I310F", score_contribution=0.75, risk_penalty=0.25, is_wildtype=False),
                ],
            ),
        ],
        incompatible_pairs=[
            IncompatiblePair(pos_a=1, sub_a="A142V", pos_b=3, sub_b="I310F", penalty_cost=15.0),
        ],
        max_mutations=2,
        coverage_penalty_weight=20.0,
        interaction_penalty_weight=15.0,
    )


def test_qubo_matrix_construction(sample_quantum_request):
    qubo = QuboFormulation(sample_quantum_request)
    assert qubo.num_vars == 7  # 3 + 2 + 2 = 7 qubits
    assert qubo.Q.shape == (7, 7)
    # QUBO matrix should be symmetric
    assert (qubo.Q == qubo.Q.T).all()


def test_verify_qaoa_correctness_check():
    check = verify_qaoa_correctness()
    assert check.test_case_qubits == 4
    assert isinstance(check.energy_match, bool)
    assert check.exact_qubo_energy <= check.qaoa_qubo_energy + 0.15
    assert check.check_time_ms >= 0


def test_pulp_classical_solver(sample_quantum_request):
    qubo = QuboFormulation(sample_quantum_request)
    result = solve_classical_ilp(qubo)
    assert result.solver_type == "classical"
    assert result.qubit_count == 7
    assert result.is_feasible is True
    assert result.honest_net_score > 0
    assert result.penalty_cost == 0.0


def test_honest_penalty_inclusion(sample_quantum_request):
    qubo = QuboFormulation(sample_quantum_request)
    # Invalid bitstring: all 1s (multiple options selected per position, incompatible pair violated)
    infeasible_bitstr = "1" * 7
    evaluated = evaluate_solver_result(
        bitstring=infeasible_bitstr,
        qubo=qubo,
        solver_name="Test Invalid Vector",
        solver_type="quantum",
        solve_time_ms=1.0,
    )
    assert evaluated.is_feasible is False
    assert len(evaluated.constraint_violations) > 0
    assert evaluated.penalty_cost > 0.0
    # honest_net_score = total_score - total_risk - penalty_cost
    expected_net = evaluated.total_property_score - evaluated.total_mutation_risk - evaluated.penalty_cost
    assert abs(evaluated.honest_net_score - expected_net) < 1e-4


@pytest.mark.asyncio
async def test_quantum_ranking_endpoint(client, sample_quantum_request):
    payload = sample_quantum_request.model_dump()
    response = await client.post("/api/v1/variants/quantum-rank", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "quantum_result" in data
    assert "classical_result" in data
    assert "correctness_check" in data
    assert data["quantum_result"]["solver_name"] == "Qiskit Aer SamplerV2 / Statevector QAOA"
    assert data["classical_result"]["solver_name"] == "PuLP Integer Linear Program (CBC)"
    assert data["correctness_check"]["test_case_qubits"] == 4
