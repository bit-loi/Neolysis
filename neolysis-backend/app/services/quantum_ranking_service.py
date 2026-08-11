"""
Neolysis — Quantum Variant Ranking Coordinator Service
======================================================

Coordinates:
  - QUBO Matrix Formulation
  - Automated Exact Verification Check against QAOA on 4-qubit test case
  - Quantum QAOA Solver execution (Qiskit Aer / Statevector)
  - Classical ILP Solver execution (PuLP)
  - Honest Penalty-Inclusive Side-by-Side Response Assembly
"""

from app.schemas.quantum_variant import (
    QuantumVariantRankRequest,
    QuantumVariantRankResponse,
)
from app.services.quantum.constants import QAOA_SOLVER_NAME, QUANTUM_VARIANT_LIMITATIONS
from app.services.quantum.evaluator import evaluate_solver_result
from app.services.quantum.qaoa_solver import solve_qaoa_qubo
from app.services.quantum.verification import verify_qaoa_correctness
from app.services.quantum_qubo import QuboFormulation
from app.services.classical_solver import solve_classical_ilp


class QuantumVariantRankingService:
    def rank_quantum_variants(self, request: QuantumVariantRankRequest) -> QuantumVariantRankResponse:
        # 1. Build QUBO Matrix
        qubo = QuboFormulation(request)
        
        # 2. Automated QAOA Correctness Check against exact solver on test case
        correctness_check = verify_qaoa_correctness()
        
        # 3. Quantum QAOA Solver
        q_bitstr, q_energy, q_time_ms = solve_qaoa_qubo(
            qubo,
            reps=request.qaoa_reps,
            max_iter=request.qaoa_max_iter,
            solver_name=QAOA_SOLVER_NAME,
        )
        quantum_result = evaluate_solver_result(
            bitstring=q_bitstr,
            qubo=qubo,
            solver_name=QAOA_SOLVER_NAME,
            solver_type="quantum",
            solve_time_ms=q_time_ms,
        )
        
        # 4. Classical ILP Solver (PuLP)
        classical_result = solve_classical_ilp(qubo)
        
        # 5. Assemble Problem Summary & Limitations
        problem_summary = {
            "num_positions": len(request.positions),
            "num_qubits": qubo.num_vars,
            "max_mutations_allowed": request.max_mutations,
            "num_incompatible_pairs": len(request.incompatible_pairs),
        }
        
        return QuantumVariantRankResponse(
            quantum_result=quantum_result,
            classical_result=classical_result,
            correctness_check=correctness_check,
            problem_summary=problem_summary,
            limitations=QUANTUM_VARIANT_LIMITATIONS,
        )


quantum_variant_ranking_service = QuantumVariantRankingService()
