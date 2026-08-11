import { Layers } from 'lucide-react';

export function QuboExplanation() {
  return (
    <div className="space-y-6 rounded-lg border border-slate-800 bg-slate-900/80 p-6 text-sm leading-relaxed text-slate-300">
      <h3 className="flex items-center gap-2 text-lg font-bold text-white">
        <Layers className="h-5 w-5 text-cyan-400" /> QUBO Mathematical Mapping & Penalty Formulation
      </h3>

      <div className="space-y-4">
        <p>
          The Quadratic Unconstrained Binary Optimization (QUBO) model converts the
          multi-choice enzyme variant selection problem into minimizing a quadratic energy
          function over binary decision variables:
        </p>

        <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950 p-4 font-mono text-xs text-cyan-300">
          E(x) = x^T Q x + C = sum_i Q_ii x_i + sum_i,j 2 Q_ij x_i x_j + C
        </div>

        <div className="grid grid-cols-1 gap-4 pt-2 md:grid-cols-2">
          <QuboTerm
            title="1. Linear Terms (Property Benefit vs Risk)"
            body="For each position substitution choice x_p,s, the linear diagonal receives the negative net benefit."
            code="Q_ii += -(Score Contribution - Risk Penalty)"
          />
          <QuboTerm
            title="2. Coverage Penalty (1 Option Per Position)"
            body="Each residue position must select exactly one option, so missing or duplicate selections receive a coverage penalty."
            code="A * (sum_s x_p,s - 1)^2"
          />
          <QuboTerm
            title="3. Incompatible Pair Penalty"
            body="Unfavorable residue mutation combinations add a quadratic interaction penalty when both options are selected."
            code="+B * x_i * x_j"
          />
          <QuboTerm
            title="4. Honest Penalty Accounting"
            body="If QAOA outputs an infeasible bitstring, the response keeps the result visible and subtracts the penalty from net score."
            code="net = score - risk - penalty"
          />
        </div>
      </div>
    </div>
  );
}

function QuboTerm({ title, body, code }: { title: string; body: string; code: string }) {
  return (
    <div className="space-y-2 rounded-lg border border-slate-800 bg-slate-800/40 p-4">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-cyan-400">{title}</h4>
      <p className="text-xs">{body}</p>
      <code className="block rounded bg-slate-950 p-2 font-mono text-cyan-300">{code}</code>
    </div>
  );
}
