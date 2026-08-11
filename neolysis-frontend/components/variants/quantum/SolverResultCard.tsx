import { AlertTriangle, Clock, Cpu, Zap, type LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

import { SolverResult } from '@/lib/quantum';

type SolverKind = 'quantum' | 'classical';

const solverTheme: Record<
  SolverKind,
  {
    accent: string;
    border: string;
    icon: LucideIcon;
    scoreText: string;
    title: string;
  }
> = {
  quantum: {
    accent: 'text-cyan-400',
    border: 'border-cyan-500/40',
    icon: Cpu,
    scoreText: 'text-cyan-300',
    title: 'Quantum QAOA Solver',
  },
  classical: {
    accent: 'text-indigo-400',
    border: 'border-indigo-500/40',
    icon: Zap,
    scoreText: 'text-indigo-300',
    title: 'Classical ILP Solver',
  },
};

export function SolverResultCard({
  result,
  kind,
}: {
  result: SolverResult;
  kind: SolverKind;
}) {
  const theme = solverTheme[kind];
  const Icon = theme.icon;

  return (
    <div className={`space-y-5 rounded-lg border bg-slate-900/90 p-6 shadow-xl ${theme.border}`}>
      <div className="flex flex-col gap-4 border-b border-slate-800 pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Icon className={`h-5 w-5 ${theme.accent}`} />
            <h3 className="text-base font-bold text-white">{theme.title}</h3>
          </div>
          <p className={`mt-0.5 font-mono text-xs ${theme.accent}`}>{result.solver_name}</p>
        </div>
        <span
          className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${
            result.is_feasible
              ? 'border-emerald-500/40 bg-emerald-950 text-emerald-300'
              : 'border-amber-500/40 bg-amber-950 text-amber-300'
          }`}
        >
          {result.is_feasible ? 'FEASIBLE' : 'INFEASIBLE (Penalized)'}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 text-xs sm:grid-cols-2">
        <MetricTile label="Honest Net Score">
          <span className={`font-mono text-2xl font-extrabold ${theme.scoreText}`}>
            {result.honest_net_score.toFixed(3)}
          </span>
        </MetricTile>
        <MetricTile label="Pure Solve Time">
          <span className="flex items-center gap-1 font-mono text-2xl font-extrabold text-white">
            <Clock className={`h-4 w-4 ${theme.accent}`} />
            {result.solve_time_ms} <span className="text-xs text-slate-400">ms</span>
          </span>
        </MetricTile>
      </div>

      <div className="space-y-2 text-xs">
        <ScoreLine
          label="Property Score Contribution (+)"
          value={`+${result.total_property_score.toFixed(3)}`}
          valueClass="text-emerald-400 font-semibold"
        />
        <ScoreLine
          label="Mutation Risk Penalty (-)"
          value={`-${result.total_mutation_risk.toFixed(3)}`}
          valueClass="text-rose-400 font-semibold"
        />
        <ScoreLine
          label="Constraint Penalty Cost (-)"
          value={`-${result.penalty_cost.toFixed(3)}`}
          valueClass="text-amber-400 font-semibold"
        />
        <ScoreLine
          label="QUBO Objective Energy"
          value={result.qubo_energy.toFixed(3)}
          valueClass={theme.scoreText}
        />
        <div className="flex justify-between gap-4 py-1 text-slate-400">
          <span>{kind === 'quantum' ? 'Qubit Count / Vector Bitstring' : 'Binary Variables / Bitstring'}</span>
          <span className="text-right font-mono text-slate-300">
            {result.qubit_count} {kind === 'quantum' ? 'qubits' : 'vars'} - {result.bitstring}
          </span>
        </div>
      </div>

      {result.constraint_violations.length > 0 && (
        <div className="space-y-1 rounded-lg border border-amber-500/30 bg-amber-950/40 p-3 text-xs">
          <span className="flex items-center gap-1 font-semibold text-amber-300">
            <AlertTriangle className="h-3.5 w-3.5" /> Constraint Penalties Applied:
          </span>
          <ul className="list-inside list-disc space-y-0.5 text-[11px] text-amber-200">
            {result.constraint_violations.map((violation) => (
              <li key={violation}>{violation}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function MetricTile({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-800/50 p-3">
      <span className="mb-1 block text-slate-400">{label}</span>
      {children}
    </div>
  );
}

function ScoreLine({
  label,
  value,
  valueClass,
}: {
  label: string;
  value: string;
  valueClass: string;
}) {
  return (
    <div className="flex justify-between gap-4 border-b border-slate-800 py-1 text-slate-300">
      <span>{label}</span>
      <span className={`text-right font-mono ${valueClass}`}>{value}</span>
    </div>
  );
}
