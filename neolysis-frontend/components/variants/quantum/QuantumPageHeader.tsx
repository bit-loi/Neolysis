import Link from 'next/link';
import { Sparkles } from 'lucide-react';

export function QuantumPageHeader() {
  return (
    <div className="overflow-hidden rounded-lg bg-slate-950 border border-indigo-500/30 p-8 shadow-2xl">
      <div className="space-y-4">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-500/30 bg-cyan-950/80 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-cyan-400">
            <Sparkles className="h-3.5 w-3.5" /> Quantum Optimization Demo
          </span>
          <span className="text-xs text-slate-400">QAOA vs Classical ILP Comparison</span>
        </div>

        <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
          Quantum-Optimized Enzyme Variant Selection
        </h1>

        <p className="max-w-3xl text-sm leading-relaxed text-slate-300 sm:text-base">
          Formulates multi-position enzyme mutation selection as a QUBO model, solves it
          using <strong className="text-cyan-300">QAOA via Qiskit Aer</strong>, verifies
          quantum correctness against an exact reference case, and compares the result
          against a <strong className="text-indigo-300">PuLP Classical ILP</strong> baseline.
        </p>

        <div className="flex flex-wrap items-center gap-4 pt-2">
          <Link
            href="/variants"
            className="flex items-center gap-1 text-xs font-medium text-cyan-400 transition hover:text-cyan-300"
          >
            Back to Heuristic Variant Ranking
          </Link>
          <span className="text-slate-600">|</span>
          <span className="text-xs text-slate-400">
            Local Simulation - Qiskit 2.5.1 - PuLP 3.3.2
          </span>
        </div>
      </div>
    </div>
  );
}
