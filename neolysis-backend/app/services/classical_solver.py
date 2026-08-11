"""
Neolysis — Classical ILP Baseline Solver (PuLP)
==============================================

Formulates and solves the exact enzyme mutation selection problem as a Binary Integer Linear Program (BILP) using PuLP (CBC Solver):

    Maximize Z = sum_{p,s} (score_{p,s} - risk_{p,s}) * x_{p,s}

    Subject to:
      1. sum_{s} x_{p,s} = 1                    forall positions p (Exactly one choice per position)
      2. x_{p1,s1} + x_{p2,s2} <= 1            forall incompatible pairs
      3. sum_{s != WT} x_{p,s} <= max_mutations (Optional capacity constraint)

Measures pure solver computation time isolated from I/O and setup.
"""

import time
import pulp
from loguru import logger

from app.schemas.quantum_variant import SolverResult
from app.services.quantum.constants import CLASSICAL_SOLVER_NAME
from app.services.quantum.evaluator import evaluate_solver_result
from app.services.quantum_qubo import QuboFormulation


def solve_classical_ilp(qubo: QuboFormulation) -> SolverResult:
    """
    Solves the mutation selection problem using PuLP Integer Linear Programming (CBC solver).
    Returns SolverResult with pure solve time isolated from problem setup.
    """
    prob = pulp.LpProblem("Enzyme_Variant_ILP_Selection", pulp.LpMaximize)
    
    # 1. Define Binary Variables x_i
    pulp_vars = {}
    for i in range(qubo.num_vars):
        pulp_vars[i] = pulp.LpVariable(f"x_{i}", cat=pulp.LpBinary)
        
    # 2. Objective Function: Maximize sum_{i} (score - risk) * x_i
    obj_terms = []
    for i in range(qubo.num_vars):
        _, _, score, risk, _ = qubo.var_map[i]
        net_benefit = score - risk
        obj_terms.append(net_benefit * pulp_vars[i])
    prob += pulp.lpSum(obj_terms), "Total_Net_Benefit"

    # 3. Position Coverage Constraint: sum_{s in O_p} x_{p,s} == 1
    for pos in qubo.positions:
        pos_indices = [
            qubo.var_lookup[(pos.position_id, opt.substitution)]
            for opt in pos.options
        ]
        prob += (
            pulp.lpSum([pulp_vars[idx] for idx in pos_indices]) == 1,
            f"Coverage_Pos_{pos.position_id}",
        )

    # 4. Incompatible Pair Constraint: x_a + x_b <= 1
    for idx_pair, pair in enumerate(qubo.incompatible_pairs):
        key_a = (pair.pos_a, pair.sub_a)
        key_b = (pair.pos_b, pair.sub_b)
        if key_a in qubo.var_lookup and key_b in qubo.var_lookup:
            idx_a = qubo.var_lookup[key_a]
            idx_b = qubo.var_lookup[key_b]
            prob += (
                pulp_vars[idx_a] + pulp_vars[idx_b] <= 1,
                f"Incompatible_{idx_pair}",
            )

    # 5. Max Non-WT Mutations Constraint: sum_{non-WT} x_i <= max_mutations
    if qubo.max_mutations is not None:
        non_wt_indices = [
            i for i in range(qubo.num_vars) if not qubo.var_map[i][4]
        ]
        prob += (
            pulp.lpSum([pulp_vars[i] for i in non_wt_indices]) <= qubo.max_mutations,
            "Max_Mutations_Limit",
        )

    # 6. Execute pure solve step with timer
    start_t = time.perf_counter()
    # Suppress solver output logs
    solver = pulp.PULP_CBC_CMD(msg=False)
    prob.solve(solver)
    elapsed_ms = (time.perf_counter() - start_t) * 1000.0

    # 7. Extract bitstring result
    bit_chars = []
    for i in range(qubo.num_vars):
        val = pulp.value(pulp_vars[i])
        bit_chars.append("1" if val is not None and val > 0.5 else "0")
    bitstring = "".join(bit_chars)

    logger.info(f"Classical PuLP ILP solver complete in {elapsed_ms:.2f}ms. Bitstring: {bitstring}")

    return evaluate_solver_result(
        bitstring=bitstring,
        qubo=qubo,
        solver_name=CLASSICAL_SOLVER_NAME,
        solver_type="classical",
        solve_time_ms=elapsed_ms,
    )
