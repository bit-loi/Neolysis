"""
Backward-compatible quantum solver facade.

New code should import from app.services.quantum.* modules directly.
"""

from app.services.quantum.evaluator import evaluate_solver_result
from app.services.quantum.exact_solver import solve_exact_qubo
from app.services.quantum.qaoa_solver import construct_qaoa_circuit, solve_qaoa_qubo
from app.services.quantum.verification import verify_qaoa_correctness

__all__ = [
    "construct_qaoa_circuit",
    "evaluate_solver_result",
    "solve_exact_qubo",
    "solve_qaoa_qubo",
    "verify_qaoa_correctness",
]
