import { AlertTriangle, CheckCircle2 } from 'lucide-react';

import { QuantumVariantRankRequest, QuantumVariantRankResponse } from '@/lib/quantum';

interface AssignmentTableProps {
  request: QuantumVariantRankRequest;
  result: QuantumVariantRankResponse;
}

export function AssignmentTable({ request, result }: AssignmentTableProps) {
  return (
    <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/80 p-6">
      <h3 className="flex items-center gap-2 text-base font-semibold text-white">
        <CheckCircle2 className="h-5 w-5 text-cyan-400" /> Position Mutation Assignment Breakdown
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="border-b border-slate-800 font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-3">Position</th>
              <th className="px-4 py-3">Quantum Choice (QAOA)</th>
              <th className="px-4 py-3">Classical Choice (PuLP)</th>
              <th className="px-4 py-3">Match Status</th>
              <th className="px-4 py-3 text-right">Score Benefit</th>
              <th className="px-4 py-3 text-right">Risk Penalty</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-slate-200">
            {request.positions.map((position) => {
              const quantumMutation = result.quantum_result.selected_mutations.find(
                (mutation) => mutation.position_id === position.position_id
              );
              const classicalMutation = result.classical_result.selected_mutations.find(
                (mutation) => mutation.position_id === position.position_id
              );
              const isMatch = quantumMutation?.substitution === classicalMutation?.substitution;

              return (
                <tr key={position.position_id} className="transition hover:bg-slate-800/30">
                  <td className="px-4 py-3 font-sans font-medium text-white">
                    {position.position_name}
                  </td>
                  <td className="px-4 py-3">
                    <MutationPill mutation={quantumMutation?.substitution} isWildtype={quantumMutation?.is_wildtype} />
                  </td>
                  <td className="px-4 py-3">
                    <MutationPill
                      mutation={classicalMutation?.substitution}
                      isWildtype={classicalMutation?.is_wildtype}
                      className="border-indigo-500/30 bg-indigo-950 text-indigo-300"
                    />
                  </td>
                  <td className="px-4 py-3 font-sans">
                    {isMatch ? (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Identical
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[11px] font-semibold text-amber-400">
                        <AlertTriangle className="h-3.5 w-3.5" /> Divergent
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right text-emerald-400">
                    +{(classicalMutation?.score_contribution ?? 0).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-right text-rose-400">
                    -{(classicalMutation?.risk_penalty ?? 0).toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MutationPill({
  mutation,
  isWildtype,
  className = 'border-cyan-500/30 bg-cyan-950 text-cyan-300',
}: {
  mutation?: string;
  isWildtype?: boolean;
  className?: string;
}) {
  const wildtypeClass = 'bg-slate-800 text-slate-400';

  return (
    <span
      className={`rounded px-2 py-0.5 font-bold ${
        isWildtype ? wildtypeClass : `border ${className}`
      }`}
    >
      {mutation ?? 'UNASSIGNED'}
    </span>
  );
}
