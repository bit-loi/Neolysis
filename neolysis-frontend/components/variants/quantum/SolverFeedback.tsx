import { AlertTriangle, Clock, Cpu, ShieldCheck } from 'lucide-react';

import { CorrectnessCheck } from '@/lib/quantum';

export function SolverErrorAlert({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-500/50 bg-red-950/60 p-4 text-sm text-red-200">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-red-400" />
      <div>
        <strong className="font-semibold text-red-100">Solver Error:</strong> {message}
      </div>
    </div>
  );
}

export function SolverLoadingPanel() {
  return (
    <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/60 p-12 text-center">
      <div className="inline-block rounded-full border border-cyan-500/30 bg-cyan-950/50 p-4 text-cyan-400 animate-pulse">
        <Cpu className="h-8 w-8 animate-spin" />
      </div>
      <h3 className="text-lg font-medium text-white">Constructing QUBO & Executing Solvers</h3>
      <p className="mx-auto max-w-md text-xs text-slate-400">
        Running Qiskit Aer statevector QAOA parameter optimizer (COBYLA) and PuLP
        Integer Linear Programming solver.
      </p>
    </div>
  );
}

export function VerificationBanner({ check }: { check: CorrectnessCheck }) {
  const passed = check.energy_match;

  return (
    <div
      className={`rounded-lg border p-5 transition-all ${
        passed ? 'border-emerald-500/40 bg-emerald-950/30' : 'border-amber-500/40 bg-amber-950/30'
      }`}
    >
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div className="flex items-start gap-3">
          {passed ? (
            <ShieldCheck className="mt-0.5 h-6 w-6 shrink-0 text-emerald-400" />
          ) : (
            <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0 text-amber-400" />
          )}
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="text-sm font-semibold text-white">
                Automated QAOA Correctness Verification Check
              </h4>
              <span
                className={`rounded border px-2 py-0.5 text-[10px] font-bold ${
                  passed
                    ? 'border-emerald-500/40 bg-emerald-900 text-emerald-300'
                    : 'border-amber-500/40 bg-amber-900 text-amber-300'
                }`}
              >
                {passed ? 'VERIFIED PASSED' : 'ENERGY GAP WARNING'}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-300">
              Tested on {check.test_case_qubits}-qubit verification problem: Exact Ground
              Truth QUBO Energy ={' '}
              <strong className="font-mono text-white">{check.exact_qubo_energy.toFixed(4)}</strong>,
              QAOA Evaluated Energy ={' '}
              <strong className="font-mono text-cyan-300">{check.qaoa_qubo_energy.toFixed(4)}</strong>{' '}
              (Gap: {check.energy_gap_percent}%).
            </p>
          </div>
        </div>

        <div className="shrink-0 text-right">
          <span className="flex items-center gap-1 text-[11px] text-slate-400">
            <Clock className="h-3 w-3" /> Check time: {check.check_time_ms} ms
          </span>
        </div>
      </div>
    </div>
  );
}
