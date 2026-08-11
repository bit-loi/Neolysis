import Link from 'next/link';
import { Cpu, Sparkles } from 'lucide-react';

export function VariantRankingHeader() {
  return (
    <div className="mb-10 max-w-3xl">
      <p className="text-sm font-medium uppercase tracking-[0.2em] text-[#5BA8B9]">
        Variant Ranking
      </p>
      <h1 className="mt-3 font-serif text-4xl font-bold tracking-tight sm:text-5xl">
        Prioritize candidate variants
      </h1>
      <p className="mt-4 text-lg leading-relaxed text-gray-700">
        Compare mutation candidates against industrial conditions with baseline fit and risk scoring.
      </p>

      <div className="mt-6 flex flex-col justify-between gap-4 rounded-lg border border-cyan-800/30 bg-[#0d162d] p-5 text-white shadow-md sm:flex-row sm:items-center">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-cyan-400">
            <Sparkles className="h-4 w-4" /> Quantum Optimization Available
          </div>
          <h3 className="text-base font-semibold">Combinatorial QUBO & QAOA Solver</h3>
          <p className="text-xs text-gray-300">
            Explore quantum-optimized multi-position mutation combination selection (QAOA vs Classical ILP).
          </p>
        </div>
        <Link
          href="/variants/quantum"
          className="inline-flex shrink-0 items-center gap-2 rounded bg-cyan-500 px-4 py-2 text-xs font-semibold text-white shadow transition hover:bg-cyan-400"
        >
          <Cpu className="h-4 w-4" /> Try Quantum Rank
        </Link>
      </div>
    </div>
  );
}
