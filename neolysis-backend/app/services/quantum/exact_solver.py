import time
from typing import Tuple

from app.services.quantum_qubo import QuboFormulation


def solve_exact_qubo(qubo: QuboFormulation) -> Tuple[str, float, float]:
    """
    Exact classical ground-truth solver using brute-force enumeration over 2^N space.
    Returns: (best_bitstring, min_qubo_energy, solve_time_ms)
    """
    start_t = time.perf_counter()
    num_states = 1 << qubo.num_vars

    best_energy = float("inf")
    best_bitstring = "0" * qubo.num_vars

    for i in range(num_states):
        bitstring = format(i, f"0{qubo.num_vars}b")
        energy = qubo.evaluate_bitstring(bitstring)
        if energy < best_energy:
            best_energy = energy
            best_bitstring = bitstring

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
    return best_bitstring, best_energy, elapsed_ms
