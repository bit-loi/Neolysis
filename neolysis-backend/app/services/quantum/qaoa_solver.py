import time
from typing import Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize

from app.services.quantum.constants import QAOA_SOLVER_NAME
from app.services.quantum_qubo import QuboFormulation


def construct_qaoa_circuit(
    qubo: QuboFormulation,
    gamma: float,
    beta: float,
) -> QuantumCircuit:
    """
    Build a 1-layer QAOA quantum circuit for the target QUBO.
    """
    n = qubo.num_vars
    qc = QuantumCircuit(n)

    for i in range(n):
        qc.h(i)

    for i in range(n):
        diag_val = qubo.Q[i, i]
        if abs(diag_val) > 1e-8:
            qc.rz(gamma * diag_val, i)

    for i in range(n):
        for j in range(i + 1, n):
            weight = qubo.Q[i, j] + qubo.Q[j, i]
            if abs(weight) > 1e-8:
                qc.rzz(gamma * weight / 2.0, i, j)

    for i in range(n):
        qc.rx(2.0 * beta, i)

    return qc


def solve_qaoa_qubo(
    qubo: QuboFormulation,
    reps: int = 1,
    max_iter: int = 50,
    solver_name: str = QAOA_SOLVER_NAME,
) -> Tuple[str, float, float]:
    """
    QAOA solver using Qiskit statevector simulation and COBYLA parameter optimizer.
    Returns: (best_bitstring, qubo_energy, solve_time_ms)
    """
    start_t = time.perf_counter()

    def objective_function(params: np.ndarray) -> float:
        gamma, beta = params[0], params[1]
        qc = construct_qaoa_circuit(qubo, gamma, beta)
        statevector = Statevector.from_instruction(qc)
        probabilities = statevector.probabilities_dict()

        exp_energy = 0.0
        for bitstr_reversed, probability in probabilities.items():
            bitstring = bitstr_reversed[::-1]
            exp_energy += probability * qubo.evaluate_bitstring(bitstring)
        return exp_energy

    init_params = np.array([0.5, 0.5])
    result = minimize(
        objective_function,
        init_params,
        method="COBYLA",
        options={"maxiter": max_iter, "tol": 1e-3},
    )

    opt_gamma, opt_beta = result.x[0], result.x[1]
    opt_circuit = construct_qaoa_circuit(qubo, opt_gamma, opt_beta)
    final_statevector = Statevector.from_instruction(opt_circuit)
    probabilities = final_statevector.probabilities_dict()

    best_bitstring = "0" * qubo.num_vars
    best_energy = float("inf")

    for bitstr_reversed in probabilities.keys():
        bitstring = bitstr_reversed[::-1]
        energy = qubo.evaluate_bitstring(bitstring)
        if energy < best_energy:
            best_energy = energy
            best_bitstring = bitstring

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
    return best_bitstring, best_energy, elapsed_ms
