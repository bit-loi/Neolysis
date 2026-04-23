import { DockingScore, ProteinTarget } from '@/lib/types';
import { formatDockingScore, getDockingScoreColor } from '@/lib/utils';

interface DockingScoreCardProps {
  dockingScore: DockingScore;
  target: ProteinTarget;
}

export function DockingScoreCard({ dockingScore, target }: DockingScoreCardProps) {
  const score = dockingScore.score;
  const normalizedScore = Math.min(Math.max((score + 10) / 7, 0), 1);
  const barColor = score <= -7 ? 'bg-emerald-500' : score <= -5 ? 'bg-amber-500' : 'bg-rose-500';

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Docking Score</h2>

      <div className="text-center mb-6">
        <div className={`text-5xl font-bold ${getDockingScoreColor(score)}`}>
          {formatDockingScore(score)}
        </div>
        <p className="text-sm text-gray-500 mt-2">AutoDock Vina binding affinity</p>
      </div>

      <div className="mb-6">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Weak (-3)</span>
          <span>Strong (-10)</span>
        </div>
        <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full ${barColor} transition-all`}
            style={{ width: `${normalizedScore * 100}%` }}
          />
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Target Protein</span>
          <span className="text-sm font-medium text-gray-900">{target.name}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Organism</span>
          <span className="text-sm font-medium text-gray-900">{target.organism}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-600">Computed</span>
          <span className="text-sm font-medium text-gray-900">{dockingScore.computedAt}</span>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          Pre-computed via AutoDock Vina. Binding site coordinates derived from PDB structure {target.pdbId}. 
          Scores represent predicted binding affinity; experimental validation required.
        </p>
      </div>
    </div>
  );
}
