import { Layers, RefreshCw } from 'lucide-react';

import { PRESET_QUANTUM_SCENARIOS, PresetScenario } from '@/lib/quantum';

interface PresetSelectorProps {
  loading: boolean;
  selectedPreset: PresetScenario;
  onRunOptimization: () => void;
  onSelectPreset: (preset: PresetScenario) => void;
}

export function PresetSelector({
  loading,
  selectedPreset,
  onRunOptimization,
  onSelectPreset,
}: PresetSelectorProps) {
  return (
    <div className="space-y-4 rounded-lg border border-slate-800 bg-slate-900/80 p-6 shadow-lg backdrop-blur-md">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
          <Layers className="h-5 w-5 text-cyan-400" /> Select Enzyme Scenario Preset
        </h2>
        <button
          onClick={onRunOptimization}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-white shadow-md transition hover:bg-cyan-400 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Solving QUBO...' : 'Re-Run Solvers'}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {PRESET_QUANTUM_SCENARIOS.map((preset) => (
          <PresetCard
            key={preset.id}
            preset={preset}
            selected={selectedPreset.id === preset.id}
            onClick={() => onSelectPreset(preset)}
          />
        ))}
      </div>
    </div>
  );
}

function PresetCard({
  preset,
  selected,
  onClick,
}: {
  preset: PresetScenario;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-lg border p-4 text-left transition-all duration-200 ${
        selected
          ? 'border-cyan-500/60 bg-cyan-950/40 shadow-lg shadow-cyan-500/10'
          : 'border-slate-800 bg-slate-800/40 hover:border-slate-700 hover:bg-slate-800/60'
      }`}
    >
      <div className="mb-1 flex items-center justify-between gap-3">
        <span className="text-xs font-medium text-cyan-400">{preset.target_enzyme}</span>
        <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] text-slate-400">
          {preset.request.positions.length} positions
        </span>
      </div>
      <h3 className="mb-1 text-sm font-semibold text-white">{preset.name}</h3>
      <p className="line-clamp-2 text-xs leading-relaxed text-slate-400">{preset.description}</p>
    </button>
  );
}
