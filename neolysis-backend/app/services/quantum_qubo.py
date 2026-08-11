"""
Neolysis — QUBO Formulation for Enzyme Variant Selection
=========================================================

Formulates candidate enzyme mutation combination selection as a Quadratic
Unconstrained Binary Optimization (QUBO) model:

    min E(x) = x^T Q x + constant

Binary Encoding:
    Each binary variable x_i represents selecting option s at position p.
    Index mapping: variable index i in [0, N-1] maps to (position_id, substitution).
    Total binary variables (qubits) N = sum_{positions} len(options).

Mathematical Terms:
    1. Linear Objective Term (Minimize -NetScore):
       To maximize (score - risk), the linear QUBO diagonal receives:
       Q_{i,i} += - (score_contribution - risk_penalty)

    2. Position Coverage Penalty (Exactly 1 option per position):
       Penalty: A * (sum_{s in O_p} x_{p,s} - 1)^2
       Expansion (using x^2 = x for x in {0,1}):
           = A * (- sum_{s in O_p} x_{p,s} + 2 * sum_{s < s'} x_{p,s} * x_{p,s'} + 1)
       - Diagonal Q_{i,i} += -A  for all options at position p
       - Off-diagonal Q_{i,j} += +2A for distinct options i, j at position p

    3. Incompatible Pair Penalty (Mutually exclusive mutations):
       Penalty: B * x_i * x_j  for incompatible pair (i, j)
       - Off-diagonal Q_{i,j} += +B

    4. Max Non-WT Mutations Soft Penalty:
       If sum_{non-WT} x_i > max_mutations, soft penalty applies in evaluation.
"""

from typing import List, Tuple, Dict, Any
import numpy as np

from app.schemas.quantum_variant import MutationPosition, IncompatiblePair, QuantumVariantRankRequest


class QuboFormulation:
    def __init__(self, request: QuantumVariantRankRequest):
        self.request = request
        self.positions = request.positions
        self.incompatible_pairs = request.incompatible_pairs
        self.max_mutations = request.max_mutations
        
        self.cov_weight = request.coverage_penalty_weight
        self.int_weight = request.interaction_penalty_weight
        
        # Build mapping index
        self.var_map: Dict[int, Tuple[int, str, float, float, bool]] = {}
        self.var_lookup: Dict[Tuple[int, str], int] = {}
        
        idx = 0
        for pos in self.positions:
            for opt in pos.options:
                self.var_map[idx] = (
                    pos.position_id,
                    opt.substitution,
                    opt.score_contribution,
                    opt.risk_penalty,
                    opt.is_wildtype,
                )
                self.var_lookup[(pos.position_id, opt.substitution)] = idx
                idx += 1
                
        self.num_vars = idx
        self.Q = np.zeros((self.num_vars, self.num_vars), dtype=float)
        self.constant_offset = 0.0
        
        self._build_qubo()

    def _build_qubo(self) -> None:
        """Construct the Q matrix (symmetric) and constant offset."""
        # 1. Linear Objective (Property Score vs Risk Penalty)
        for i in range(self.num_vars):
            pos_id, sub, score, risk, is_wt = self.var_map[i]
            net_benefit = score - risk
            self.Q[i, i] += -net_benefit

        # 2. Position Coverage Penalty: A * (sum_{s} x_{p,s} - 1)^2
        A = self.cov_weight
        for pos in self.positions:
            pos_indices = [
                self.var_lookup[(pos.position_id, opt.substitution)]
                for opt in pos.options
            ]
            # Diagonal terms: -A * x_i
            for idx in pos_indices:
                self.Q[idx, idx] += -A
            
            # Off-diagonal terms: +2A * x_i * x_j (symmetric: +A on each side)
            for i_idx in range(len(pos_indices)):
                for j_idx in range(i_idx + 1, len(pos_indices)):
                    idx_a = pos_indices[i_idx]
                    idx_b = pos_indices[j_idx]
                    self.Q[idx_a, idx_b] += A
                    self.Q[idx_b, idx_a] += A
                    
            # Constant offset per position: +A
            self.constant_offset += A

        # 3. Incompatible Pair Penalty: B * x_i * x_j
        for pair in self.incompatible_pairs:
            key_a = (pair.pos_a, pair.sub_a)
            key_b = (pair.pos_b, pair.sub_b)
            if key_a in self.var_lookup and key_b in self.var_lookup:
                idx_a = self.var_lookup[key_a]
                idx_b = self.var_lookup[key_b]
                b_weight = pair.penalty_cost or self.int_weight
                self.Q[idx_a, idx_b] += b_weight / 2.0
                self.Q[idx_b, idx_a] += b_weight / 2.0

    def evaluate_bitstring(self, bitstring: str) -> float:
        """Evaluate QUBO energy E(x) = x^T Q x + constant for a given bitstring."""
        x = np.array([int(b) for b in bitstring], dtype=float)
        return float(x.T @ self.Q @ x + self.constant_offset)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "num_qubits": self.num_vars,
            "matrix_shape": list(self.Q.shape),
            "coverage_penalty_weight": self.cov_weight,
            "interaction_penalty_weight": self.int_weight,
            "constant_offset": self.constant_offset,
            "variable_mapping": [
                {
                    "qubit_idx": i,
                    "position_id": self.var_map[i][0],
                    "substitution": self.var_map[i][1],
                    "score_contribution": self.var_map[i][2],
                    "risk_penalty": self.var_map[i][3],
                    "is_wildtype": self.var_map[i][4],
                }
                for i in range(self.num_vars)
            ],
        }
