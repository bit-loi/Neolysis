import { QuantumVariantRankRequest, QuantumVariantRankResponse } from '@/lib/quantum';

import { AssignmentTable } from './AssignmentTable';
import { SolverResultCard } from './SolverResultCard';

interface SolverComparisonProps {
  request: QuantumVariantRankRequest;
  result: QuantumVariantRankResponse;
}

export function SolverComparison({ request, result }: SolverComparisonProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SolverResultCard result={result.quantum_result} kind="quantum" />
        <SolverResultCard result={result.classical_result} kind="classical" />
      </div>

      <AssignmentTable request={request} result={result} />
    </div>
  );
}
