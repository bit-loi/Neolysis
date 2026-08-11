from typing import Dict, List, Tuple
from app.schemas.quantum_variant import SelectedMutation, SolverResult
from app.services.quantum_qubo import QuboFormulation


def evaluate_solver_result(
    bitstring: str,
    qubo: QuboFormulation,
    solver_name: str,
    solver_type: str,
    solve_time_ms: float,
) -> SolverResult:
    """
    Evaluates a binary decision vector bitstring and applies HONEST penalty accounting.
    If constraints are violated, penalty cost is added and subtracted from honest_net_score.
    """
    selected_mutations: List[SelectedMutation] = []
    total_score = 0.0
    total_risk = 0.0
    constraint_violations: List[str] = []
    penalty_cost = 0.0

    # 1. Inspect selected variables
    selected_by_pos: Dict[int, List[Tuple[str, float, float, bool]]] = {}
    non_wt_count = 0

    for idx, bit_char in enumerate(bitstring):
        if bit_char == "1":
            pos_id, sub, score, risk, is_wt = qubo.var_map[idx]
            pos_name = next(p.position_name for p in qubo.positions if p.position_id == pos_id)

            selected_mutations.append(
                SelectedMutation(
                    position_id=pos_id,
                    position_name=pos_name,
                    substitution=sub,
                    score_contribution=score,
                    risk_penalty=risk,
                    is_wildtype=is_wt,
                )
            )
            total_score += score
            total_risk += risk

            if not is_wt:
                non_wt_count += 1

            if pos_id not in selected_by_pos:
                selected_by_pos[pos_id] = []
            selected_by_pos[pos_id].append((sub, score, risk, is_wt))

    # 2. Position Coverage Constraint (Exactly 1 option selected per position)
    for pos in qubo.positions:
        count = len(selected_by_pos.get(pos.position_id, []))
        if count != 1:
            violation = (
                f"Position {pos.position_id} ({pos.position_name}) has {count} options selected (required: exactly 1)"
            )
            constraint_violations.append(violation)
            penalty_cost += qubo.cov_weight * abs(count - 1)

    # 3. Incompatible Pairs Constraint
    for pair in qubo.incompatible_pairs:
        key_a = (pair.pos_a, pair.sub_a)
        key_b = (pair.pos_b, pair.sub_b)
        if key_a in qubo.var_lookup and key_b in qubo.var_lookup:
            idx_a = qubo.var_lookup[key_a]
            idx_b = qubo.var_lookup[key_b]
            if bitstring[idx_a] == "1" and bitstring[idx_b] == "1":
                v_cost = pair.penalty_cost or qubo.int_weight
                violation = (
                    f"Incompatible pair selected: Pos {pair.pos_a} ({pair.sub_a}) and Pos {pair.pos_b} ({pair.sub_b})"
                )
                constraint_violations.append(violation)
                penalty_cost += v_cost

    # 4. Max Mutations Constraint
    if qubo.max_mutations is not None and non_wt_count > qubo.max_mutations:
        excess = non_wt_count - qubo.max_mutations
        pen = qubo.request.max_mutations_penalty_weight * excess
        constraint_violations.append(
            f"Selected {non_wt_count} mutations, exceeding maximum allowed limit of {qubo.max_mutations}"
        )
        penalty_cost += pen

    # Calculate honest net score
    honest_net_score = total_score - total_risk - penalty_cost
    qubo_energy = qubo.evaluate_bitstring(bitstring)
    is_feasible = (len(constraint_violations) == 0)

    return SolverResult(
        solver_name=solver_name,
        solver_type=solver_type,
        selected_mutations=selected_mutations,
        total_property_score=round(total_score, 4),
        total_mutation_risk=round(total_risk, 4),
        constraint_violations=constraint_violations,
        penalty_cost=round(penalty_cost, 4),
        honest_net_score=round(honest_net_score, 4),
        qubo_energy=round(qubo_energy, 4),
        solve_time_ms=round(solve_time_ms, 2),
        is_feasible=is_feasible,
        qubit_count=qubo.num_vars,
        bitstring=bitstring,
    )
