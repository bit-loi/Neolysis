import time

from loguru import logger

from app.schemas.quantum_variant import (
    CorrectnessCheck,
    MutationOption,
    MutationPosition,
    QuantumVariantRankRequest,
)
from app.services.quantum.exact_solver import solve_exact_qubo
from app.services.quantum.qaoa_solver import solve_qaoa_qubo
from app.services.quantum_qubo import QuboFormulation


def build_correctness_fixture() -> QuantumVariantRankRequest:
    return QuantumVariantRankRequest(
        positions=[
            MutationPosition(
                position_id=1,
                position_name="Test Pos 1",
                options=[
                    MutationOption(
                        substitution="WT",
                        score_contribution=0.0,
                        risk_penalty=0.0,
                        is_wildtype=True,
                    ),
                    MutationOption(
                        substitution="A50V",
                        score_contribution=0.8,
                        risk_penalty=0.2,
                        is_wildtype=False,
                    ),
                ],
            ),
            MutationPosition(
                position_id=2,
                position_name="Test Pos 2",
                options=[
                    MutationOption(
                        substitution="WT",
                        score_contribution=0.0,
                        risk_penalty=0.0,
                        is_wildtype=True,
                    ),
                    MutationOption(
                        substitution="E100K",
                        score_contribution=0.6,
                        risk_penalty=0.1,
                        is_wildtype=False,
                    ),
                ],
            ),
        ],
        coverage_penalty_weight=15.0,
        interaction_penalty_weight=10.0,
        qaoa_reps=1,
        qaoa_max_iter=50,
    )


def verify_qaoa_correctness() -> CorrectnessCheck:
    """
    Run a tiny 4-qubit QUBO through exact and QAOA solvers and compare energies.
    """
    start_t = time.perf_counter()
    qubo = QuboFormulation(build_correctness_fixture())

    exact_bitstring, exact_energy, _ = solve_exact_qubo(qubo)
    qaoa_bitstring, qaoa_energy, _ = solve_qaoa_qubo(qubo, reps=1, max_iter=50)

    energy_diff = abs(qaoa_energy - exact_energy)
    denom = abs(exact_energy) if abs(exact_energy) > 1e-6 else 1.0
    gap_pct = (energy_diff / denom) * 100.0
    is_match = energy_diff <= 0.15 or gap_pct <= 5.0
    elapsed_ms = (time.perf_counter() - start_t) * 1000.0

    log_msg = (
        f"Correctness Verification (4 qubits): Exact Energy = {exact_energy:.4f} ({exact_bitstring}), "
        f"QAOA Energy = {qaoa_energy:.4f} ({qaoa_bitstring}), Energy Gap = {gap_pct:.2f}%, Match = {is_match}"
    )
    logger.info(log_msg)

    return CorrectnessCheck(
        test_case_qubits=4,
        exact_qubo_energy=exact_energy,
        qaoa_qubo_energy=qaoa_energy,
        energy_match=is_match,
        energy_gap_percent=round(gap_pct, 2),
        check_time_ms=round(elapsed_ms, 2),
        verification_log=log_msg,
    )
