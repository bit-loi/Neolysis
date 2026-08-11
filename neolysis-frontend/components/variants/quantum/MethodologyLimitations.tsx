import { HelpCircle } from 'lucide-react';

export function MethodologyLimitations({ limitations }: { limitations: string[] }) {
  return (
    <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/80 p-6 text-sm leading-relaxed text-slate-300">
      <h3 className="flex items-center gap-2 text-lg font-bold text-white">
        <HelpCircle className="h-5 w-5 text-cyan-400" /> Portfolio Scope & Scientific Disclaimers
      </h3>

      <ul className="list-inside list-disc space-y-2 text-xs">
        {limitations.map((limitation) => (
          <li key={limitation} className="leading-relaxed">
            {limitation}
          </li>
        ))}
      </ul>

      <div className="rounded-lg border border-cyan-500/30 bg-cyan-950/30 p-4 text-xs text-cyan-200">
        <strong>Technical Summary:</strong> Classical exact ILP solvers (CBC/PuLP) execute
        quickly at this problem scale (8-16 qubits). QAOA serves as an algorithmic
        demonstration of quantum combinatorial optimization mapping, statevector parameter
        optimization, and penalty formulation in quantum computing.
      </div>
    </div>
  );
}
